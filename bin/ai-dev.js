#!/usr/bin/env node
'use strict';
const path=require('node:path');const {spawnSync}=require('node:child_process');const fs=require('node:fs');const {setup,installSkills}=require('../lib/install');
const {init}=require('../lib/init');const {inspect,repair}=require('../lib/deps');const {installCrg}=require('../lib/crg');const {install:installPlaywright}=require('../lib/playwright');const {repairSession,upgradeSessionReport}=require('../lib/repair');const {sessionStatus,formatStatus}=require('../lib/status');
const {manage,sync,stage,validate,load,DEFAULT,STAGES}=require('../lib/skill-manager');
const {upgrade:upgradeReporting}=require('../lib/upgrade-reporting');
const {upgrade:upgradeGuides}=require('../lib/upgrade-guides');
const [command,...argv]=process.argv.slice(2);const get=(k,d)=>{const i=argv.indexOf(k);return i<0?d:argv[i+1]};const has=(k)=>argv.includes(k);const project=path.resolve(get('--project',process.cwd()));
try{
 if(!command||['help','--help'].includes(command)){console.log(`ai-dev v1.0.4\n  init <PATH> [--agents all|opencode|codex|claude] [--dry-run] [--source-dir PATH] [--pins FILE] [--skip-crg] [--skip-playwright]\n  check-deps [--project PATH] [--agents all|...] [--json]\n  repair-deps [--project PATH] [--agents all|...] [--dry-run] [--source-dir PATH] [--pins FILE] [--skip-crg] [--skip-playwright]\n  install-playwright [--project PATH] [--agents all|opencode|codex|claude] [--dry-run]
  install-crg [--project PATH] [--agents all|opencode|codex|claude] [--dry-run]\n  upgrade-guides [--project PATH] [--dry-run] (add project docs; propose safe AGENTS.md replacement)\n  upgrade-reporting [--project PATH] [--dry-run] (safe managed reporting guidance update)\n  setup [--project PATH] [--agents all|opencode|codex|claude] [--dry-run]\n  install-skills [--project PATH] [--agents all|...] [--source-dir PATH] [--dry-run] [--update] [--pins FILE]\n  status [--project PATH] [--json]\n  repair-session [--project PATH] [--dry-run]\n  upgrade-session-report [--project PATH] [--dry-run]\n  skill manage [--policy PATH] (interactive manager)\n  skill dashboard [--policy PATH] (all stages overview)
  skill list | validate | add <id> <git-url> <sha> [skills/path] | disable|enable <id>
  skill stage list|add|remove|replace|mode <stage> [skill] [value]
  skill sync [--project PATH] [--install-custom] [--dry-run]
  skill show-stage <stage> [--project PATH]
  work <workflow.py arguments>\n  doctor [--project PATH]\n\nNote: setup installs native hooks + docs; install-skills fetches unmodified upstream skills separately.`);process.exit(0)}
 if(command==='init'){init(argv);process.exit(0)}
 if(command==='skill'){
  const [op,...rest]=argv;
  if(op==='manage'){require('../lib/skill-tui').run({file:get('--policy',DEFAULT)}).catch(e=>{console.error('ERROR:',e.message);process.exitCode=2});}
  else if(op==='dashboard'){require('../lib/skill-tui').render(load(get('--policy',DEFAULT)));}
  else if(op==='sync'){if(!fs.existsSync(project))throw Error('Project not found');console.log(sync(project,{dry:has('--dry-run'),allowGit:has('--install-custom'),agents:get('--agents','all')}).join('\n'))}
  else if(op==='show-stage')console.log(JSON.stringify(stage(project,rest[0]),null,2));
  else if(op==='validate'){validate(load(get('--policy',DEFAULT)));console.log('SKILL_POLICY_VALID')}
  else if(op==='stage'){const [action,...params]=rest;console.log(manage({file:get('--policy',DEFAULT),action:'stage-'+action,args:params.filter(x=>!x.startsWith('--'))}))}
  else console.log(manage({file:get('--policy',DEFAULT),action:op,args:rest.filter(x=>!x.startsWith('--'))}));
  if(op!=='manage')process.exit(0);
  else process.exitCode=0;
 }
 if(command!=='skill'&&(!fs.existsSync(project)||!fs.statSync(project).isDirectory()))throw Error('Project directory must exist: '+project);
 if(command==='check-deps'){const result=inspect(project,{agents:get('--agents','all')});console.log(JSON.stringify(result,null,2));if(!result.healthy)process.exitCode=1;}
 else if(command==='repair-deps'){const result=repair(project,{agents:get('--agents','all'),sourceDir:get('--source-dir',undefined),pins:get('--pins',undefined),dry:has('--dry-run'),skipCrg:has('--skip-crg'),skipPlaywright:has('--skip-playwright')});for(const a of result.actions)console.log(a);console.log('Dependency check:',JSON.stringify(result.after));}
 else if(command==='upgrade-guides'){for(const a of upgradeGuides(project,{dry:has('--dry-run')}))console.log(a);}
 else if(command==='upgrade-reporting'){for(const a of upgradeReporting(project,{dry:has('--dry-run')}))console.log(a);}
 else if(command==='setup'){for(const action of setup(project,{dry:has('--dry-run'),agents:get('--agents','all')}))console.log(action);console.log('Native hooks may need host trust approval; see README.');}
 else if(command==='install-playwright'){for(const line of installPlaywright(project,{agents:get('--agents','all'),dry:has('--dry-run')}))console.log(line);}
 else if(command==='install-crg'){for(const line of installCrg(project,{agents:get('--agents','all'),dry:has('--dry-run')}))console.log(line);}
 else if(command==='install-skills')installSkills(project,{agents:get('--agents','all'),sourceDir:get('--source-dir',undefined),dry:has('--dry-run'),update:has('--update'),pins:get('--pins',undefined)});
 else if(command==='repair-session'){console.log(repairSession(project,{dry:has('--dry-run')}));}
 else if(command==='upgrade-session-report'){console.log(upgradeSessionReport(project,{dry:has('--dry-run')}));}
 else if(command==='status'){const s=sessionStatus(project);console.log(has('--json')?JSON.stringify(s,null,2):formatStatus(s));}
 else if(command==='doctor'){
  const paths=['AGENTS.md','scripts/workflow.py','.ai-dev/session-status.cjs','.claude/settings.json','.codex/hooks.json','.opencode/plugins/ai-dev-session.js'];let fail=0;
  for(const p of paths){const good=fs.existsSync(path.join(project,p));console.log((good?'PASS ':'MISSING ')+p);if(!good)fail++}
  for(const [name,dir] of Object.entries({codex:'.agents/skills',opencode:'.opencode/skills',claude:'.claude/skills'})){const full=path.join(project,dir);console.log((fs.existsSync(full)?'FOUND ':'NOT INSTALLED ')+`${name} upstream skills`)}
  const crg=path.join(project,'.ai-dev','crg-install.json');console.log((fs.existsSync(crg)?'PASS ':'MISSING ')+'CRG installation record');if(!fs.existsSync(crg))fail++;
  if(fail)process.exitCode=1;
 }
 else if(command==='work'){const rest=argv.filter((_,i)=>!(argv[i-1]==='--project'||argv[i]==='--project'));const r=spawnSync('python3',[path.join(project,'scripts','workflow.py'),...rest],{stdio:'inherit',cwd:project});process.exitCode=r.status??2;}
 else if(command!=='skill')throw Error('Unknown command: '+command);
}catch(e){console.error('ERROR:',e.message);process.exitCode=2}
