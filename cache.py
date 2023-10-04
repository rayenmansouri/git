import os
from util import get_gitdir_path
import math
from exc import CacheFileNotFound
#change
class CacheEntry(object):
    def __init__(self,ctime=None,mtime=None,dev=None,
                 ino=None,mode_type=None,mode_perms=None,
                 uid=None,gid=None,fsize=None,sha=None,
                 flag_assume_valid=None,flag_stage=None,name=None):
        self.ctime = ctime
        self.mtime = mtime
        self.dev = dev
        self.ino = ino
        self.mode_type = mode_type
        self.mode_perms = mode_perms
        self.uid = uid
        self.gid = gid
        self.fsize = fsize
        self.sha = sha
        self.flag_assume_valid = flag_assume_valid
        self.flag_stage = flag_stage
        self.name = name
    def print_entry(self):
        print("ctime :",self.ctime)
        print("dev :",self.dev)
        print("ino :",self.ino)
        print("ctime :",self.ctime)

        
class Cache(object):
    entries = []
    version = 2
    def __init__(self,version=2,entries=None):
        if entries is None:
            entries = []
        self.version = version
        self.entries = entries

    def save(self,directory_cache = os.path.join(get_gitdir_path() or "",'.git/index')):
        self.entries.sort(key=lambda e:e.name)
        with open(directory_cache,"wb") as f:
            f.write(b"DIRC")
            f.write(self.version.to_bytes(4, "big"))
            f.write(len(self.entries).to_bytes(4, "big"))
            idx = 0
            for e in self.entries:
                f.write(e.ctime[0].to_bytes(4, "big"))
                f.write(e.ctime[1].to_bytes(4, "big"))
                f.write(e.mtime[0].to_bytes(4, "big"))
                f.write(e.mtime[1].to_bytes(4, "big"))
                f.write(e.dev.to_bytes(4, "big"))
                f.write(e.ino.to_bytes(4, "big"))
                mode = (e.mode_type << 12) | e.mode_perms
                f.write(mode.to_bytes(4, "big"))

                f.write(e.uid.to_bytes(4, "big"))
                f.write(e.gid.to_bytes(4, "big"))
                f.write(e.fsize.to_bytes(4, "big"))
                # @FIXME Convert back to int.
                f.write(int(e.sha, 16).to_bytes(20, "big"))
                flag_assume_valid = 0x1 << 15 if e.flag_assume_valid else 0
                name_bytes = e.name.encode("utf8")
                bytes_len = len(name_bytes)
                if bytes_len >= 0xFFF:
                    name_length = 0xFFF
                else:
                    name_length = bytes_len
                f.write((flag_assume_valid | e.flag_stage | name_length).to_bytes(2, "big"))
                f.write(name_bytes)
                f.write((0).to_bytes(1, "big"))

                idx += 62 + len(name_bytes) + 1

                # Add padding if necessary.
                if idx % 8 != 0:
                    pad = 8 - (idx % 8)
                    f.write((0).to_bytes(pad, "big"))
                    idx += pad

    def read(self,cache_directory = ".git/index"):
        try:
            with open(cache_directory,"rb") as f:
                raw = f.read()
        except FileNotFoundError:
            return []
            
        header = raw[:12]
        signature = header[:4]
        assert signature == b"DIRC"
        version = int.from_bytes(header[4:8],"big")
        assert version == 2
        count = int.from_bytes(header[8:],"big")
        entries = []
        content = raw[12:]
        idx = 0
        for i in range(count):
            ctime_s =  int.from_bytes(content[idx: idx+4], "big")
            ctime_ns = int.from_bytes(content[idx+4: idx+8], "big")
            mtime_s = int.from_bytes(content[idx+8: idx+12], "big")
            mtime_ns = int.from_bytes(content[idx+12: idx+16], "big")
            dev = int.from_bytes(content[idx+16: idx+20], "big")
            ino = int.from_bytes(content[idx+20: idx+24], "big")
            unused = int.from_bytes(content[idx+24: idx+26], "big")
            assert 0 == unused
            mode = int.from_bytes(content[idx+26: idx+28], "big")
            mode_type = mode >> 12
            assert mode_type in [0b1000, 0b1010, 0b1110]
            mode_perms = mode & 0b0000000111111111
            uid = int.from_bytes(content[idx+28: idx+32], "big")
            gid = int.from_bytes(content[idx+32: idx+36], "big")
            fsize = int.from_bytes(content[idx+36: idx+40], "big")
            sha = format(int.from_bytes(content[idx+40: idx+60], "big"), "040x")
            flags = int.from_bytes(content[idx+60: idx+62], "big")
            flag_assume_valid = (flags & 0b1000000000000000) != 0
            flag_extended = (flags & 0b0100000000000000) != 0
            assert not flag_extended
            flag_stage =  flags & 0b0011000000000000
            # Length of the name.  This is stored on 12 bits, some max
            # value is 0xFFF, 4095.  Since names can occasionally go
            # beyond that length, git treats 0xFFF as meaning at least
            # 0xFFF, and looks for the final 0x00 to find the end of the
            # name --- at a small, and probably very rare, performance
            # cost.
            name_length = flags & 0b0000111111111111
            # We've read 62 bytes so far.
            idx += 62
            if name_length < 0xFFF:
                assert content[idx + name_length] == 0x00
                raw_name = content[idx:idx+name_length]
                idx += name_length + 1
            else:
                print("Notice: Name is 0x{:X} bytes long.".format(name_length))
                # This probably wasn't tested enough.  It works with a
                # path of exactly 0xFFF bytes.  Any extra bytes broke
                # something between git, my shell and my filesystem.
                null_idx = content.find(b'\x00', idx + 0xFFF)
                raw_name = content[idx: null_idx]
                idx = null_idx + 1
            # Just parse the name as utf8.
            name = raw_name.decode("utf8")
            # Data is padded on multiples of eight bytes for pointer
            # alignment, so we skip as many bytes as we need for the next
            # read to start at the right position.
            idx = 8 * math.ceil(idx / 8)
            entries.append(CacheEntry(ctime=(ctime_s, ctime_ns),
                                     mtime=(mtime_s,  mtime_ns),
                                     dev=dev,
                                     ino=ino,
                                     mode_type=mode_type,
                                     mode_perms=mode_perms,
                                     uid=uid,
                                     gid=gid,
                                     fsize=fsize,
                                     sha=sha,
                                     flag_assume_valid=flag_assume_valid,
                                     flag_stage=flag_stage,
                                     name=name))
        self.entries = entries
        self.version = version
        return entries
    
    def add(self,entry):
        index = self.find(entry.name)
        if index > -1:
            self.entries[index] = entry
        else:
            self.entries.append(entry)

    def find(self,path):
        for i in range(len(self.entries)):
            if self.entries[i].name.startswith(path):
                return i
        return -1
    
    def remove(self,path):
        index = self.find(path)
        if index > -1:
            self.entries.pop(index)
        else:
           raise CacheFileNotFound("File not found "+ path)
        
    def tree_format(self):
        entries = self.entries
        tree = {}
        for entry in entries:
            dname =  os.path.dirname(entry.name).split("/")
            node = tree
            for sub_path in dname:
                if not sub_path:
                    break
                if not sub_path in node:
                    node[sub_path] = {"type":"tree","entries":{}}
                node = node[sub_path]["entries"]
            node[entry.name] = {
                "type":"blob",
                "entry":{
                    "mode":"{:02o}{:04o}".format(entry.mode_type, entry.mode_perms),
                    "name":entry.name,
                    "sha":entry.sha
                }
            }
        return tree

