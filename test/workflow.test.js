const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const os=require('node:os');const path=require('node:path');const {setup}=require('../lib/install');const {sessionStatus}=require('../lib/status');
const temp=()=>fs.mkdtempSync(path.join(os.tmpdir(),'ai-dev-kit-'));
test('creates 3 native hooks, preserves old AGENTS and is idempotent',()=>{const p=temp();fs.writeFileSync(path.join(p,'AGENTS.md'),'user policy\n');setup(p);assert.equal(fs.readFileSync(path.join(p,'AGENTS.md'),'utf8'),'user policy\n');assert.ok(fs.existsSync(path.join(p,'.opencode/plugins/ai-dev-session.js')));assert.ok(fs.existsSync(path.join(p,'.codex/hooks.json')));assert.ok(fs.existsSync(path.join(p,'.claude/settings.json')));setup(p);for(const f of ['.claude/settings.json','.codex/hooks.json'])assert.equal(JSON.parse(fs.readFileSync(path.join(p,f),'utf8')).hooks.SessionStart.length,1);fs.rmSync(p,{recursive:true,force:true})});
test('status reads existing tasks without writing',()=>{const p=temp();const d=path.join(p,'docs/exec-plans/active/TASK-001');fs.mkdirSync(d,{recursive:true});fs.writeFileSync(path.join(d,'status.json'),JSON.stringify({title:'Demo',approved:false}));const before=fs.statSync(path.join(d,'status.json')).mtimeMs;const s=sessionStatus(p);assert.equal(s.active_count,1);assert.equal(s.tasks[0].phase,'PLAN_DRAFT');assert.equal(fs.statSync(path.join(d,'status.json')).mtimeMs,before);fs.rmSync(p,{recursive:true,force:true})});
test('preserves unrelated existing hooks',()=>{const p=temp();const f=path.join(p,'.claude/settings.json');fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,JSON.stringify({hooks:{SessionStart:[{hooks:[{type:'command',command:'echo old'}]}]}}));setup(p);assert.equal(JSON.parse(fs.readFileSync(f,'utf8')).hooks.SessionStart.length,2);fs.rmSync(p,{recursive:true,force:true})});
const {spawnSync}=require('node:child_process');
test('installed session hook and CLI use identical status classification',()=>{
 const p=temp();try{
  setup(p);
  const dir=path.join(p,'docs/exec-plans/active/TASK-001');fs.mkdirSync(dir,{recursive:true});
  fs.writeFileSync(path.join(dir,'status.json'),JSON.stringify({title:'Todo',approved:false}));
  for(const fn of ['spec.md','plan.md'])fs.writeFileSync(path.join(dir,fn),'content');
  fs.writeFileSync(path.join(dir,'ac-tests.json'),JSON.stringify({'AC-01':'node --test'}));
  const cli=sessionStatus(p);assert.equal(cli.tasks[0].phase,'PLAN_APPROVAL_REQUIRED');
  const r=spawnSync('node',[path.join(p,'.ai-dev/session-status.cjs')],{encoding:'utf8'});
  assert.equal(r.status,0,r.stderr);assert.match(r.stdout,/TASK-001 \| PLAN_APPROVAL_REQUIRED \| Todo/);
  fs.writeFileSync(path.join(dir,'status.json'),JSON.stringify({title:'Todo',approved:true,review:{verdict:'PASS'}}));
  const next=sessionStatus(p);assert.equal(next.tasks[0].phase,'REVERIFY_OR_COMPLETION_CHECK');
  const rr=spawnSync('node',[path.join(p,'.ai-dev/session-status.cjs')],{encoding:'utf8'});
  assert.equal(rr.status,0,rr.stderr);assert.match(rr.stdout,/REVERIFY_OR_COMPLETION_CHECK/);
 }finally{fs.rmSync(p,{recursive:true,force:true})}
});
test('missing required upstream skill fails atomically, no installed copies or lockfile',()=>{
 const p=temp();const src=temp();try{
  for(const vendor of ['mattpocock','superpowers','ponytail'])fs.mkdirSync(path.join(src,vendor,'skills'),{recursive:true});
  const script=path.resolve(__dirname,'../scripts/external-install.py');
  const r=spawnSync('python3',[script,'--project',p,'--agents','all','--source-dir',src],{encoding:'utf8'});
  assert.notEqual(r.status,0);assert.match(r.stderr,/REQUIRED skill/);
  assert.equal(fs.existsSync(path.join(p,'.external-skills-lock.json')),false);
  assert.equal(fs.existsSync(path.join(p,'.agents/skills')),false);
 }finally{fs.rmSync(p,{recursive:true,force:true});fs.rmSync(src,{recursive:true,force:true})}
});
test('offline full fixture installs 19 upstream skill directories per agent and is idempotent',()=>{
 const p=temp();const src=temp();try{
  const groups={mattpocock:['grill-with-docs','to-spec','to-tickets','implement','implement-spec','code-review','retro','diagnosing-bugs'],superpowers:['brainstorming','writing-plans','test-driven-development','systematic-debugging','verification-before-completion','requesting-code-review','receiving-code-review','using-git-worktrees','subagent-driven-development','using-superpowers'],ponytail:['ponytail']};
  for(const [vendor,skills] of Object.entries(groups))for(const name of skills){const d=path.join(src,vendor,'skills',name);fs.mkdirSync(d,{recursive:true});fs.writeFileSync(path.join(d,'SKILL.md'),`---\nname: ${name}\ndescription: fixture\n---\n\nFixture instructions\n`)}
  const args=[path.resolve(__dirname,'../scripts/external-install.py'),'--project',p,'--agents','all','--source-dir',src];
  let r=spawnSync('python3',args,{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
  for(const dest of ['.agents/skills','.opencode/skills','.claude/skills'])assert.equal(fs.readdirSync(path.join(p,dest)).length,19);
  assert.equal(Object.keys(JSON.parse(fs.readFileSync(path.join(p,'.external-skills-lock.json'))).files).length,57);
  r=spawnSync('python3',args,{encoding:'utf8'});assert.equal(r.status,0,r.stderr);assert.equal((r.stdout.match(/SKIP IDENTICAL/g)||[]).length,57);
 }finally{fs.rmSync(p,{recursive:true,force:true});fs.rmSync(src,{recursive:true,force:true})}
});

test('sessionStatus warns on orphan and dual-presence task folders',()=>{const p=temp();try{
  const done=path.join(p,'docs/exec-plans/completed/TASK-001');fs.mkdirSync(done,{recursive:true});fs.writeFileSync(path.join(done,'status.json'),JSON.stringify({id:'TASK-001',title:'Done',approved:true}));
  fs.mkdirSync(path.join(p,'docs/exec-plans/active/TASK-001/evidence'),{recursive:true});
  const s=sessionStatus(p);assert.equal(s.active_count,0);assert.ok(s.warnings.some(w=>/TASK-001.*orphan/.test(w)));assert.ok(s.warnings.some(w=>/TASK-001.*both active and completed/.test(w)));
 }finally{fs.rmSync(p,{recursive:true,force:true})}
});
test('workflow.py session warns on orphans and resolves real completed task despite active orphan',()=>{
  const p=temp();try{
   fs.mkdirSync(path.join(p,'scripts'),{recursive:true});fs.copyFileSync(path.resolve(__dirname,'../scripts/workflow.py'),path.join(p,'scripts','workflow.py'));
   const done=path.join(p,'docs/exec-plans/completed/TASK-001');fs.mkdirSync(done,{recursive:true});fs.writeFileSync(path.join(done,'status.json'),JSON.stringify({id:'TASK-001',title:'Done',approved:true}));
   fs.mkdirSync(path.join(p,'docs/exec-plans/active/TASK-001/evidence'),{recursive:true});
   const r=spawnSync('python3',[path.join(p,'scripts','workflow.py'),'session'],{encoding:'utf8'});
   assert.equal(r.status,0,r.stderr);assert.match(r.stdout,/WARNING: docs\/exec-plans\/active\/TASK-001 orphan folder without status\.json/);assert.match(r.stdout,/WARNING: docs\/exec-plans\/active\/TASK-001 task folder exists in both active and completed/);
   const ap=spawnSync('python3',[path.join(p,'scripts','workflow.py'),'approve','--id','TASK-001','--user-confirmed'],{encoding:'utf8'});
   assert.match(ap.stderr,/completed task/);
  }finally{fs.rmSync(p,{recursive:true,force:true})}
});
