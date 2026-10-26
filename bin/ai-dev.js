#!/usr/bin/env node
'use strict';
const path=require('node:path');const {spawnSync}=require('node:child_process');const fs=require('node:fs');const {setup,installSkills}=require('../lib/install');
const {init}=require('../lib/init');const {repairSession}=require('../lib/repair');const {sessionStatus,formatStatus}=require('../lib/status');
const [command,...argv]=process.argv.slice(2);const get=(k,d)=>{const i=argv.indexOf(k);return i<0?d:argv[i+1]};const has=(k)=>argv.includes(k);const project=path.resolve(get('--project',process.cwd()));
try{
 if(!command||['help','--help'].includes(command)){console.log(`ai-dev v0.8.2\n  init <PATH> [--agents all|opencode|codex|claude] [--dry-run] [--source-dir PATH] [--pins FILE]\n  setup [--project PATH] [--agents all|opencode|codex|claude] [--dry-run]\n  install-skills [--project PATH] [--agents all|...] [--source-dir PATH] [--dry-run] [--update] [--pins FILE]\n  status [--project PATH] [--json]\n  repair-session [--project PATH] [--dry-run]\n  work <workflow.py arguments>\n  doctor [--project PATH]\n\nNote: setup installs native hooks + docs; install-skills fetches unmodified upstream skills separately.`);process.exit(0)}
 if(command==='init'){init(argv);process.exit(0)}
 if(!fs.existsSync(project)||!fs.statSync(project).isDirectory())throw Error('Project directory must exist: '+project);
 if(command==='setup'){for(const action of setup(project,{dry:has('--dry-run'),agents:get('--agents','all')}))console.log(action);console.log('Native hooks may need host trust approval; see README.');}
 else if(command==='install-skills')installSkills(project,{agents:get('--agents','all'),sourceDir:get('--source-dir',undefined),dry:has('--dry-run'),update:has('--update'),pins:get('--pins',undefined)});
 else if(command==='repair-session'){console.log(repairSession(project,{dry:has('--dry-run')}));}
 else if(command==='status'){const s=sessionStatus(project);console.log(has('--json')?JSON.stringify(s,null,2):formatStatus(s));}
 else if(command==='doctor'){
  const paths=['AGENTS.md','scripts/workflow.py','.ai-dev/session-status.cjs','.claude/settings.json','.codex/hooks.json','.opencode/plugins/ai-dev-session.js'];let fail=0;
  for(const p of paths){const good=fs.existsSync(path.join(project,p));console.log((good?'PASS ':'MISSING ')+p);if(!good)fail++}
  for(const [name,dir] of Object.entries({codex:'.agents/skills',opencode:'.opencode/skills',claude:'.claude/skills'})){const full=path.join(project,dir);console.log((fs.existsSync(full)?'FOUND ':'NOT INSTALLED ')+`${name} upstream skills`)}
  if(fail)process.exitCode=1;
 }
 else if(command==='work'){const rest=argv.filter((_,i)=>!(argv[i-1]==='--project'||argv[i]==='--project'));const r=spawnSync('python3',[path.join(project,'scripts','workflow.py'),...rest],{stdio:'inherit',cwd:project});process.exitCode=r.status??2;}
 else throw Error('Unknown command: '+command);
}catch(e){console.error('ERROR:',e.message);process.exitCode=2}
