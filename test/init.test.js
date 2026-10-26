'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const os=require('node:os');const path=require('node:path');const {spawnSync}=require('node:child_process');
const cli=path.resolve(__dirname,'../bin/ai-dev.js');
const execute=(args)=>spawnSync(process.execPath,[cli,...args],{encoding:'utf8'});
test('init dry-run on nonexisting project does not create files',()=>{const home=fs.mkdtempSync(path.join(os.tmpdir(),'init-preview-'));try{const dest=path.join(home,'new');const r=execute(['init',dest,'--dry-run']);assert.equal(r.status,0,r.stderr);assert.equal(fs.existsSync(dest),false);assert.match(r.stdout,/WOULD CREATE/)}finally{fs.rmSync(home,{recursive:true,force:true})}});
test('init rejects invalid agent and missing project name',()=>{assert.notEqual(execute(['init']).status,0);assert.notEqual(execute(['init','x','--agents','bad','--dry-run']).status,0)});
test('init on existing project dry-run retains data',()=>{const dest=fs.mkdtempSync(path.join(os.tmpdir(),'init-existing-'));try{fs.writeFileSync(path.join(dest,'keep.txt'),'keep');const r=execute(['init',dest,'--dry-run']);assert.equal(r.status,0,r.stderr);assert.equal(fs.readFileSync(path.join(dest,'keep.txt'),'utf8'),'keep');assert.equal(fs.existsSync(path.join(dest,'AGENTS.md')),false)}finally{fs.rmSync(dest,{recursive:true,force:true})}});
test('one-command init creates project and installs all 18 original-layout fixtures for three agents',()=>{
 const base=fs.mkdtempSync(path.join(os.tmpdir(),'init-e2e-'));
 try{
  const groups={mattpocock:['grill-with-docs','to-spec','to-tickets','implement','implement-spec','code-review','retro','diagnosing-bugs'],superpowers:['brainstorming','writing-plans','test-driven-development','systematic-debugging','verification-before-completion','requesting-code-review','receiving-code-review','using-git-worktrees','subagent-driven-development'],ponytail:['ponytail']};
  for(const [vendor,skills] of Object.entries(groups))for(const name of skills){const d=path.join(base,'source',vendor,'skills',name);fs.mkdirSync(d,{recursive:true});fs.writeFileSync(path.join(d,'SKILL.md'),`---\nname: ${name}\ndescription: fixture\n---\n\nFixture\n`)}
  const dest=path.join(base,'project');const r=execute(['init',dest,'--source-dir',path.join(base,'source'),'--skip-crg']);
  assert.equal(r.status,0,r.stderr);assert.match(r.stdout,/INIT COMPLETE/);
  assert.ok(fs.existsSync(path.join(dest,'AGENTS.md')));
  for(const location of ['.agents/skills','.opencode/skills','.claude/skills'])assert.equal(fs.readdirSync(path.join(dest,location)).length,18);
  assert.ok(fs.existsSync(path.join(dest,'.external-skills-lock.json')));
 }finally{fs.rmSync(base,{recursive:true,force:true})}
});
