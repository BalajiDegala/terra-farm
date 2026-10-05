"""Build a versioned source ZIP containing the workshop, never learner state or tools."""
import hashlib
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP_FILES = ("README.md", "MVP.md", "CHANGELOG.md", "VERSION", ".gitignore",
             ".gitattributes", ".terraform-version", "compose.yaml", "compose.lambda.yaml")
SOURCE_DIRS = (".github", "runbooks", "examples", "scripts", "tests", "config")
SOURCE_SUFFIXES = {".md", ".tf", ".hcl", ".tftpl", ".py", ".ps1", ".ini", ".yml", ".yaml"}
EXCLUDED_DIRS = {".terraform", "__pycache__", "build", "generated", ".git", ".workshop"}


def release_files(root=ROOT):
    files = [root / name for name in TOP_FILES]
    for folder in SOURCE_DIRS:
        if not (root / folder).is_dir():
            raise RuntimeError(f"Missing source directory: {folder}")
        for path in (root / folder).rglob("*"):
            relative = path.relative_to(root)
            if any(part in EXCLUDED_DIRS for part in relative.parts):
                continue
            if path.is_file() and (path.suffix in SOURCE_SUFFIXES or path.name == "terraform.tfvars.example"):
                files.append(path)
    for path in files:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise RuntimeError(f"Missing or non-local source file: {path}")
        relative = path.relative_to(root)
        if any((root / Path(*relative.parts[:n])).is_symlink() for n in range(1, len(relative.parts))):
            raise RuntimeError(f"Symlink source directory: {path}")
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def build_archive(root=ROOT):
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise RuntimeError("VERSION must contain a release number such as 0.1.0")
    name = f"terraform-floci-lab-{version}"
    destination = root / "dist"
    destination.mkdir(exist_ok=True)
    archive = destination / f"{name}.zip"
    manifest = []
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in release_files(root):
            relative = path.relative_to(root).as_posix()
            data = path.read_bytes()
            manifest.append(f"{hashlib.sha256(data).hexdigest()}  {relative}")
            entry = zipfile.ZipInfo(f"{name}/{relative}")
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            output.writestr(entry, data)
        entry = zipfile.ZipInfo(f"{name}/MANIFEST.sha256")
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        output.writestr(entry, "\n".join(manifest) + "\n")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(".zip.sha256")
    checksum.write_bytes(f"{digest}  {archive.name}\n".encode("utf-8"))
    print(f"Packaged {len(manifest)} source files: {archive}")
    print(f"SHA256: {digest}")
    return archive


if __name__ == "__main__":
    try:
        build_archive()
    except (OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
