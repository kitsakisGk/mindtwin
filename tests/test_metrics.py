import math

import pytest

from mindtwin.evaluation import phm08_score, rmse


def test_rmse():
    assert rmse([0, 0], [3, 4]) == pytest.approx(math.sqrt(12.5))


def test_phm08_perfect_is_zero():
    assert phm08_score([10, 20], [10, 20]) == 0.0


def test_phm08_late_costs_more_than_early():
    early = phm08_score([50], [40])  # 10 cycles early
    late = phm08_score([50], [60])  # 10 cycles late
    assert early == pytest.approx(math.exp(10 / 13) - 1)
    assert late == pytest.approx(math.e - 1)
    assert late > early
