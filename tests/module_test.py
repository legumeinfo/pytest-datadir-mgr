# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# third-party imports
import pytest

DLFILE = "LICENSE"
TESTFILE = "data1.txt"
NEWPATH = Path("new") / "subdir" / "hello.txt"
NEWMSG = "data saved from test_in_tmp_dir\n"
LOGPATH = Path("test_in_tmp_dir.log")


def test_function_scope(datadir_mgr):
    print("testing function scope")
    data1_path = datadir_mgr[TESTFILE]
    with open(data1_path, "r") as fh:
        contents = fh.read()
        assert contents == "data at function scope\n"


def test_download(datadir_mgr):
    print("testing downloads")
    datadir_mgr.download(
        "https://raw.githubusercontent.com/ncgr/pytest-datadir-mgr/master/",
        files=[DLFILE],
        scope="module",
        progressbar=True,
    )
    bionorm_license_path = datadir_mgr[DLFILE]
    self_license_path = Path(__file__).parent.parent / DLFILE
    with open(bionorm_license_path, "r") as dlfh:
        BSD3 = dlfh.read()
    with open(self_license_path, "r") as selffh:
        license_txt = selffh.read()
    assert license_txt == BSD3


def test_saved_data(datadir_mgr):
    print("testing saved data")
    datadir_mgr.add_scope("saved data", module="global_test", func="test_savepath")
    data1_path = datadir_mgr[TESTFILE]
    with open(data1_path, "r") as fh:
        contents = fh.read()
        assert contents == "data saved from test_savepath\n"


def test_in_tmp_dir(datadir_mgr):
    print("testing in_tmp_dir")
    with datadir_mgr.in_tmp_dir(
        inpathlist=[DLFILE, TESTFILE], save_outputs=True, outscope="function", excludepattern="*.log"
    ):
        data1 = open(datadir_mgr[TESTFILE]).read()
        dlpath = Path(DLFILE)
        assert data1 == "data at module scope\n"
        assert dlpath.exists()
        NEWPATH.parent.mkdir(parents=True, exist_ok=True)
        with NEWPATH.open("w") as fh:
            fh.write(NEWMSG)
        with LOGPATH.open("w") as logfh:
            logfh.write("here is a log file")
    assert not dlpath.exists()


def test_autosaved_data(datadir_mgr):
    print("testing autosaved data")
    datadir_mgr.add_scope("autosaved data", module="module_test", func="test_in_tmp_dir")
    with pytest.raises(KeyError):  # better not find the log file
        logpath = datadir_mgr[LOGPATH]
    print(f"log file {logpath} was not saved, as it should be.")
    with datadir_mgr.in_tmp_dir(inpathlist=[NEWPATH]):
        hellomsg = NEWPATH.open().read()
        assert hellomsg == NEWMSG
