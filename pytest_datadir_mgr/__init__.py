# -*- coding: utf-8 -*-
"""datadir_mgr fixture for pytest."""

# standard library imports
import contextlib
import gzip
import hashlib
import os
import shutil
from collections import OrderedDict
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
SCOPES = ("function", "class", "module", "global")  # ordered from lowest to highest


class DataDirManager(object):

    """Download, cache, and optionally verify and gzip test files from a specified URL."""

    class NameObject(object):

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

        class Scope(object):

            """Class holding a path and a name."""

            def __init__(self, basepath, name):
                """Save path and name."""
                self.path = basepath / name
                self.name = name

        def __init__(self, globalpath, nameobj, keep_global=True):
            """Create dictionary of paths at different scopes."""
            dict.__init__(self)  # create empty dict
            self["global"] = self.Scope(globalpath.parent, str(globalpath.name))
            self["module"] = self.Scope(self["global"].path, nameobj.module.__name__)
            if nameobj.cls is not None:
                self["class"] = self.Scope(self["module"].path, nameobj.cls.__name__)
                if nameobj.function.__name__ is not None:
                    self["function"] = self.Scope(self["class"].path, nameobj.function.__name__)
            else:
                if nameobj.function.__name__ is not None:
                    self["function"] = self.Scope(self["module"].path, nameobj.function.__name__)
            if not keep_global:
                del self["global"]

    def __init__(self, request, tmp_path):
        """Stash a copy of the request and init."""
        self.request = request
        self.datapath = Path(request.fspath.dirpath()) / GLOBAL_SUBDIR
        self.tmp_path = tmp_path
        self.request_scopes = self.ScopedDataDirDict(self.datapath, request)
        self.scopes = OrderedDict([("request", self.request_scopes)])

    def __getitem__(self, filepath):
        """Look for a filepath in all the datadirs, with smallest scope first."""
        for scopekey in reversed(self.scopes.keys()):  # search last-added first
            for level in SCOPES:  # search smallest scope first
                if level in self.scopes[scopekey]:  # not every scope may exist
                    levelpath = self.scopes[scopekey][level].path
                    name = self.scopes[scopekey][level].name
                    datapath = levelpath / filepath
                    if datapath.exists():
                        print(f'path "{filepath}" found in scope "{scopekey}" level "{level}" name "{name}"')
                        return datapath
        raise KeyError(f"Path '{filepath}' not found in the datadir scopes {self.scopes.keys()}")

    def add_scope(self, scope_name, module=None, cls=None, func=None):
        """Add scopes to be searched for data files, in addition to request."""
        self.scopes[scope_name] = self.ScopedDataDirDict(
            self.datapath, self.NameObject(module, cls=cls, func=func), keep_global=False
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

    def download(self, download_url=None, files=None, scope="module", gunzip=False, md5_check=False, progressbar=False):
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
                    print(f"downloading {download_url}{dlname} with MD5 check")
                    md5_path = download_path / md5
                    if not md5_path.exists():
                        request_download(download_url + md5, md5_path)
                    md5_val = md5_path.read_text().split()[0]
                    md5_path.unlink()
                else:
                    check_type = ""
                    print(f"downloading {download_url}{dlname}")
                tmp_path = download_path / (dlname + ".tmp")
                hasher = HashTracker(hashlib.md5())
                if progressbar:
                    trackers = (hasher, ProgressTracker(DataTransferBar()))
                else:
                    trackers = (hasher,)
                request_download(download_url + dlname, tmp_path, trackers=trackers)
                hash_val = hasher.hashobj.hexdigest()
                if (not md5_check) or (md5_val == hash_val):
                    if gunzip:
                        with gzip.open(tmp_path, "rb") as f_in:
                            with path.open("wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        tmp_path.unlink()
                        print(f"ungzipped {check_type} file to {path}")
                    else:
                        tmp_path.rename(path)
                        print(f"downloaded {check_type} file to {path}")
                else:
                    raise ValueError(f"\nhash of {dlname}={hash_val}, expected {md5_val}")

    @contextlib.contextmanager
    def in_tmp_dir(self, inpathlist=None, save_outputs=False, outscope="module", excludepattern=""):
        """Copy data and change context to tmp_path directory."""
        cwd = Path.cwd()
        if inpathlist is not None:
            inpathlist = [Path(path) for path in inpathlist]
            for inpath in inpathlist:
                inpathdir = self.tmp_path / inpath.parent
                inpathdir.mkdir(exist_ok=True, parents=True)
                shutil.copy2(self[Path(inpath)], inpathdir / inpath.name)
        os.chdir(self.tmp_path)
        print(f"running test in {self.tmp_path}")
        try:
            yield
        finally:
            if save_outputs:
                outpaths = self.find_all_files(Path("."), excludepaths=inpathlist, excludepattern=excludepattern)
                for outpath in outpaths:
                    self.savepath(outpath, scope=outscope)
            os.chdir(cwd)

    def savepath(self, path, scope="module"):
        """Save a path in cwd to datadir at specified scope."""
        scopedir = self.scope_to_path(scope)
        print(f'saving "{path}" to {scopedir}"')
        outdir = scopedir / path.parent
        if outdir != scopedir and not outdir.exists():
            outdir.mkdir(parents=True)
        shutil.copy2(path, outdir / path.name)

    def find_all_files(self, directory, excludepaths=None, excludepattern=None):
        """Return a list of all files in directory not in exclusion list."""
        file_list = []
        for x in directory.iterdir():
            if x.is_file() and (x not in excludepaths):
                if (not excludepattern == None) and (x.match(excludepattern)):
                    continue
                else:
                    file_list.append(x)
            elif x.is_dir():
                file_list.extend(self.find_all_files(x, excludepaths=excludepaths, excludepattern=excludepattern))
        return file_list

    def __repr__(self):
        """Show base directory."""
        return f"Manager of test data under {self.datapath}"


@pytest.fixture
def datadir_mgr(request, tmp_path):
    """Enable downloading and caching of data files.

    Inspired by the `pytest-datadir-ng plugin <https://github.com/Tblue/pytest-datadir-ng>`_,
    it implements the same directory hierarchy.
    """
    return DataDirManager(request, tmp_path)
