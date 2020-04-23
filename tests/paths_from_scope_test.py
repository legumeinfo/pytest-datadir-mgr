# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# third-party imports
import pytest


TESTFILE = "data1.txt"
NEWPATH = Path("new") / "subdir" / "hello.txt"
NEWMSG = "data saved from test_in_tmp_dir\n"

def test_paths_from_scope(datadir_mgr):
    """Test finding sets of saved data."""
    in_tmp_paths = datadir_mgr.paths_from_scope(module="module_test", func="test_in_tmp_dir")
    print("in_tmp_paths=", in_tmp_paths)
    assert len(in_tmp_paths) == 1
    assert in_tmp_paths[0] == NEWPATH
    module_test_paths = datadir_mgr.paths_from_scope(module="module_test")
    print("module_test_paths=", module_test_paths)
    assert len(module_test_paths) == 2
    datadir_mgr.add_scope("autosaved data", module="module_test", func="test_in_tmp_dir")
    with datadir_mgr.in_tmp_dir(inpathlist=in_tmp_paths):
        hellomsg = NEWPATH.open().read()
        assert hellomsg == NEWMSG
