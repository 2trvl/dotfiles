#!/usr/bin/env python3

'''
This file is part of 2trvl/dotfiles
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
          Backup Comparison Utility          
---------------------------------------------
Detects backups on connected drives and
compares them with the current state located
at BACKUP_DESTINATION

'''
import filecmp
import multiprocessing
import os
import shutil
import tempfile
from itertools import filterfalse
from typing import IO

from archiver import ZipFile
from core.common import run_as_admin
from core.widgets import ProgressBar

if os.name == "nt":
    import ctypes


class DirCmpUtils():
    
    @staticmethod
    def parse_dirs(
        files: list[str],
        rootPath: str,
        dirs: dict=None,
        dirsFiles: dict=None,
        recursive: bool=True,
        basePath: str = ""
    ):
        '''
        Parse dirs from given files in format
        {"dirname": "rootPath", "dirname/subdirname": "subdirPath"}

        And files
        {"subdir/filename": "filepath"}

        Args:
            files (list[str]): Folder files
            rootPath (str): Folder path
            dirs (dict, optional): Dict, where 
                to write dirs found among folder
                files. Defaults to None
            dirsFiles (dict, optional): Dict, 
                where to write files found 
                among folder files. Defaults
                to None
            recursive (bool, optional): Parse
                subdirs contents. Defaults to
                True
            basePath (str, optional): Can be used
                for calculating full file prefix
                when rootPath is a subdirectory:
                subdir/file to subdir/subdir/.../file.
                Also will prevent reading the same files
                when using symlinks. Use basePath
                equal to rootPath to parse faster
                and more accurately
        '''
        for file in files:
            file = file.rstrip(os.sep)
            file = file.split(os.sep)[-1]
            filepath = os.path.join(rootPath, file)
            #  Calculate full subdir prefix
            if basePath:
                file = os.path.relpath(filepath, basePath)
            
            #  Fix layering of multiple calls
            if os.path.exists(filepath):
                
                #  Don't parse files, if it's a symbolic link
                #  that points to files in the same parent directory
                if basePath and os.path.islink(filepath):
                    targetpath = os.path.realpath(filepath)
                    if basePath in targetpath:
                        continue

                if os.path.isdir(filepath):

                    if dirs is not None:
                        dirs[f"{file}{os.sep}"] = rootPath
                        
                        #  Recursively extract subdirs and files
                        if recursive:
                            subdirs = {}
                            subdirsFiles = {}

                            DirCmpUtils.parse_dirs(
                                os.listdir(filepath),
                                filepath,
                                subdirs,
                                subdirsFiles,
                                True,
                                basePath
                            )

                            #  Convert names to subdir/name
                            #  Filenames are added recursively on the left:
                            #  subdir2/subdir1/subdir0/file
                            #  If basePath defined, then name calculations already done
                            if not basePath:
                                for name, filepath in subdirs.copy().items():
                                    subdir = os.path.basename(filepath)
                                    subdirs[f"{subdir}{os.sep}{name}"] = subdirs.pop(name)
                                for name, filepath in subdirsFiles.copy().items():
                                    subdir = os.path.basename(filepath)
                                    subdirsFiles[f"{subdir}{os.sep}{name}"] = subdirsFiles.pop(name)

                            dirs.update(subdirs)

                            if dirsFiles is not None:
                                dirsFiles.update(subdirsFiles)
                
                elif dirsFiles is not None:
                    dirsFiles[file] = rootPath

            elif dirsFiles is not None:
                dirsFiles.pop(file, None)
    
    @staticmethod
    def list_to_dict(files: list[str], path) -> dict[str, str]:
        '''
        Convert filenames list to dict
        {"filename": "filepath"}

        Args:
            path (str): Filepath
            files (list[str): Filenames

        Returns:
            dict[str, str]: Converted dict
        '''
        return dict((file, path) for file in files)
    
    @staticmethod
    def dict_to_list(files: dict[str, str]) -> list[str]:
        '''
        Convert filenames dict to list
        ["filename", "subdirname/filename"]

        Args:
            files (dict[str, str]): Filenames

        Returns:
            list[str]: Converted list
        '''
        return list(files.keys())

    @staticmethod
    def join_subdir(subdir: str, files: list[str]):
        '''
        Convert filenames to subdir/name format

        Args:
            subdir (str): Subdir name to join
            files (list[str]): Filenames to convert

        Overwrites files list with changes
        '''
        for file in files.copy():
            files.append(f"{subdir}{os.sep}{file}")
            files.remove(file)
    
    @staticmethod
    def update_list(values: list, target: list):
        '''
        dictionary.update for list
        Adds values to the list only if they are not in it

        Args:
            values (list): Values to add
            target (list): List
        '''
        for value in values:
            if value not in target:
                target.append(value)


