# Product Manager Skills

A self-contained library of 54 product-management skills from
[deanpeters/Product-Manager-Skills](https://github.com/deanpeters/Product-Manager-Skills),
vendored into this repo so they're available across Claude Code web sessions.

This folder is the **single source of truth** for the PM skills. It is fully
independent — it has nothing to do with any other skill in this repo.

## Layout

```
pm-skills/
├── skills/            # 54 skills, each with SKILL.md (+ examples/templates)
├── commands/          # workflow command templates (discover, write-prd, ...)
├── .claude-plugin/    # upstream plugin/marketplace manifests (for /plugin use)
└── UPSTREAM_README.md # original upstream README
```

## How Claude Code loads them

Claude Code auto-discovers skills from `.claude/skills/<name>/SKILL.md`. To keep
the real files here (and out of `.claude/skills/`) while still loading them,
each skill is symlinked:

```
.claude/skills/<skill-name>  ->  ../../pm-skills/skills/<skill-name>
```

Edit or update a skill in `pm-skills/skills/`; the symlink picks it up
automatically. To refresh from upstream, re-download the repo and re-copy into
`pm-skills/skills/`.

## Re-linking after a fresh clone

Symlinks are committed to git, so a normal clone restores them. If they're ever
missing, recreate them:

```bash
cd .claude/skills
for d in ../../pm-skills/skills/*/; do
  name=$(basename "$d")
  ln -sfn "../../pm-skills/skills/$name" "$name"
done
```

## Categories

Discovery · Strategy · Delivery · Finance · AI PM · Career/Leadership.
See `UPSTREAM_README.md` for the full skill catalog and descriptions.
