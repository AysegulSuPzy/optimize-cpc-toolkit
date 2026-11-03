#!/usr/bin/env python3
"""fetch.py — Phase 1: fetch the in-scope products into products.json (Shopify fetch format, same shape as
shopify_api.py fetch / source_windows.py / head_check.py expect). Zero model tokens.

  python3 fetch.py all            products.json
  python3 fetch.py draft          products.json
  python3 fetch.py active         products.json
  python3 fetch.py tag:<tag>      products.json

Also writes raw/pNN.json (one file per product, 2-digit index) for the candidates agent, and old_titles.json
({product_id: {"title", "seo_title", "seo_description", "productType"}}) — the revert source if the project doc is lost.
"""
import json, os, sys
from shopify_api import gql

FIELDS = """id handle title descriptionHtml vendor productType tags status category { id name fullName }
 seo { title description } variants(first: 20) { edges { node { id price title selectedOptions { name value } } } }
 media(first: 20) { edges { node { id alt mediaContentType ... on MediaImage { image { url } } } } }"""

def scope_query(scope):
    s = scope.lower()
    if s == "all": return ""
    if s == "draft": return "status:draft"
    if s == "active": return "status:active"
    if s.startswith("tag:"): return f"tag:{scope[4:]}"
    sys.exit(f"fetch: unknown scope '{scope}' (all | draft | active | tag:<tag>)")

def fetch(scope):
    q, nodes, after = scope_query(scope), [], None
    while True:
        d = gql("query($q:String,$after:String){ products(query:$q, first:50, after:$after){ edges{ node{ %s } } pageInfo{ hasNextPage endCursor } } }" % FIELDS,
                {"q": q or None, "after": after})["data"]["products"]
        nodes += [e["node"] for e in d["edges"]]
        sys.stderr.write(f"fetch: {len(nodes)} products\n")
        if not d["pageInfo"]["hasNextPage"]: return nodes
        after = d["pageInfo"]["endCursor"]

if __name__ == "__main__":
    scope, out = sys.argv[1], sys.argv[2]
    nodes = fetch(scope)
    if not nodes: sys.exit("fetch: zero products in scope — nothing to do")
    json.dump({"data": {"products": {"edges": [{"node": n} for n in nodes]}}}, open(out, "w"))
    os.makedirs("raw", exist_ok=True)
    old = {}
    for i, n in enumerate(nodes):
        n = dict(n); n["idx"] = i
        json.dump(n, open(f"raw/p{i:02d}.json", "w"), indent=1)
        old[n["id"]] = {"idx": i, "handle": n["handle"], "title": n["title"], "seo_title": (n.get("seo") or {}).get("title"),
                        "seo_description": (n.get("seo") or {}).get("description"), "productType": n.get("productType")}
    json.dump(old, open("old_titles.json", "w"), indent=1)
    print(len(nodes), "products ->", out, "+ raw/pNN.json + old_titles.json")
