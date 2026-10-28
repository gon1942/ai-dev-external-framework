'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {install,inspect}=require('../lib/rtk');const {load}=require('../lib/skill-manager');
const temp=()=>fs.mkdtempSync(path.join(os.tmpdir(),'rtk-ai-'));
test('central policy registers RTK as a component',()=>{const p=load();assert.equal(p.skills.rtk.kind,'rtk');assert.equal(p.skills.rtk.source,'rtk-ai/rtk')});
test('dry run does not mutate or execute anything',()=>{const root=temp();try{const x=install(root,{dry:true,runner:()=>{throw Error('runner should not execute')}});assert.ok(x.some(y=>y.includes('curl -fsSL')));assert.ok(x.some(y=>y.includes('rtk')&&y.includes('init')));assert.equal(fs.readdirSync(root).length,0)}finally{fs.rmSync(root,{recursive:true,force:true})}});
test('fixture binary present: installs record and reports installed',()=>{const root=temp();const runner=(cmd,args)=>{if(args[0]==='--version'&&String(cmd).includes('rtk'))return {status:0,stdout:'rtk 1.1.0',stderr:''};return {status:0,stdout:'',stderr:''}};try{
 const result=install(root,{runner});
 assert.ok(result.some(y=>y.includes('RTK binary present')));
 assert.ok(fs.existsSync(path.join(root,'.ai-dev','rtk-install.json')));
 assert.equal(inspect(root,{runner}).installed,true);
 assert.equal(install(root,{runner})[0],'RTK ALREADY INSTALLED');
}finally{fs.rmSync(root,{recursive:true,force:true})}});
test('inspect on empty project reports not installed without throwing',()=>{const root=temp();const runner=()=>({error:Error('no binary'),status:null});try{const s=inspect(root,{runner});assert.equal(s.installed,false);assert.equal(s.binary,null)}finally{fs.rmSync(root,{recursive:true,force:true})}});
