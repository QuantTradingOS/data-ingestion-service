# Context for commits (data-ingestion-service)

**Read this when committing so the repo and layout stay correct.**

## Repo identity

- **This repository:** [QuantTradingOS/data-ingestion-service](https://github.com/QuantTradingOS/data-ingestion-service) on GitHub (to be created).
- **Remote:** `origin` → `https://github.com/QuantTradingOS/data-ingestion-service.git`
- **Branch:** `main` (push to `origin main`).

Data-ingestion-service is a **standalone repo** in the QuantTradingOS organization. It is **not** inside a parent "QuantTradingOS" repo on the remote.

## Commit and push rules

1. **Commit from the data-ingestion-service directory.**  
   Run `git` from `data-ingestion-service/` (this folder). Do not commit this folder as a subfolder of a parent repo that would create a "QuantTradingOS" folder on the remote.

2. **Remote root = data-ingestion-service contents.**  
   The remote repo root should be the contents of this folder (e.g. `api/`, `ingestion/`, `db/`, `README.md`). There must be **no parent folder named "QuantTradingOS"** on the remote.

3. **Push:**  
   `git push origin main` from inside `data-ingestion-service/`.

## On-disk layout

- On your machine, `data-ingestion-service/` usually sits next to sibling repos (orchestrator, qtos-core, agents) under a common parent directory.
- Those siblings are **separate** GitHub repos under the QuantTradingOS org; each has its own `.git` and remote.
- The service can be run standalone (API + scheduler) or integrated with the orchestrator/agents via the API endpoints.

## Summary

| What | Where |
|------|--------|
| This repo on GitHub | **QuantTradingOS/data-ingestion-service** (no parent QuantTradingOS folder) |
| Where to run `git` | Inside **data-ingestion-service/** |
| Where to run API/scheduler | Inside **data-ingestion-service/** |
