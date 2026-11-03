#!/usr/bin/env python3
"""cpc_check.py — Phase 5: push-blocking checks of rules/cpc-title-rule.md §4 on titles_draft.json. Zero model tokens.

  python3 cpc_check.py            # exit 1 on any FAIL; prints FAIL / WARN / MANUAL lines and a summary

Reads: titles_draft.json  {"NN": {"title": "...", "seo_title": "...", "tier_trigger": "A|B|null"}}  (title agent output)
       select/sNN.json    (cpc_select.py output: ceiling, exception flag, candidates, heads)
       kw.txt, products.json (source windows gate), skip_reasons.json ({"NN": {"keyword": "reason"}}, optional)
Writes: titles_final.json on 0 FAIL — the push input.
"""
import json, os, re, sys
from head_check import sing, same, STOP, SYN
from source_windows import norm as sw_norm, windows as sw_windows

KW = {}
for ln in open("kw.txt"):
    ln = ln.rstrip("\n")
    if not ln or ln.startswith("#"): continue
    k, v, c, p = ln.split("|"); KW[k] = {"v": int(v), "c": c, "cpc": float(p) if p else 0.0}
T = json.load(open("titles_draft.json"))
SR = json.load(open("skip_reasons.json")) if os.path.exists("skip_reasons.json") else {}
SW = {"for","the","and","with","of","a","in","to","on"}
def words(s): return re.findall(r"[a-z0-9]+", s.lower())
def wset(s): return frozenset(words(s)) - SW
fails, warns, manual = [], [], []
F = lambda p, m: fails.append(f"[FAIL] {p}  {m}")
W = lambda p, m: warns.append(f"[WARN] {p}  {m}")
M = lambda p, m: manual.append(f"[MANUAL] {p}  {m}")

# batch gate: every source-title window measured (§2 step 4)
snap = json.load(open("products.json")); edges = snap["data"]["products"]["edges"]
want = set()
for e in edges: want |= sw_windows(sw_norm(e["node"].get("title", "")))
miss = sorted(w for w in want if w not in KW)
if miss: F("batch", f"source windows NOT measured — {len(miss)} of {len(want)} missing from kw.txt (e.g. {miss[:3]}); run source_windows.py → kw_measure.py")

