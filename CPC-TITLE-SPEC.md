# CPC-TITLE-SPEC — the single small-context title subagent (main model, all N products in one context)

Inputs on disk: select/sNN.json (cpc_select.py: opener_candidates, cluster_candidates, ceiling, ceiling_exception, heads,
old_title), kw.txt, raw/pNN.json (facts for a defining attribute), rules/cpc-title-rule.md and rules/title-format-rule.md §2–§6
(read IN FULL), cap.py.

Procedure per product:

1. **Opener = select/sNN.json opener_candidates[0]** — the highest-volume keyword that names the product and has a measured
   CPC under the ceiling. You do not re-rank by volume/CPC ratio, difficulty or taste. If you believe opener_candidates[0]
   does not fit the product, it is a fit error: write the regex into fit_rejects.json for that product, return the product to
   the main context for `cpc_select.py` to re-run — never silently open on #2.
   `ceiling_exception: true` → opener_candidates holds the three cheapest head-noun keywords, highest volume first; the same
   rule applies (#1 opens), and every other keyword in the title must be under `cluster_ceiling`.
2. **Clusters** = cluster_candidates in order, as many as fit the tiers naturally, each as a contiguous phrase, with a defining
   attribute (size, material, pack count — US units only) between them where it reads naturally. Never a keyword with cpc 0
   (unknown) or ≥ the ceiling — they are not in the lists, do not add them from kw.txt by hand.
3. **Tail** (optional, 1): a cluster_candidate that is also below the product's median CPC, commercial/transactional, and opens
   a new query family; it is what legitimises 120–135 (trigger B). Trigger A = a ≥ 20,000 under-ceiling keyword that cannot be
   built contiguously within 120. Name the trigger in `tier_trigger`.
4. **Length**: 70–120; 120–135 only with a trigger; 135–145 only on both triggers or a second ≥ 20,000 cluster; 145 never;
   under 70 never. Head noun ≤ 3 occurrences (prefer 2). Two head nouns joined with a comma, never "and". No brand, no
   promotional words, no ALL CAPS, no size/colour unless defining, no metric units. Measure every draft with
   `python3 cap.py "<title>"`.
5. **A keyword you need that is not in kw.txt**: do not write it unmeasured. Collect across the batch, hand the list to the
   main context for ONE kw_measure.py call, continue after it lands.
6. **SEO title**: `[Opener] - [Cluster 2], [one attribute]`, under 70 characters, only keywords that are in the title.
7. **Every legal keyword ≥ 1,000 (cluster_candidates) you leave out that beats your weakest non-opener cluster** gets one line
   in `skip_reasons.json` ({"NN": {"keyword": "reason"}}): "over 120 with no trigger", "needs a 4th head noun", "breaks the
   opener order", "subset of a captured family". "Sounded better" is not a reason.

Write `titles_draft.json`: {"NN": {"title": "...", "seo_title": "...", "tier_trigger": "A" | "B" | null}} and
`skip_reasons.json`. Run `python3 cpc_check.py` yourself until 0 FAIL; read every MANUAL line and fix or justify it.

Q5 = Manual (the brief's candidate-review question): before writing titles_draft.json, return to the main context one block per
product — top-5 opener_candidates as `keyword | volume | $cpc`, the proposed title, its length — and wait; apply the user's
choices, then continue.

Return to the main context ONLY: count of titles per tier, the ceiling-exception products, the skip_reasons count, and the
cpc_check summary line. Nothing else.
