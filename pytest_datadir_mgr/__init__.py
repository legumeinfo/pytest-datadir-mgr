# -*- coding: utf-8 -*-
"""datadir_mgr fixture for pytest."""

# standard library imports
import contextlib
import gzip
import hashlib
import os
import shutil
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

# third-party imports
import pytest
from progressbar import DataTransferBar
from requests_download import HashTracker
from requests_download import ProgressTracker
from requests_download import download as request_download

# global constants
GLOBAL_SUBDIR = "data"
SCOPES = (
    "function",
    "class",
    "module",
    "global",
)  # ordered from lowest to highest
__version__ = "1.2.4"


class DataDirManager:

    """Download, cache, and optionally verify and gzip test files from a specified URL."""

    class NameObject:

        """Holder of names for module, class, and function that mimics request."""

        def __init__(self, module, cls=None, func=None):
            """Initialize object from dictionary, 'module' is required key."""
            self.module = SimpleNamespace(__name__=module)
            if cls is not None:
                self.cls = SimpleNamespace(__name__=cls)
            else:
                self.cls = None
            if func is not None:
                self.function = SimpleNamespace(__name__=func)
            else:
                self.function = SimpleNamespace(__name__=None)

    class ScopedDataDirDict(dict):

        """Dictionary of paths specifying test data directories at different scopes."""

        class Scope:

            """Class holding a path and a name."""

            def __init__(self, basepath, name):
                """Save path and name."""
                self.path = basepath / name
                self.name = name

        def __init__(self, globalpath, nameobj, keep_global=True):
            """Create dictionary of paths at different scopes."""
            dict.__init__(self)  # create empty dict
            self["global"] = self.Scope(
                globalpath.parent, str(globalpath.name)
            )
            module = nameobj.module.__name__
            module_split = module.split(".")
            if len(module_split) > 1:  # module could be in tests module
                module = ".".join(module_split[1:])
            self["module"] = self.Scope(self["global"].path, module)
            if nameobj.cls is not None:
                self["class"] = self.Scope(
                    self["module"].path, nameobj.cls.__name__
                )
                if nameobj.function.__name__ is not None:
                    self["function"] = self.Scope(
                        self["class"].path, nameobj.function.__name__
                    )
            else:
                if nameobj.function.__name__ is not None:
                    self["function"] = self.Scope(
                        self["module"].path, nameobj.function.__name__
                    )
            if not keep_global:
                del self["global"]

    def __init__(self, request, tmp_path, config):
        """Stash a copy of the request and init."""
        self.request = request
        self.datapath = Path(request.fspath.dirpath()) / GLOBAL_SUBDIR
        self.tmp_path = tmp_path
        self.verbose = config.getoption("verbose") > 0
        self.request_scopes = self.ScopedDataDirDict(self.datapath, request)
        self.scopes = OrderedDict([("request", self.request_scopes)])

    def __getitem__(self, filepath):
        """Look for a filepath in all the datadirs, with smallest scope first."""
        for scopekey in reversed(
            self.scopes.keys()
        ):  # search last-added first
            for level in SCOPES:  # search smallest scope first
                if level in self.scopes[scopekey]:  # not every scope may exist
                    levelpath = self.scopes[scopekey][level].path
                    name = self.scopes[scopekey][level].name
                    datapath = levelpath / filepath
                    if datapath.exists():
                        if self.verbose:
                            print(
                                f'path "{filepath}" found in scope "{scopekey}"'
                                + f'" level "{level}" name "{name}"'
                            )
                        return datapath
        raise KeyError(
            f"Path '{filepath}' not found in the datadir scopes {self.scopes.keys()}"
        )

    def add_scope(self, scope_name, module=None, cls=None, func=None):
        """Add scopes to be searched for data files, in addition to request."""
        self.scopes[scope_name] = self.ScopedDataDirDict(
            self.datapath,
            self.NameObject(module, cls=cls, func=func),
            keep_global=False,
        )

    def scope_to_path(self, scope="module", create=True):
        """Return the path of a request scope with optional directory creation."""
        if scope not in SCOPES:
            raise ValueError(f"unknown datadir_mgr scope {scope}")
        if scope not in self.request_scopes:
            raise ValueError(f"scope {scope} not found in request")
        outdir = self.request_scopes[scope].path
        if create and not outdir.exists():
            outdir.mkdir(exist_ok=True, parents=True)
        return outdir

    def paths_from_scope(
        self,
        module=None,
        cls=None,
        func=None,
        excludepaths=None,
        excludepatterns=None,
    ):
        """Return all paths to files in a given scope."""
        search_scopes = self.ScopedDataDirDict(
            self.datapath,
            self.NameObject(module, cls=cls, func=func),
            keep_global=True,
        )
        for scope in SCOPES:  # find most-specific scope requested
            if scope in search_scopes:
                search_scope = search_scopes[scope]
                break
        search_dir = search_scope.path
        if not search_dir.exists():
            if self.verbose:
                print("No extant datadir at requested scope")
            return []
        found_paths = self.find_all_files(
            search_dir,
            excludepaths=excludepaths,
            excludepatterns=excludepatterns,
            relative=True,
        )
        if self.verbose:
            print(
                f"Found {len(found_paths)} paths from scope {search_dir.name}."
            )
        return found_paths

    def download(
        self,
        download_url=None,
        files=None,
        scope="module",
        gunzip=False,
        md5_check=False,
        progressbar=False,
    ):
        """Download files to datafile directory at scope with optional gunzip and MD5 check."""
        if download_url is None:
            raise ValueError("download_url must be specified")
        if files is None:
            raise ValueError("iterable of files must be specified")
        download_path = self.scope_to_path(scope)
        for filename in files:
            if not (download_path / filename).exists():
                if not download_url.endswith("/"):
                    download_url += "/"
                path = download_path / filename
                dlname = filename
                if gunzip:
                    dlname += ".gz"
                if md5_check:
                    md5 = dlname + ".md5"
                    check_type = "MD5 checked"
                    if self.verbose:
                        print(
                            f"downloading {download_url}{dlname} with MD5 check"
                        )
                    md5_path = download_path / md5
                    if not md5_path.exists():
                        request_download(download_url + md5, md5_path)
                    md5_val = md5_path.read_text().split()[0]
                    md5_path.unlink()
                else:
                    check_type = ""
                    if self.verbose:
                        print(f"downloading {download_url}{dlname}")
                tmp_path = download_path / (dlname + ".tmp")
                hasher = HashTracker(hashlib.md5())
                if progressbar:
                    trackers = (hasher, ProgressTracker(DataTransferBar()))
                else:
                    trackers = (hasher,)
                request_download(
                    download_url + dlname, tmp_path, trackers=trackers
                )
                hash_val = hasher.hashobj.hexdigest()
                if (not md5_check) or (md5_val == hash_val):
                    if gunzip:
                        with gzip.open(tmp_path, "rb") as f_in:
                            with path.open("wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        tmp_path.unlink()
                        if self.verbose:
                            print(f"ungzipped {check_type} file to {path}")
                    else:
                        tmp_path.rename(path)
                        if self.verbose:
                            print(f"downloaded {check_type} file to {path}")
                else:
                    raise ValueError(
                        f"\nhash of {dlname}={hash_val}, expected {md5_val}"
                    )

    @contextlib.contextmanager
    def in_tmp_dir(
        self,
        inpathlist=None,
        save_outputs=False,
        outscope="module",
        excludepaths=None,
        excludepatterns=None,
        progressbar=False,
    ):
        """Copy data and change context to tmp_path directory."""
        cwd = Path.cwd()
        if excludepaths is None:
            excludepaths = []
        if inpathlist is None:
            inpathlist = []
        else:
            inpaths = [Path(p) for p in inpathlist]
            scoped_paths = [self[p] for p in inpaths]
            path_sizes = [p.stat().st_size for p in scoped_paths]
            total_input_filesize = sum(path_sizes)
            if progressbar:
                print(
                    f"Copying {len(inpaths)} files into {self.tmp_path}",
                    flush=True,
                )
                progress_bar = DataTransferBar()
                progress_bar.start(max_value=total_input_filesize)
                transferred = 0
            for i, inpath in enumerate(inpaths):
                inpathdir = self.tmp_path / inpath.parent
                inpathdir.mkdir(exist_ok=True, parents=True)
                shutil.copy2(scoped_paths[i], inpathdir / inpath.name)
                if progressbar:
                    transferred += path_sizes[i]
                    progress_bar.update(transferred)
            if progressbar:
                progress_bar.finish()
        os.chdir(self.tmp_path)
        try:
            yield
        finally:
            if save_outputs:
                self.save_outputs(
                    excludepaths=inpathlist + excludepaths,
                    excludepatterns=excludepatterns,
                    progressbar=progressbar,
                    scope=outscope,
                )
            os.chdir(cwd)

    def save_outputs(
        self,
        excludepaths=None,
        excludepatterns=None,
        progressbar=False,
        scope="module",
    ):
        """Save all outputs, with exclusions,  to a scope."""
        if excludepaths is None:
            excluded_paths = []
        else:
            excluded_paths = [Path(path) for path in excludepaths]
        outpaths = self.find_all_files(
            Path("."),
            excludepaths=excluded_paths,
            excludepatterns=excludepatterns,
        )
        path_sizes = [p.stat().st_size for p in outpaths]
        total_save_filesize = sum(path_sizes)
        if progressbar:
            print(
                f"Saving {len(outpaths)} output files from {self.tmp_path}",
                flush=True,
            )
            progress_bar = DataTransferBar()
            progress_bar.start(max_value=total_save_filesize)
            transferred = 0
        for i, outpath in enumerate(outpaths):
            outpath = outpaths[i]
            self.savepath(outpath, scope=scope)
            if progressbar:
                transferred += path_sizes[i]
                progress_bar.update(transferred)
        if progressbar:
            progress_bar.finish()

    def savepath(self, path, scope="module"):
        """Save a path in cwd to datadir at specified scope."""
        scopedir = self.scope_to_path(scope)
        if self.verbose:
            print(f'saving "{path}" to {scopedir}"', flush=True)
        outdir = scopedir / path.parent
        if outdir != scopedir and not outdir.exists():
            outdir.mkdir(parents=True)
        shutil.copy2(path, outdir / path.name)

    def find_all_files(
        self, dir_path, excludepaths=None, excludepatterns=None, relative=False
    ):
        """Return a list of all files in directory not in exclusion list."""
        file_list = []
        if excludepatterns is None:
            excludepatterns = []
        if excludepaths is None:
            excludepaths = []
        # Exclude directories whose names conflict with module or test functions.
        excludepaths += [
            d.relative_to(dir_path)
            for d in dir_path.glob("test_*")
            if d.is_dir()
        ]
        excludepaths += [
            d.relative_to(dir_path)
            for d in dir_path.glob("*_test")
            if d.is_dir()
        ]
        excluded_paths = set(excludepaths)
        file_paths = [f for f in dir_path.rglob("*") if f.is_file()]
        for abspath in file_paths:
            relpath = abspath.relative_to(dir_path)
            try:
                top_parent = list(relpath.parents)[-2]
            except IndexError:
                top_parent = None
            if (relpath in excluded_paths) or (top_parent in excluded_paths):
                continue
            if any([relpath.match(p) for p in excludepatterns]):
                continue
            if relative:
                file_list.append(relpath)
            else:
                file_list.append(abspath)
        if self.verbose:
            print(
                f"{len(file_list)} out of {len(file_list)} file paths passed exclusion."
            )
        return file_list

    def __repr__(self):
        """Show base directory."""
        return f"Manager of test data under {self.datapath}"


@pytest.fixture
def datadir_mgr(request, tmp_path, pytestconfig):
    """Enable downloading and caching of data files.

    Inspired by the `pytest-datadir-ng plugin <https://github.com/Tblue/pytest-datadir-ng>`_,
    it implements the same directory hierarchy.
    """
    return DataDirManager(request, tmp_path, pytestconfig)
