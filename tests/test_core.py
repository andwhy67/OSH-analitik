from __future__ import annotations

import numpy as np
import pandas as pd

from app.modules.core.expert import (
    kemeny_distance,
    kendall_w,
    median_ranking,
)
from app.modules.core.matrix import BinaryMatrix
from app.modules.core.optimization import KhubaevOptimizer, OptimizationConfig
from app.modules.core.ranking import (
    missing_characteristics,
    rank_objects_by_dominance,
    rank_objects_by_richness,
)
from app.modules.core.similarity import (
    inclusion_matrix,
    jaccard_matrix,
    sorensen_dice_matrix,
)


def _toy_matrix() -> BinaryMatrix:
    data = np.array(
        [
            [1, 1, 1, 0, 0],
            [1, 1, 0, 0, 0],
            [1, 1, 1, 1, 1],
            [0, 0, 1, 1, 0],
        ],
        dtype=np.int8,
    )
    return BinaryMatrix(data, objects=list("ABCD"), features=list("vwxyz"))


def test_jaccard_basic():
    bm = _toy_matrix()
    j = jaccard_matrix(bm)
    assert j.shape == (4, 4)
    assert np.allclose(np.diag(j), 1.0)
    # B имеет 2 признака, оба есть у A — jaccard(A,B)=2/3
    assert abs(j[0, 1] - 2 / 3) < 1e-9


def test_inclusion_asymmetric():
    bm = _toy_matrix()
    inc = inclusion_matrix(bm)
    # B полностью включён в A: inc[B,A] == 1
    assert inc[1, 0] == 1.0
    # обратное — нет
    assert inc[0, 1] < 1.0


def test_sorensen_in_range():
    bm = _toy_matrix()
    s = sorensen_dice_matrix(bm)
    assert (s >= 0.0).all() and (s <= 1.0).all()


def test_rankings_and_missing():
    bm = _toy_matrix()
    rich = rank_objects_by_richness(bm)
    assert list(rich["object"])[0] == "C"  # C — самый "богатый"
    dom = rank_objects_by_dominance(bm)
    assert "object" in dom.columns
    miss = missing_characteristics(bm, min_coverage=0.5)
    assert {"object", "feature", "coverage"} <= set(miss.columns)


def test_optimizer_runs():
    bm = _toy_matrix()
    res = KhubaevOptimizer(
        OptimizationConfig(min_feature_frequency=0.1, max_feature_frequency=0.99)
    ).run(bm)
    assert res.optimized_matrix.n_features >= 1
    assert {"feature", "informativeness", "frequency", "kept"} <= set(
        res.feature_importance.columns
    )


def test_expert_metrics():
    df = pd.DataFrame(
        [[1, 2, 3], [1, 3, 2], [2, 1, 3]],
        index=["E1", "E2", "E3"],
        columns=["A", "B", "C"],
    )
    d = kemeny_distance(df.iloc[0].to_numpy(), df.iloc[1].to_numpy())
    assert d == 1
    w = kendall_w(df)
    assert 0.0 <= w <= 1.0
    med = median_ranking(df)
    assert set(med.values) == {1, 2, 3}


def test_loader_roundtrip(tmp_path):
    from app.modules.data.io import DataLoader, LoadOptions, save_matrix

    bm = _toy_matrix()
    p = tmp_path / "m.csv"
    save_matrix(bm, p)
    loaded = DataLoader(LoadOptions()).load(p)
    assert loaded.shape == bm.shape
    assert loaded.objects == bm.objects
    assert loaded.features == bm.features
    assert (loaded.data == bm.data).all()
