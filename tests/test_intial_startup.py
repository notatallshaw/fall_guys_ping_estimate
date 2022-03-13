import os
from fgpe.__main__ import set_up_logs, DATA_DIRECTORY


def test_log_setup():
    _ = set_up_logs()
    assert os.path.isdir(DATA_DIRECTORY)
