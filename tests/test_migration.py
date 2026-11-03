import json
import tempfile
import unittest
from pathlib import Path
from teamdev import core, migration

class MigrationTests(unittest.TestCase):
    def test_preserve_custom_settings_and_backup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            core.copy_assets(root)
            settings = root / 'opencode.json'
            settings.write_text(json.dumps({'default_agent':'build','plugin':['my-plugin']}))
            role = root / '.opencode/agents/coordinator.md'
            role.write_text('my custom agent content')
            preview = migration.upgrade_routing(root)
            self.assertFalse(preview['applied'])
            self.assertEqual(role.read_text(), 'my custom agent content')
            applied = migration.upgrade_routing(root, apply=True)
            self.assertTrue(applied['applied'])
            self.assertEqual(core.json_read(settings)['plugin'], ['my-plugin'])
            self.assertEqual(core.json_read(settings)['default_agent'], 'coordinator')
            self.assertEqual((Path(applied['backup']) / '.opencode/agents/coordinator.md').read_text(), 'my custom agent content')

if __name__ == '__main__':
    unittest.main()
