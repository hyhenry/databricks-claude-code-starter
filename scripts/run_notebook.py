"""Run a standard Databricks source notebook (.py) locally via Databricks Connect, headless.

The notebook itself stays a plain Databricks notebook: this runner supplies `spark`,
`dbutils` and `display` the same way the VS Code extension does, executes every cell
in a Jupyter kernel, and prints a per-cell summary of outputs and errors.

Usage:
    uv run python scripts/run_notebook.py <notebook.py> [--profile NAME] [--timeout 600]

The profile defaults to $DATABRICKS_CONFIG_PROFILE, then the `profile:` in databricks.yml.

Outputs:
    .runs/<name>.ipynb      executed notebook (open it in VS Code to see tables/charts)
    .runs/<name>/cellNN.png every chart, for inspection
Exit code is 1 if any cell raised.
"""
import argparse
import base64
import os
import re
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

BOOTSTRAP = '''\
import os
os.environ.setdefault("DATABRICKS_CONFIG_PROFILE", {profile!r})
os.environ.setdefault("DATABRICKS_SERVERLESS_COMPUTE_ID", "auto")
from databricks.sdk.runtime import spark, dbutils
import IPython.display as _ipd
def display(obj=None, *args, **kwargs):
    """Databricks-style display(): Spark DataFrames are rendered as (up to 1000-row) pandas tables."""
    if hasattr(obj, "toPandas") and hasattr(obj, "schema"):
        obj = obj.limit(1000).toPandas()
    _ipd.display(obj)
%matplotlib inline
'''

SKIP_MAGICS = ("%pip", "%sh", "%run", "%fs", "%scala", "%r ")


def parse_cells(text: str):
    text = text.replace("# Databricks notebook source\n", "", 1)
    for chunk in text.split("# COMMAND ----------"):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        lines = chunk.splitlines()
        if all(l.startswith("# MAGIC") or not l.strip() for l in lines):
            body = "\n".join(re.sub(r"^# MAGIC ?", "", l) for l in lines).strip()
            if body.startswith("%md"):
                yield nbf.v4.new_markdown_cell(re.sub(r"^%md ?\n?", "", body).strip())
            elif body.startswith("%sql"):
                sql = re.sub(r"^%sql ?\n?", "", body).strip()
                yield nbf.v4.new_code_cell(f'display(spark.sql("""{sql}"""))')
            elif body.startswith("%python"):
                yield nbf.v4.new_code_cell(re.sub(r"^%python ?\n?", "", body))
            elif body.startswith(SKIP_MAGICS):
                yield nbf.v4.new_code_cell(f"print('SKIPPED locally (unsupported magic): {body.splitlines()[0]}')")
            else:
                yield nbf.v4.new_code_cell(body)
        else:
            yield nbf.v4.new_code_cell(chunk)


def default_profile():
    if os.environ.get("DATABRICKS_CONFIG_PROFILE"):
        return os.environ["DATABRICKS_CONFIG_PROFILE"]
    yml = Path(__file__).resolve().parent.parent / "databricks.yml"
    if yml.exists():
        m = re.search(r"^\s*profile:\s*['\"]?([^'\"\s#]+)", yml.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    return "DEFAULT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notebook")
    ap.add_argument("--profile", default=default_profile())
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    print(f"Profile: {args.profile} | serverless via Databricks Connect")
    src = Path(args.notebook)
    name = src.stem
    out_dir = Path(".runs")
    img_dir = out_dir / name
    img_dir.mkdir(parents=True, exist_ok=True)
    for old in img_dir.glob("*.png"):
        old.unlink()

    cells = [nbf.v4.new_code_cell(BOOTSTRAP.format(profile=args.profile))]
    cells += list(parse_cells(src.read_text(encoding="utf-8")))
    nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})

    failed = False
    try:
        NotebookClient(nb, timeout=args.timeout, kernel_name="python3", allow_errors=False,
                       resources={"metadata": {"path": str(src.parent.resolve())}}).execute()
    except CellExecutionError:
        failed = True
    finally:
        nbf.write(nb, out_dir / f"{name}.ipynb")

    # Summary (cell numbers match the source notebook; bootstrap is cell 0)
    for i, cell in enumerate(nb.cells[1:], start=1):
        if cell.cell_type != "code":
            continue
        lines = []
        for o in cell.get("outputs", []):
            if o.output_type == "stream":
                lines.append(o.text.rstrip())
            elif o.output_type == "error":
                failed = True
                lines.append(f"ERROR {o.ename}: {o.evalue}")
            else:
                data = o.get("data", {})
                if "image/png" in data:
                    p = img_dir / f"cell{i:02d}.png"
                    p.write_bytes(base64.b64decode(data["image/png"]))
                    lines.append(f"[chart -> {p.as_posix()}]")
                elif "text/plain" in data:
                    lines.append(data["text/plain"][:1500])
        if lines:
            print(f"--- cell {i} ---")
            print("\n".join(lines))

    print(f"\nExecuted notebook: {(out_dir / f'{name}.ipynb').as_posix()}")
    print("RESULT:", "FAILED" if failed else "OK")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
