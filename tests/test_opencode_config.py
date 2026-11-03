import json
import tempfile
import unittest
from pathlib import Path
from teamdev import core, migration


class OpenCodeConfigTests(unittest.TestCase):
    def test_init_template(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            core.copy_assets(root)
            data = core.json_read(root / 'opencode.json')
            self.assertEqual(data['default_agent'], 'coordinator')
            self.assertEqual(data['permission']['read'], 'allow')
            self.assertEqual(data['permission']['edit'], 'allow')
            self.assertEqual(data['permission']['task'], 'allow')
            self.assertEqual(data['permission']['skill'], 'allow')
            self.assertEqual(data['permission']['external_directory'], 'allow')
            self.assertEqual(data['permission']['bash']['git push *'], 'ask')
            self.assertTrue(data['lsp'])

    def test_upgrade_preview_apply_preserves_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            core.copy_assets(root)
            cfg = root / 'opencode.json'
            original = {'default_agent':'coordinator', 'permission':{'bash':{'git push *':'deny', 'custom *':'ask'}, 'edit':'deny'},
                        'lsp': False, 'provider':{'custom':{'url':'http://localhost'}}}
            cfg.write_text(json.dumps(original))
            preview = migration.upgrade_opencode_config(root)
            self.assertFalse(preview['applied'])
            self.assertEqual(core.json_read(cfg), original)
            applied = migration.upgrade_opencode_config(root, apply=True)
            self.assertTrue(applied['applied'])
            self.assertEqual(json.loads(Path(applied['backup']).read_text()), original)
            new = core.json_read(cfg)
            self.assertEqual(new['provider'], original['provider'])
            self.assertEqual(new['permission']['bash']['custom *'], 'ask')
            self.assertEqual(new['permission']['bash']['git push *'], 'ask')
            self.assertEqual(new['permission']['external_directory'], 'allow')
            self.assertTrue(new['lsp'])
            self.assertFalse(migration.upgrade_opencode_config(root, apply=True)['applied'])

    def test_invalid_permission_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            core.copy_assets(root)
            cfg = root / 'opencode.json'
            cfg.write_text('{"permission":{"bash":"deny"}}')
            with self.assertRaises(core.WorkflowError):
                migration.upgrade_opencode_config(root, apply=True)
            self.assertEqual(core.json_read(cfg)['permission']['bash'], 'deny')

if __name__ == '__main__':
    unittest.main()
