from .base import GenericObject,parse_objcet
import hashlib
"""
    blob is the easiest object type in git
    it's just plain binary that's it
"""
class BlobObject(GenericObject):

    def serialize(self, deserialized):
        if not isinstance(deserialized,bytes):
            raise Exception("this is not valid blob format")
        self.serialized = f"blob {len(deserialized)}\0".encode() + deserialized
        self.sha1 = hashlib.sha1(self.serialized).hexdigest()
        try:
            self.deserialized = self.serialized.decode()
        except Exception as exc:
            self.deserialized = deserialized

    def deserialize(self, serialized):
        parsed = parse_objcet(serialized)
        if parsed["fmt"] != "blob":
            raise Exception(f"Object with hash {self.sha1} is not a blob object")
        self.deserialized = parsed["data"].decode()
        
    def get_content(self):
        return self.deserialized
    
