from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.modules.core.clustering import cluster_experts, cluster_objects
from app.modules.core.expert import (
    aggregate_binary_experts,
    kemeny_distance,
    kendall_w,
    median_ranking,
)
from app.modules.core.matrix import BinaryMatrix
from app.modules.core.optimization import KhubaevOptimizer, OptimizationConfig
from app.modules.core.similarity import inclusion_matrix, jaccard_matrix


def test_matrix_all_zeros():
    bm = BinaryMatrix(np.zeros((3, 4), dtype=np.int8))
    sim = jaccard_matrix(bm)
    assert sim.shape == (3, 3)
    assert np.allclose(np.diag(sim), 1.0)
    # вне диагонали — нули (пересечение пустых множеств)
    assert sim[0, 1] == 0.0


def test_matrix_all_ones():
    bm = BinaryMatrix(np.ones((3, 4), dtype=np.int8))
    sim = jaccard_matrix(bm)
    assert np.allclose(sim, 1.0)
    inc = inclusion_matrix(bm)
    assert np.allclose(inc, 1.0)


def test_single_object_matrix():
    bm = BinaryMatrix(np.array([[1, 0, 1]], dtype=np.int8))
    sim = jaccard_matrix(bm)
    assert sim.shape == (1, 1)
    assert sim[0, 0] == 1.0


def test_optimizer_preserves_minimum_features():
    bm = BinaryMatrix(
        np.array([[1, 1, 1], [0, 0, 0], [1, 0, 1]], dtype=np.int8),
        objects=["A", "B", "C"],
        features=["x", "y", "z"],
    )
    cfg = OptimizationConfig(
        min_feature_frequency=0.99,  # агрессивный порог — захочется удалить почти всё
        max_feature_frequency=0.999,
        informativeness_threshold=1e3,
    )
    result = KhubaevOptimizer(cfg).run(bm)
    assert result.optimized_matrix.n_features >= 2


def test_optimizer_identical_rows():
    rows = np.tile(np.array([1, 0, 1, 1], dtype=np.int8), (4, 1))
    bm = BinaryMatrix(rows)
    res = KhubaevOptimizer().run(bm)
    # на идентичных строках сходство всех со всеми равно 1
    assert np.allclose(res.similarity_after, 1.0)


def test_io_xlsx_roundtrip(tmp_path):
    from app.modules.data.io import DataLoader, LoadOptions, save_matrix

    bm = BinaryMatrix(
        np.array([[1, 0], [1, 1], [0, 1]], dtype=np.int8),
        objects=["o1", "o2", "o3"],
        features=["f1", "f2"],
    )
    p = tmp_path / "m.xlsx"
    save_matrix(bm, p)
    loaded = DataLoader(LoadOptions()).load(p)
    assert (loaded.data == bm.data).all()
    assert loaded.objects == bm.objects
    assert loaded.features == bm.features


def test_io_orientation_columns(tmp_path):
    from app.modules.data.io import DataLoader, LoadOptions

    # объекты по столбцам, характеристики по строкам
    df = pd.DataFrame(
        {"A": [1, 0, 1], "B": [1, 1, 0], "C": [0, 0, 1]},
        index=["feat1", "feat2", "feat3"],
    )
    p = tmp_path / "transposed.csv"
    df.to_csv(p)
    bm = DataLoader(LoadOptions(orientation="objects_in_columns")).load(p)
    assert bm.objects == ["A", "B", "C"]
    assert bm.features == ["feat1", "feat2", "feat3"]


def test_clustering_small():
    bm = BinaryMatrix(np.array([[1, 1], [1, 0]], dtype=np.int8))
    res = cluster_objects(bm, n_clusters=2)
    assert len(res.labels) == 2


def test_clustering_single_object():
    bm = BinaryMatrix(np.array([[1, 0, 1]], dtype=np.int8))
    res = cluster_objects(bm, n_clusters=1)
    assert len(res.labels) == 1


def test_kemeny_zero_when_identical():
    r = np.array([1, 2, 3, 4])
    assert kemeny_distance(r, r) == 0


def test_kemeny_max_when_reversed():
    a = np.array([1, 2, 3, 4])
    b = np.array([4, 3, 2, 1])
    # для n=4 максимум пар расхождения = C(4,2) = 6
    assert kemeny_distance(a, b) == 6


def test_kendall_w_unanimous():
    df = pd.DataFrame(
        [[1, 2, 3, 4]] * 5,
        index=[f"E{i}" for i in range(5)],
        columns=list("ABCD"),
    )
    w = kendall_w(df)
    assert abs(w - 1.0) < 1e-9


def test_kendall_w_single_expert_is_nan():
    df = pd.DataFrame([[1, 2, 3]], index=["E1"], columns=list("ABC"))
    assert np.isnan(kendall_w(df))


def test_median_ranking_unanimous():
    df = pd.DataFrame(
        [[1, 2, 3, 4]] * 4,
        index=[f"E{i}" for i in range(4)],
        columns=list("ABCD"),
    )
    med = median_ranking(df)
    assert list(med.values) == [1, 2, 3, 4]


def test_median_ranking_greedy_matches_exact():
    rng = np.random.default_rng(3)
    n = 5
    rows = []
    for _ in range(4):
        order = rng.permutation(n) + 1
        rows.append(order)
    df = pd.DataFrame(rows, columns=[f"O{i}" for i in range(n)])
    exact = median_ranking(df, exact_limit=10)
    greedy = median_ranking(df, exact_limit=0)
    # жадная может отличаться, но сумма расстояний жадной не сильно хуже точной
    def total(order):
        return sum(kemeny_distance(order.to_numpy(), r) for r in df.to_numpy())
    assert total(greedy) <= total(exact) * 1.5 + 1


def test_aggregate_binary_experts_mismatched_shapes_raises():
    a = BinaryMatrix(np.ones((2, 3), dtype=np.int8))
    b = BinaryMatrix(np.ones((2, 4), dtype=np.int8))
    with pytest.raises(ValueError):
        aggregate_binary_experts([a, b])


def test_aggregate_binary_experts_majority():
    objs = ["x", "y"]
    feats = ["a", "b"]
    m1 = BinaryMatrix(np.array([[1, 0], [1, 0]], dtype=np.int8), objects=objs, features=feats)
    m2 = BinaryMatrix(np.array([[1, 1], [0, 0]], dtype=np.int8), objects=objs, features=feats)
    m3 = BinaryMatrix(np.array([[1, 0], [1, 1]], dtype=np.int8), objects=objs, features=feats)
    agg = aggregate_binary_experts([m1, m2, m3], threshold=0.5)
    assert agg.matrix.data.tolist() == [[1, 0], [1, 0]]


def test_cluster_experts_basic():
    df = pd.DataFrame(
        [[1, 2, 3], [1, 2, 3], [3, 2, 1]],
        index=["E1", "E2", "E3"],
        columns=list("ABC"),
    )
    res = cluster_experts(df, n_clusters=2)
    # E1 и E2 идентичны — должны попасть в один кластер
    assert res.labels[0] == res.labels[1]
