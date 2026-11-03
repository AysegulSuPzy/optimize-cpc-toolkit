#!/usr/bin/env python3
"""cpc_select.py — Phase 3: apply the Optimize-CPC selection rule (rules/cpc-title-rule.md §1) to every product's
measured candidates and write the ranked, gated shortlist the title agent builds from. Zero model tokens.

  python3 cpc_select.py [--ceiling 2.00] [--top 12]

Reads:  kw.txt (keyword|volume|competition|cpc — kw_measure.py format; cpc 0 = unknown/null),
        candidates/cNN.json ({"idx", "candidates": [...]}), raw/pNN.json (productType, title),
        fit_rejects.json ({"NN": ["regex", ...]} — the fit-gate patterns the main context wrote per product; optional),
        producttype.json ({"NN": "Title Case singular productType"} — optional override of raw productType).
Writes: select/sNN.json per product:
          opener_candidates  — fit-clean, cpc>0, cpc<ceiling, head-noun ok, sorted by volume desc (top N)
          cluster_candidates — fit-clean, cpc>0, cpc<ceiling, sorted by volume desc (top N)
          ceiling_exception  — true when opener_candidates is empty; then opener_candidates = highest-volume of the
                               three cheapest fit-clean head-noun keywords, cluster ceiling = opener cpc * 1.5
          rejects            — {"fit": [...], "cpc_over": [...], "cpc_unknown": [...]} each (volume, cpc, keyword)
        rejects.json — the same rejects for all products (second net for descriptions; never for titles).
Prints one line per product: idx | opener | cpc | volume | n_clusters | EXCEPTION?
"""
import argparse, glob, json, os, re, sys
from head_check import sing, same, pt_head, STOP

ap = argparse.ArgumentParser()
ap.add_argument("--ceiling", type=float, default=2.00)
ap.add_argument("--top", type=int, default=12)
a = ap.parse_args()

KW = {}
for ln in open("kw.txt"):
    ln = ln.rstrip("\n")
    if not ln or ln.startswith("#"): continue
    k, v, c, p = ln.split("|")
    KW[k] = {"v": int(v), "c": c, "cpc": float(p) if p else 0.0}
FR = json.load(open("fit_rejects.json")) if os.path.exists("fit_rejects.json") else {}
PT = json.load(open("producttype.json")) if os.path.exists("producttype.json") else {}
os.makedirs("select", exist_ok=True)
INFO = re.compile(r"\b(how to|what is|vs|versus|review|reviews|best|top \d+|diy|near me|amazon|walmart|ebay)\b")

def heads_of(pt):
    seg = re.split(r"\b(for|with)\b", pt, maxsplit=1, flags=re.I)[0]
    ws = [w for w in re.findall(r"[A-Za-z]+", seg) if w.lower() not in STOP]
    h = [sing(ws[-1])] if ws else []
    if pt_head(pt) not in h: h.append(pt_head(pt))
    return h

def names_product(k, heads):
    return any(same(sing(w), h) for h in heads for w in re.findall(r"[a-z]+", k))

allrej = {}
for f in sorted(glob.glob("candidates/c*.json")):
    d = json.load(open(f)); i = int(d["idx"]); nn = f"{i:02d}"
    raw = json.load(open(f"raw/p{nn}.json"))
    pt = PT.get(nn) or PT.get(str(i)) or raw.get("productType") or ""
    heads = heads_of(pt)
    pats = [re.compile(p, re.I) for p in FR.get(nn, FR.get(str(i), []))]
    cands = sorted({k.strip().lower() for k in d["candidates"] if k.strip()})
    fit, rej_fit, rej_over, rej_unknown = [], [], [], []
    for k in cands:
        if k not in KW or KW[k]["v"] <= 0: continue           # unmeasured / zero volume: not a candidate
        row = (KW[k]["v"], KW[k]["cpc"], k)
        if INFO.search(k) or any(p.search(k) for p in pats): rej_fit.append(row); continue
        if KW[k]["cpc"] <= 0: rej_unknown.append(row); continue
        if KW[k]["cpc"] >= a.ceiling: rej_over.append(row); continue
        fit.append(row)
    fit.sort(key=lambda r: (-r[0], r[1], len(r[2])))
    openers = [r for r in fit if names_product(r[2], heads)]
    exception = False; cluster_ceiling = a.ceiling
    if not openers:
        # ceiling exception (rule §1): all fit-clean measured-cpc head-noun keywords, cheapest three, highest volume opens
        pool = sorted([r for r in rej_over if names_product(r[2], heads)], key=lambda r: (r[1], -r[0]))
        if pool:
            exception = True
            three = pool[:3]
            openers = sorted(three, key=lambda r: -r[0])
            cluster_ceiling = openers[0][1] * 1.5
            fit = sorted([r for r in rej_over if r[1] <= cluster_ceiling] + fit, key=lambda r: (-r[0], r[1]))
            rej_over = [r for r in rej_over if r[1] > cluster_ceiling]
    out = {"idx": i, "product_id": raw["id"], "handle": raw["handle"], "old_title": raw["title"], "productType": pt, "heads": heads,
           "ceiling": a.ceiling, "cluster_ceiling": round(cluster_ceiling, 2), "ceiling_exception": exception,
           "opener_candidates": openers[:a.top], "cluster_candidates": fit[:a.top * 2],
           "rejects": {"fit": sorted(rej_fit, reverse=True)[:15], "cpc_over": sorted(rej_over, reverse=True)[:15],
                       "cpc_unknown": sorted(rej_unknown, reverse=True)[:15]}}
    json.dump(out, open(f"select/s{nn}.json", "w"), indent=1)
    allrej[nn] = out["rejects"]
    if openers:
        v, c, k = openers[0]
        print(f"{nn} | {k} | ${c:.2f} | {v:,} | {len(fit)} under ceiling" + (" | CEILING EXCEPTION" if exception else ""))
    else:
        print(f"{nn} | NO OPENER — no fit-clean head-noun keyword with a measured cpc (even over ceiling); product needs manual review")
json.dump(allrej, open("rejects.json", "w"), indent=1)
