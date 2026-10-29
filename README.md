# repo.io

Helps beginner to expert coders find the GitHub repos, AI skills, prompts, plugins and connectors that fit what they're building. You describe the project in plain English and get a short "stack" of 3 to 5 picks, each with the reason it was chosen and a one-line install command.

## What's here

| Path | What it is |
|---|---|
| `catalog/ecc.json` | 563 items imported from [Everything Claude Code](https://github.com/affaan-m/ECC) (MIT): 311 skills, 71 agents, 97 commands, 22 rule packs, 27 hooks, 34 MCP servers and the full plugin bundle. |
| `scripts/import_ecc.py` | Rebuilds `catalog/ecc.json` from a checkout of ECC. Reads files only; never runs ECC code. |
| `web/index.html` | The finder prototype. Searches the catalog in the browser and builds the stack. |

## Run the finder locally

Serve the repo root (the page loads `../catalog/ecc.json`), then open the page:

```bash
python3 -m http.server 8000
# open http://localhost:8000/web/
```

## Refresh the ECC catalog

```bash
git clone --depth 1 https://github.com/affaan-m/ECC.git .ecc-src
python3 -I scripts/import_ecc.py .ecc-src catalog/ecc.json
```

The importer prints item counts per type. Each item records the ECC commit it came from.

## Catalog format (`repo.io/catalog@1`)

Each item in `items` has:

- `id`: `ecc:<type>:<slug>`, stable across refreshes
- `type`: `skill`, `agent`, `command`, `rule`, `hook`, `mcp` or `plugin`
- `name`, `summary`, `tags`, `url`
- `level`: `beginner`, `intermediate` or `expert`. This is a heuristic from the item's name and type, not a curated rating.
- `install.claude_code`: a copy-paste install command, plus `install.note` when setup needs extra steps
- `source`: repo, path, commit and license

## How ranking works

The finder scores each item on how many of your words appear in its slug, name, tags and summary. Rare words count for more than common ones. Items named for a different language or framework than the one you mention drop down. The stack takes the best match of each type (skill, agent, command, rule, MCP server, hook), so you get tools that work together instead of five similar ones.
