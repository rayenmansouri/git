"""
    objects are at the core of git
    this file represent an abstraction to interact with opbject
    object do few things:
        - serialize itself to proper binary structure
        - deserialize itself from binary structure to the parsed version
        - get actual human readable value of objects
        - save it serialized content to sha1 file
    attrs:
        - serialized (<objecttype> <objectsize>\0<serialized-content>)
        - sha1 (hex sha1 of object)
        - desrialized (deserialized structure of object)
"""
import zlib 
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from util import get_gitdir_path

def parse_objcet(data):
    decomp = zlib.decompress(data)
    header = decomp.split(b"\0")[0]
    data = b"\0".join(decomp.split(b"\0")[1:])
    fmt = header.split(b" ")[0].decode()
    size = len(data)
    return {
        "data":data,
        "fmt":fmt,
        "size":size
    }

def is_sha1(s):
    if len(s) != 40:
        return False
    try:
        sha_int = int(s, 16)
    except ValueError:
        return False
    return True

class GenericObject:
    def __init__(self,src = None):
        if not src:
            raise Exception("fatal: you cannot construct an emptry object name you need at least the sha1 or parsed structure")
        if is_sha1(src):
            self.sha1 = src
            path = os.path.join(get_gitdir_path(),".git/objects",src[:2],src[2:]) 
            with open(path,"rb") as f:
                self.serialized = f.read()
                self.deserialize(self.serialized)
        else:
            self.deserialized = src
            self.serialize(src)

    def serialize(self,deserialized):
        pass

    def deserialize(self,serialized):
        pass

    def save(self):
        if self.serialized and self.sha1:
            sha = self.sha1
            path = os.path.join(get_gitdir_path(),".git/objects",sha[:2])
            if not os.path.exists(path):
                os.mkdir(path)
            with open(os.path.join(path,sha[2:]),"wb") as f:
                f.write(zlib.compress(self.serialized))
            

    
