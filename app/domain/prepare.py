from app.catalog import SPEC
from app.domain.helpers import D, DAY, I, M, TS, optional
from app.intake.normalize import canonical


PARSERS = {
    "money": lambda value, code: M(value, code),
    "decimal": lambda value, code: D(value, code),
    "decimal_optional": lambda value, code: optional(D, value, code),
    "int": lambda value, code: I(value, code),
    "int_positive": lambda value, code: positive(I(value, code)),
    "date": lambda value, code: DAY(value, code),
    "date_optional": lambda value, code: optional(DAY, value, code),
    "datetime": lambda value, code: TS(value, code),
}


def positive(value):
    if value <= 0:
        raise ValueError("BAD_POSITIVE")
    return value


def _typed(rows):
    typed, issues = [], []
    for raw in rows:
        item = dict(raw)
        try:
            if not canonical(item.get(SPEC["key"], "")):
                raise ValueError("KEY_MISSING")
            for field, kind in SPEC["types"].items():
                code = "INVALID_" + field.upper()
                item[field] = PARSERS[kind](item.get(field), code)
            typed.append(item)
        except ValueError as exc:
            issues.append({"line": raw.get("_line", 0), "key": raw.get(SPEC["key"], ""), "code": str(exc)})
    return typed, issues


def prepare_rows(rows):
    typed, issues = _typed(rows)
    rows = typed
    items = []
    for item in typed:
        try:
            if not canonical(item.get(SPEC["key"], "")):
                raise ValueError("KEY_MISSING")
            if item["qty_in"] < 0 or item["qty_out"] < 0 or item["loss_qty"] < 0:
                raise ValueError("BAD_QUANTITY")
            if item["qty_in"] != item["qty_out"] + item["loss_qty"]:
                raise ValueError("MASS_MISMATCH")
            parent_spec = item["parent_lot"]
            contributions = {}
            for edge in parent_spec.split(";") if parent_spec else []:
                parent, separator, quantity = edge.partition(":")
                parent = parent.strip()
                if not parent or parent in contributions or (not separator and ";" in parent_spec):
                    raise ValueError("BAD_PARENT_EDGE")
                if parent == item["lot_id"]:
                    raise ValueError("CYCLE")
                contribution = I(quantity, "BAD_PARENT_EDGE") if separator else item["qty_in"]
                if contribution <= 0:
                    raise ValueError("BAD_PARENT_EDGE")
                contributions[parent] = contribution
            if contributions and sum(contributions.values()) != item["qty_in"]:
                raise ValueError("PARENT_INPUT_MISMATCH")
            item["contributions"] = contributions
            if item["recall"] not in {0, 1}:
                raise ValueError("BAD_RECALL")
            items.append(item)
        except ValueError as exc:
            issues.append({"line": item.get("_line", 0), "key": item.get(SPEC["key"], ""), "code": str(exc)})
    return items, issues
