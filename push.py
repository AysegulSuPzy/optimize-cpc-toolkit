#!/usr/bin/env python3
"""push.py — Phase 6: push titles_final.json to Shopify in batches of 10 (title + seo{title, description}).
seo.description is COPIED from old_titles.json so it is never nulled (Shopify nulls a missing half of `seo`).

  python3 push.py [--status ACTIVE|DRAFT] [--dry]          # default: keep current status

Writes push/mutNN.json (one per batch) then fires them; prints one line per batch and a summary; push/errors.json on failures.
"""
import argparse, json, os, sys
from shopify_api import gql

ap = argparse.ArgumentParser(); ap.add_argument("--status"); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
T = json.load(open("titles_final.json")); OLD = json.load(open("old_titles.json"))
items = sorted(T.values(), key=lambda x: x["idx"]); os.makedirs("push", exist_ok=True)
batches = [items[i:i + 10] for i in range(0, len(items), 10)]
errors = {}
for b, batch in enumerate(batches):
    decl, body, vars_ = [], [], {}
    for j, it in enumerate(batch):
        old = OLD[it["product_id"]]
        inp = {"id": it["product_id"], "title": it["title"], "seo": {"title": it["seo_title"], "description": old.get("seo_description") or ""}}
        if a.status: inp["status"] = a.status.upper()
        decl.append(f"$p{j}: ProductUpdateInput!"); body.append(f"p{j}: productUpdate(product: $p{j}) {{ userErrors {{ field message }} }}")
        vars_[f"p{j}"] = inp
    m = {"query": f"mutation({', '.join(decl)}) {{ {' '.join(body)} }}", "variables": vars_}
    json.dump(m, open(f"push/mut{b:02d}.json", "w"), indent=1)
    if a.dry: print(f"push: batch {b} ready ({len(batch)} products) [dry]"); continue
    d = gql(m["query"], m["variables"])
    for j, it in enumerate(batch):
        ue = d["data"][f"p{j}"]["userErrors"]
        if ue: errors[it["product_id"]] = ue
    print(f"Products {batch[0]['idx']}–{batch[-1]['idx']} pushed" + (f" ({sum(1 for it in batch if it['product_id'] in errors)} errors)" if errors else ""))
if errors: json.dump(errors, open("push/errors.json", "w"), indent=1)
print(f"push: {len(items) - len(errors)} ok, {len(errors)} failed" + (" — see push/errors.json" if errors else ""))
