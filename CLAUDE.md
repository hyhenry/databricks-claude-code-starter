# Databricks exploratory notebooks (local)

Notebooks in `notebooks/` are **standard Databricks source notebooks**:
- `.py` files that start with `# Databricks notebook source`
- cells separated by `# COMMAND ----------`
- markdown written as `# MAGIC %md`, SQL as `# MAGIC %sql`

They run unchanged in a Databricks workspace, or locally through Databricks Connect. Locally, Spark runs on Databricks **serverless**, and pandas, sklearn and matplotlib run on this machine.

## Environment
- **Workspace and CLI profile:** read `host` and `profile` from `databricks.yml`. Pass `--profile <that profile>` to every `databricks` CLI command.
- **Python:** `.venv` is managed by uv and was provisioned with `databricks environments setup-local --serverless-version <N>`. That command manages the `[tool.uv]` constraints block in `pyproject.toml`, so never hand-edit it. Add packages with `uv add --dev <pkg>`.
- **Windows Git Bash:** set `MSYS_NO_PATHCONV=1` before CLI commands that take workspace paths like `/Users/...`.

## Notebook conventions
- Write notebooks exactly as you would in the workspace. Use `spark`, `dbutils`, `display` and `dbutils.widgets` as globals, and **never** add `DatabricksSession` setup code. The VS Code Databricks extension (interactive) and `scripts/run_notebook.py` (headless) both provide these globals.
- Locally, widgets return their default values.
- Do heavy filtering and aggregation in Spark, and only `.toPandas()` small results.
- Don't display PII columns (emails, phone numbers, addresses, card numbers).
- Start each step with a `# MAGIC %md` header that explains what it does.

## Workflow for Claude
1. **Check the data first.** Look at schemas before writing queries:
   - `databricks tables get <catalog>.<schema>.<table> --profile <profile> -o json`
   - `databricks experimental aitools tools query "<SQL>" --profile <profile>`
2. **Edit the `.py` notebook** directly and keep its cell structure. The user may have it open in the notebook view. Outputs of unchanged cells are preserved, so prefer targeted edits over rewrites.
3. **Check every change by running the notebook headless:**
   `uv run python scripts/run_notebook.py notebooks/<name>.py`
   - It prints each cell's output and any errors. Cell numbers count from the top of the source file.
   - Charts are saved to `.runs/<name>/cellNN.png`. Open them to check how they look.
   - The executed copy is written to `.runs/<name>.ipynb`.
   - Exit code 1 means a cell failed.
4. Report results from the actual outputs, not from assumptions.
