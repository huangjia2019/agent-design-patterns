"""Invariants for the collaboration-module stress ablation."""

from __future__ import annotations

from collaboration import stress_collab as lab


def test_each_pattern_closes_its_own_boundary_leak() -> None:
    results = lab.run_all()

    assert [result["vector"] for result in results] == lab.VNAMES
    assert [result["closes_at"] for result in results] == [
        "C1",
        "C2",
        "C3",
        "C4",
    ]
    assert all(result["naive_leaked"] for result in results)
    assert all(result["guarded_blocked"] for result in results)


def test_ablation_ladder_closes_exactly_one_more_vector_per_level() -> None:
    for level_index, (level, _title) in enumerate(lab.LEVELS):
        closed = sum(lab._cell(vector_index, level) == "✓" for vector_index in range(4))
        assert closed == level_index


def test_table_reports_a_clean_final_level(capsys) -> None:
    lab.table()

    output = capsys.readouterr().out
    assert "Stress 协作全景" in output
    assert "L4" in output
    assert "全干净" in output
    for vector in lab.VNAMES:
        assert vector in output
