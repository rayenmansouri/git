import os


GIT_DIR = {
        ".git":{
            "type":"dir",
            "subdirs":{
                "HEAD":{"type":"file","content":"ref: refs/heads/main"},
                "objects":{"type":"dir","subdirs":{}},
                "refs":{
                    "type":"dir",
                    "subdirs":{
                        "heads":{"type":"dir","subdirs":{}},
                    }
                }
            }
        }
}

def get_gitdir_path(current_directory = os.getcwd()):
    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    if os.path.exists(current_directory + "/.git"):
        return current_directory
    elif current_directory != "/":
        return get_gitdir_path(parent_directory)
    return None
def create_dirs(git_dir = GIT_DIR,parent = "."):
    for dirname in git_dir:
        path = os.path.join(parent,dirname)
        params = git_dir[dirname]
        if params["type"] == "dir":
                os.mkdir(path)
                create_dirs(params["subdirs"],path)    
        else:
            with open(path,"w")  as f:
                f.write(params["content"])
            
