"""Copy the next chapter's reference files into lab/. Never run Terraform or touch state."""
import argparse
import datetime
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "lab"
PROGRESS = LAB / ".chapter.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chapter", type=int, choices=range(1, 13))
    args = parser.parse_args()
    previous = json.loads(PROGRESS.read_text())["chapter"] if PROGRESS.exists() else 0
    if args.chapter != previous + 1:
        parser.error(f"Last copied chapter: {previous:02d}. Next must be {previous + 1:02d}. This tracks files, not completed exercises.")
    sources = sorted((ROOT / "examples" / f"{args.chapter:02d}").rglob("*"))
    sources = [path for path in sources if path.is_file()
               and '__pycache__' not in path.parts and '.terraform' not in path.parts
               and path.suffix != '.pyc']
    # Chapters 10 and 11 are exercises in the existing project; all others need source files.
    if not sources and args.chapter not in {10, 11}:
        parser.error(f"Reference files for Chapter {args.chapter:02d} are missing. Restore examples/ from the workshop download before continuing.")
    if args.chapter == 1 and LAB.exists() and any(LAB.iterdir()):
        parser.error("lab/ is not empty. Preserve your work and state before starting a new workshop.")
    LAB.mkdir(exist_ok=True)
    backup = ROOT / ".workshop" / "backups" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    for source in sources:
        relative = source.relative_to(ROOT / "examples" / f"{args.chapter:02d}")
        destination = LAB / relative
        if destination.is_symlink() or any(p.is_symlink() for p in destination.parents if p != ROOT.parent):
            parser.error(f"Refusing symlink destination: {destination}")
        if destination.exists() and destination.read_bytes() != source.read_bytes():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, saved)
            print(f"Backed up: {relative} -> {saved.relative_to(ROOT)}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        print(f"Copied: lab/{relative.as_posix()}")
    if args.chapter == 1:
        (LAB / "config").mkdir(exist_ok=True)
        shutil.copy2(ROOT / "config" / "aws-local.ini", LAB / "config" / "aws-local.ini")
    (LAB / "build").mkdir(exist_ok=True)
    (LAB / "generated").mkdir(exist_ok=True)
    PROGRESS.write_text(json.dumps({"chapter": args.chapter}) + "\n")
    print("Read the chapter, inspect the copied files, then run Terraform yourself from lab/.")


if __name__ == "__main__":
    main()
