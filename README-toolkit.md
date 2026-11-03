# Optimize-CPC toolkit — how a session runs a batch

Rule of the project: `rules/cpc-title-rule.md` (selection = fit gate → CPC < ceiling → highest volume). Character tiers,
opener/head-noun, contiguous-phrase, tail gates: `rules/title-format-rule.md` §2–§6 word for word — EXCEPT its §1
selection order ("volume first, CPC tiebreaker") and its §2.5 old-vs-new-volume FAIL, which cpc-title-rule.md overrides.
Never Haiku anywhere; every agent runs on the main model or Sonnet.

Session start = `00-SESSION-START.md` (clone, manifest, credentials from the brief's Q0, store confirmation).
Working dir = the clone (`/home/claude/work`). All JSON stays offline; chat shows ≤ 50-char progress lines.

0. **Phase 0** — brief read back in one line; Manual: confirm store, ask the test-run question (one product first / full batch),
   wait. Scheduled: never wait.

1. **Phase 1 — fetch**: `python3 fetch.py <all|draft|active|tag:X> products.json` → products.json, raw/pNN.json, old_titles.json.
   Zero match → stop and report.

2. **Phase 2 — candidates** (CANDIDATES-SPEC.md): ONE agent per ~10 products, main model, reads raw/pNN.json, writes
   `candidates/cNN.json` (40–70 keywords, singular+plural heads, clusters, tails, synonyms, AND the neighbouring families
   expected to fail fit) and `producttype.json` ({"NN": "Title Case singular productType"}; head_check needs the head noun).
   Then, zero tokens:

       python3 source_windows.py products.json kw.txt > candidates/source_windows.txt
       python3 kw_measure.py candidates/c*.json candidates/source_windows.txt --kw kw.txt --cache /mnt/user-data/outputs/kw-cache-<tag>.md

   kw.txt lines are `keyword|volume|competition|cpc`; **cpc 0 = unknown** (DataForSEO returned null) and is treated as
   `cpc_unknown` by every later step. Send kw-cache-<tag>.md to the chat; it is not a project doc.

3. **Phase 3 — fit + gates**: the main context writes `fit_rejects.json` ({"NN": ["regex", …]}) — the §6 fit gate per product
   (wrong product type, wrong form factor, brand, informational) — then `python3 cpc_select.py --ceiling <Q2>` → select/sNN.json
   (opener_candidates, cluster_candidates, ceiling_exception flag, rejects) + rejects.json. Read the one-line-per-product print:
   every CEILING EXCEPTION and every NO OPENER is named in the run log; NO OPENER products are handed to the user (Manual) or
   skipped (Scheduled).

4. **Phase 4 — titles** (CPC-TITLE-SPEC.md): ONE small-context subagent for all N products, main model. Builds each title from
   select/sNN.json — opener = opener_candidates[0], clusters = cluster_candidates in order, tail optional — per the §3 format and
   the §4 tiers; measures with `python3 cap.py "<title>"`; writes `titles_draft.json` ({"NN": {"title", "seo_title", "tier_trigger"}})
   and `skip_reasons.json` for every legal keyword ≥ 1,000 it left out. Q5 = Manual: show the user, per product, the top-5
   opener candidates (volume / cpc) and the proposed title; wait; apply the user's choice.
   A keyword the agent needs that is not in kw.txt: collect across the batch, measure in ONE extra kw_measure.py call, never guess.

5. **Phase 5 — checks**: `python3 cpc_check.py` until **0 FAIL** (MANUAL lines are read and either fixed or accepted with a
   reason in the run log; WARN lines go to the run log). It writes titles_final.json. Then `python3 head_check.py titles_final.json`
   must print 0 FAIL. Then — ONLY after the user has approved the run (project docs are never written without explicit approval):
   write `claude/backup-titles-<tag>.md` to the Claude project (index | id | handle | old title | old SEO title | new title),
   BEFORE anything is pushed. If that project_write fails, stop; never push without the backup.

6. **Phase 6 — push**: `python3 push.py [--status ACTIVE]` — 10 per mutation, title + seo{title, description copied from
   old_titles.json}. Errors to push/errors.json; the batch never stops for one product.

7. **Phase 7 — verify**: `python3 verify.py` → 0 mismatches. Then `claude/run-log-<tag>.md` to the project (after approval):
   N pushed / N failed / N ceiling exceptions / N NO OPENER, the WARN and MANUAL lines, every product's old → new opener with
   cpc, and any toolkit file changed in the run.

**Revert <tag>** (Manual only): save the project's `claude/backup-titles-<tag>.md` to disk → `python3 revert.py <file>` →
`python3 verify.py` is not applicable; spot-check 3 products by `get-product` query instead. Scheduled runs never revert.

**Where run artefacts go**: only `claude/backup-titles-<tag>.md` and `claude/run-log-<tag>.md` go to the project, each only
after the user's approval. kw-cache and any other file go to /mnt/user-data/outputs/ and the chat.

**Multi-store**: nothing in this repo is store-specific. The store is the brief's Q0; `fetch.py`, `push.py`, `revert.py`,
`verify.py` all go through `shopify_api.py`, which reads only `secrets/shopify.json`.
