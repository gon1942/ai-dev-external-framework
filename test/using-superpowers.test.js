'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
test('21 components register original using-superpowers and all six stages',()=>{
 const policy=require('../skill-policy.json');assert.equal(Object.keys(policy.skills).length,23);
 assert.deepEqual(policy.skills['using-superpowers'],{kind:'upstream',source:'superpowers',enabled:true});
 for(const stage of ['analyze','plan','implement','verify','review','complete'])assert.ok(policy.stages[stage].some(s=>s.id==='using-superpowers'));
});
test('upstream installer and dependency check track using-superpowers',()=>{
 assert.match(fs.readFileSync(path.join(root,'scripts/external-install.py'),'utf8'),/using-superpowers/);
 assert.match(fs.readFileSync(path.join(root,'lib/deps.js'),'utf8'),/using-superpowers/);
 assert.match(fs.readFileSync(path.join(root,'templates/.ai-dev/dependency-check.cjs'),'utf8'),/using-superpowers/);
});
