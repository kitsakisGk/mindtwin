import logging
from pathlib import Path

import pytest
from pydantic import ValidationError

from mindtwin.config import Settings, load_settings
from mindtwin.log import get_logger, setup_logging


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for name in Settings.model_fields:
        monkeypatch.delenv(f"MINDTWIN_{name.upper()}", raising=False)
    monkeypatch.delenv("MINDTWIN_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)


def test_defaults():
    s = load_settings()
    assert s.rul_cap == 125
    assert s.data_dir == Path("data/raw/cmapss")


def test_file_then_env_precedence(tmp_path, monkeypatch):
    cfg = tmp_path / "mindtwin.toml"
    cfg.write_text('seed = 7\nrul_cap = 130\nlog_level = "DEBUG"\n')
    assert load_settings().seed == 7
    monkeypatch.setenv("MINDTWIN_SEED", "3")
    s = load_settings()
    assert (s.seed, s.rul_cap, s.log_level) == (3, 130, "DEBUG")


def test_invalid_values_rejected(tmp_path):
    cfg = tmp_path / "bad.toml"
    cfg.write_text("rul_cap = -1\n")
    with pytest.raises(ValidationError):
        load_settings(cfg)
    cfg.write_text("unknown_field = 1\n")
    with pytest.raises(ValidationError):
        load_settings(cfg)


def test_get_logger_namespacing():
    assert get_logger().name == "mindtwin"
    assert get_logger("mindtwin.data").name == "mindtwin.data"
    assert get_logger("experiments").name == "mindtwin.experiments"


def test_setup_logging_is_idempotent():
    logger = setup_logging("WARNING")
    setup_logging("WARNING")
    ours = [h for h in logger.handlers if getattr(h, "_mindtwin", False)]
    assert len(ours) == 1
    assert logger.level == logging.WARNING
