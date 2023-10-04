import os
import shutil
from cache import Cache,CacheEntry
from objects import object_builder,BlobObject,Tree,Commit
from head import Head
import datetime
from util import get_gitdir_path,create_dirs

#repository is main interface to git internal
class Repo:
    def __init__(self,repo_path = get_gitdir_path()):
        self.repo_path = repo_path
        if self.repo_path:
            self.cache = Cache()
            self.head = Head(repo_path=self.repo_path)

   
    def init(self):
        if os.path.exists(".git"):
            shutil.rmtree(".git")
            create_dirs()
            print("reinitialized git repository")
        else:
            create_dirs()
            print("initialized git repository")
            self.repo_path = os.getcwd()
        self.cache = Cache()
        self.head = Head(self.repo_path)

    def must_git_dir(self):
        if not self.is_gitdir():
            raise Exception("fatal: not git directory")

    def is_gitdir(self):
        return not self.repo_path is None
 
    def add(self,files):
        self.must_git_dir()
        self.cache.read()
        for file_path in files:
            try:
                with open(file_path,"rb") as f:
                    b = BlobObject(f.read())
                    b.save()
            except FileNotFoundError:
                print("removing")
                self.cache.remove(file_path)
                continue
            
            #save file in cache
            stat = os.stat(file_path)
            ctime_s = int(stat.st_ctime)
            ctime_ns = stat.st_ctime_ns % 10**9
            mtime_s = int(stat.st_mtime)
            mtime_ns = stat.st_mtime_ns % 10**9
            entry = CacheEntry(ctime=(ctime_s, ctime_ns), mtime=(mtime_s, mtime_ns), dev=stat.st_dev, ino=stat.st_ino,
                                mode_type=0b1000, mode_perms=0o644, uid=stat.st_uid, gid=stat.st_gid,
                                fsize=stat.st_size, sha=b.sha1, flag_assume_valid=False,
                                flag_stage=False, name=file_path)
            self.cache.add(entry)
        self.cache.save()

    def _staged_to_be_committed(self,tree):
        self.must_git_dir()
        cache = self.cache
        cache.read()
        ret = []
        for entry in cache.entries:
            if entry.name in tree:
                if entry.sha != tree[entry.name]["sha"]:
                    ret.append({"state":"modified","name":entry.name})
                del tree[entry.name]
            else:
                 ret.append({"state":"new file","name":entry.name})
        for name in tree.keys():
             ret.append({"state":"deleted","name":name})
        return ret

    
    def _not_staged(self,entries):
        not_staged = []
        untracked = []
        all_files = []
        for (root, dirs, files) in os.walk(self.repo_path, True):
            dirs[:] = [d for d in dirs if not d.startswith(".") and not d.startswith("__")]
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, self.repo_path)
                all_files.append(rel_path)
        for entry in entries:
            full_path = os.path.join(self.repo_path,entry.name)
            if not os.path.exists(full_path):
                not_staged.append({
                    "state":"deleted",
                    "name":entry.name
                })
                continue
            stat = os.stat(full_path)
              # Compare metadata
            ctime_ns = entry.ctime[0] * 10**9 + entry.ctime[1]
            mtime_ns = entry.mtime[0] * 10**9 + entry.mtime[1]
            if (stat.st_ctime_ns != ctime_ns) or (stat.st_mtime_ns != mtime_ns):
                not_staged.append({
                    "state":"modified",
                    "name":entry.name
                })
            if entry.name in all_files:
                all_files.remove(entry.name)
        for path in all_files:
            untracked.append(path)
        return not_staged,untracked
    
    def status(self):
        self.must_git_dir()
        cache = self.cache
        tree = self.head.tree()
        if tree :
            tree = tree.flat()
        else:
            tree = {}
        print("On branch "+self.head.branch + "\n")
        if(not len(tree)):
            print("No commits yet\n")
        staged_to_be_committed = self._staged_to_be_committed(tree) 
        print("""Changes to be committed:
  (use "git rm --cached <file>..." to unstage)""" )
        for obj in staged_to_be_committed:
            state = obj["state"]
            name = obj["name"]
            print(f"\033[32m\t{state}:   {name}\033[0m")
        print()
        print("""Changes not staged for commit:
  (use "git add/rm <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)""")
        unstaged,untracked = self._not_staged(cache.entries)
        for obj in unstaged:
            state = obj["state"]
            name = obj["name"]
            print(f"\033[91;1m\t{state}:   {name}\033[0m")
        print("""
Untracked files:
  (use "git add <file>..." to include in what will be committed)""")
        for path in untracked:
            print("\t",path)
        
    #i know that this sucks but i cannot find any better way to do it
    def write_tree(self):
        self.cache.read()
        tree = Tree(self.cache.tree_format())
        return tree.sha1
    
    
    def read_object(self,sha):
        self.must_git_dir()
        b = object_builder(sha)
        return b
    
    def commit(self,message = "commit ",timestamp = datetime.datetime.now()):
        tree = self.head.tree()
        if tree :
            tree = tree.flat()
        else:
            tree = {}
        if len(self._staged_to_be_committed(tree)) == 0:
            print("Nothing added to commit")
            return None
        h = self.head
        parent = h.commit()
        tree = self.write_tree()
        kvlm = {}
        kvlm[b"tree"] = tree
        if parent:
            kvlm[b"parent"] = parent.sha1
        # Format timezone
        offset = int(timestamp.astimezone().utcoffset().total_seconds())
        hours = offset // 3600
        minutes = (offset % 3600) // 60
        tz = "{}{:02}{:02}".format("+" if offset > 0 else "-", hours, minutes)
        author = "Mansouri Rayen " + timestamp.strftime(" %s ") + tz
        kvlm[b"author"] = author
        kvlm[b"committer"] = author
        kvlm[None] = message.encode("utf8")
        commit = Commit(kvlm)
        commit.save()
        h.update(commit.sha1)
        return None





        


        