#!/usr/bin/env python3
"""Check the installed pstack baseline and local removals before skill sync."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat


def installed_files(root):
    files = [root / 'RUNTIME.md']
    for directory in ('skills', 'agents'):
        files.extend(p for p in (root / directory).rglob('*')
                     if p.is_file() and not any(part in {'__pycache__', 'node_modules'} for part in p.parts))
    return {p.relative_to(root).as_posix(): {
        'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
        'executable': bool(p.stat().st_mode & stat.S_IXUSR),
    } for p in sorted(files)}


def validate(root):
    policy = json.loads((root / 'LOCAL_POLICY.json').read_text())
    if policy.get('version') != 1 or not policy.get('installedFiles'):
        raise ValueError('Missing version 1 installed baseline')
    errors = []
    shared = root.parent / 'skills'
    for name in policy['removedSkills']:
        for path in (shared / name, root / 'skills' / name):
            if path.exists() or path.is_symlink():
                errors.append(f'Removed skill restored: {path}')
    for resource in policy['removedResources']:
        if (root / resource).exists() or (root / resource).is_symlink():
            errors.append(f'Removed resource restored: {resource}')
    current = installed_files(root)
    baseline = policy['installedFiles']
    for resource in sorted(set(current) | set(baseline)):
        if current.get(resource) != baseline.get(resource):
            errors.append(f'Review required: {resource}')
    prohibited = re.compile(r'opening-a-pr\.md|\*\*Opening a PR\*\*|`(?:grok[\w.-]*|claude-opus[\w.-]*|gpt-\d[\w.-]*)`|environment:\s*["\']cloud["\']', re.I)
    for resource in current:
        if resource.endswith('.md'):
            for number, line in enumerate((root / resource).read_text().splitlines(), 1):
                if prohibited.search(line):
                    errors.append(f'Unsupported upstream instruction: {resource}:{number}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent / 'pstack')
    args = parser.parse_args()
    try:
        errors = validate(args.root)
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    for error in errors:
        print(error)
    if errors:
        print('Adapt and review the changed files before updating LOCAL_POLICY.json. See docs/pstack-skills.md.')
        return 1
    print('Pstack baseline and removal checks passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
