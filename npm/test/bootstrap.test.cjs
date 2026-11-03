const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {parse,isLegacyProject,isTeamdevProject,changes} = require('../lib/bootstrap.cjs');
test('parse init/upgrade and reject unsafe flags', () => {
  assert.equal(parse(['init','abc']).dir,'abc');
  assert.equal(parse(['upgrade','--project','.','--apply']).apply,true);
  assert.throws(()=>parse(['upgrade','--apply','--dry-run']));
});
test('legacy framework is detected for migration safety', ()=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'teamdev-legacy-'));
  fs.mkdirSync(path.join(root,'scripts'));
  fs.writeFileSync(path.join(root,'scripts','workflow.py'),'');
  assert.equal(isLegacyProject(root),true);
  assert.equal(isTeamdevProject(root),false);
  fs.rmSync(root,{recursive:true,force:true});
});
test('upgrade actions include self improvement and document sources',()=>{
  const names=changes('.').map(x=>x.command);
  assert.ok(names.includes('upgrade-self-improvement'));
  assert.ok(names.includes('upgrade-document-sources'));
  assert.ok(names.includes('upgrade-report-contract'));
});
