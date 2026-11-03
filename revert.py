#!/usr/bin/env python3
"""revert.py — `Revert <tag>`: restore old title + old SEO title from a backup-titles doc (or old_titles.json).
seo.description is copied from the LIVE product so it is never nulled. Batches of 10. Manual runs only.

  python3 revert.py backup-titles-<tag>.md        # project doc saved to disk (table: index | id | handle | old title | old SEO title | new title)
  python3 revert.py old_titles.json               # same session's fetch output
"""
import json, re, sys
from shopify_api import gql

src = sys.argv[1]; rows = []
if src.endswith(".json"):
    for pid, o in json.load(open(src)).items(): rows.append((pid, o["title"], o.get("seo_title") or ""))
else:
    for ln in open(src, encoding="utf-8"):
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) >= 5 and re.fullmatch(r"\d+", c[1]): rows.append((f"gid://shopify/Product/{c[1]}", c[3], c[4]))
if not rows: sys.exit("revert: no rows found")
print(f"revert: {len(rows)} products from {src}")
live = {}
for i in range(0, len(rows), 50):
    ids = [r[0] for r in rows[i:i + 50]]
    d = gql("query($ids:[ID!]!){ nodes(ids:$ids){ ... on Product { id seo { description } } } }", {"ids": ids})
    for n in d["data"]["nodes"]:
        if n: live[n["id"]] = (n.get("seo") or {}).get("description") or ""
errors = {}
for b in range(0, len(rows), 10):
    batch = rows[b:b + 10]; decl, body, vars_ = [], [], {}
    for j, (pid, title, seo_t) in enumerate(batch):
        decl.append(f"$p{j}: ProductUpdateInput!"); body.append(f"p{j}: productUpdate(product: $p{j}) {{ userErrors {{ field message }} }}")
        vars_[f"p{j}"] = {"id": pid, "title": title, "seo": {"title": seo_t, "description": live.get(pid, "")}}
    d = gql(f"mutation({', '.join(decl)}) {{ {' '.join(body)} }}", vars_)
    for j, (pid, *_) in enumerate(batch):
        if d["data"][f"p{j}"]["userErrors"]: errors[pid] = d["data"][f"p{j}"]["userErrors"]
    print(f"reverted {b}–{b + len(batch) - 1}")
print(f"revert: {len(rows) - len(errors)} ok, {len(errors)} failed", errors or "")
