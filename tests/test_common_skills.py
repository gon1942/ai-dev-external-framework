import tempfile, unittest
from pathlib import Path
from teamdev import core,common_skills,cli,orchestrator

class CommonSkillTests(unittest.TestCase):
    def setUp(self):
        self.ctx=tempfile.TemporaryDirectory();self.root=Path(self.ctx.name);core.copy_assets(self.root)
    def tearDown(self):self.ctx.cleanup()
    def test_all_three_runtimes_have_locked_skills(self):
        info=common_skills.status(self.root)
        self.assertTrue(info['ok'])
        self.assertEqual(info['total'],20)
        self.assertEqual(info['runtimes'],{'codex':20,'opencode':20,'claude':20})
    def test_missing_file_detected_and_repaired(self):
        file=self.root/'.opencode/skills/brainstorming/SKILL.md';file.unlink()
        self.assertEqual(cli.main(['--root',str(self.root),'skills-status','--strict']),2)
        info=common_skills.sync(self.root,apply=True)
        self.assertTrue(info['status']['ok'])
    def test_modified_skill_protected_until_force(self):
        file=self.root/'.claude/skills/brainstorming/SKILL.md';file.write_text('modified')
        self.assertTrue(common_skills.sync(self.root,apply=True)['conflicts'])
        self.assertEqual(file.read_text(),'modified')
        self.assertTrue(common_skills.sync(self.root,apply=True,force=True)['status']['ok'])
    def test_upgrade_old_project_preserves_legacy_task(self):
        core.create_task(self.root,'KEEP-001','Preserve me')
        old=self.root/'docs/tasks/KEEP-001/state.json';content=old.read_bytes()
        for item in ['.ai-dev/skills.lock.json','.agents/skills/brainstorming/SKILL.md']:
            (self.root/item).unlink()
        out=common_skills.upgrade(self.root,True)
        self.assertTrue(out['ok'])
        self.assertEqual(old.read_bytes(),content)
        self.assertTrue(common_skills.status(self.root)['ok'])
    def test_worker_dispatch_prevented_on_integrity_error(self):
        task='TASK-199';core.create_task(self.root,task,'Example')
        state=core.json_read(self.root/f'docs/tasks/{task}/state.json')
        state.update(stage='IMPLEMENT',status='APPROVED')
        core.atomic_json(self.root/f'docs/tasks/{task}/state.json',state)
        # When approval seal is absent, lifecycle/plan check should also block.
        (self.root/'.opencode/skills/brainstorming/SKILL.md').unlink()
        self.assertFalse(common_skills.status(self.root)['ok'])
