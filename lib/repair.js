'use strict';
const fs=require('node:fs');const path=require('node:path');const {spawnSync}=require('node:child_process');
const oldStatus='`ai-dev status`';
function repairSession(project,{dry=false}={}){
 const instructions=path.join(project,'AGENTS.md');
 if(!fs.existsSync(instructions))throw Error('AGENTS.md not found: '+instructions);
 const current=fs.readFileSync(instructions,'utf8');
 const substitutions=[
  ['`ai-dev status`','`node .ai-dev/session-status.cjs`'],
  ['`ai-dev work new','`python3 scripts/workflow.py new'],
  ['`ai-dev work approve','`python3 scripts/workflow.py approve'],
  ['`ai-dev work gate','`python3 scripts/workflow.py gate']
 ];
 let next=current;for(const [from,to] of substitutions)next=next.split(from).join(to);
 const status=path.join(project,'.ai-dev','session-status.cjs');
 if(!fs.existsSync(status))throw Error('Local session status script is missing; initialize project first: '+status);
 const check=spawnSync(process.execPath,[status],{cwd:project,encoding:'utf8',timeout:15000});
 if(check.status!==0)throw Error('Local session status failed: '+(check.stderr||check.error?.message||'unknown'));
 if(next===current)return 'UNCHANGED AGENTS.md; local session check PASS';
 if(dry)return 'WOULD_REPAIR AGENTS.md; local session check PASS';
 const backup=path.join(project,'AGENTS.md.pre-ai-dev-0.8.2.bak');
 if(fs.existsSync(backup))throw Error('Backup already exists, inspect before retrying: '+backup);
 fs.copyFileSync(instructions,backup,fs.constants.COPYFILE_EXCL);
 fs.writeFileSync(instructions,next);
 return 'REPAIRED AGENTS.md (backup: '+backup+'); local session check PASS';
}
module.exports={repairSession};
