from pathlib import Path, PurePath
import os
from pprint import pp
from tqdm import tqdm

def compare(baseFolder: Path, *moreFolders: Path):
    """
    "Simple" script to take n-Folders with similar folder structure and compare each and every file based on the last modified timestamp.
    Spits out a dict with each path from each folders root assigned another array with the actual paths from oldest to newest.
    """
    pathsList = [baseFolder, *moreFolders]
    pathsListMapped = list(map(lambda x : [x, dict()], pathsList))

    # Should contain a dict of Path keys with more dicts attached to them. The dicts will contain all files and their absolute path with timestamp
    # So to find a single specific file it would look something like this: paths[0][Path('my/path/one')][Path('/home/user/Documents/my/path/one/README.md')] = 1756136450000
    paths: dict[Path, dict[Path, float]] = dict(pathsListMapped)

    # Iterate over each parent Folder
    for path, irrelevant in tqdm(paths.items(), desc='Getting Files and Time'):
        # Get all files - Note: COMPUTATIONALLY EXPENSIVE. If you know how to improve performance and keep it working on all platforms, make a pull request.
        files = sorted(path.rglob('*'))
        files = list(filter(lambda x : x.is_file(), files))
        # Map each file to last creation
        filesTimeMapped = dict(map(lambda x : [x, os.path.getmtime(str(x))], files))
        paths[path] = filesTimeMapped

    # Iterate over all of them again, this time keeping the same root and "merging" the entries
    # This can be represented as result[PurePath('README.md')] = [Path('/home/user/Documents/my/path/one/README.md), Path('/home/user/Documents/my/path/two/README.md)]
    root: dict[PurePath, dict[Path, float]] = dict()
    for parentPath, contents in tqdm(paths.items(), desc='Fuse different Roots'):
        for filePath, time in tqdm(contents.items(), desc='File progress', leave=False):
            # Get relative path, this cuts out things like '/home/user/Documents' from before the path, essentially making this our own root
            relative = PurePath(filePath).relative_to(parentPath)
            # Get already existing entries in result variable
            filesInDict: dict[Path, float] = root.get(relative, dict())
            # Set key-value time based on real absolute path
            filesInDict[filePath] = time
            # Set data back into the dict
            root[relative] = filesInDict

    # Now that we have all the necessary data set, it's time to loop over it AGAIN and sort out some other things
    rootTmp = root
    for rootFile, absoluteFiles in tqdm(root.items(), desc='Sort by time'):
        # Fix up candidates/absoluteFiles, by removing the associated time and just sorting it and returning it as a list
        # https://stackoverflow.com/a/7340031
        root[rootFile] = sorted(absoluteFiles, key=absoluteFiles.get)
    
    result: dict[PurePath, list[Path]] = rootTmp # Fix up type hintings
    return result

def merge(baseFolder: Path, *moreFolders: Path):
    """
    Same as the compare function, except this one disregards the timestamp and merges them by order as they're given.
    """
    # I just copied the whole function and changed a few things because the other one used dicts and this one just goes straight to lists, so it would be a pain to have one function do two things
    # TODO: offload common tasks between the two functions to different function
    pathsList = [baseFolder, *moreFolders]
    pathsListMapped = list(map(lambda x : [x, list()], pathsList))

    # Should contain a dict of Path keys with more lists attached to them. The lists will contain all files and their absolute path
    # So to find a single specific file it would look something like this: paths[0][Path('my/path/one')][Path('/home/user/Documents/my/path/one/README.md')] = 1756136450000
    paths: dict[Path, list[Path]] = dict(pathsListMapped)

    # Iterate over each parent Folder
    for path, irrelevant in tqdm(paths.items(), desc='Getting Files'):
        # Get all files - Note: COMPUTATIONALLY EXPENSIVE. If you know how to improve performance and keep it working on all platforms, make a pull request.
        files = sorted(path.rglob('*'))
        files = list(filter(lambda x : x.is_file(), files))
        paths[path] = files

    # Iterate over all of them again, this time keeping the same root and "merging" the entries
    # This can be represented as result[PurePath('README.md')] = [Path('/home/user/Documents/my/path/one/README.md), Path('/home/user/Documents/my/path/two/README.md)]
    root: dict[PurePath, list[Path]] = dict()
    for parentPath, contents in tqdm(paths.items(), desc='Fuse different Roots'):
        for filePath in tqdm(contents, desc='File progress', leave=False):
            # Get relative path, this cuts out things like '/home/user/Documents' from before the path, essentially making this our own root
            relative = PurePath(filePath).relative_to(parentPath)
            # Get already existing entries in result variable
            filesInDict: list[Path] = root.get(relative, list())
            # Append Absolute Path to Relative Path
            filesInDict.append(filePath)
            # Set data back into the dict
            root[relative] = filesInDict

    # Now that we have all the necessary data set, it's time to loop over it AGAIN and sort out some other things
    rootTmp = root
    # for rootFile, absoluteFiles in root.items():
    #     # Fix up candidates/absoluteFiles, by removing the associated time and just sorting it and returning it as a list
    #     # https://stackoverflow.com/a/7340031
    #     root[rootFile] = sorted(absoluteFiles, key=absoluteFiles.get)
    
    result: dict[PurePath, list[Path]] = rootTmp # Fix up type hintings
    return result

# pp(compare(Path("D:\\MyFiles\\Moon - My Love\\file merger by last modified\\Anya~Leo - pc"), Path("D:\\MyFiles\\Moon - My Love\\file merger by last modified\\Anya~Leo - laptop")))
# pp(merge(Path("D:\\MyFiles\\Moon - My Love\\file merger by last modified\\Anya~Leo - pc"), Path("D:\\MyFiles\\Moon - My Love\\file merger by last modified\\Anya~Leo - laptop")))