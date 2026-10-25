const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const os=require('node:os');const path=require('node:path');const {spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
test('published files contain executable CLI and original-skill fetcher',()=>{
 const p=require('../package.json');assert.equal(p.private,false);
 for(const file of [p.bin['ai-dev'],'scripts/external-install.py','scripts/workflow.py','templates/AGENTS.md'])assert.ok(fs.existsSync(path.join(root,file)));
});
test('npx-equivalent CLI setup from package without global install',()=>{
 const work=fs.mkdtempSync(path.join(os.tmpdir(),'ai-dev-npx-'));
 try{const cli=path.join(root,'bin/ai-dev.js');let p=spawnSync(process.execPath,[cli,'setup','--project',work,'--agents','all'],{encoding:'utf8'});assert.equal(p.status,0,p.stderr);p=spawnSync(process.execPath,[cli,'status','--project',work],{encoding:'utf8'});assert.equal(p.status,0,p.stderr);assert.match(p.stdout,/Active tasks: 0/);
 }finally{fs.rmSync(work,{recursive:true,force:true})}
});
