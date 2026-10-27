// Read-only, project-local session inventory. No network calls or mutation.
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const skills=['grill-with-docs','to-spec','to-tickets','implement','implement-spec','code-review','retro','diagnosing-bugs','brainstorming','writing-plans','test-driven-development','systematic-debugging','verification-before-completion','requesting-code-review','receiving-code-review','using-git-worktrees','subagent-driven-development','ponytail','using-superpowers'];
const agents={opencode:'.opencode/skills',codex:'.agents/skills',claude:'.claude/skills'};
console.log('=== 외부 스킬 설치 현황 (세션 시작) ===');
let missing=0;
for(const [agent,dir] of Object.entries(agents)){
 const installed=[],absent=[];
 for(const name of skills){
  let ok=false;try{ok=Boolean(fs.readFileSync(path.join(root,dir,name,'SKILL.md'),'utf8').trim())}catch{}
  (ok?installed:absent).push(name);
 }
 console.log('['+agent+'] 설치 '+installed.length+'/'+skills.length+' · 미설치 '+absent.length+'/'+skills.length);
 console.log('  설치: '+(installed.join(', ')||'없음'));
 console.log('  미설치: '+(absent.join(', ')||'없음'));
 missing+=absent.length;
}
const exe=path.join(root,'.ai-dev','crg-venv','bin','code-review-graph');
const record=path.join(root,'.ai-dev','crg-install.json');
let crg=false;
try{const data=JSON.parse(fs.readFileSync(record,'utf8'));crg=fs.existsSync(exe)&&['opencode','codex','claude'].every(a=>data.agents?.includes(a))}catch{}
console.log('[CRG] '+(crg?'설치 기록 및 실행 파일 확인됨 (MCP 실연결은 별도 확인 필요)':'미설치 또는 설치 불완전 (CLI/MCP)'));
console.log('[전체] 스킬 '+(skills.length*3-missing)+'/'+(skills.length*3)+' (에이전트별 '+skills.length+'개) · CRG '+(crg?'확인':'미확인'));
if(missing||!crg){
 console.log('[복구] npx --yes @gon1942/ai-dev-external-framework@1.0.1 repair-deps --project . --agents all');
 process.exitCode=1;
}


const pwCli=path.join(root,'.ai-dev','playwright','node_modules','.bin','playwright-cli');
const pwAgents={};for(const [name,dir] of Object.entries(agents)){pwAgents[name]=fs.existsSync(path.join(root,dir,'playwright-cli','SKILL.md'))}
const pwInstalled=fs.existsSync(pwCli)&&Object.values(pwAgents).every(Boolean);
console.log('[Playwright CLI] '+(pwInstalled?'설치 확인 (브라우저 실행은 별도 검증)':'미설치 또는 불완전')+'; agent skill files: '+JSON.stringify(pwAgents));
console.log('[전체] 기본 구성 요소: 외부 원본 19종 + CRG 1종 + Playwright CLI 1종 = 21종');
if(!pwInstalled)process.exitCode=1;
