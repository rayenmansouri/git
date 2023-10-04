import os
import hashlib
from .base import GenericObject,parse_objcet

class Tree(GenericObject):
    def serialize(self, deserialized):
        data = b""
        for key,value in deserialized.items():
            if value["type"] == "blob":
                entry = value["entry"]
                data += entry["mode"].encode()
                data += b" "
                data += os.path.basename(entry["name"]).encode("utf8")
                data += b"\x00"
                sha = int(entry["sha"], 16)
                data += sha.to_bytes(20,byteorder="big")
            else:
                sha = Tree(value["entries"]).sha1
                data += b"40000"
                data += b" "
                data += os.path.basename(key).encode("utf8")
                data += b"\0"
                sha = int(sha, 16)
                data += sha.to_bytes(20,byteorder="big")

        self.serialized = f"tree {len(data)}\0".encode() + data
        self.sha1 = hashlib.sha1(self.serialized).hexdigest()
        self.save()
        return self.sha1
    
    def deserialize(self, serialized):
        parsed = parse_objcet(serialized)
        if parsed["fmt"] != "tree":
            raise Exception(f"Object with hash {self.sha1} is not a blob object")
        self.deserialized = self.parse_tree(parsed["data"])

    def parse_tree(self,bin):
        parsed = {}
        #find mode
        while bin:
            null_index = bin.find(b"\0")
            first_part = bin[:null_index]
            sha = bin[null_index+1:null_index+21].hex()
            bin = bin[null_index+21:]
            parts = first_part.split(b" ")
            name = parts[1].decode()
            mode = parts[0].decode()           
            if mode.startswith("4"):
                t = Tree(sha)
                parsed[name] = {
                    "type":"tree",
                    "sha":sha,
                    "mode":mode,
                    "entries":t.deserialized
                }
            else:
                parsed[name] = {
                    "type":"blob",
                    "entry":{
                        "name":name,
                        "mode":mode,
                        "sha":sha
                    }
                }
        return parsed
    
    def flat(self,root = ""):
        entries = {}
        if self.deserialized:
            for key,value in self.deserialized.items():
                if value["type"] == "tree":
                    t = Tree(value["sha"])
                    entries.update(t.flat(os.path.join(root,key)))
                else:
                    entries[os.path.join(root,key)] = {
                        "name":os.path.join(root,key),
                        "mode":value["entry"]["name"],
                        "sha":value["entry"]["sha"]
                    }
        return entries
    def get_content(self):
        ret = ""
        for key,value in self.deserialized.items():
            if value["type"] == "blob":
                entry = value["entry"]
                name = entry["name"]
                mode = entry["mode"]
                sha = entry["sha"]
                ret += f"{mode} blob {sha}    {name}\n"
            else:
                name = key
                mode = value["mode"]
                sha = value["sha"]
                ret += f"0{mode} tree {sha}    {name}\n"

        return ret[:-1]