class DirCmp(filecmp.dircmp):

    def __init__(
        self,
        leftPath: str,
        rightPath: str,
        ignore: list[str]=None,
        hide: list[str]=None,
        subdirMode: bool=False,
        leftBasePath: str="",
        rightBasePath: str="",
        progressbar: bool=False
    ):
        '''
        Better dircmp with subdirs indexing

        Args:
            leftPath (str): Left directory path
            rightPath (str): Right directory path
            ignore (list[str], optional): List of names to ignore.
                Defaults to filecmp.DEFAULT_IGNORES.
            hide (list[str], optional): List of names to hide.
                Defaults to [os.curdir, os.pardir].
            subdirMode (bool, optional): System argument indicating
                that the current comparison is for a subdirectory.
                Defaults to False.
            leftBasePath (str, optional): System argument, points
                to the root of the left directory. Needed to 
                calculate names. Defaults to "".
            rightBasePath (str, optional): System argument, points
                to the root of the right directory. Needed to 
                calculate names. Defaults to "".
            progressbar (bool, optional): Render progress bar while
                running or not. If True an object of type ProgressBar
                is created, to stop it set the finished variable to True.
                Defaults to False.

        If you use progressbar option on Windows - run your code in the
        "if __name__ == '__main__'" statement
        '''
        super().__init__(leftPath, rightPath, ignore, hide)
        self.subdirMode = subdirMode
        
        if not subdirMode:
            self.leftBasePath = self.left
            self.rightBasePath = self.right
        else:
            self.leftBasePath = leftBasePath
            self.rightBasePath = rightBasePath

        self.progressbar = progressbar

        if progressbar:
            prefix = multiprocessing.Array("c", 1)
            prefix.value = b""
            self.postfix = multiprocessing.Array("c", 11)
            self.postfix.value = b"in process"
            self.finished = multiprocessing.Value("b", False)
            #  This class is designed in such way that when
            #  accessing a variable, make multiple function
            #  calls, so we omit counter, since it is impossible
            #  to track number of indexed files for sure
            self.renderingProcess = multiprocessing.Process(
                target=ProgressBar(size=40, clearMode=True).start_rendering_mp,
                args=(prefix, multiprocessing.Value("i", -1), self.postfix, self.finished),
                daemon=True
            )
            self.renderingProcess.start()

    def __enter__(self) -> "DirCmp":
        return self

    def __exit__(self, excType, excValue, traceback):
        self.finish_progressbar()

    def __repr__(self) -> str:
        return (
            "dircmp("
            f"leftPath=\"{self.left}\", "
            f"rightPath=\"{self.right}\", "
            f"ignore={self.ignore}, "
            f"hide={self.hide}, "
            f"progressbar={self.progressbar}"
            ")"
        )
    
    def finish_progressbar(self):
        '''
        Finish progressbar if it exists
        '''
        if hasattr(self, "renderingProcess"):
            with (self.postfix.get_lock(), self.finished.get_lock()):
                self.postfix.value = f"finished".encode()
                self.finished.value = True
            self.renderingProcess.join()

    def phase1(self):
        '''
        Compute common names but with subdirs
        '''
        left = dict(zip(map(os.path.normcase, self.left_list), self.left_list))
        right = dict(zip(map(os.path.normcase, self.right_list), self.right_list))
        self.common = list(map(left.__getitem__, filter(right.__contains__, left)))
        self.left_only = list(map(left.__getitem__, filterfalse(right.__contains__, left)))
        self.right_only = list(map(right.__getitem__, filterfalse(left.__contains__, right)))
        
        #  SubdirMode : Convert filenames to subdir/names
        if self.subdirMode:
            subdir = os.path.relpath(self.left, self.leftBasePath)
            #  Need to access vars in this order
            #  otherwise there will be errors
            #  common needed for common_files
            #  common_files needed for diff_files, funny_files
            DirCmpUtils.join_subdir(subdir, self.left_only)
            DirCmpUtils.join_subdir(subdir, self.right_only)
            DirCmpUtils.join_subdir(subdir, self.left_list)
            DirCmpUtils.join_subdir(subdir, self.right_list)
            DirCmpUtils.join_subdir(subdir, self.diff_files)
            DirCmpUtils.join_subdir(subdir, self.same_files)
            DirCmpUtils.join_subdir(subdir, self.funny_files)
            DirCmpUtils.join_subdir(subdir, self.common_files)
            DirCmpUtils.join_subdir(subdir, self.common_funny)
            DirCmpUtils.join_subdir(subdir, self.common)

        #  Convert to format {"filename": "filepath"}
        self.left_only = DirCmpUtils.list_to_dict(self.left_only, self.left)
        self.right_only = DirCmpUtils.list_to_dict(self.right_only, self.right)

        #  Recursively parse common dirs
        for dir in self.common_dirs:
            left = os.path.join(self.leftBasePath, dir)
            right = os.path.join(self.rightBasePath, dir)
            compared = DirCmp(
                leftPath=left,
                rightPath=right,
                subdirMode=True,
                leftBasePath=self.leftBasePath,
                rightBasePath=self.rightBasePath
            )
            #  Load subdirs values
            self.left_only_dirs.update(compared.left_only_dirs)
            self.right_only_dirs.update(compared.right_only_dirs)
            self.left_only.update(compared.left_only)
            self.right_only.update(compared.right_only)
            #  Prevent adding same values when recursing
            DirCmpUtils.update_list(compared.left_list, self.left_list)
            DirCmpUtils.update_list(compared.right_list, self.right_list)
            DirCmpUtils.update_list(compared.diff_files, self.diff_files)
            DirCmpUtils.update_list(compared.same_files, self.same_files)
            DirCmpUtils.update_list(compared.funny_files, self.funny_files)
            DirCmpUtils.update_list(compared.common_dirs, self.common_dirs)
            DirCmpUtils.update_list(compared.common_files, self.common_files)
            DirCmpUtils.update_list(compared.common_funny, self.common_funny)
            DirCmpUtils.update_list(compared.common, self.common)
        
        #  Force parse left_only_dirs and right_only_dirs
        #  Cast dir names to dir/ format
        if not self.common_dirs:
            self.phase5()
    
    def phase2(self):
        '''
        Add conversion dir names to dir/ format
        '''
        super().phase2()
        common_dirs = {}
        
        DirCmpUtils.parse_dirs(
            files=self.common_dirs,
            rootPath=self.left,
            dirs=common_dirs,
            recursive=False,
            basePath=self.leftBasePath
        )
        
        self.common_dirs = DirCmpUtils.dict_to_list(common_dirs)
        
        for dir in self.common_dirs:
            oldDir = dir.split(os.sep)[-2]
            self.common.remove(oldDir)
            self.common.append(dir)

            oldDir = dir[:-1]
            self.left_list.remove(oldDir)
            self.right_list.remove(oldDir)
            
            self.left_list.append(dir)
            self.right_list.append(dir)

    def phase3(self):
        '''
        Compare files content, not only os.stat attributes
        '''
        xx = filecmp.cmpfiles(
            a=self.left,
            b=self.right,
            common=self.common_files,
            shallow=False
        )
        self.same_files, self.diff_files, self.funny_files = xx

    def phase4(self):
        '''
        Find out all subdirectories not only common
        '''
        common_dirs = DirCmpUtils.list_to_dict(
            self.common_dirs,
            self.left
        )
        self.subdirs = {
            **common_dirs,
            **self.left_only_dirs,
            **self.right_only_dirs
        }

    def phase5(self):
        '''
        left_only_dirs and right_only_dirs with subdirs
        also update left_only and right_only files
        '''
        self.left_only_dirs = {}
        DirCmpUtils.parse_dirs(
            DirCmpUtils.dict_to_list(self.left_only),
            self.left,
            self.left_only_dirs,
            self.left_only,
            True,
            self.leftBasePath
        )
        #  Remove old dir names without /
        for dir in self.left_only_dirs.keys():
            self.left_only.pop(dir[:-1], None)
            if dir[:-1] in self.left_list:
                self.left_list.remove(dir[:-1])
        self.left_only.update(self.left_only_dirs)
        DirCmpUtils.update_list(
            DirCmpUtils.dict_to_list(self.left_only_dirs),
            self.left_list
        )
        
        self.right_only_dirs = {}
        DirCmpUtils.parse_dirs(
            DirCmpUtils.dict_to_list(self.right_only),
            self.right,
            self.right_only_dirs,
            self.right_only,
            True,
            self.rightBasePath
        )
        for dir in self.right_only_dirs.keys():
            self.right_only.pop(dir[:-1], None)
            if dir[:-1] in self.right_list:
                self.right_list.remove(dir[:-1])
        self.right_only.update(self.right_only_dirs)
        DirCmpUtils.update_list(
            DirCmpUtils.dict_to_list(self.right_only_dirs),
            self.right_list
        )

    methodmap = dict(
        subdirs=phase4,
        same_files=phase3,
        diff_files=phase3,
        funny_files=phase3,
        common_dirs=phase2,
        common_files=phase2,
        common_funny=phase2,
        common=phase1,
        left_only=phase1,
        left_only_dirs=phase5,
        right_only=phase1,
        right_only_dirs=phase5,
        left_list=filecmp.dircmp.phase0,
        right_list=filecmp.dircmp.phase0
    )


