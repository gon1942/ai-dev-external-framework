'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..');
test('dashboard enumerates all six stages and CRG',()=>{const r=cp.spawnSync(process.execPath,[path.join(root,'bin/ai-dev.js'),'skill','dashboard'],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);for(const s of ['ANALYZE','PLAN','IMPLEMENT','VERIFY','REVIEW','COMPLETE'])assert.match(r.stdout,new RegExp(s));assert.match(r.stdout,/code-review-graph/)});
test('source ships quick management prompts for three agents',()=>{for(const p of ['.opencode/commands/skill-manager.md','.claude/commands/skill-manager.md','.codex/prompts/skill-manager.md'])assert.ok(fs.existsSync(path.join(root,p)))});
