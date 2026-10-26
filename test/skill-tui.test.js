'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const {manage,load}=require('../lib/skill-manager');
const root=path.resolve(__dirname,'..');
test('manager and agent CLI share one central policy engine and create backup',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'skill-admin-'));
 try{
 const policy=path.join(dir,'skill-policy.json');fs.copyFileSync(path.join(root,'skill-policy.json'),policy);
 const before=fs.readFileSync(policy,'utf8');
 const result=cp.spawnSync(process.execPath,[path.join(root,'bin/ai-dev.js'),'skill','stage','remove','review','code-review','--policy',policy],{encoding:'utf8'});
 assert.equal(result.status,0,result.stderr);
 assert.equal(fs.readFileSync(policy+'.bak','utf8'),before);
 assert.ok(!load(policy).stages.review.some(x=>x.id==='code-review'));
 assert.equal(cp.spawnSync(process.execPath,[path.join(root,'bin/ai-dev.js'),'skill','validate','--policy',policy]).status,0);
 }finally{fs.rmSync(dir,{recursive:true,force:true})}
});
test('interactive manager requires TTY instead of silently changing files',()=>{
 const result=cp.spawnSync(process.execPath,[path.join(root,'bin/ai-dev.js'),'skill','manage'],{encoding:'utf8',input:'3\nyes\n'});
 assert.equal(result.status,2);
 assert.match(result.stderr,/TTY/);
});
test('framework management instructions are provided for all three agents',()=>{
 for(const folder of ['.opencode/skills','.agents/skills','.claude/skills'])assert.ok(fs.existsSync(path.join(root,folder,'framework-skill-admin','SKILL.md')));
 assert.ok(fs.existsSync(path.join(root,'manage-skills.sh')));
});
