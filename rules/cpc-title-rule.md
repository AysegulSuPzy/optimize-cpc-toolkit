# Optimize CPC — Project Description (multi-store)

Purpose: rewrite product titles + SEO titles so Google Shopping / PMax matches the product to queries that are **high-volume but cheap (CPC < $2.00)** and that **truly describe the product**. Everything else (descriptions, prices, status, tags, images) is untouched unless the brief says otherwise.

Multi-store project. The store is chosen in the brief (Q0); nothing in this document is store-specific.

**Execution route:** before anything else, read `00-SESSION-START.md` in the toolkit repo `https://github.com/AysegulSuPzy/optimize-cpc-toolkit` and do its git clone, then follow `README-toolkit.md`. Shopify is accessed by script via `shopify_api.py` with the credentials from the brief's Q0; DataForSEO via the project doc `dataforseo-credentials.md`. Never the Shopify MCP for fetch, push or verification. No credential is ever written to the repo, a project doc, a run log or the chat.

---

## The Brief

Q0 — Store access (required, one line):
`Store: <name> | Shop: <handle>.myshopify.com | Client ID: <…> | Client secret: <shpss_…>`
The run writes these into toolkit/secrets/shopify.json at session start (token cache cleared). If Q0 is missing, Manual: ask for it; Scheduled: stop with a one-line error. The app must have scopes read_products, write_products (and read_themes/write_themes only if theme work is asked). Phase 0 confirms the store by `shop { name primaryDomain { host } }` and shows it before anything else.
Q1 — Scope: (All / Draft only / Active only / By Tag: ___)
Q2 — CPC ceiling (USD): default **2.00**
Q3 — Status after push: (Active / Keep current)
Q4 — Also rewrite SEO description? (Yes / No) — default No
Q5 — Candidate review: (Auto — agent decides fit / Manual — show top-5 per product, user picks opener)
Q6 — Run mode: (Manual / Scheduled)

Title length is NOT a brief question. It is a fixed rule (§3) and is never asked, never overridden by a brief.

---

## 1. Keyword selection — THE rule of this project

Order of operations per product:

1. **Fit gate (first, non-negotiable).** A keyword qualifies only if it names this product's type and does not contradict a defining attribute. Tests: *would someone typing this query be satisfied landing on this product?* Head-noun test: the keyword's last word = the product's own last word (singular/plural ok). Discard: parent categories as opener (`security camera` on a nanny cam), wrong form factor (`arm blood pressure monitor` on a wrist unit), other product (`thermal camera` on an IR night-vision unit unless the product truly images heat), brand names (omron, ring, wyze…), informational/navigational intent (`how to`, `vs`, `review`, `best`).
2. **CPC ceiling.** Drop every keyword with CPC ≥ Q2. No exceptions, whatever the volume. A keyword with null/missing CPC (written as 0 in kw.txt) is unknown and is dropped from the title entirely (opener, cluster and tail) — it goes to rejects.json as `cpc_unknown`.
3. **Rank the survivors by volume, descending.** The highest-volume keyword that passed 1–2 = **opener**. Next highest = clusters, in volume order. There is no minimum volume — always the biggest available under the ceiling.
4. **Tie-break** at similar volume (±15%): lower CPC → lower competition → fewer characters.

**Ceiling exception — product with nothing under the ceiling.** If, after the fit gate, no fit-clean keyword with a measured CPC < Q2 passes the head-noun test (i.e. no legal opener exists), the product is NOT skipped. Instead the ceiling is lifted for that product only: sort its fit-clean, measured-CPC keywords by CPC ascending, take the **three cheapest**, and the highest-volume of those three opens; clusters follow the same rule (cheapest first, then volume) with the same relaxed ceiling = the opener's CPC × 1.5. The product is marked `ceiling_exception: true` in titles_final.json with its opener CPC, listed separately in the run log, and counted in the summary ("N products over ceiling"). Null-CPC keywords stay excluded even here.

That is it. CPC is a hard gate, volume is the ranking: among everything that fits and is under $2, the biggest volume wins every slot. We do not use a volume/CPC ratio, we do not use keyword difficulty.

