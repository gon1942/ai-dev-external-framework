#!/usr/bin/env node
'use strict';
const path=require('node:path'),fs=require('node:fs');
const root=path.resolve(__dirname,'..');
const file=path.join(root,'.ai-dev','stage-skills.json');
const engine=require('./skill-manager-engine.cjs');
const args=process.argv.slice(2);
if(!fs.existsSync(file)){console.error('No synced skill policy. Run framework init or skill sync first.');process.exit(2)}
const [command,action,...rest]=args;
try{
 if(!command||command==='dashboard'||command==='list'){
  const p=engine.load(file);
  for(const stage of engine.STAGES){console.log('\n['+stage.toUpperCase()+'] '+p.stages[stage].length);for(const item of p.stages[stage])console.log(' - '+item.id+' ['+item.mode+'] '+(p.skills[item.id].enabled?'enabled':'disabled'));}
  console.log('\nScope: LOCAL project only. Central team policy changes require framework source release.');
 }else if(command==='validate'){engine.validate(engine.load(file));console.log('LOCAL_SKILL_POLICY_VALID')}
 else if(command==='check-deps'){require('./dependency-check.cjs')}
 else if(command==='stage'){
  const map={add:'stage-add',remove:'stage-remove',replace:'stage-replace',mode:'stage-mode'};
  if(action==='list'){const p=engine.load(file);if(!engine.STAGES.includes(rest[0]))throw Error('Unknown stage');console.log(JSON.stringify(p.stages[rest[0]],null,2))}
  else if(map[action]){
   if(!args.includes('--yes'))throw Error('Local project changes require --yes after explicit user approval. No changes made.');
   const clean=rest.filter(x=>x!=='--yes');console.log(engine.manage({file,action:map[action],args:clean}));engine.validate(engine.load(file));console.log('LOCAL_SKILL_POLICY_VALID');
  }else throw Error('Unknown stage action');
 }else throw Error('Usage: node .ai-dev/skill-manager.cjs [dashboard|validate|check-deps|stage list <stage>|stage add/remove/replace/mode <stage> ... --yes]');
}catch(e){console.error('ERROR:',e.message);process.exitCode=2}
