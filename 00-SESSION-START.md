# 00-SESSION-START — the first thing every Optimize-CPC session does

The toolkit lives in GitHub: `https://github.com/AysegulSuPzy/optimize-cpc-toolkit` (public, no token). The repo is the
source of truth; never copy toolkit docs out of a Claude project.

## Step A — clone (one command, zero model tokens)

    rm -rf /home/claude/work && git clone -q https://github.com/AysegulSuPzy/optimize-cpc-toolkit.git /home/claude/work && cd /home/claude/work

## Step B — integrity check

    awk '/^```$/{f=!f;next} f' MANIFEST.md > MANIFEST.sha256 && sha256sum -c MANIFEST.sha256 --quiet

Any FAILED line = a file was edited without its MANIFEST line being recomputed: report it in the run log and continue.

## Step C — credentials (NEVER into the repo; `secrets/` and `rules/dataforseo-credentials.md` are git-ignored)

1. **Shopify — from the brief's Q0 line**, not from any project doc:
   `Store: <name> | Shop: <handle>.myshopify.com | Client ID: <…> | Client secret: <…>` →
   write `secrets/shopify.json` as `{"shop": "<handle>.myshopify.com", "client_id": "…", "client_secret": "…"}` and delete any
   `secrets/token.json`. Q0 missing → Manual: ask; Scheduled: one-line error, stop.
2. **DataForSEO** — `project_read dataforseo-credentials.md` from the Claude project → write to `rules/dataforseo-credentials.md`
   (format: `- Login: \`…\`` / `- Password: \`…\``; kw_measure.py reads it there).
3. `python3 shopify_api.py shop` → state the store name + domain in one line (Phase 0). Manual: wait for the user to confirm.

Never print, echo, log or commit a credential. Never write one to a project doc, a run log, kw-cache or a backup doc.

## Step D — continue with README-toolkit.md from step 1.

## When a toolkit file changes during a run

Edit it in the clone, recompute its `sha256sum` line in MANIFEST.md, commit and push to the repo (or hand both files to the
user with SendUserFile for upload at `https://github.com/AysegulSuPzy/optimize-cpc-toolkit/upload/main`). Before any
commit: `git status` must show nothing under `secrets/` and no `dataforseo-credentials.md`.
