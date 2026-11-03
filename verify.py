#!/usr/bin/env python3
"""verify.py — Phase 7: re-fetch every pushed product and compare title / seo.title / seo.description to titles_final.json
+ old_titles.json. "No userErrors" is not proof; this is.

  python3 verify.py            # prints mismatches and a summary; exit 1 on any mismatch
"""
import json, sys
from shopify_api import gql

T = json.load(open("titles_final.json")); OLD = json.load(open("old_titles.json"))
items = sorted(T.values(), key=lambda x: x["idx"]); bad = []
for i in range(0, len(items), 50):
    chunk = items[i:i + 50]
    d = gql("query($ids:[ID!]!){ nodes(ids:$ids){ ... on Product { id title status seo { title description } } } }", {"ids": [x["product_id"] for x in chunk]})
    live = {n["id"]: n for n in d["data"]["nodes"] if n}
    for it in chunk:
        n = live.get(it["product_id"])
        if not n: bad.append((it["idx"], "not found")); continue
        if n["title"] != it["title"]: bad.append((it["idx"], f"title live='{n['title'][:60]}'"))
        if (n["seo"] or {}).get("title") != it["seo_title"]: bad.append((it["idx"], "seo.title differs"))
        if ((n["seo"] or {}).get("description") or "") != (OLD[it["product_id"]].get("seo_description") or ""): bad.append((it["idx"], "seo.description changed/nulled"))
for b in bad: print("[MISMATCH]", *b)
print(f"verify: {len(items) - len({b[0] for b in bad})} ok, {len({b[0] for b in bad})} mismatched of {len(items)}")
sys.exit(1 if bad else 0)
