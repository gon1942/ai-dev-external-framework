import tempfile
import unittest
from pathlib import Path
from teamdev import core, migration


class DocumentSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        core.copy_assets(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_new_project_contains_guidance(self):
        self.assertTrue((self.root / 'docs/design-docs/README.md').is_file())
        self.assertTrue((self.root / 'docs/references/README.md').is_file())
        self.assertTrue((self.root / 'docs/DOCUMENT-SOURCES.md').is_file())
        self.assertIn('## Design Documents and References (v0.18)', (self.root / 'AGENTS.md').read_text())

    def test_existing_project_preview_and_apply_preserves_custom_docs(self):
        root = self.root
        (root / 'docs/design-docs/README.md').write_text('custom design intro', encoding='utf-8')
        custom = root / 'docs/references/legacy-rag/source.md'
        custom.parent.mkdir(parents=True, exist_ok=True)
        custom.write_text('# legacy data\n', encoding='utf-8')
        (root / 'docs/references/README.md').unlink()
        doc = root / 'AGENTS.md'
        doc.write_text('# existing project AGENTS\n', encoding='utf-8')
        preview = migration.upgrade_document_sources(root)
        self.assertFalse(preview['applied'])
        self.assertEqual(doc.read_text(), '# existing project AGENTS\n')
        self.assertFalse((root / 'docs/references/README.md').exists())
        applied = migration.upgrade_document_sources(root, apply=True)
        self.assertTrue(applied['applied'])
        self.assertEqual((root / 'docs/design-docs/README.md').read_text(), 'custom design intro')
        self.assertEqual(custom.read_text(), '# legacy data\n')
        self.assertTrue((root / 'docs/references/README.md').exists())
        self.assertTrue((root / 'docs/DOCUMENT-SOURCES.md').exists())
        self.assertIn('## Design Documents and References (v0.18)', doc.read_text())
        self.assertEqual((Path(applied['backup']) / 'AGENTS.md').read_text(), '# existing project AGENTS\n')
        again = migration.upgrade_document_sources(root, apply=True)
        self.assertFalse(again['applied'])
        self.assertEqual(doc.read_text().count('## Design Documents and References (v0.18)'), 1)

    def test_task_state_untouched(self):
        task = self.root / 'docs/tasks/DEMO/state.json'
        task.parent.mkdir(parents=True, exist_ok=True)
        task.write_text('{"status":"DISPATCHED"}', encoding='utf-8')
        migration.upgrade_document_sources(self.root, apply=True)
        self.assertEqual(task.read_text(), '{"status":"DISPATCHED"}')


if __name__ == '__main__':
    unittest.main()