def contains_only(
    string: str,
    substring: str,
    exclude: list[str]=[]
) -> bool:
    '''
    Check if a string contains a substring
    and does not contain any other substrings

    Args:
        string (str): String
        substring (str): Substring to look for in the string
        exclude (list[str], optional): Substrings that should
            not be in the string. Defaults to [].

    Returns:
        bool: A substring was found in a string and no
            substrings were found from exclude
    '''
    if not substring in string:
        return False
    if exclude:
        if any(substring in string for substring in exclude):
            return False
    return True


def insert_to_sorted(strings: list[str], sortedStrings: list[str]):
    '''
    Insert strings into an already sorted list

    Args:
        strings (list[str]): Strings to insert
        sortedStrings (list[str]): Sorted list

    Overwrites sortedStrings with inserted strings into it
    '''
    for string in strings:
        for sortedString in sortedStrings:
            if sortedString > string:
                index = sortedStrings.index(sortedString)
                sortedStrings.insert(index, string)
                break


def sorted_paths(files: list[str]) -> list[str]:
    '''
    Sort files by dirs

    Args:
        files (list[str]): Files to sort

    Returns:
        list[str]: Sorted files
    '''
    files = files.copy()
    files.sort()
    dirs = []

    #  Find dirs
    for file in files.copy():
        if file.endswith(os.sep):
            files.remove(file)
            dirs.append(file)
    
    if not dirs:
        return files

    dirs.sort()
    sortedFiles = []

    for dir in dirs.copy():
        sortedFiles.append(dir)
        dirs.remove(dir)
        for file in files.copy():
            if contains_only(file, dir, dirs):
                files.remove(file)
                sortedFiles.append(file)
    
    insert_to_sorted(files, sortedFiles)
    return sortedFiles


