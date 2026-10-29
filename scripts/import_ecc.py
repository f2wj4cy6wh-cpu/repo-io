"""Import Everything Claude Code (ECC) into the repo.io catalog format.

Usage: python3 -I import_ecc.py <ecc-checkout> <out.json>

Reads files only; never executes anything from the checkout.
"""
import json
import os
import re
import subprocess
import sys

REPO = "affaan-m/ECC"
BRANCH = "main"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
TREE = f"https://github.com/{REPO}/tree/{BRANCH}"
BLOB = f"https://github.com/{REPO}/blob/{BRANCH}"

LANGS = {
    "python", "django", "flask", "fastapi", "typescript", "javascript", "react", "nextjs", "vue",
    "nuxt", "angular", "svelte", "go", "golang", "rust", "java", "kotlin", "swift", "cpp", "csharp",
    "dotnet", "fsharp", "ruby", "rails", "php", "laravel", "perl", "dart", "flutter", "elixir",
    "springboot", "quarkus", "postgres", "clickhouse", "docker", "kubernetes", "terraform", "arkts",
}
TOPICS = {
    "security": "security", "test": "testing", "tdd": "testing", "e2e": "testing", "review": "code-review",
    "refactor": "refactoring", "debug": "debugging", "build": "build", "deploy": "devops", "ci": "devops",
    "docs": "docs", "doc": "docs", "api": "api", "database": "database", "db": "database", "sql": "database",
    "agent": "agents", "eval": "evals", "llm": "ai", "prompt": "ai", "mcp": "mcp", "frontend": "frontend",
    "design": "design", "ui": "frontend", "a11y": "accessibility", "perf": "performance",
    "performance": "performance", "git": "git", "commit": "git", "plan": "planning", "architect": "architecture",
    "architecture": "architecture", "video": "media", "orch": "orchestration", "harness": "agents",
    "learning": "memory", "memory": "memory", "context": "context", "cost": "cost",
}
# Words that suggest a beginner can pick the item up without much setup.
BEGINNER_HINTS = {"standards", "coding", "style", "testing", "tdd", "build-fix", "explain", "docs",
                  "code-review", "review", "plan", "commit", "debug", "patterns"}
# Words that suggest multi-agent, harness, or ops work aimed at experts.
EXPERT_HINTS = {"orch", "harness", "autonomous", "enterprise", "ops", "eval", "governance", "continuous",
                "multi", "loop", "swarm", "team", "fleet", "security-scan", "compact", "hookify"}


def frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    meta = {}
    if not m:
        return meta, text
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if kv:
            meta[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return meta, text[m.end():]


def first_heading_and_para(body):
    title, para = None, None
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block:
            continue
        if block.startswith("# ") and not title:
            title = block.splitlines()[0][2:].strip()
        elif not block.startswith(("#", ">", "-", "|", "```", "<")) and not para:
            para = " ".join(block.split())
        if title and para:
            break
    return title, para


def humanize(slug):
    return slug.replace("-", " ").replace("_", " ").strip().capitalize()


def tags_for(slug, text):
    words = set(re.split(r"[-_\s/]+", slug.lower()))
    words |= set(re.findall(r"[a-z0-9+#.]+", text.lower()))
    tags = {w for w in words if w in LANGS}
    tags |= {TOPICS[w] for w in words if w in TOPICS}
    return sorted(tags)


def level_for(kind, slug):
    words = set(re.split(r"[-_]+", slug.lower()))
    if kind in ("hook", "mcp") or words & EXPERT_HINTS:
        return "expert"
    if kind in ("rule", "command") or words & BEGINNER_HINTS:
        return "beginner"
    return "intermediate"


def clip(s, n=280):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def item(kind, slug, name, summary, path, install, extra=None, text=""):
    d = {
        "id": f"ecc:{kind}:{slug}",
        "type": kind,
        "slug": slug,
        "name": name,
        "summary": clip(summary),
        "tags": tags_for(slug, text),
        "level": level_for(kind, slug),
        "source": {"collection": "Everything Claude Code", "repo": REPO, "path": path, "license": "MIT"},
        "url": f"{TREE if not path.endswith(('.md', '.json')) else BLOB}/{path}",
        "install": install,
    }
    if extra:
        d.update(extra)
    return d


def read(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def skills(root):
    out = []
    for slug in sorted(os.listdir(os.path.join(root, "skills"))):
        p = os.path.join(root, "skills", slug, "SKILL.md")
        if not os.path.isfile(p):
            continue
        text = read(p)
        meta, body = frontmatter(text)
        title, para = first_heading_and_para(body)
        out.append(item(
            "skill", slug, title or humanize(meta.get("name", slug)), meta.get("description") or para,
            f"skills/{slug}",
            {
                "claude_code": f"npx degit {REPO}/skills/{slug} ~/.claude/skills/{slug}",
                "from_clone": f"./install.sh --target claude --skills {slug}",
            },
            text=meta.get("description") or para or "",
        ))
    return out


def agents(root):
    out = []
    for fn in sorted(os.listdir(os.path.join(root, "agents"))):
        if not fn.endswith(".md"):
            continue
        slug = fn[:-3]
        text = read(os.path.join(root, "agents", fn))
        meta, body = frontmatter(text)
        title, para = first_heading_and_para(body)
        extra = {"model": meta["model"]} if meta.get("model") else None
        out.append(item(
            "agent", slug, humanize(meta.get("name", slug)), meta.get("description") or para,
            f"agents/{fn}",
            {"claude_code": f"mkdir -p ~/.claude/agents && curl -fsSL {RAW}/agents/{fn} -o ~/.claude/agents/{fn}"},
            extra, text=meta.get("description") or para or "",
        ))
    return out


def commands(root):
    out = []
    for fn in sorted(os.listdir(os.path.join(root, "commands"))):
        if not fn.endswith(".md"):
            continue
        slug = fn[:-3]
        text = read(os.path.join(root, "commands", fn))
        meta, body = frontmatter(text)
        title, para = first_heading_and_para(body)
        out.append(item(
            "command", slug, f"/{slug}", meta.get("description") or para,
            f"commands/{fn}",
            {"claude_code": f"mkdir -p ~/.claude/commands && curl -fsSL {RAW}/commands/{fn} -o ~/.claude/commands/{fn}"},
            text=meta.get("description") or para or "",
        ))
    return out


def rules(root):
    out = []
    rdir = os.path.join(root, "rules")
    for pack in sorted(os.listdir(rdir)):
        pdir = os.path.join(rdir, pack)
        if not os.path.isdir(pdir):
            continue
        files = sorted(f for f in os.listdir(pdir) if f.endswith(".md"))
        topics = ", ".join(f[:-3].replace("-", " ") for f in files)
        name = "Common rules" if pack == "common" else f"{humanize(pack)} rules"
        summary = (f"Always-loaded {'cross-language' if pack == 'common' else pack} standards for Claude Code: {topics}.")
        out.append(item(
            "rule", pack, name, summary, f"rules/{pack}",
            {"claude_code": f"npx degit {REPO}/rules/{pack} ~/.claude/rules/ecc/{pack}"},
            {"files": files}, text=pack + " " + topics,
        ))
    return out


def hooks(root):
    p = os.path.join(root, "hooks", "hooks.metadata.json")
    data = json.loads(read(p))
    out = []

    def walk(node, event=None):
        if isinstance(node, dict):
            if "id" in node and "description" in node:
                hid = node["id"]
                slug = re.sub(r"[^a-z0-9]+", "-", hid.lower()).strip("-")
                out.append(item(
                    "hook", slug, hid, node["description"], "hooks/hooks.json",
                    {"claude_code": f"/plugin marketplace add {REPO} && /plugin install ecc@ecc",
                     "note": "Hooks ship together with the ECC plugin; most can be toggled via ECC env vars."},
                    {"event": event} if event else None, text=node["description"],
                ))
            for k, v in node.items():
                walk(v, k if k[:1].isupper() else event)
        elif isinstance(node, list):
            for v in node:
                walk(v, event)

    walk(data)
    return out


def mcps(root):
    data = json.loads(read(os.path.join(root, "mcp-configs", "mcp-servers.json")))
    out = []
    for key, cfg in sorted(data.get("mcpServers", {}).items()):
        snippet = {k: v for k, v in cfg.items() if k != "description"}
        out.append(item(
            "mcp", key, humanize(key), cfg.get("description", ""), "mcp-configs/mcp-servers.json",
            {"claude_code": f"claude mcp add-json {key} '{json.dumps(snippet)}'",
             "note": "Fill in any placeholder paths or API keys before adding."},
            text=key + " " + cfg.get("description", ""),
        ))
    return out


def bundle(root):
    version = read(os.path.join(root, "VERSION")).strip()
    return item(
        "plugin", "ecc", "Everything Claude Code (full plugin)",
        "The whole ECC operator layer in one install: agents, skills, legacy commands, hooks and rules "
        "for Claude Code, Codex, Cursor, OpenCode and other harnesses. Start here if you want a complete setup.",
        ".claude-plugin/marketplace.json",
        {"claude_code": f"/plugin marketplace add {REPO}\n/plugin install ecc@ecc",
         "npm": f"npx ecc-universal@{version} install --profile minimal --target claude"},
        {"version": version}, text="plugin",
    )


def main():
    root, out_path = sys.argv[1], sys.argv[2]
    try:
        commit = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = ""
    items = [bundle(root)] + skills(root) + agents(root) + commands(root) + rules(root) + hooks(root) + mcps(root)
    seen = set()
    for it in items:
        if it["id"] in seen:
            raise SystemExit(f"duplicate id {it['id']}")
        seen.add(it["id"])
        it["source"]["commit"] = commit
    counts = {}
    for it in items:
        counts[it["type"]] = counts.get(it["type"], 0) + 1
    catalog = {
        "schema": "repo.io/catalog@1",
        "source": {"name": "Everything Claude Code", "repo": REPO, "commit": commit,
                   "version": items[0]["version"], "license": "MIT", "homepage": "https://ecc.tools"},
        "counts": counts,
        "items": items,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=1, ensure_ascii=False)
    print(json.dumps(counts), len(items))


if __name__ == "__main__":
    main()
