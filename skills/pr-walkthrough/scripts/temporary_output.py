import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import time


TASK_PREFIX = "handoff-"
RETENTION_SECONDS = 7 * 24 * 60 * 60


def require_outside_git(directory):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(LC_ALL="C", GIT_DISCOVERY_ACROSS_FILESYSTEM="1")
    probe = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--absolute-git-dir"],
        capture_output=True,
        text=True,
        env=env,
    )
    missing_repository = any(
        line.startswith("fatal: not a git repository") for line in probe.stderr.splitlines()
    )
    if probe.returncode != 128 or not missing_repository:
        raise ValueError(f"Cannot verify temporary storage is outside Git: {directory}")


def remove_task(directory):
    try:
        shutil.rmtree(directory)
    except FileNotFoundError:
        if directory.exists():
            raise


def main():
    parser = argparse.ArgumentParser(description="Manage temporary PR walkthrough directories.")
    parser.add_argument("--remove", type=Path, metavar="DIRECTORY", help="Remove a task directory.")
    args = parser.parse_args()

    try:
        parent = Path(os.environ.get("TMPDIR") or "/tmp").resolve(strict=True)
        require_outside_git(parent)
        root = parent / f"pr-walkthroughs-{os.getuid()}"
        root.mkdir(mode=0o700, exist_ok=True)
        info = root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError(f"Walkthrough storage must be a private directory: {root}")
        require_outside_git(root)

        if args.remove is not None:
            directory = args.remove
            if directory.parent.resolve() != root or not directory.name.startswith(TASK_PREFIX):
                raise ValueError(f"Expected a walkthrough task directory under {root}: {directory}")
            remove_task(root / directory.name)
            return

        cutoff = time.time() - RETENTION_SECONDS
        for directory in root.glob(f"{TASK_PREFIX}*"):
            try:
                info = directory.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISDIR(info.st_mode) and info.st_mtime < cutoff:
                remove_task(directory)

        print(tempfile.mkdtemp(prefix=TASK_PREFIX, dir=root))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