def print_files(title: str, files: list[str], output: IO):
    '''
    Print files list

    Args:
        title (str): List title
        files (list[str]): Files names
        output (IO): Output source. Use sys.stdout for printing in terminal
    '''
    if files:
        print(f"{title}:", file=output, flush=True)
        for file in sorted_paths(files):
            print(f"    {file}", file=output, flush=True)


def get_storage_drives() -> set[str]:
    '''
    Get available storage drives, but not system

    Returns:
        set[str]: Storage drives paths
    '''
    drives = set()

    if os.name == "nt":
        bufferSize = ctypes.windll.kernel32.GetLogicalDriveStringsW(0, None)
        buffer = ctypes.create_string_buffer(bufferSize * 2)
        ctypes.windll.kernel32.GetLogicalDriveStringsW(bufferSize, buffer)
        
        drives = buffer.raw.decode("utf-16-le").split("\0")
        drives = filter(None, drives)
        
        systemDrive = os.environ.get("SYSTEMDRIVE")
        systemDrive = os.path.join(systemDrive, os.sep)
        drives = set(filter(systemDrive.__ne__, drives))
    
    #  Only Linux support (using procfs)
    else:
        #  parse filesystems
        fstypes = set()
        with open("/proc/filesystems", "r") as fsFile:
            for fstype in fsFile.readlines():
                fstype = fstype.strip()
                if not fstype.startswith("nodev"):
                    fstypes.add(fstype)
                else:
                    #  ignore all lines except nodev zfs
                    fstype = fstype.split("\t")[1]
                    if fstype == "zfs":
                        fstypes.add("zfs")

        #  find mounts file
        if os.path.isfile("/etc/mtab"):
            mountsPath = os.path.realpath("/etc/mtab")
        else:
            mountsPath = os.path.realpath("/proc/self/mounts")

        #  parse partitions
        with open(mountsPath, "r") as mountsFile:
            for mount in mountsFile.readlines():
                device, mountPoint, fstype = mount.split()[:3]
                if fstype not in fstypes:
                    continue
                if mountPoint in ("/", "/boot", "/home"):
                    continue
                if device == "none" or device in ("/dev/root", "rootfs"):
                    continue
                drives.add(mountPoint)

    return drives


