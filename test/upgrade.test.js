'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {upgradeFiles}=require('../lib/upgrade');
const tmp=()=>fs.mkdtempSync(path.join(os.tmpdir(),'ai-upg-'));
// 합성 템플릿: base(구버전) → new(최신) 차이는 (a) 같은 줄 수정 (b) 말미 새 섹션 추가
const B='# T\nrule one\nrule two\n';
const N='# T\nrule one CHANGED\nrule two\n\n## new section\n';
const BP='# P\np1\n',NP='# P\np1\np2\n';
const BD="console.log('dc1');\n",ND="console.log('dc1');\nconsole.log('dc2');\n";
function setup(ours){
 const root=tmp();
 const tDir=path.join(root,'tpl'),hDir=path.join(root,'hist'),proj=path.join(root,'proj');
 fs.mkdirSync(path.join(tDir,'docs'),{recursive:true});fs.mkdirSync(path.join(tDir,'.ai-dev'),{recursive:true});
 fs.mkdirSync(hDir);fs.mkdirSync(path.join(proj,'docs'),{recursive:true});fs.mkdirSync(path.join(proj,'.ai-dev'),{recursive:true});
 fs.writeFileSync(path.join(tDir,'AGENTS.md'),N);
 fs.writeFileSync(path.join(tDir,'docs','PLANS.md'),NP);
 fs.writeFileSync(path.join(tDir,'.ai-dev','dependency-check.cjs'),ND);
 fs.writeFileSync(path.join(hDir,'AGENTS-v1.md'),B);
 fs.writeFileSync(path.join(hDir,'PLANS-v1.md'),BP);
 fs.writeFileSync(path.join(hDir,'dependency-check-v1.cjs'),BD);
 fs.writeFileSync(path.join(proj,'AGENTS.md'),ours);
 fs.writeFileSync(path.join(proj,'docs','PLANS.md'),BP);
 fs.writeFileSync(path.join(proj,'.ai-dev','dependency-check.cjs'),BD);
 return {root,tDir,hDir,proj};
}
test('pristine old template is auto-upgraded to new template',()=>{const s=setup(B);try{
 const a=upgradeFiles(s.proj,{templatesDir:s.tDir,historyDir:s.hDir});
 assert.ok(a.some(x=>x.startsWith('MERGED AGENTS.md')));
 assert.equal(fs.readFileSync(path.join(s.proj,'AGENTS.md'),'utf8'),N);
 assert.ok(fs.existsSync(path.join(s.proj,'AGENTS.md.bak-upgrade')));
}finally{fs.rmSync(s.root,{recursive:true,force:true})}});
test('user additions are preserved alongside template changes',()=>{const s=setup(B+'## my team rule\n- 커스텀\n');try{
 const a=upgradeFiles(s.proj,{templatesDir:s.tDir,historyDir:s.hDir});
 assert.ok(a.some(x=>x.startsWith('MERGED AGENTS.md')));
 const out=fs.readFileSync(path.join(s.proj,'AGENTS.md'),'utf8');
 assert.match(out,/my team rule/);      // 사용자 섹션 보존
 assert.match(out,/## new section/);    // 신규 템플릿 섹션 반영
 assert.doesNotMatch(out,/<{7}/);       // 충돌 없음
}finally{fs.rmSync(s.root,{recursive:true,force:true})}});
test('editing the same line as the template yields conflict markers and report',()=>{const s=setup('# T\nrule one USER\nrule two\n');try{
 const a=upgradeFiles(s.proj,{templatesDir:s.tDir,historyDir:s.hDir});
 assert.ok(a.some(x=>x.startsWith('CONFLICT AGENTS.md')));
 const out=fs.readFileSync(path.join(s.proj,'AGENTS.md'),'utf8');
 assert.match(out,/<{7} current/);assert.match(out,/={7}/);assert.match(out,/>{7} new/);
}finally{fs.rmSync(s.root,{recursive:true,force:true})}});
test('unknown base produces a proposed copy without touching the original',()=>{const s=setup('완전 다른 내용\n');try{
 const a=upgradeFiles(s.proj,{templatesDir:s.tDir,historyDir:s.hDir});
 assert.ok(a.some(x=>x.startsWith('PROPOSED AGENTS.md')));
 assert.equal(fs.readFileSync(path.join(s.proj,'AGENTS.md'),'utf8'),'완전 다른 내용\n');
 assert.equal(fs.readFileSync(path.join(s.proj,'AGENTS.md.ai-dev-upgrade-proposed'),'utf8'),N);
}finally{fs.rmSync(s.root,{recursive:true,force:true})}});
test('missing file is created; identical file is unchanged; dry-run writes nothing',()=>{const s=setup(N);try{
 fs.rmSync(path.join(s.proj,'AGENTS.md'));
 let a=upgradeFiles(s.proj,{templatesDir:s.tDir,historyDir:s.hDir,dry:true});
 assert.ok(a.some(x=>x.includes('WOULD CREATE')));
 assert.equal(fs.readdirSync(s.proj).filter(f=>f.startsWith('AGENTS')).length,0);
 a=upgradeFiles(s.proj,{templatesDir:s.tDir,historyDir:s.hDir});
 assert.ok(a.some(x=>x.startsWith('CREATED')));
 a=upgradeFiles(s.proj,{templatesDir:s.tDir,historyDir:s.hDir});
 assert.ok(a.some(x=>x.startsWith('UNCHANGED')));
}finally{fs.rmSync(s.root,{recursive:true,force:true})}});
