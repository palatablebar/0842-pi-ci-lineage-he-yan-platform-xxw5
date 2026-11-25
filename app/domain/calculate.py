from datetime import date, timedelta
from app.catalog import SPEC
from app.domain.helpers import *  # noqa: F401,F403


def calculate_rows(items):
    out = []
    rows = items
    lots = {item["lot_id"]: item for item in items}
    parents = {lot_id: item["contributions"] for lot_id, item in lots.items()}
    children = {lot_id: set() for lot_id in lots}
    used = {lot_id: 0 for lot_id in lots}
    indegree = {lot_id: 0 for lot_id in lots}
    for child, upstream in parents.items():
        for parent, quantity in upstream.items():
            if parent not in lots:
                lots[child]["problem"] = "PARENT_MISSING"
                continue
            children[parent].add(child)
            used[parent] += quantity
            indegree[child] += 1
    for parent, quantity in used.items():
        if quantity > lots[parent]["qty_out"]:
            lots[parent]["problem"] = "OVERDRAW"
            for child in children[parent]:
                lots[child]["problem"] = "OVERDRAW"
    queue = [lot_id for lot_id, count in indegree.items() if count == 0]
    while queue:
        parent = queue.pop()
        for child in children[parent]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    for lot_id, count in indegree.items():
        if count:
            lots[lot_id]["problem"] = "CYCLE_OR_DEPENDENT"

    recalled = {item["lot_id"] for item in items if item["recall"] == 1}
    affected = set(recalled)
    for graph in (parents, children):
        visited = set(recalled)
        queue = list(recalled)
        while queue:
            for neighbor in graph.get(queue.pop(), ()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        affected.update(visited)
    for item in items:
        item["affected"] = item["lot_id"] in affected
        item["breakdown"] = [f"{parent} · 投入 {quantity}" for parent, quantity in item["contributions"].items()]
        item["metric"] = D(str(item["qty_in"]), "CALC")
        item["limit"] = D(str(item["qty_out"]), "LIMIT")
        out.append(item)
    for item in out:
        item.setdefault("label", str(item.get(SPEC["key"], "")))
    return out
