# CANDIDATES-SPEC — the candidates agent (main model; ~10 products per agent; no credentials, no API calls)

Read raw/pNN.json fully (title, descriptionHtml, productType, category, tags, variants with selectedOptions, media filenames).

Write two things per product:

## candidates/cNN.json

    {"idx": N, "identity": "one-line plain statement of WHAT the product is (head noun + defining attributes)",
     "candidates": [ ... 40–70 lowercase keyword strings ... ]}

The candidates are what a US Google shopper would type for THIS product:
- head nouns in singular AND plural (`nanny camera`, `nanny cameras`)
- modifier + noun clusters (`wireless nanny camera`, `nanny camera with audio`, `mini spy camera`)
- use-case / audience tails (`camera for nursery`, `baby monitor camera`)
- synonyms and alternate names (`hidden camera`, `spy cam`)
- the exact words of the old title's first phrase (always)
- **and the neighbouring product families you expect to FAIL product fit** (`home security camera`, `outdoor security camera`,
  `baby monitor`) — they must be measured so the fit-reject is on record with its volume; never reject unmeasured.
Rules: lowercase; no brand names; no spec values (`48khz`, `4000mah`); ≤ 80 characters, ≤ 10 words each; no "best / how to /
vs / review" phrases (they are dropped anyway). Identity is based on the DOMINANT evidence (spec table, package contents,
gallery filenames, variants) — the old supplier title is the WEAKEST evidence.

## producttype.json (one file for the batch, merged by the main context)

    {"NN": "Nanny Camera", "NN+1": "Wrist Blood Pressure Monitor", ...}

Title Case, singular, the product's OWN type (not the parent category: `Nanny Camera`, not `Security Camera`; `Wrist Blood
Pressure Monitor`, not `Health Monitor`). Its last word is the head noun every opener must carry (head_check.py).

Return to the main context ONLY one line per product: `NN | identity | <count> candidates | productType`.
