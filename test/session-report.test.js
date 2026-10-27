
'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const {setup}=require('../lib/install');const {upgradeSessionReport}=require('../lib/repair');
test('session start visibly lists installed and missing names and CRG when no active tasks',()=>{
 const p=fs.mkdtempSync(path.join(os.tmpdir(),'session-report-'));try{setup(p);
 const d=path.join(p,'.opencode','skills','to-spec');fs.mkdirSync(d,{recursive:true});fs.writeFileSync(path.join(d,'SKILL.md'),'skill');
 const r=spawnSync(process.execPath,[path.join(p,'.ai-dev/session-status.cjs')],{encoding:'utf8'});
 assert.match(r.stdout,/설치 1\/19/);assert.match(r.stdout,/설치: to-spec/);assert.match(r.stdout,/미설치: grill-with-docs/);assert.match(r.stdout,/\[CRG\].*미설치/);assert.match(r.stdout,/Active tasks: 0/);
 const guide=fs.readFileSync(path.join(p,'AGENTS.md'),'utf8');assert.match(guide,/사용자에게 보고한다/);
 }finally{fs.rmSync(p,{recursive:true,force:true})}
});
test('existing v0.8.4 project report can be upgraded with backups and without touching skills',()=>{
 const p=fs.mkdtempSync(path.join(os.tmpdir(),'upgrade-report-'));try{setup(p);
 const chk=path.join(p,'.ai-dev/dependency-check.cjs');fs.writeFileSync(chk,'console.log("old")');
 const a=path.join(p,'AGENTS.md');fs.appendFileSync(a,'\n# custom user instruction\n');
 assert.match(upgradeSessionReport(p,{dry:true}),/WOULD UPGRADE/);assert.match(fs.readFileSync(chk,'utf8'),/old/);
 assert.match(upgradeSessionReport(p),/UPGRADED/);
 assert.match(fs.readFileSync(a,'utf8'),/custom user instruction/);
 assert.match(fs.readFileSync(a,'utf8'),/ai-dev-session-report-v0.8.5/);
 assert.ok(fs.existsSync(a+'.pre-ai-dev-0.8.5.bak'));
 assert.equal(upgradeSessionReport(p),'UNCHANGED session report v0.8.5');
 }finally{fs.rmSync(p,{recursive:true,force:true})}
});
