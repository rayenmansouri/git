import os
from objects import object_builder
class Head:
    def __init__(self,repo_path):
        self.branch = "main"
        self.repo_path = repo_path
        try:
            with open(os.path.join(repo_path,".git/refs/heads/main"),"r") as f:
                self.commit_sha1 = f.read().replace("\n","")
        except FileNotFoundError:
            self.commit_sha1 = None
    
    def commit(self):
        if self.commit_sha1:
            o = object_builder(self.commit_sha1)
            return o
        return None
    
    def tree(self):
        commit = self.commit()
        if commit:
            tree_sha1 = commit.deserialized[b"tree"].decode()
            return object_builder(tree_sha1)
        return None

    def update(self,sha1):
        with open(os.path.join(self.repo_path,".git/refs/heads/main"),"w") as f:
               f.write(sha1 + "\n")
       
    
     
      