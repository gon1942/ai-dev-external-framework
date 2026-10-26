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
function upgradeSessionReport(project,{dry=false}={}){
 const checker=path.join(project,'.ai-dev','dependency-check.cjs');
 const status=path.join(project,'.ai-dev','session-status.cjs');
 const instructions=path.join(project,'AGENTS.md');
 for(const file of [checker,status,instructions])if(!fs.existsSync(file))throw Error('Missing installed framework file: '+file);
 const template=fs.readFileSync(path.join(__dirname,'..','templates','.ai-dev','dependency-check.cjs'),'utf8');
 const existing=fs.readFileSync(checker,'utf8');
 const marker='<!-- ai-dev-session-report-v0.8.5 -->';
 const note=`\n${marker}\n## 새 세션 사용자 보고 필수\n새 에이전트 세션이 시작되면 (인사만 한 경우에도) \`node .ai-dev/session-status.cjs\`를 실행한다. 출력된 OpenCode·Codex·Claude Code별 **설치 개수, 설치된 스킬 이름 전체, 미설치된 스킬 이름 전체, CRG 설치 상태, 활성 작업**을 사용자에게 답변 본문으로 표시한다. Hook 알림이나 내부 로그만으로 대체하지 않는다. 누락 항목 복구 후에는 재검사 결과를 표시한다. 실제로 검사하지 않은 항목을 설치되었다고 주장하지 않는다.\n`;
 const current=fs.readFileSync(instructions,'utf8');
 const updated=current.includes(marker)?current:current+note;
 if(existing===template&&current===updated)return 'UNCHANGED session report v0.8.5';
 if(dry)return 'WOULD UPGRADE session report; AGENTS.md changes appended only';
 const backups=[checker,instructions].filter(f=>f===checker?existing!==template:current!==updated).map(f=>[f,f+'.pre-ai-dev-0.8.5.bak']);
 for(const [f,b] of backups)if(fs.existsSync(b))throw Error('Backup already exists: '+b);
 for(const [f,b] of backups)fs.copyFileSync(f,b,fs.constants.COPYFILE_EXCL);
 if(existing!==template)fs.writeFileSync(checker,template);
 if(current!==updated)fs.writeFileSync(instructions,updated);
 const check=spawnSync(process.execPath,[status],{cwd:project,encoding:'utf8',timeout:15000});
 // Non-zero is expected when dependencies are missing. Inventory must still print.
 if(!check.stdout?.includes('외부 스킬 설치 현황'))throw Error('Session report output not detected: '+(check.stderr||check.error?.message||''));
 return 'UPGRADED session report v0.8.5; backups saved; installed/missing inventory available';
}
module.exports={repairSession,upgradeSessionReport};
