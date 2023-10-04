import os
import sys
import argparse
from repo import Repo
from objects import Commit
parser = argparse.ArgumentParser(
                    prog='git',
                    description='Stupid directory manager',
                    epilog='Text at the bottom of help')

subparsers = parser.add_subparsers(title="Commands", dest="command")
subparsers.required = True
#init command
argsp = subparsers.add_parser("init", help="Initialize a new, empty repository.")
#add command
argsp = subparsers.add_parser("add", help="git-add - Add file contents to the index")
argsp.add_argument("path", nargs="+", help="Files to add")
#cat-file command
argsp = subparsers.add_parser("cat-file", help="git-status - see file status")
argsp.add_argument("sha1", help="sha1 of tree")
#write tree command
argsp = subparsers.add_parser("write-tree", help="git-write-tree - write tree to repo")
#status command
argsp = subparsers.add_parser("status", help="git-write-tree - write tree to repo")
#commit command
argsp = subparsers.add_parser("commit", help="git-write-tree - write tree to repo")
#log command

argsp.add_argument("-m",
                   metavar="message",
                   dest="message",
                   help="Message to associate with this commit.")

argsp = subparsers.add_parser("log", help="git-write-tree - write tree to repo")


args = parser.parse_args(sys.argv[1:])

if args.command == "init":
   git = Repo()
   git.init()
elif args.command == "add":
    files = []
    paths = args.path
    for path in paths:
      if os.path.isdir(path):
         for root, directories, fnames in os.walk(path): 
             directories[:] = [d for d in directories if not d.startswith(".")]
             for fname in fnames:
                files.append(os.path.join(root,fname).replace("./",""))
      else:
         files.append(path) 
    git = Repo()
    git.add(files)
elif args.command == "cat-file":
   git = Repo()
   o = git.read_object(args.sha1)
   print(o.get_content())
elif args.command == "write-tree":
   git = Repo()
   print(git.write_tree())
elif args.command == "status":
   git = Repo()
   git.status()
elif args.command == "commit":
   git = Repo()
   git.commit(message=args.message)
elif args.command == "log":
   git = Repo()
   commit = git.head.commit()
   while True:
      print(commit.get_content())
      if not b"parent" in commit.deserialized:
         break
      commit = Commit(commit.deserialized[b"parent"].decode())

