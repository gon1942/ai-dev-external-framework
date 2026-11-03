import tempfile
import unittest
from pathlib import Path
from teamdev import core, migration

class UpgradeIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        core.copy_assets(self.root)
    def tearDown(self):self.tmp.cleanup()
    def test_new_project_has_integrity_docs(self):
        self.assertTrue((self.root/'docs/LIFECYCLE-INTEGRITY.md').is_file())
        self.assertIn('## Lifecycle integrity (v0.10)',(self.root/'AGENTS.md').read_text())
    def test_upgrade_existing_instructions_preserved_and_idempotent(self):
        ag=self.root/'AGENTS.md'
        ag.write_text('custom instructions\n')
        (self.root/'docs/LIFECYCLE-INTEGRITY.md').unlink()
        self.assertFalse(migration.upgrade_lifecycle_integrity(self.root)['applied'])
        result=migration.upgrade_lifecycle_integrity(self.root,True)
        self.assertTrue(result['applied'])
        self.assertIn('custom instructions',ag.read_text())
        self.assertIn('## Lifecycle integrity (v0.10)',ag.read_text())
        self.assertTrue(Path(result['backup']).joinpath('AGENTS.md').is_file())
        self.assertFalse(migration.upgrade_lifecycle_integrity(self.root,True)['applied'])

if __name__=='__main__': unittest.main()
