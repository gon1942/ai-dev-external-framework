'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {load}=require('../lib/skill-manager');
test('self-improving-agent is registered as a pinned git skill',()=>{const p=load();const s=p.skills['self-improving-agent'];assert.ok(s,'policy entry exists');assert.equal(s.kind,'git');assert.equal(s.url,'https://github.com/Grail-Computer/Self-Improving-Agent.git');assert.match(s.ref,/^[a-f0-9]{40}$/i);assert.equal(s.directory,'skills/self-improving-agent');assert.equal(s.enabled,true)});
test('self-improving-agent is assigned to the complete stage',()=>{const p=load();const item=p.stages.complete.find(x=>x.id==='self-improving-agent');assert.ok(item,'assigned to complete stage');assert.equal(item.mode,'recommended')});
test('template AGENTS.md carries the self-correction protocol and learning section',()=>{const fs=require('node:fs'),path=require('node:path');const t=fs.readFileSync(path.join(__dirname,'..','templates','AGENTS.md'),'utf8');assert.match(t,/## 6\. 자기교정 프로토콜/);assert.match(t,/## 학습된 규칙/);assert.match(t,/승인/);assert.match(t,/크기 규율/)});
test('template PLANS.md complete stage includes reflection hook',()=>{const fs=require('node:fs'),path=require('node:path');const t=fs.readFileSync(path.join(__dirname,'..','templates','docs','PLANS.md'),'utf8');assert.match(t,/자기교정 회고.*self-improving-agent/s)});
