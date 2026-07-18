from __future__ import annotations

import contextlib
import io
import json
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = ROOT / "TalkToData_Assignment.ipynb"
OUTPUT_PATH = ROOT / "artifacts" / "TalkToData_Assignment.executed.ipynb"


def stream_output(name: str, text: str) -> dict:
    return {
        "name": name,
        "output_type": "stream",
        "text": text.splitlines(keepends=True),
    }


def error_output(exc: BaseException) -> dict:
    return {
        "output_type": "error",
        "ename": type(exc).__name__,
        "evalue": str(exc),
        "traceback": traceback.format_exc().splitlines(),
    }


def execute_notebook() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    exec_globals: dict[str, object] = {}
    execution_count = 1

    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue

        source = "".join(cell.get("source", []))
        stdout = io.StringIO()
        stderr = io.StringIO()
        cell["execution_count"] = execution_count
        cell["outputs"] = []

        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec(compile(source, f"<notebook-cell-{execution_count}>", "exec"), exec_globals)
            if stdout.getvalue():
                cell["outputs"].append(stream_output("stdout", stdout.getvalue()))
            if stderr.getvalue():
                cell["outputs"].append(stream_output("stderr", stderr.getvalue()))
        except BaseException as exc:  # noqa: BLE001
            if stdout.getvalue():
                cell["outputs"].append(stream_output("stdout", stdout.getvalue()))
            if stderr.getvalue():
                cell["outputs"].append(stream_output("stderr", stderr.getvalue()))
            cell["outputs"].append(error_output(exc))
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
            raise

        execution_count += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")


if __name__ == "__main__":
    execute_notebook()
