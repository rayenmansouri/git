import collections
import hashlib
from .base import GenericObject,parse_objcet

def kvlm_parse(raw, start=0, dct=None):
    if not dct:
        dct = collections.OrderedDict()
    spc = raw.find(b' ', start)
    nl = raw.find(b'\n', start)
    if (spc < 0) or (nl < spc):
        assert nl == start
        dct[None] = raw[start+1:]
        return dct
    key = raw[start:spc]
    end = start
    while True:
        end = raw.find(b'\n', end+1)
        if raw[end+1] != ord(' '): break
    value = raw[spc+1:end].replace(b'\n ', b'\n')
    if key in dct:
        if type(dct[key]) == list:
            dct[key].append(value)
        else:
            dct[key] = [ dct[key], value ]
    else:
        dct[key]=value
    return kvlm_parse(raw, start=end+1, dct=dct)

def kvlm_serialize(kvlm):
    ret = ''
    for k in kvlm.keys():
        if k == None: continue
        val = kvlm[k]
        if type(val) != list:
            val = [ val ]
        for v in val:
            ret += k.decode() + ' ' + (str(v).replace('\n', '\n ')) + '\n'
    ret += '\n' + kvlm[None].decode() + '\n'
    return ret

class Commit(GenericObject):
    fmt="commit"
  
    def serialize(self,deserliazed):
        serliazed = kvlm_serialize(deserliazed).encode() 
        self.serialized = f"commit {len(serliazed)}\0".encode() + serliazed
        self.sha1 = hashlib.sha1(self.serialized).hexdigest()
    
    def deserialize(self, serialized):
        parsed = parse_objcet(serialized)
        if parsed["fmt"] != "commit":
            raise Exception(f"Object with hash {self.sha1} is not a commit object")
        self.deserialized = kvlm_parse(parsed["data"])

    def get_content(self):
        ret = ""
        for item in self.deserialized:
            k = item.decode() + " " if item else ""
            ret += k + self.deserialized[item].decode() + "\n"
        ret = ret[:-1]
        return ret
