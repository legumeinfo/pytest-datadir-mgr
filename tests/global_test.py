# -*- coding: utf-8 -*-

# standard library imports
import os
import shutil
from pathlib import Path


def test_setup(request):
    """Remove datadir, if it exists, and install copies of static data."""
    testdir = Path(request.fspath.dirpath())
    datadir = testdir / "data"
    if datadir.exists():
        shutil.rmtree(datadir)  # remove anything left in data directory
    filesdir = testdir / "testdata"
    shutil.copytree(filesdir, datadir)


def test_global_scope(datadir_mgr):
    """Test file at global scope."""
    data1_path = datadir_mgr["data1.txt"]
    with open(data1_path, "r") as fh:
        contents = fh.read()
        assert contents == "data at global scope\n"


def test_add_scope(datadir_mgr):
    """Test add scope to a search path."""
    datadir_mgr.add_scope("function from global", module="module_test", func="test_function_scope")
    data1_path = datadir_mgr["data1.txt"]
    with open(data1_path, "r") as fh:
        contents = fh.read()
        assert contents == "data at function scope\n"


def test_savepath(datadir_mgr, tmpdir):
    """Test saving file to a scope."""
    os.chdir(tmpdir)
    data1_path = Path("data1.txt")
    with data1_path.open("w") as fh:
        fh.write("data saved from test_savepath\n")
    datadir_mgr.savepath(data1_path, scope="function")
