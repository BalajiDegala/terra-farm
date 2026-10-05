"""Validate the workshop in an isolated directory; never provision infrastructure."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def run(arguments, cwd=ROOT, env=None, input=None, expected=0, timeout=600):
    result = subprocess.run([str(arg) for arg in arguments], cwd=cwd, env=env,
                            input=input, capture_output=True, text=True,
                            encoding="utf-8", timeout=timeout)
    if result.returncode != expected:
        raise RuntimeError(f"Command failed ({result.returncode}): {arguments}\n"
                           f"{result.stdout}\n{result.stderr}")
    return result.stdout


def terraform_binary(value=None):
    if value:
        candidate = shutil.which(value) or str(Path(value).resolve())
    else:
        local = ROOT / ".tools/terraform" / ("terraform.exe" if os.name == "nt" else "terraform")
        candidate = str(local) if local.is_file() else shutil.which("terraform")
    if not candidate or not Path(candidate).is_file():
        raise RuntimeError("Install Terraform on PATH, or pass --terraform with its executable path.")
    return candidate


def isolated_workspace(prefix):
    parent = (ROOT / ".workshop").resolve()
    parent.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=prefix, dir=parent)).resolve()
    for name in ("examples", "config", "scripts"):
        shutil.copytree(ROOT / name, work / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".terraform"))
    return work


def remove_workspace(work):
    # Check the final absolute target before recursively removing a disposable workspace.
    work = work.resolve()
    if work.parent != (ROOT / ".workshop").resolve():
        raise RuntimeError(f"Refusing to remove a directory outside .workshop/: {work}")
    shutil.rmtree(work)


def initialize(terraform, directory, plugin_dir=None, env=None, backend=False):
    args = [terraform, "init", "-input=false", "-no-color", "-lockfile=readonly"]
    if not backend:
        args.append("-backend=false")
    if plugin_dir:
        args.append(f"-plugin-dir={Path(plugin_dir).resolve().as_posix()}")
    return run(args, cwd=directory, env=env)


def copy_chapter(work, number):
    run([sys.executable, work / "scripts/chapter.py", number], cwd=work)


def import_example():
    lesson = (ROOT / "runbooks/11-state.md").read_text(encoding="utf-8")
    return lesson.split("```hcl\n", 1)[1].split("```", 1)[0]


def check_sources(root=ROOT):
    for number in range(15):
        lessons = list((root / "runbooks").glob(f"{number:02d}-*.md"))
        if len(lessons) != 1:
            raise RuntimeError(f"Expected exactly one runbook for Chapter {number:02d}.")
        lesson = lessons[0].read_text(encoding="utf-8")
        for section in ("**Goal:**", "**Exercise:**", "**Checkpoint:**"):
            if section not in lesson:
                raise RuntimeError(f"Missing {section} in {lessons[0]}")
    documents = sorted(root.glob("*.md")) + sorted((root / "runbooks").glob("*.md"))
    links = 0
    for path in documents:
        content = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
            parsed = urlsplit(target)
            if parsed.scheme or not parsed.path:
                continue
            linked = (path.parent / unquote(parsed.path)).resolve()
            if not linked.is_relative_to(root.resolve()) or not linked.exists():
                raise RuntimeError(f"Broken local link in {path}: {target}")
            links += 1
        if path.parent.name == "runbooks":
            for line in content.splitlines():
                if line.startswith("terraform ") and re.search(r'(?<![\w"\'])-(?:out|replace|var)=[^\s`"\']+', line):
                    raise RuntimeError(f"Quote the whole Terraform option for PowerShell in {path}: {line}")
    for folder in ("scripts", "tests", "examples"):
        for path in (root / folder).rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"PASS: chapter runbooks, {links} local links, shell option quoting, and Python syntax", flush=True)


def check_terraform(terraform, plugin_dir=None):
    run([terraform, "fmt", "-check", "-recursive", "examples"])
    work = isolated_workspace("check-")
    print(f"Validating in {work}", flush=True)
    try:
        for number in range(1, 13):
            copy_chapter(work, number)
            lab = work / "lab"
            if number == 11:
                (lab / "imported.tf").write_text(import_example(), encoding="utf-8")
            if number in (1, 3, 7, 12):
                initialize(terraform, lab, plugin_dir)
            run([terraform, "validate", "-no-color"], cwd=lab)
            print(f"PASS: cumulative Chapter {number:02d}", flush=True)
        bootstrap = work / "state-bootstrap"
        shutil.copytree(work / "examples/13-bootstrap", bootstrap)
        initialize(terraform, bootstrap, plugin_dir)
        run([terraform, "validate", "-no-color"], cwd=bootstrap)
        print("PASS: locked bootstrap configuration", flush=True)
        if os.name == "nt":
            shell = work / "shell-check"
            (shell / "build").mkdir(parents=True)
            (shell / "main.tf").write_text('output "example" { value = 1 }\n', encoding="utf-8")
            env = os.environ.copy()
            env["WORKSHOP_TERRAFORM"] = terraform
            command = '& $env:WORKSHOP_TERRAFORM plan "-out=build/shell.tfplan" -no-color; exit $LASTEXITCODE'
            run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command], cwd=shell, env=env)
            print("PASS: native Windows PowerShell plan command", flush=True)
    except BaseException:
        print(f"Validation files preserved for inspection: {work}", file=sys.stderr)
        raise
    remove_workspace(work)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terraform", help="Terraform executable; defaults to the local install or PATH")
    parser.add_argument("--plugin-dir", help="Optional existing Terraform provider mirror for offline validation")
    parser.add_argument("--skip-terraform", action="store_true", help="Check docs, Python syntax, and unit tests only")
    args = parser.parse_args()
    check_sources()
    print(run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]), end="")
    print("PASS: Python regression tests", flush=True)
    if not args.skip_terraform:
        check_terraform(terraform_binary(args.terraform), args.plugin_dir)
    print("PASS: workshop checks completed", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
