import os
from fgpe.__main__ import set_up_logs, run_overlay, DATA_DIRECTORY


def test_log_setup():
    _ = set_up_logs()
    assert os.path.isdir(DATA_DIRECTORY)


def test_overlay_starts_and_exits():
    try:
        _ = run_overlay(1)
    except SystemExit as e:
        # Considering System Exit with 0 return code as graceful exit
        if e.args[0] == 0:
            pass
    assert os.path.isdir(DATA_DIRECTORY)
