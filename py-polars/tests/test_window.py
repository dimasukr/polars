from typing import Type

import numpy as np
import pytest

import polars as pl


@pytest.mark.parametrize("dtype", [pl.Float32, pl.Float64, pl.Int32])
def test_std(dtype: Type[pl.DataType]) -> None:
    if dtype == pl.Int32:
        df = pl.DataFrame(
            [
                pl.Series("groups", ["a", "a", "b", "b"]),
                pl.Series("values", [1, 2, 3, 4], dtype=dtype),
            ]
        )
    else:
        df = pl.DataFrame(
            [
                pl.Series("groups", ["a", "a", "b", "b"]),
                pl.Series("values", [1.0, 2.0, 3.0, 4.0], dtype=dtype),
            ]
        )

    out = df.select(pl.col("values").std().over("groups"))
    assert np.isclose(out["values"][0], 0.7071067690849304)

    out = df.select(pl.col("values").var().over("groups"))
    assert np.isclose(out["values"][0], 0.5)
    out = df.select(pl.col("values").mean().over("groups"))
    assert np.isclose(out["values"][0], 1.5)


def test_issue_2529() -> None:
    def stdize_out(value: str, control_for: str) -> pl.Expr:
        return (pl.col(value) - pl.mean(value).over(control_for)) / pl.std(value).over(
            control_for
        )

    df = pl.from_dicts(
        [
            {"cat": cat, "val1": cat + _, "val2": cat + _}
            for cat in range(2)
            for _ in range(2)
        ]
    )

    out = df.select(
        [
            "*",
            stdize_out("val1", "cat").alias("out1"),
            stdize_out("val2", "cat").alias("out2"),
        ]
    )
    assert out["out1"].to_list() == out["out2"].to_list()


def test_window_function_cache() -> None:
    # ensures that the cache runs the flattened first (that are the sorted groups)
    # otherwise the flattened results are not ordered correctly
    out = pl.DataFrame(
        {
            "groups": ["A", "A", "B", "B", "B"],
            "groups_not_sorted": ["A", "B", "A", "B", "A"],
            "values": range(5),
        }
    ).with_columns(
        [
            pl.col("values")
            .list()
            .over("groups")
            .alias("values_list"),  # aggregation to list + join
            pl.col("values")
            .list()
            .over("groups")
            .flatten()
            .alias("values_flat"),  # aggregation to list + explode and concat back
            pl.col("values")
            .reverse()
            .list()
            .over("groups")
            .flatten()
            .alias("values_rev"),  # use flatten to reverse within a group
        ]
    )

    assert out["values_list"].to_list() == [
        [0, 1],
        [0, 1],
        [2, 3, 4],
        [2, 3, 4],
        [2, 3, 4],
    ]
    assert out["values_flat"].to_list() == [0, 1, 2, 3, 4]
    assert out["values_rev"].to_list() == [1, 0, 4, 3, 2]


def test_arange_no_rows() -> None:
    df = pl.DataFrame(dict(x=[5, 5, 4, 4, 2, 2]))
    out = df.with_column(pl.arange(0, pl.count()).over("x"))  # type: ignore
    assert out.frame_equal(
        pl.DataFrame({"x": [5, 5, 4, 4, 2, 2], "literal": [0, 1, 0, 1, 0, 1]})
    )

    df = pl.DataFrame(dict(x=[]))
    out = df.with_column(pl.arange(0, pl.count()).over("x"))  # type: ignore
    assert out.frame_equal(pl.DataFrame({"x": [], "literal": []}))


def test_no_panic_on_nan_3067() -> None:
    df = pl.DataFrame(
        {
            "group": ["a", "a", "a", "b", "b", "b"],
            "total": [1.0, 2, 3, 4, 5, np.NaN],
        }
    )

    df.select([pl.col("total").shift().over("group")])["total"].to_list() == [
        None,
        1.0,
        2.0,
        None,
        4.0,
        5.0,
    ]


def test_quantile_as_window() -> None:
    assert (
        pl.DataFrame(
            {
                "group": [0, 0, 1, 1],
                "value": [0, 1, 0, 2],
            }
        )
        .select(pl.quantile("value", 0.9).over("group"))
        .to_series()
        .series_equal(pl.Series("value", [1.0, 1.0, 2.0, 2.0]))
    )
