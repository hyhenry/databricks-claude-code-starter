# Databricks notebooks, locally, with Claude Code

This template is for exploratory data work in **VS Code**, using **standard Databricks notebooks**, with **Claude Code** as an assistant (similar to Genie Code in the workspace).

- Spark runs on your Databricks workspace's **serverless** compute through **Databricks Connect**.
- pandas, scikit-learn and matplotlib run on your machine.
- Notebooks are plain Databricks `.py` source files. Copy one into the workspace and it runs unchanged.

```
VS Code ── notebook view (Databricks Notebook extension)
   │          └─ kernel: .venv  ── Databricks Connect ──► Databricks serverless (Spark)
   ├─ Databricks extension (sign-in, compute, Run in Databricks Connect)
   └─ Claude Code (edits notebooks, checks data, runs them headless to verify)
```

---

## Before you start

You need the software and VS Code extensions below on your machine. Everything else is set up per project in the [setup steps](#setup-windows): the workspace login (step 1), and Python, `databricks-connect` and the other packages in this project's `.venv` (step 2).

**Don't:**
- Install Python yourself. uv downloads the Python version that matches serverless.
- `pip install databricks-connect` or `pip install pyspark`. Step 2 installs the right version, and an extra `pyspark` breaks Databricks Connect.
- Let the Databricks extension create a different Python environment. Point it at `.venv`.

### Software

| Software | Notes |
|---|---|
| Git | |
| Visual Studio Code | |
| Databricks CLI | v1.16.0 or newer |
| uv (Astral) | Python package and environment manager; `databricks environments setup-local` depends on it |
| Claude Code | Command-line tool |

### VS Code extensions

| Extension | Marketplace ID | What it's for |
|---|---|---|
| Python | `ms-python.python` | Python language support and interpreter selection |
| Jupyter | `ms-toolsai.jupyter` | Runs notebook cells in a local kernel |
| Databricks | `databricks.databricks` | Workspace sign-in, compute selection, `spark`/`dbutils`/`display` in your notebooks |
| Databricks Notebook | `andrewgross.databricks-notebook` | Opens Databricks `.py` files as a real notebook instead of `# MAGIC` text |
| Claude Code | `anthropic.claude-code` | Claude panel inside VS Code |

### Network access

Setup and day-to-day use need outbound HTTPS to:
- your Databricks workspace
- PyPI (`pypi.org`, `files.pythonhosted.org`) for Python packages, or your company's internal mirror
- GitHub (`github.com`), where uv downloads its managed Python builds
- Anthropic (`claude.ai`, `api.anthropic.com`) for Claude Code

### Access and accounts

- your Databricks workspace URL, e.g. `https://YOUR-WORKSPACE.cloud.databricks.com`
- permission to use serverless compute in that workspace
- a Claude account for Claude Code

### Check the install

Once everything is installed, open a terminal and confirm each tool responds:

```powershell
git --version
code --version
databricks --version   # must be v1.16.0 or newer
uv --version
claude --version
```

---

## Setup (Windows)

### 1. Get the template and sign in to Databricks

Copy this template folder (or clone your team's repo) to wherever you keep projects, e.g. `C:\dev\my-analysis`. Then in PowerShell, inside that folder:

```powershell
cd C:\dev\my-analysis
databricks auth login --host https://YOUR-WORKSPACE.cloud.databricks.com --profile my-workspace
```

A browser window opens. Log in and come back. Then confirm the profile is valid:

```powershell
databricks auth profiles     # your profile should show Valid: YES
```

Open **`databricks.yml`** and fill in the same two values:

```yaml
      host: https://YOUR-WORKSPACE.cloud.databricks.com
      profile: my-workspace
```

### 2. Create the Python environment

From the project folder:

```powershell
databricks environments setup-local --profile my-workspace --serverless-version 6
```

This command:
- installs Python 3.12 and `databricks-connect`
- pins every package in `pyproject.toml` to the versions Databricks serverless uses
- creates `.venv` and `uv.lock`

It takes about a minute. Expect a warning that `requires-python` was replaced; that's normal. A `pyproject.toml.bak` backup is left behind, and you can delete it.

> **Which serverless version?** Use the newest one available (6 at the time of writing). If you get `E_ENV_UNSUPPORTED`, that version isn't published yet, so try one lower. You can preview the changes first by adding `--dry-run`.

### 3. Check that everything works, without VS Code

```powershell
uv run python scripts/run_notebook.py notebooks/example_exploration.py
```

You should see tables of transactions and revenue, and the final line should be `RESULT: OK`. If so, Databricks Connect, your login and serverless all work.

### 4. Open the project in VS Code

```powershell
code .
```

1. **Pick the Python interpreter.** Open the Command Palette (`Ctrl+Shift+P`), run **Python: Select Interpreter**, and choose `.venv`. It's usually picked already.
2. **Connect the Databricks extension.** Click the **Databricks** icon in the left sidebar. It reads `databricks.yml`; sign in with your profile if asked. Under compute, choose **Serverless**.
   - If the extension offers to install `databricks-connect`, it isn't using `.venv`. Fix the interpreter first.
3. **Open a notebook as a notebook.** Right-click `notebooks/example_exploration.py` and choose **Open as Databricks Notebook**. The `# MAGIC %md` blocks now show as formatted markdown.
4. **Pick the kernel.** Choose the `.venv` kernel (top right of the notebook) and click **Run All**.

You can also run a `.py` notebook in the plain text editor, using the **Run Cell** / **Run in Databricks Connect** buttons the Databricks extension adds.

### 5. Start Claude Code

Open the Claude Code panel in VS Code (the Claude icon in the sidebar or editor title bar), or run `claude` in the VS Code terminal. Sign in the first time.

Claude reads `CLAUDE.md` in this folder, which teaches it the setup: your profile, the notebook format, and how to check its own work. Try prompts like:

- *"What tables are in samples.bakehouse, and how do they relate?"*
- *"Create notebooks/franchise_performance.py comparing revenue by franchise and city, with a chart."*
- *"Add a day-of-week breakdown to example_exploration and run it."*

Claude edits the `.py` notebook, then runs it headless with `scripts/run_notebook.py` and reads the outputs and charts before reporting back. If you have the notebook open, cells it didn't touch keep their outputs.

---

## Day-to-day

| Task | How |
|---|---|
| New notebook | Copy `notebooks/example_exploration.py`, or ask Claude for one |
| Run interactively | Open as Databricks Notebook, then Run All / run cells |
| Run headless | `uv run python scripts/run_notebook.py notebooks/<name>.py` (outputs go to `.runs/`) |
| Add a package | `uv add --dev <package>`, never `pip install` |
| Move to the workspace | Import the `.py` into the workspace; it opens as a normal notebook |
| Log in again after a session expires | `databricks auth login --profile my-workspace` |
| Upgrade to a newer serverless version | Re-run step 2 with the new `--serverless-version` |

**Notebook rules,** so a notebook works both locally and in the workspace:
- Use `spark`, `dbutils`, `display` and `dbutils.widgets` as-is. Don't create your own Spark session.
- Locally, widgets just return their default values.
- Do heavy work in Spark, and only `.toPandas()` small results.
- `%pip`, `%sh`, `%run` and `%fs` cells are skipped by the headless runner.

## What's in this template

```
databricks.yml               workspace + profile (the Databricks extension reads this)
pyproject.toml               local packages; setup-local adds the serverless version pins
CLAUDE.md                    instructions Claude Code follows in this project
notebooks/
  example_exploration.py     starter notebook; also the setup check
scripts/
  run_notebook.py            runs a Databricks notebook headless via Databricks Connect
.vscode/
  settings.json              uses .venv; treats "# COMMAND ----------" as a cell marker
  extensions.json            recommended extensions
```

Generated by setup:
- `.venv/`, `.databricks/` and `.runs/` are ignored by git.
- `uv.lock` is not ignored. Commit it so everyone gets identical package versions.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `databricks` / `uv` / `claude` is not recognized | Close and reopen the terminal (and VS Code) after installing. If it still fails, the tool isn't on your PATH |
| Step 2 fails downloading Python or packages | A proxy or firewall is blocking GitHub or PyPI. See [Network access](#network-access) |
| `NameError: name 'spark' is not defined` in the notebook view | The kernel isn't `.venv`, or the Databricks extension isn't connected. Redo step 4.1–4.2, then restart the kernel |
| You see `# MAGIC` text instead of a notebook | Right-click the file and choose **Open as Databricks Notebook** |
| `E_ENV_UNSUPPORTED` in step 2 | That serverless version isn't published; use a lower `--serverless-version` |
| Auth or `401` errors | `databricks auth login --profile <name>`, then check with `databricks auth profiles` |
| `PERMISSION_DENIED` on a table | You need Unity Catalog access to it; ask a workspace admin |
| Serverless not available | Your workspace or role may not allow serverless. Ask an admin, or pick a cluster in the Databricks extension |
| Import works locally but not in the workspace | The package isn't on serverless. Add it in the notebook's **Environment** panel in the workspace |

## macOS / Linux

Everything is the same except one path: change the interpreter path in `.vscode/settings.json` to `${workspaceFolder}/.venv/bin/python`.
