'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..');
test('setup installs executable project-local skill manager and per-agent commands',()=>{
 const project=fs.mkdtempSync(path.join(os.tmpdir(),'ai-manager-'));
 try{
  const {setup}=require('../lib/install');setup(project,{agents:'all'});
  for(const p of ['.opencode/commands/skill-manager.md','.claude/commands/skill-manager.md','.codex/prompts/skill-manager.md','.ai-dev/skill-manager.cjs','.ai-dev/skill-manager-engine.cjs'])assert.ok(fs.existsSync(path.join(project,p)),p);
  fs.writeFileSync(path.join(project,'.ai-dev/stage-skills.json'),fs.readFileSync(path.join(root,'skill-policy.json')));
  const run=(...args)=>cp.spawnSync(process.execPath,[path.join(project,'.ai-dev/skill-manager.cjs'),...args],{encoding:'utf8',cwd:project});
  const view=run('dashboard');assert.equal(view.status,0,view.stderr);assert.match(view.stdout,/PLAYWRIGHT|playwright-cli/i);
  assert.notEqual(run('stage','remove','verify','playwright-cli').status,0);
  assert.equal(run('stage','remove','verify','playwright-cli','--yes').status,0);
  assert.equal(run('validate').status,0);
  const rerun=setup(project,{agents:'all'});assert.ok(rerun.some(x=>x.includes('UNCHANGED .opencode/commands/skill-manager.md')));
 }finally{fs.rmSync(project,{recursive:true,force:true})}
});