final = {}
for nn, d in sorted(T.items()):
    S = json.load(open(f"select/s{nn}.json"))
    t = d["title"]; tl = t.lower(); L = len(t); ceil = S["cluster_ceiling"] if S["ceiling_exception"] else S["ceiling"]
    # length tiers — identical to title-format-rule.md §4
    if L > 145: F(nn, f"title {L} chars > 145 hard ceiling")
    elif L > 135: F(nn, f"title {L} chars — 135-145 only on both triggers / second >=20K cluster; name it") if not d.get("tier_trigger") else M(nn, f"title {L} chars, trigger {d.get('tier_trigger')} — confirm")
    elif L > 120: F(nn, f"title {L} chars in 120-135 with no named trigger (A: >=20K under-ceiling keyword, B: tail)") if not d.get("tier_trigger") else M(nn, f"title {L} chars, trigger {d.get('tier_trigger')}")
    elif L < 70: F(nn, f"title {L} chars < 70 — unspent base budget")
    ws = words(t)
    if ws:
        noun, n = max(((w, ws.count(w)) for w in set(ws)), key=lambda x: x[1])
        if n >= 4: F(nn, f"head noun '{noun}' x{n} — cap is 3")
        elif n == 3: M(nn, f"head noun '{noun}' x3 — allowed only if the captured volume justifies it")
    for bad in ("free shipping", "sale", "best", "cheapest", "% off"):
        if bad in tl: F(nn, f"promotional text in title: '{bad}'")
    if re.search(r"\b(\d+(?:[.,]\d+)?)\s?(cm|mm|km|kg|mg|ml|liters?|litres?|grams?|kilograms?|met(?:er|re)s?|centimet(?:er|re)s?|millimet(?:er|re)s?)\b", t, re.I):
        F(nn, "metric unit in title — inch/ft/oz/lb only (§5)")
    if re.search(r"\b[A-Z]{3,}\b", re.sub(r"\b(LED|RGB|USB|IPX?\d+|HD|DVR|PU|TPR|CCTV|RV|PC|TF|AUX|WiFi|SATA|IDE|UV|BP|GPS|LCD|OLED|TV)\b", "", t)):
        W(nn, "possible ALL-CAPS word in title")
    if " and " in tl and re.search(r"\b[a-z]+ and [a-z]+\b", tl): M(nn, "'and' in title — two head nouns must be joined with a comma (§3.9)")
    # captured keywords
    captured = [k for k in KW if KW[k]["v"] > 0 and k in tl]
    if not captured: F(nn, "title captures no measured keyword")
    # the CPC gate runs on maximal phrases only: a sub-phrase of a longer captured keyword (`vision device` inside
    # `night vision device`) is a measurement artefact of source windows, not a keyword the title was built on
    maximal = [k for k in captured if not any(k != o and k in o for o in captured)]
    def canon(w):
        w = sing(w)
        for syn in SYN:
            if w in syn: return min(syn)
        return w
    def fam(k): return frozenset(canon(w) for w in words(k)) - SW        # singular/plural + synonym + word-order family
    def reason_for(k):
        rs = SR.get(nn) or {}
        return rs.get(k) or next((r for kk, r in rs.items() if fam(kk) == fam(k)), None)
    # §1/§4.2 CPC gate on every captured keyword
    for k in maximal:
        if KW[k]["cpc"] <= 0: F(nn, f"'{k}' has no measured CPC (0/null) — not allowed in a title (cpc_unknown)")
        elif KW[k]["cpc"] >= ceil: F(nn, f"'{k}' cpc ${KW[k]['cpc']:.2f} >= ceiling ${ceil:.2f}" + (" (exception ceiling)" if S["ceiling_exception"] else ""))
    # opener: first comma segment up to the head noun
    heads = S["heads"]
    seg = re.split(r"\b(for|with)\b", t.split(",")[0], maxsplit=1, flags=re.I)[0]
    segw = re.findall(r"[A-Za-z0-9]+", seg)
    hi = next((i for i in range(len(segw) - 1, -1, -1) if any(same(sing(segw[i]), h) for h in heads)), None)
    if hi is None:
        F(nn, f"opener '{seg.strip()}' has no word matching productType head {heads} — head-noun test")
    else:
        phrase = " ".join(segw[:hi + 1]).lower(); pset = wset(phrase)
        inside = [k for k in KW if KW[k]["v"] > 0 and (k in phrase or wset(k) == pset or wset(k) == wset(seg))]
        if not inside: F(nn, f"opener phrase '{phrase}' was never measured — measure it (one DataForSEO call) before it may open")
        else:
            top_in = max(inside, key=lambda k: KW[k]["v"])
            # §4.3 — highest-volume legal opener candidate must be inside the opener (tie ok) unless skip_reasons says why
            legal = [tuple(x) for x in S["opener_candidates"]]
            if legal:
                best_v, best_c, best_k = legal[0]
                if KW[top_in]["v"] < best_v and best_k not in phrase and wset(best_k) != pset:
                    reason = reason_for(best_k)
                    if reason: M(nn, f"opener '{phrase}' ({KW[top_in]['v']:,}) below legal best '{best_k}' ({best_v:,}, ${best_c:.2f}) — reason: {reason}")
                    else: F(nn, f"'{best_k}' ({best_v:,}, ${best_c:.2f}) is the highest-volume legal opener but the opener is '{phrase}' ({KW[top_in]['v']:,}) — open on it or write a reason in skip_reasons.json")
            if S["ceiling_exception"]:
                three = {x[2] for x in S["opener_candidates"][:3]}
                if not any(k in three for k in inside): F(nn, f"ceiling exception: opener must be one of the three cheapest head-noun keywords {sorted(three)}")
    # §4.7 unused legal cluster bigger than the weakest non-opener captured keyword
    non_opener = [k for k in captured if hi is not None and k not in " ".join(segw[:hi + 1]).lower()]
    weakest = min((KW[k]["v"] for k in non_opener if KW[k]["v"] >= 1000), default=0)   # clusters are >= 1,000 phrases; smaller captures are incidental
    for v, c, k in S["cluster_candidates"]:
        if k in tl or any(fam(k) == fam(x) for x in captured): continue
        if v >= 1000 and v > weakest and weakest > 0:
            reason = reason_for(k)
            if reason: M(nn, f"unused '{k}' ({v:,}, ${c:.2f}) > weakest cluster ({weakest:,}) — reason: {reason}")
            else: F(nn, f"unused legal keyword '{k}' ({v:,}, ${c:.2f}) beats the weakest non-opener cluster ({weakest:,}) — use it or write a reason in skip_reasons.json")
            break
    # SEO title
    st = d.get("seo_title") or ""
    if not st: F(nn, "seo_title missing")
    elif len(st) >= 70: F(nn, f"seo.title {len(st)} chars >= 70")
    else:
        stc = [k for k in KW if KW[k]["v"] > 0 and k in st.lower()]
        for k in [k for k in stc if not any(k != o and k in o for o in stc)]:
            if KW[k]["cpc"] <= 0 or KW[k]["cpc"] >= ceil: F(nn, f"seo.title keyword '{k}' fails the CPC gate (${KW[k]['cpc']:.2f})")
    # old-vs-new volume: WARN only (§4.9)
    old_cap = sum(KW[k]["v"] for k in KW if KW[k]["v"] > 0 and k in S["old_title"].lower())
    new_cap = sum(KW[k]["v"] for k in captured)
    if new_cap < old_cap: W(nn, f"captured volume {old_cap:,} -> {new_cap:,} (expected when expensive keywords leave)")
    final[nn] = {"idx": int(nn), "product_id": S["product_id"], "handle": S["handle"], "old_title": S["old_title"], "title": t,
                 "seo_title": st, "len": L, "opener": S["opener_candidates"][0][2] if S["opener_candidates"] else None,
                 "opener_cpc": S["opener_candidates"][0][1] if S["opener_candidates"] else None,
                 "captured": sorted(((KW[k]["v"], KW[k]["cpc"], k) for k in captured), reverse=True),
                 "ceiling_exception": S["ceiling_exception"], "tier_trigger": d.get("tier_trigger")}

for x in fails + warns + manual: print(x)
print(f"cpc_check: {len(fails)} FAIL, {len(warns)} WARN, {len(manual)} MANUAL over {len(T)} titles")
if not fails:
    json.dump(final, open("titles_final.json", "w"), indent=1); print("-> titles_final.json written")
sys.exit(1 if fails else 0)
