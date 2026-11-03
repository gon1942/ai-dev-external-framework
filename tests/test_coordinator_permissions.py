import tempfile
import unittest
from pathlib import Path
from teamdev import core, migration


class CoordinatorPermissionTests(unittest.TestCase):
    def test_new_template_has_both_globs_and_preserves_restrictions(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            core.copy_assets(root)
            content = (root/'.opencode/agents/coordinator.md').read_text()
            self.assertIn('"**/docs/product-specs/**": allow',content)
            self.assertIn('"**/docs/exec-plans/active/**": allow',content)
            self.assertIn('"**/docs/tasks/**": allow',content)
            self.assertIn('"*": deny',content)
            self.assertIn('implementer: allow',content)
            self.assertIn('## Coordinator Progress Reporting (v0.14)',content)
            self.assertEqual(migration.upgrade_coordinator_permissions(root)['status'],'UP_TO_DATE')

    def test_migrate_old_scoped_permissions_and_preserve_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            core.copy_assets(root)
            file=root/'.opencode/agents/coordinator.md'
            original=file.read_text().replace(migration.COORDINATOR_EDIT_RULES,
                                               migration.COORDINATOR_EDIT_RULES_V014,1)
            file.write_text(original)
            preview=migration.upgrade_coordinator_permissions(root)
            self.assertFalse(preview['applied'])
            self.assertEqual(file.read_text(),original)
            result=migration.upgrade_coordinator_permissions(root,apply=True)
            self.assertTrue(result['applied'])
            self.assertEqual(Path(result['backup']).read_text(),original)
            updated=file.read_text()
            self.assertEqual(updated,original.replace(migration.COORDINATOR_EDIT_RULES_V014,
                                                      migration.COORDINATOR_EDIT_RULES,1))
            self.assertEqual(migration.upgrade_coordinator_permissions(root,apply=True)['status'],'UP_TO_DATE')

    def test_unknown_custom_permission_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            core.copy_assets(root)
            file=root/'.opencode/agents/coordinator.md'
            custom=file.read_text().replace(migration.COORDINATOR_EDIT_RULES,'  edit: ask\n',1)
            file.write_text(custom)
            with self.assertRaises(core.WorkflowError):
                migration.upgrade_coordinator_permissions(root,apply=True)
            self.assertEqual(file.read_text(),custom)

if __name__=='__main__':
    unittest.main()