def compare_backups(
    backupFilename: str,
    backupDestination: str,
    backupPassword: bytes | None=None,
    reportFilepath: str="compared.txt",
    preferredEncoding: str="cp866",
    ignore: list[str]=[".git"],
    path: str | None=None
):
    '''
    Detects backups on connected drives and
    compares them with the current state located
    at backupDestination

    Args:
        backupFilename (str): Filename with extension
            to look for on drives.
        backupDestination (str): Path of backup with
            which to compare.
        backupPassword (bytes | None, optional): Password
            to extract a backup from an encrypted archive
        reportFilepath (str, optional): Path of detailed
            report. Defaults to "compared.txt".
        preferredEncoding (str, optional): Encoding to use
            when guessing zip filenames original.
            Defaults to "cp866".
        ignore (list[str], optional): Filenames to ignore
            in backup. Defaults [".git"]
        path (str | None, optional): Path of backup to
            compare with backupDestination. Disables
            auto discovery. Defaults to None
    '''
    if path:
        path = path.rstrip("/").rstrip("\\")
        path, backupFilename = os.path.split(path)
        drives = { path }
    else:
        drives = get_storage_drives()
    
    report = open(reportFilepath, "w", encoding="utf-8")
    backupName, backupExtension = os.path.splitext(backupFilename)

    for drive in drives.copy():
        try:
            if backupFilename in os.listdir(drive):
                print(f"Found backup in {drive}")
                backupFilepath = os.path.join(drive, backupFilename)
                
                if backupExtension:
                    # windows create symbolic links rights
                    if os.name == "nt":
                        run_as_admin()
                    
                    print(f"Extracting {backupFilepath}")

                    if backupExtension == ".zip":
                        with ZipFile(
                            file=backupFilepath,
                            mode="r",
                            preferredEncoding=preferredEncoding,
                            ignore=ignore,
                            progressbar=True,
                            useBarPrefix=False
                        ) as zip:
                            zip.extractall(
                                path=tempfile.gettempdir(),
                                pwd=backupPassword
                            )

                    backupFilepath = os.path.join(tempfile.gettempdir(), backupName)

                print(f"Comparing with {backupDestination}")
                compared = DirCmp(
                    leftPath=backupDestination,
                    rightPath=backupFilepath,
                    ignore=ignore,
                    progressbar=True
                )

                print(
                    f"( {backupDestination}, {os.path.join(drive, backupFilename)} ):",
                    end="\n\n",
                    file=report,
                    flush=True
                )
                print_files(
                    "New",
                    DirCmpUtils.dict_to_list(compared.right_only),
                    report
                )
                print_files(
                    "Modified",
                    compared.diff_files,
                    report
                )
                print_files(
                    "Removed",
                    DirCmpUtils.dict_to_list(compared.left_only),
                    report
                )
                print_files(
                    "Error",
                    compared.funny_files,
                    report
                )
                print(
                    f"\n( new: {len(compared.right_only)}, modified: {len(compared.diff_files)}, removed: {len(compared.left_only)} )",
                    end="\n",
                    file=report,
                    flush=True
                )

                compared.finish_progressbar()

                print(
                    f"( new: {len(compared.right_only)}, modified: {len(compared.diff_files)}, removed: {len(compared.left_only)} )",
                    end="\n\n"
                )

                if backupExtension:
                    shutil.rmtree(backupFilepath)

            else:
                raise FileNotFoundError
        
        except (PermissionError, FileNotFoundError):
            drives.remove(drive)
    
    if drives:
        print(f"View {os.path.basename(reportFilepath)} for detailed report")
    else:
        print("No backups found")

    report.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Backup Comparison Utility")
    parser.add_argument(
        "-n",
        "--name",
        help="filename with extension to look for on drives"
    )
    parser.add_argument(
        "-d",
        "--destination",
        help="path of backup with which to compare"
    )
    parser.add_argument(
        "--password",
        type=os.fsencode,
        default=None,
        help="password to extract a backup from an encrypted archive"
    )
    parser.add_argument(
        "--report",
        default="compared.txt",
        help="path of detailed report"
    )
    parser.add_argument(
        "--preferred-encoding",
        default="cp866",
        help="encoding to use when guessing zip filenames original"
    )
    parser.add_argument(
        "--ignore",
        nargs="*",
        default=[".git"],
        help="filenames to ignore in backup"
    )
    parser.add_argument(
        "-p",
        "--path",
        help="path of backup to compare with destination. disables auto discovery"
    )
    args = parser.parse_args()

    if args.name and args.destination:
        compare_backups(
            backupFilename=args.name,
            backupDestination=args.destination,
            backupPassword=args.password,
            reportFilepath=args.report,
            preferredEncoding=args.preferred_encoding,
            ignore=args.ignore
        )

    elif args.destination and args.path:
        compare_backups(
            backupFilename="",
            backupDestination=args.destination,
            backupPassword=args.password,
            reportFilepath=args.report,
            preferredEncoding=args.preferred_encoding,
            ignore=args.ignore,
            path=args.path
        )
