# Publishing the dashboard

Only when the user says "publish". The account folder is the master; the dashboard is a published build of it. Each account has its own artifact, recorded in `data/published.json` `artifact`.

## First publish (new account, no `data/published.json`)

1. `Artifact` `action: "quickstart"`, `intent: "other"`: it names the type to start from (the core **Data** type: dashboards, metrics pages and scorecards).
2. Publish with that `type_url`, `title` = `portfolio.json` `name`, no files, `auto_open: "after_first_write"`. The result gives the new artifact's `url` and the type's instructions. Read them; where they differ from the steps below, they win.
3. For each `data/*.json` file (not `published.json`): upload it (`Artifact` publish with `url`, `file_path`, `asset: true`; returns `/_blob/<id>`), then load `ArtifactData` and `set` its `datasets/<id>` document (`<id>` = file name without `.json`) with a `title`, `description`, `source: {kind: "file", url: <blob url>, name, format: "json"}`, `updated: {at: <UTC now>, by: "Claude"}` and `edit: {via: "claude", at: <UTC now>}`. Batch the writes.
4. `set` `files/index.html` with `{text: <data/index.html>, edit: {...}}`.
5. Write `data/published.json` (shape in `references/files.md`) and give the user the link.
6. Read `data/users/me` (`check`, `runs`) and report any failure. `not_shown` only means the tab was hidden.

## Later publishes

1. Compare each file's sha256 with `data/published.json`. Only files that differ get published; if none differ, say "already up to date". A JSON file not yet listed is a new dataset: handle it as in First publish, step 3 (`set`, not `update`).
2. For each changed JSON file:
   1. Upload it (as above). This returns `/_blob/<id>`.
   2. `get` its `datasets/<id>` document for its version, then `update` it with `if_version`, the new `source.url`, `updated` and `edit`. Batch all updates into one write.
   3. Delete the old blob (`Artifact` delete with `url` + `path` = the old blob id from `published.json`).
3. If `index.html` changed: `get` `files/index.html`. If its version is newer than `page.doc_version` in `published.json`, someone edited it on the web: merge that edit into the template or `portfolio.json` `text`, rebuild, then write. `set` it with `{text, edit}` and `if_version`.
4. Rewrite `data/published.json` with the new blob ids, sha256 values, page version and `published_at`.
5. Read `data/users/me` as in First publish, step 6.

## Amounts (only when `portfolio.json` `amounts` is "dashboard")

The page's "Your money" block (total value, gain to date, money added since, what 1 point is worth) stays hidden unless an `amounts` dataset exists. Its file lives only in `private/`, so it never reaches git:
1. `python3 -I $S/money.py page` writes `private/amounts.json` (one row, chmod 600).
2. Upload it as above and `set` (first time) or `update` `datasets/amounts` with the new `source.url`; delete the old blob.
3. Record only `"amounts": {"file": "private/amounts.json", "blob": <id>}` in `data/published.json`: no sha256, because that file is never committed. Re-upload on every publish after a holdings screenshot or deposit.

Anyone the artifact is shared with sees these amounts; say so once when the user first chooses "dashboard". If `amounts` is no longer "dashboard" but `published.json` still lists `amounts`, delete the `datasets/amounts` document and its blob and drop the entry.

A renamed dataset field (for example in `macro.json`) only works once both the dataset and `index.html` are published, so publish them together.
