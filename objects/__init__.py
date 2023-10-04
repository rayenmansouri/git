import os
import zlib
import sys

from .blob import BlobObject
from .tree import Tree
from .commit import Commit


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from util import get_gitdir_path

def object_builder(sha1):
    with open(os.path.join(get_gitdir_path(),".git/objects",sha1[:2],sha1[2:]),"rb") as f:
        data = f.read()
    decomp = zlib.decompress(data)
    header = decomp.split(b"\0")[0]
    data = b"\0".join(decomp.split(b"\0")[1:])
    fmt = header.split(b" ")[0].decode()
    if fmt == "tree":
        return Tree(sha1)
    elif fmt == "blob":
        return BlobObject(sha1)
    elif fmt == "commit":
        return Commit(sha1)
        