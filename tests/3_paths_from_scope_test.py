# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# first-party imports
from tests.common import DLFILE
from tests.common import NEWPATH
from tests.common import TESTFILE


def test_paths_from_scope(datadir_mgr):
    """Test finding sets of saved data."""
    in_tmp_paths = datadir_mgr.paths_from_scope(module="2_module_test", func="test_in_tmp_dir")
    assert len(in_tmp_paths) == 1
    assert in_tmp_paths[0] == NEWPATH
    module_test_paths = datadir_mgr.paths_from_scope(module="2_module_test")
    assert len(module_test_paths) == 2
    datadir_mgr.add_scope("autosaved data", module="2_module_test", func="test_in_tmp_dir")
    with datadir_mgr.in_tmp_dir(inpathlist=in_tmp_paths + module_test_paths):
        filepaths = [p for p in Path(".").rglob("*") if p.is_file()]
        assert len(filepaths) == 3
        assert NEWPATH in filepaths
        assert Path(TESTFILE) in filepaths
        assert Path(DLFILE) in filepaths