**What this changes vs. the backend project:** there, the highest-volume fitting keyword always opens. Here, the highest-volume fitting keyword **under $2** opens. `home security camera` 74,000 / $11.11 is discarded; `nanny camera with audio` 2,400 / $1.43 opens. `night vision device` 60,500 / $0.77 opens. `wrist bp monitor` 22,200 / $1.32 opens over `home blood pressure monitor` 60,500 / $2.38.

Expensive keywords are not lost: every discarded keyword goes into `rejects.json` and may be used in the **description** (second net), never in the title or SEO title.

---

## 2. Candidate pool — identical to the backend project (README-toolkit.md step 2, CANDIDATES-SPEC.md)

1. **Extraction agent** (main model, never Haiku) writes `candidates/cNN.json` per product: **40–70 keyword strings a US Google shopper would type for this product** — head nouns singular AND plural, modifier+noun clusters, use-case/audience tails, synonyms, **and the neighbouring product families expected to FAIL product fit** (they must be measured, never rejected unmeasured). Lowercase, no brand names, no spec values like "48khz". Must include the exact words of the old title's first phrase.
2. **`python3 source_windows.py products.json`** (script, zero tokens): every contiguous 2–4-word window of every source title becomes a candidate. It only ADDS; fit decides later.
3. **Measure everything in one pass:** cNN.json ∪ source_windows.txt → `kw_measure.py` → DataForSEO (≤950 keywords per call). **Word-order guard:** keywords that are the same words in a different order go in SEPARATE calls (Google folds them and returns the low variant for both). Output `kw.txt` as `keyword|volume|competition|cpc` (kw_measure.py format; **cpc 0 = null/unknown**); `kw-cache-<tag>.md` goes to outputs, not to the project.
4. A keyword used in a title but absent from kw.txt is a push-blocking FAIL — measure it in one extra call (CPC-TITLE-SPEC step 5), never guess.

No DataForSEO suggestion/related-keyword expansion; the pool is the extraction list + source windows, exactly as in the backend project.

## 3. Title format — FIXED RULE: character limits are identical to the backend project (title-format-rule.md §3–§4)

**Locked, not configurable:** 70–120 normal / 120–135 on trigger / 145 absolute ceiling / under 70 is a violation / SEO title under 70. The same tiers, triggers and tail gates as the backend project apply word for word; a brief cannot change them.

Structure: `[Opener keyword] – [Cluster 2] – [defining attribute / size / material] – [Cluster 3 or use-case tail]`

- Contiguous-phrase rule: a keyword counts only when its words appear contiguously, in order.
- Opener = highest-volume keyword that passed §1. Its last word = product head noun.
- Head noun repeated ≤ 3 times (prefer 2). Natural English, no keyword stuffing, no ALL CAPS, no brand, no size/color unless defining.
- Two head nouns joined with a comma, never "and".
- US units only (inch / ft / oz / lb); convert metric, odd conversions go to the description.
- **Length tiers (identical to backend project):**
  - **70–120** normal zone; under 70 is a violation (unspent budget).
  - **120–135** only on trigger A (a ≥ 20,000-volume **fitting, under-ceiling** keyword that cannot be built contiguously within 120) or trigger B (a tail keyword passing the tail gates).
  - **135–145** only if both triggers or a second ≥ 20,000 cluster; **145 absolute ceiling, never.**
- **Tail zone (optional, 1 keyword):** fit ✓, contiguous ✓, CPC < Q2 **and** below the product cluster's median CPC, commercial/transactional, opens a new query family. No volume floor — the highest-volume keyword passing these gates takes the slot.
- **SEO title:** `[Opener] - [Cluster 2], [one attribute]`, **under 70 characters**, same keywords only — every keyword in it passed the same §1 gates (fit, CPC < Q2 or ceiling exception, measured CPC).
- SEO description untouched unless Q4 = Yes; every SEO push carries BOTH seo.title and seo.description (copy the existing description), or Shopify nulls the missing half.

---

## 4. Push-blocking checks (title-check equivalent; 0 FAIL before push)

