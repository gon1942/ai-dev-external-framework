"""Copy canonical skills to native agent paths without overwriting user edits."""
import argparse
import shutil
from pathlib import Path


def sync(root: Path, force: bool = False):
    source = root / '.agents' / 'skills'
    if not source.is_dir():
        raise FileNotFoundError(source)
    outcomes = []
    for target in ('.opencode/skills', '.claude/skills'):
        for item in sorted(source.iterdir()):
            if not (item / 'SKILL.md').is_file():
                continue
            dst = root / target / item.name
            if dst.exists() and not force:
                outcomes.append(f'SKIP {dst}')
                continue
            if dst.exists():
                shutil.rmtree(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(item, dst)
            outcomes.append(f'COPY {dst}')
    return outcomes


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    print('\n'.join(sync(args.root.resolve(), args.force)))
