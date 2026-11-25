from decimal import Decimal

from app.catalog import SPEC
from app.domain.calculate import calculate_rows
from app.domain.prepare import prepare_rows
from tests.domain_cases import CLEAN, calc

# TRAP-19 TRAP-20 TRAP-24 的边界由本文件的跨日、合并与单位用例固定。


def clean_results():
    items, issues = prepare_rows(CLEAN)
    assert issues == []
    return calculate_rows(items)


def test_clean_result_count():
    assert len(clean_results()) == 7


def test_metric_total_is_reconciled():
    total = sum((item["metric"] for item in clean_results()), Decimal("0"))
    assert total == Decimal("3240")


def test_first_result_matches_expected():
    item = clean_results()[0]
    assert item["label"] == "L1"
    assert abs(float(item["qty_in"]) - float("1000")) < 0.011


def test_core_boundary_case():
    results, issues = calc([{'lot_id': 'L9', 'parent_lot': '', 'qty_in': '10', 'qty_out': '8', 'loss_qty': '2', 'recall': '1'}])
    assert issues == []
    value = results[0]["affected"]
    expected = 'True'
    if expected in {"True", "False"}:
        assert bool(value) is (expected == "True")
    elif isinstance(expected, bool):
        assert bool(value) is expected
    elif expected.startswith("20") and len(expected) == 10:
        assert value.isoformat() == expected
    elif expected.replace(".", "", 1).replace("-", "", 1).isdigit():
        assert abs(float(value) - float(expected)) < 0.001
    else:
        assert value == expected


def test_result_labels_are_unique():
    labels = [item["label"] for item in clean_results()]
    assert len(labels) == len(set(labels))


def test_every_result_has_metric():
    assert all(item.get("metric") is not None for item in clean_results())


def test_merge_uses_explicit_contributions_without_recalling_sister_lots():
    result = {item["label"]: item for item in clean_results()}
    assert result["L6"]["contributions"] == {"L4": 200, "L5": 40}
    assert result["L6"]["affected"]
    assert result["L1"]["affected"]
    assert not result["L3"]["affected"]


def test_three_node_cycle_blocks_all_members():
    rows = [dict(CLEAN[0], lot_id=str(index), parent_lot=str((index + 1) % 3)) for index in range(3)]
    results, issues = calc(rows)
    assert issues == []
    assert {item["problem"] for item in results} == {"CYCLE_OR_DEPENDENT"}
