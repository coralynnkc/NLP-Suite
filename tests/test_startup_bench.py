"""tests/startup_bench.py: targets are parsed and the report is built from the recorded times."""

import os

import pytest
import startup_bench as sb


def test_a_dev_env_target_is_python_and_src(tmp_path):
    label, py, src = sb.parse_target(f"dev=/usr/bin/python3:{tmp_path}")
    assert (label, py, src) == ("dev", "/usr/bin/python3", str(tmp_path))


def test_a_bundle_target_uses_its_python_env(tmp_path):
    (tmp_path / "python-env" / "bin").mkdir(parents=True)
    (tmp_path / "python-env" / "bin" / "python3").write_text("")
    (tmp_path / "src").mkdir()
    label, py, src = sb.parse_target(f"1.6.47={tmp_path}")
    assert py == os.path.join(str(tmp_path), "python-env", "bin", "python3")
    assert src == os.path.join(str(tmp_path), "src")


def test_a_target_without_a_label_is_refused():
    with pytest.raises(SystemExit):
        sb.parse_target("/some/folder")


def test_report_gives_first_warm_and_the_ratio_to_the_first_target():
    times = lambda first, warm: {"first": first, "median": warm, "samples": [first, warm, warm], "error": ""}  # noqa: E731
    result = {
        "repeat": 3,
        "targets": {
            "old": {"times": {"python": times(0.1, 0.02), "guis:a_main.py": times(4.0, 2.0)}},
            "new": {"times": {"python": times(0.1, 0.01), "guis:a_main.py": times(3.0, 1.0)}},
        },
    }
    text = sb.report(result)
    assert "| python | 0.10 | 0.02 | 0.10 | 0.01 | 0.50 |" in text
    assert "| a_main.py | 4.00 | 2.00 | 3.00 | 1.00 | 0.50 |" in text
