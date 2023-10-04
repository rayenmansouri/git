class NoGitRepository(Exception):
    """Fatal:not git respository"""

class CacheFileNotFound(Exception):
    """File does not exist in the file system nor in index"""

class BranchDoesNotHaveCommit(Exception):
    """fatal: your current branch 'main' does not have any commits yet"""