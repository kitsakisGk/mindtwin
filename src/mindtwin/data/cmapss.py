"""NASA C-MAPSS turbofan engine degradation dataset.

Saxena, Goebel, Simon and Eklund (2008). Damage propagation modeling for aircraft engine
run-to-failure simulation. PHM08.

Usage::

    python -m mindtwin.data.cmapss download          # once, ~12 MB
    from mindtwin.data.cmapss import load_cmapss
    data = load_cmapss("FD001")
    data.train.head()

The data directory defaults to ``./data/raw/cmapss`` and can be changed with the
``MINDTWIN_DATA_DIR`` environment variable.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DATA_URL = (
    "https://phm-datasets.s3.amazonaws.com/NASA/"
    "6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip"
)
DATA_SHA256 = "c9c5dec12a945a82e8bb4446589d7fb3cc057b5e5d81fa1a12e25ee9912ad3b2"
INNER_ZIP = "6. Turbofan Engine Degradation Simulation Data Set/CMAPSSData.zip"

SUBSETS = ("FD001", "FD002", "FD003", "FD004")

# Subset facts from the dataset readme, checked against the files. The readme swaps the FD004
# unit counts (it says 248 train / 249 test); the files contain 249 train / 248 test.
SUBSET_INFO = {
    "FD001": {"conditions": 1, "fault_modes": ("HPC",), "train_units": 100, "test_units": 100},
    "FD002": {"conditions": 6, "fault_modes": ("HPC",), "train_units": 260, "test_units": 259},
    "FD003": {
        "conditions": 1,
        "fault_modes": ("HPC", "Fan"),
        "train_units": 100,
        "test_units": 100,
    },
    "FD004": {
        "conditions": 6,
        "fault_modes": ("HPC", "Fan"),
        "train_units": 249,
        "test_units": 248,
    },
}

# Sensor names and meaning (Saxena et al. 2008, Table 2).
SENSOR_INFO = {
    "s1": ("T2", "Total temperature at fan inlet", "°R"),
    "s2": ("T24", "Total temperature at LPC outlet", "°R"),
    "s3": ("T30", "Total temperature at HPC outlet", "°R"),
    "s4": ("T50", "Total temperature at LPT outlet", "°R"),
    "s5": ("P2", "Pressure at fan inlet", "psia"),
    "s6": ("P15", "Total pressure in bypass duct", "psia"),
    "s7": ("P30", "Total pressure at HPC outlet", "psia"),
    "s8": ("Nf", "Physical fan speed", "rpm"),
    "s9": ("Nc", "Physical core speed", "rpm"),
    "s10": ("epr", "Engine pressure ratio (P50/P2)", "-"),
    "s11": ("Ps30", "Static pressure at HPC outlet", "psia"),
    "s12": ("phi", "Ratio of fuel flow to Ps30", "pps/psi"),
    "s13": ("NRf", "Corrected fan speed", "rpm"),
    "s14": ("NRc", "Corrected core speed", "rpm"),
    "s15": ("BPR", "Bypass ratio", "-"),
    "s16": ("farB", "Burner fuel-air ratio", "-"),
    "s17": ("htBleed", "Bleed enthalpy", "-"),
    "s18": ("Nf_dmd", "Demanded fan speed", "rpm"),
    "s19": ("PCNfR_dmd", "Demanded corrected fan speed", "rpm"),
    "s20": ("W31", "HPT coolant bleed", "lbm/s"),
    "s21": ("W32", "LPT coolant bleed", "lbm/s"),
}

SETTING_COLS = ["setting1", "setting2", "setting3"]
SENSOR_COLS = list(SENSOR_INFO)
COLUMNS = ["unit", "cycle", *SETTING_COLS, *SENSOR_COLS]

DEFAULT_RUL_CAP = 125


@dataclass
class CMAPSSData:
    """One C-MAPSS subset.

    ``train`` and ``test`` have one row per (unit, cycle) and a ``rul`` column with the true
    remaining useful life at that cycle. ``test_rul`` holds the official target: the RUL at the
    last observed cycle of each test unit.
    """

    subset: str
    train: pd.DataFrame
    test: pd.DataFrame
    test_rul: pd.Series

    def test_last_cycles(self) -> pd.DataFrame:
        """Last observed row of each test unit (the rows scored in the benchmark)."""
        return self.test.groupby("unit", as_index=False).last()


def default_data_dir() -> Path:
    return Path(os.environ.get("MINDTWIN_DATA_DIR", "data/raw/cmapss"))


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract(archive: bytes, data_dir: Path) -> None:
    """Extract the .txt files of the inner CMAPSSData.zip into ``data_dir``."""
    outer = zipfile.ZipFile(io.BytesIO(archive))
    inner = zipfile.ZipFile(io.BytesIO(outer.read(INNER_ZIP)))
    data_dir.mkdir(parents=True, exist_ok=True)
    for info in inner.infolist():
        name = Path(info.filename).name
        if name.endswith(".txt"):
            (data_dir / name).write_bytes(inner.read(info))


def download(data_dir: Path | None = None, force: bool = False) -> Path:
    """Download and extract C-MAPSS. Verifies the archive checksum. Returns the data dir."""
    data_dir = Path(data_dir) if data_dir else default_data_dir()
    if not force and all((data_dir / f"train_{s}.txt").exists() for s in SUBSETS):
        return data_dir
    with urllib.request.urlopen(DATA_URL, timeout=120) as response:
        archive = response.read()
    digest = _sha256(archive)
    if digest != DATA_SHA256:
        raise ValueError(f"Checksum mismatch for C-MAPSS archive: {digest}")
    extract(archive, data_dir)
    return data_dir


def read_raw(path: Path) -> pd.DataFrame:
    """Read one space-separated C-MAPSS text file."""
    df = pd.read_csv(path, sep=r"\s+", header=None, names=COLUMNS, engine="python")
    return df.astype({"unit": int, "cycle": int})


def load_cmapss(subset: str, data_dir: Path | None = None) -> CMAPSSData:
    """Load a subset (``"FD001"`` … ``"FD004"``) with RUL labels."""
    subset = subset.upper()
    if subset not in SUBSETS:
        raise ValueError(f"Unknown subset {subset!r}, expected one of {SUBSETS}")
    data_dir = Path(data_dir) if data_dir else default_data_dir()
    train_path = data_dir / f"train_{subset}.txt"
    if not train_path.exists():
        raise FileNotFoundError(
            f"{train_path} not found. Run `python -m mindtwin.data.cmapss download` first."
        )

    train = read_raw(train_path)
    train["rul"] = train.groupby("unit")["cycle"].transform("max") - train["cycle"]

    test = read_raw(data_dir / f"test_{subset}.txt")
    rul_values = np.loadtxt(data_dir / f"RUL_{subset}.txt", dtype=int, ndmin=1)
    units = np.sort(test["unit"].unique())
    test_rul = pd.Series(rul_values, index=pd.Index(units, name="unit"), name="rul")
    last_cycle = test.groupby("unit")["cycle"].transform("max")
    test["rul"] = test["unit"].map(test_rul) + (last_cycle - test["cycle"])

    return CMAPSSData(subset=subset, train=train, test=test, test_rul=test_rul)


def piecewise_rul(rul: pd.Series | np.ndarray, cap: int = DEFAULT_RUL_CAP):
    """Piecewise-linear RUL target: constant ``cap`` early in life, then linear to zero."""
    return np.minimum(rul, cap)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m mindtwin.data.cmapss")
    sub = parser.add_subparsers(dest="command", required=True)
    dl = sub.add_parser("download", help="download and extract the dataset")
    dl.add_argument("--data-dir", type=Path, default=None)
    dl.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "download":
        path = download(args.data_dir, force=args.force)
        print(f"C-MAPSS ready in {path}")


if __name__ == "__main__":
    main()
