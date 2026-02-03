# Context for commits (parent workspace)

**Read this when committing from or affecting this workspace.**

## What this folder is

This directory is a **local workspace** that holds multiple projects under the [QuantTradingOS](https://github.com/QuantTradingOS) organization. Each subfolder (orchestrator, qtos-core, Market-Regime-Agent, etc.) is or maps to its **own GitHub repo** — e.g. `QuantTradingOS/orchestrator`, `QuantTradingOS/qtos-core`, `QuantTradingOS/Market-Regime-Agent`.

- **Parent folder name on disk:** often `QuantTradingOS` (or similar).
- **On GitHub:** There is **no** single repo that contains this whole tree. Do **not** create a parent repo whose root would be a "QuantTradingOS" folder on the remote.

## Commit and push rules

1. **Commit from inside each project folder.**  
   Run `git add` / `git commit` / `git push` from the project directory (e.g. `orchestrator/`, `qtos-core/`), not from this parent. Each project has its own `.git` and `origin` pointing to its repo (e.g. `https://github.com/QuantTradingOS/orchestrator.git`).

2. **No parent "QuantTradingOS" folder on remote.**  
   Pushing from this parent directory would create a repo whose root is a single "QuantTradingOS" folder containing everything. That is **not** desired. The remote root for each repo should be that project’s contents (e.g. orchestrator’s `api.py`, `run.py`, etc.), not a wrapper folder.

3. **Per-project context.**  
   Some projects have a `CONTEXT.md` (e.g. `orchestrator/CONTEXT.md`) with repo identity and commit rules for that repo. Check it before committing in that project.

4. **Org profile README (what others see).**  
   To update what visitors see on [github.com/QuantTradingOS](https://github.com/QuantTradingOS) (project status, repository map, getting started, etc.), edit **`.github-repo/profile/README.md`**. Commit and push from **`.github-repo/`** (that folder is the QuantTradingOS/.github repo). The file at `.github-repo/profile/README.md` is the source of truth for the org profile; copy it to the root `README.md` of the `.github` repo when you want the live profile to reflect your changes (or keep profile content in `profile/README.md` and use it as the org profile README per GitHub’s convention).

## Projects in this workspace

| Folder | GitHub repo (typical) | Notes |
|--------|------------------------|--------|
| `.github-repo/` | QuantTradingOS/.github | Org profile. **Update `.github-repo/profile/README.md`** for others to see status, repo map, getting started. Commit from `.github-repo/`. |
| `orchestrator/` | QuantTradingOS/orchestrator | See `orchestrator/CONTEXT.md` |
| `qtos-core/` | QuantTradingOS/qtos-core | Core engine, backtesting, execution |
| `Market-Regime-Agent/` | QuantTradingOS/Market-Regime-Agent | Regime detection |
| `Capital-Allocation-Agent/` | QuantTradingOS/Capital-Allocation-Agent | Allocation rules |
| `Portfolio-Analyst-Agent/` | QuantTradingOS/Portfolio-Analyst-Agent | Portfolio analytics |
| `Execution-Discipline-Agent/` | QuantTradingOS/Execution-Discipline-Agent | Execution discipline |
| `Capital-Guardian-Agent/` | QuantTradingOS/Capital-Guardian-Agent | Risk guardrails |
| `Sentiment-Shift-Alert-Agent/` | QuantTradingOS/Sentiment-Shift-Alert-Agent | Sentiment alerts |
| `Equity-Insider-Intelligence-Agent/` | QuantTradingOS/Equity-Insider-Intelligence-Agent | Insider intelligence |
| `Trade-Journal-Coach-Agent/` | QuantTradingOS/Trade-Journal-Coach-Agent | Trade journal coaching |

(Repo names may vary; confirm with `git remote -v` inside each folder.)

## Summary

| What | Rule |
|------|------|
| Where to run `git` | **Inside** each project folder (e.g. `orchestrator/`), not from this parent |
| Remote layout | Each repo’s root = that project’s contents. **No** parent "QuantTradingOS" folder on remote |
| Before committing | Read this file at parent level; read the project’s `CONTEXT.md` if it has one |
