
#!/usr/bin/env python3
import json, sys, argparse, datetime
from collections import defaultdict, deque

TYPE_BASE = {
    "doc": 0.8,
    "code": 1.0,
    "cli": 0.9,
    "mcp": 1.2,
    "ide": 1.0,
    "config": 0.9,
    "test": 1.1
}

def load_tasks(p):
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "tasks" not in data or not isinstance(data["tasks"], list):
        raise ValueError("Invalid tasks.json: missing 'tasks' list")
    return data

def topo_order(tasks):
    # Build graph
    id_index = {t["id"]: i for i, t in enumerate(tasks)}
    indeg = defaultdict(int)
    adj = defaultdict(list)
    for t in tasks:
        deps = t.get("deps", [])
        for d in deps:
            adj[d].append(t["id"])
            indeg[t["id"]] += 1
        if t["id"] not in indeg:
            indeg[t["id"]] = indeg.get(t["id"], 0)
    # Kahn
    q = deque([tid for tid, deg in indeg.items() if deg == 0])
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    # Detect cycle
    cycle = None
    if len(order) != len(tasks):
        # crude cycle detection: nodes with indeg>0
        cycle = [tid for tid, deg in indeg.items() if deg > 0]
    return order, cycle, adj

def score_complexity(task, adj, reverse_adj):
    base = TYPE_BASE.get(task.get("type","code"), 1.0)
    deps = len(task.get("deps", []))
    dependents = len(adj.get(task["id"], []))
    title_bonus = 0.0
    title = (task.get("title") or "").lower()
    if any(k in title for k in ["reflect", "dependency", "graph", "mcp"]):
        title_bonus += 0.2
    # simple formula bounded to [0.8, 3.0]
    cx = base + 0.2*deps + 0.1*dependents + title_bonus
    return max(0.8, min(3.0, round(cx, 2)))

def build_reverse(adj):
    rev = defaultdict(list)
    for u, vs in adj.items():
        for v in vs:
            rev[v].append(u)
    return rev

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="outp", required=True)
    ap.add_argument("--report", dest="report", required=True)
    args = ap.parse_args()

    data = load_tasks(args.inp)
    tasks = data["tasks"]
    order, cycle, adj = topo_order(tasks)
    rev = build_reverse(adj)

    # attach order index + recompute complexity
    order_index = {tid: i for i, tid in enumerate(order)}
    for t in tasks:
        t["order"] = order_index.get(t["id"], 9999)
    for t in tasks:
        t["complexity"] = float(score_complexity(t, adj, rev))

    data["meta"] = data.get("meta", {})
    data["meta"]["reflected_at"] = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    data["meta"]["topo_order"] = order

    with open(args.outp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # write report
    lines = []
    lines.append("# Tasks Reflect Report")
    lines.append("Generated: " + data["meta"]["reflected_at"])
    lines.append("")
    if cycle:
        lines.append("## ⚠️ Cycle Detected")
        lines.append("- Nodes in cycle or blocked: " + ", ".join(cycle))
    else:
        lines.append("## ✅ No Cycles")
    lines.append("")
    lines.append("## Execution Order")
    for i, tid in enumerate(order):
        lines.append(f"{i+1}. {tid}")
    lines.append("")
    lines.append("## Complexity Summary")
    for t in sorted(tasks, key=lambda x: x["order"]):
        lines.append(f"- {t['id']}: type={t.get('type')} deps={len(t.get('deps',[]))} dependents={len(adj.get(t['id'],[]))} complexity={t['complexity']} order={t['order']}")
    with open(args.report, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    main()
