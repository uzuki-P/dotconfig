"""Regression checks use isolated repos and copies, never real worktree deletion."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = load('guard', ROOT / 'validate-pstack.py')
AUDIT = load('audit', ROOT / 'pstack/skills/poteto-mode/scripts/worktree-audit.py')


class WorktreeAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pstack-audit-')
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git(self.repo, 'init', '-b', 'main')
        self.git(self.repo, 'config', 'user.name', 'Fixture')
        self.git(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'file').write_text('base\n')
        (self.repo / '.gitignore').write_text('.env\nbuild/\n')
        self.git(self.repo, 'add', '.')
        self.git(self.repo, 'commit', '-m', 'base')
        self.tree = self.root / 'worktree with spaces'
        self.git(self.repo, 'worktree', 'add', '-b', 'topic', str(self.tree))

    def tearDown(self):
        self.temp.cleanup()

    def git(self, repo, *args):
        return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)

    def row(self, **kwargs):
        rows = AUDIT.audit(self.repo, 'main', **kwargs)
        self.assertEqual(rows[0]['bucket'], 'hold-main')
        return rows[1]

    def commit_topic(self):
        (self.tree / 'file').write_text('unique\n')
        self.git(self.tree, 'commit', '-am', 'unique')

    def test_clean_merged_and_no_mutation(self):
        before = self.git(self.repo, 'show-ref'), self.git(self.repo, 'worktree', 'list', '--porcelain')
        self.assertEqual(self.row()['bucket'], 'candidate-clean-merged')
        self.assertEqual(self.row()['active'], 'UNKNOWN')
        after = self.git(self.repo, 'show-ref'), self.git(self.repo, 'worktree', 'list', '--porcelain')
        self.assertEqual(before, after)

    def test_closed_pr_does_not_preserve_unique_commit(self):
        self.commit_topic()
        row = self.row(prs=[{'number': 1, 'headRefName': 'topic', 'state': 'CLOSED'}])
        self.assertEqual(row['bucket'], 'review-unmerged')
        self.assertEqual(row['merged'], 'NO')

    def test_squash_merge_needs_review(self):
        self.commit_topic()
        self.assertEqual(self.row(prs=[{'number': 1, 'headRefName': 'topic', 'state': 'MERGED'}])['bucket'], 'review-squash-merge')

    def test_every_file_category_holds(self):
        (self.tree / 'file').write_text('edited\n')
        (self.tree / 'new file').write_text('untracked\n')
        (self.tree / '.env').write_text('fixture only\n')
        (self.tree / 'build').mkdir()
        (self.tree / 'build/artifact').write_text('fixture\n')
        row = self.row()
        self.assertEqual(row['bucket'], 'hold-files')
        self.assertIn('file', row['tracked'])
        self.assertIn('new file', row['untracked'])
        self.assertIn('.env', row['ignored'])
        self.assertIn('build/', row['ignored'])

    def test_staged_addition_holds(self):
        (self.tree / 'new').write_text('added\n')
        self.git(self.tree, 'add', 'new')
        self.assertIn('new', self.row()['tracked'])
        self.assertEqual(self.row()['bucket'], 'hold-files')

    def test_active_and_locked_and_open_pr_hold(self):
        self.assertEqual(self.row(active=[self.tree])['bucket'], 'hold-active')
        self.assertEqual(self.row(prs=[{'number': 1, 'headRefName': 'topic', 'state': 'OPEN'}])['bucket'], 'hold-open-pr')
        self.git(self.repo, 'worktree', 'lock', str(self.tree))
        self.assertEqual(self.row()['bucket'], 'hold-locked')

    def test_invalid_base_fails(self):
        with self.assertRaises(ValueError):
            AUDIT.audit(self.repo, 'missing-ref')


class UpdateGuard(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pstack-policy-')
        self.root = Path(self.temp.name) / 'pstack'
        shutil.copytree(ROOT / 'pstack', self.root, ignore=shutil.ignore_patterns('__pycache__', 'node_modules'))

    def tearDown(self):
        self.temp.cleanup()

    def test_current_installation_passes(self):
        self.assertEqual(GUARD.validate(self.root), [])

    def test_restored_pr_playbook_is_rejected(self):
        (self.root / 'skills/poteto-mode/playbooks/opening-a-pr.md').write_text('restored')
        self.assertTrue(any('Removed resource restored' in e for e in GUARD.validate(self.root)))

    def test_restored_chrome_is_rejected(self):
        (self.root.parent / 'skills/chrome-extensions').mkdir(parents=True)
        self.assertTrue(any('Removed skill restored' in e for e in GUARD.validate(self.root)))

    def test_changed_and_new_resources_are_rejected(self):
        (self.root / 'RUNTIME.md').write_text('overwritten')
        (self.root / 'skills/poteto-mode/new.md').write_text('new instructions')
        errors = GUARD.validate(self.root)
        self.assertIn('Review required: RUNTIME.md', errors)
        self.assertIn('Review required: skills/poteto-mode/new.md', errors)

    def test_model_rule_rejected_even_if_hash_accepted(self):
        (self.root / 'skills/poteto-mode/new.md').write_text('Always use `grok-5`')
        policy = json.loads((self.root / 'LOCAL_POLICY.json').read_text())
        policy['installedFiles'] = GUARD.installed_files(self.root)
        (self.root / 'LOCAL_POLICY.json').write_text(json.dumps(policy))
        self.assertTrue(any('Unsupported upstream instruction' in e for e in GUARD.validate(self.root)))


class PlanCheck(unittest.TestCase):
    def run_plan(self, content):
        with tempfile.TemporaryDirectory(prefix='pstack-plan-') as temp:
            path = Path(temp) / 'plan.md'
            path.write_text(content)
            return subprocess.run(['node', str(ROOT / 'pstack/skills/poteto-mode/scripts/check-plan.mjs'), str(path)], capture_output=True, text=True)

    def valid_plan(self):
        return "# Goal\n\n## Scope\nNamed work.\n\n## Units\n\n### First\n- Depends on: none.\n- Files: src/app.py.\n- Outcome: requested behavior.\n- Verify: run the regression recipe.\n\n## Open questions\nNone.\n"

    def test_concrete_plan_passes(self):
        self.assertEqual(self.run_plan(self.valid_plan()).returncode, 0)

    def test_missing_verification_rejected(self):
        result = self.run_plan(self.valid_plan().replace('- Verify: run the regression recipe.\n', ''))
        self.assertEqual(result.returncode, 1)
        self.assertIn('missing Verify', result.stderr)


if __name__ == '__main__':
    unittest.main()
