from app.catalog import SPEC
from app.domain.calculate import calculate_rows
from app.domain.decision import decide_rows
from app.domain.prepare import prepare_rows
from app.intake.service import load

CLEAN = [{'lot_id': 'L1', 'parent_lot': '', 'qty_in': '1000', 'qty_out': '1000', 'loss_qty': '0', 'recall': '0'},
 {'lot_id': 'L2', 'parent_lot': 'L1', 'qty_in': '600', 'qty_out': '600', 'loss_qty': '0', 'recall': '0'},
 {'lot_id': 'L3', 'parent_lot': 'L1', 'qty_in': '400', 'qty_out': '400', 'loss_qty': '0', 'recall': '0'},
 {'lot_id': 'L4', 'parent_lot': 'L2', 'qty_in': '360', 'qty_out': '350', 'loss_qty': '10', 'recall': '0'},
 {'lot_id': 'L5', 'parent_lot': 'L2', 'qty_in': '240', 'qty_out': '240', 'loss_qty': '0', 'recall': '1'},
 {'lot_id': 'L6',
  'parent_lot': 'L4:200;L5:40',
  'qty_in': '240',
  'qty_out': '235',
  'loss_qty': '5',
  'recall': '0'},
 {'lot_id': 'L7', 'parent_lot': 'L3', 'qty_in': '400', 'qty_out': '400', 'loss_qty': '0', 'recall': '0'}]


def row(**changes):
    item = dict(CLEAN[0])
    item.update(changes)
    return item


def calc(rows):
    items, issues = prepare_rows(rows)
    return calculate_rows(items), issues


def run(rows):
    items, issues = prepare_rows(rows)
    return decide_rows(calculate_rows(items)), issues


def run_profile(profile):
    return run(load(profile)["rows"])
