'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {setup,installSkills}=require('./install');
const {spawnSync}=require('node:child_process');
const {installCrg}=require('./crg');
function init(argv){
 const value=(key)=>{const i=argv.indexOf(key);if(i<0)return undefined;if(!argv[i+1]||argv[i+1].startsWith('--'))throw Error(`Missing value for ${key}`);return argv[i+1]};
 const positional=argv.filter((x,i)=>!x.startsWith('--')&&!['--agents','--pins','--source-dir'].includes(argv[i-1]));
 const target=positional[0];
 if(!target||positional.length!==1)throw Error('Usage: ai-dev init <project-directory> [--agents all] [--dry-run]');
 const project=path.resolve(target),dry=argv.includes('--dry-run');
 const agents=value('--agents')||'all',sourceDir=value('--source-dir'),pins=value('--pins');
 if(!['all','opencode','codex','claude'].includes(agents))throw Error('Unknown agents option: '+agents);
 if(fs.existsSync(project)&&!fs.statSync(project).isDirectory())throw Error('Target exists and is not a directory: '+project);
 if(!fs.existsSync(project)){
  console.log(`${dry?'WOULD CREATE':'CREATE'} project ${project}`);
  if(!dry)fs.mkdirSync(project,{recursive:true});
 }
 // All setup actions are planned before any upstream fetch. Existing project files are never overwritten.
 // A failed upstream fetch leaves installed docs intact, so retrying `init` is possible.
 if(!dry||fs.existsSync(project))for(const action of setup(project,{dry,agents}))console.log(action);
 if(dry&&!fs.existsSync(project)){
  console.log('Dry-run: new project does not yet exist; setup and upstream skills would be installed at '+project);
  console.log('WOULD INSTALL original upstream skills (fetch required on real install)');
  console.log('WOULD INSTALL CRG unless --skip-crg');return;
 }
 if(dry){console.log('Dry-run does not download upstream repositories.');if(!argv.includes('--skip-crg'))console.log(installCrg(project,{agents,dry:true}).join('\n'));return;}
 console.log('Installing original upstream skills...');
 installSkills(project,{agents,sourceDir,pins});
 if(!argv.includes('--skip-crg')){
  console.log('Installing Code Review Graph (CRG) MCP + skills...');
  for(const line of installCrg(project,{agents}))console.log(line);
 } else console.log('SKIPPED CRG (--skip-crg)');
 console.log('INIT COMPLETE '+project);
 console.log('Run `opencode`, `codex`, or `claude` inside the project after checking the installation.');
}
module.exports={init};
