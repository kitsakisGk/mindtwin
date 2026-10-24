import io
import zipfile

import numpy as np
import pytest

from mindtwin.data import cmapss


def _row(unit, cycle, base=1.0):
    values = [unit, cycle, 0.0, 0.0, 100.0] + [base + cycle * 0.1] * 21
    return " ".join(str(v) for v in values)


@pytest.fixture
def data_dir(tmp_path):
    """A tiny fake FD001: 2 train units (3 and 4 cycles), 2 test units (2 cycles each)."""
    train = [_row(1, c) for c in range(1, 4)] + [_row(2, c) for c in range(1, 5)]
    test = [_row(1, c) for c in range(1, 3)] + [_row(2, c) for c in range(1, 3)]
    (tmp_path / "train_FD001.txt").write_text("\n".join(train) + "\n")
    (tmp_path / "test_FD001.txt").write_text("\n".join(test) + "\n")
    (tmp_path / "RUL_FD001.txt").write_text("10 \n20 \n")
    return tmp_path


def test_columns():
    assert len(cmapss.COLUMNS) == 26
    assert len(cmapss.SENSOR_COLS) == 21


def test_load_train_rul(data_dir):
    data = cmapss.load_cmapss("fd001", data_dir)
    unit1 = data.train[data.train.unit == 1]
    assert unit1["rul"].tolist() == [2, 1, 0]
    assert data.train.groupby("unit")["rul"].min().tolist() == [0, 0]


def test_load_test_rul(data_dir):
    data = cmapss.load_cmapss("FD001", data_dir)
    assert data.test_rul.tolist() == [10, 20]
    unit2 = data.test[data.test.unit == 2]
    assert unit2["rul"].tolist() == [21, 20]
    last = data.test_last_cycles()
    assert last["rul"].tolist() == [10, 20]


def test_unknown_subset(data_dir):
    with pytest.raises(ValueError):
        cmapss.load_cmapss("FD999", data_dir)


def test_missing_files_hint(tmp_path):
    with pytest.raises(FileNotFoundError, match="download"):
        cmapss.load_cmapss("FD001", tmp_path)


def test_piecewise_rul():
    assert cmapss.piecewise_rul(np.array([200, 125, 50, 0])).tolist() == [125, 125, 50, 0]


def test_extract_nested_zip(tmp_path):
    inner_buf = io.BytesIO()
    with zipfile.ZipFile(inner_buf, "w") as inner:
        inner.writestr("train_FD001.txt", "x")
        inner.writestr("readme.txt", "r")
        inner.writestr("Damage Propagation Modeling.pdf", "pdf")
    outer_buf = io.BytesIO()
    with zipfile.ZipFile(outer_buf, "w") as outer:
        outer.writestr(cmapss.INNER_ZIP, inner_buf.getvalue())
    cmapss.extract(outer_buf.getvalue(), tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["readme.txt", "train_FD001.txt"]