1. Opener unmeasured (not in kw.txt).
2. Opener CPC ≥ Q2, any title keyword CPC ≥ Q2, or any title keyword with null CPC — unless the product carries `ceiling_exception: true`, in which case the check is: opener is one of the three cheapest fit-clean keywords, and every title keyword CPC ≤ opener CPC × 1.5.
3. A higher-volume keyword that passed §1 sits behind the opener (it must open, or be fit-rejected with a written reason).
4. Opener fails the head-noun test.
5. Length outside tier, or 120+ with no named trigger, or > 145.
6. Metric unit in the title.
7. Unused measured keyword ≥ 1,000, under ceiling, fit-clean, bigger than the weakest cluster → needs one line in skip_reasons.json ("over 120 with no trigger", "needs 4th head noun", "breaks opener order"). "Sounded better" is not a reason.
8. SEO title ≥ 70 chars, or SEO push without seo.description.
9. **Captured-volume comparison is informational only** here: the new title will usually capture less raw volume than the old one because expensive keywords were removed. A WARN, never a FAIL.

---

## 5. Workflow

**Phase 0 — Scope** (write Q0 credentials to secrets/shopify.json, query shop name + domain, state it. Manual: confirm store + brief, ask test-run question. Scheduled: one line, go.)
**Phase 1 — Fetch** in-scope products via shopify_api.py → products.json (id, handle, title, productType, category, seo, descriptionHtml for seeds only). Snapshot old titles.
**Phase 2 — Candidates + DataForSEO** per §2 → kw.txt, candidates/cNN.json.
**Phase 3 — Fit + gates** per §1 → fit_rejects.json (regex per product, written by the main context) → `cpc_select.py --ceiling <Q2>` → select/sNN.json + rejects.json (fit / cpc_over / cpc_unknown, each with volume + cpc).
**Phase 4 — Titles** in one small-context subagent (main model, never Haiku) per §3 → titles_final.json (id, handle, old_title, new_title, len, opener, opener_cpc, captured[], rejected_expensive[], tier, trigger). Q5 = Manual: show top-5 candidates + proposed title per product, wait for user; Q5 = Auto: agent decides fit, logs every rejection.
**Phase 5 — Checks** per §4: `cpc_check.py` + `head_check.py` until 0 FAIL → titles_final.json. Write `claude/backup-titles-<tag>.md` (old title, old SEO title, new title, opener cpc) to the project BEFORE push — only after user approval of the run (project docs are never written without explicit approval).
**Phase 6 — Push** `push.py`: productUpdate batches of 10 (title + seo{title, description}), status per Q3. userErrors logged, batch never stops for one product.
**Phase 7 — Verify** `verify.py`: re-fetch every pushed product, compare to titles_final.json; summary: N pushed, N failed, N ceiling exceptions.

Context rules: no per-product progress, no schema dumps, ≤ 50-char progress lines, all JSON offline.

**Revert.** `Revert <tag>` (with Q0 for the store) restores every product of that run from `claude/backup-titles-<tag>.md` via `revert.py`: old title + old SEO title, seo.description copied from the live product (never nulled), batches of 10, then verify 3 products. Nothing else is touched. Manual: confirm store + count first; Scheduled: not allowed — revert is always manual.

---

## 6. Rejects → description (second net)

Keywords rejected ONLY for CPC (fit-clean, high volume) are listed in `rejects.json` under `cpc_over`. They are allowed in the product description's first paragraph / key features so the page still ranks organically; they never appear in title or SEO title. This is a separate optional step (description rewrite per the backend project rules), not part of a title run.

---

## 7. Worked example (from the 2026-11-03 audit)

| Product | Old opener | vol / cpc | New opener | vol / cpc |
|---|---|---|---|---|
| Nanny cam | home security camera | 74,000 / $11.11 ✗ ceiling | nanny camera with audio | 2,400 / $1.43 |
| Night vision | night vision device | 60,500 / $0.77 ✓ keep | night vision device (drop "thermal" unless the unit images heat) | 60,500 / $0.77 |
| Wrist BP | home blood pressure monitor | 60,500 / $2.38 ✗ ceiling | wrist bp monitor | 22,200 / $1.32 |

Clusters for nanny cam under $2: `indoor security camera` 8,100 / $4.00 ✗ → rejected; `mini nanny camera`, `wireless nanny cam` to be measured.
