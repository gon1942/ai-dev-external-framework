'use strict';
// upgrade — 3-way merge of framework-managed files for existing projects.
// 순정(=과거 템플릿과 동일)이면 자동 교체, 사용자 수정이 있으면 git merge-file로 병합,
// base를 못 찾으면 제안본만 생성한다. 항상 백업 후 작업하며 dry-run을 지원한다.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const ROOT=path.join(__dirname,'..');
const MANAGED=[
 {tpl:'AGENTS.md',dest:'AGENTS.md',hist:'AGENTS'},
 {tpl:'docs/PLANS.md',dest:'docs/PLANS.md',hist:'PLANS'},
 {tpl:'.ai-dev/dependency-check.cjs',dest:'.ai-dev/dependency-check.cjs',hist:'dependency-check'},
];
function historyBases(hist,{historyDir}={}){
 const dir=historyDir||path.join(ROOT,'templates-history');
 if(!fs.existsSync(dir))return [];
 return fs.readdirSync(dir).filter(f=>f.startsWith(hist+'-v')).sort().map(f=>fs.readFileSync(path.join(dir,f)));
}
function mergeContents(ours,base,theirs){
 const os=require('node:os');
 const d=fs.mkdtempSync(path.join(os.tmpdir(),'ai-upgrade-'));
 const o=path.join(d,'ours'),b=path.join(d,'base'),t=path.join(d,'theirs');
 fs.writeFileSync(o,ours);fs.writeFileSync(b,base);fs.writeFileSync(t,theirs);
 try{
  const r=cp.spawnSync('git',['merge-file','-p','--diff3','-L','current(사용자)','-L','base(설치당시)','-L','new(최신템플릿)',o,b,t],{encoding:'utf8',maxBuffer:32*1024*1024});
  if(r.error)throw r.error;
  if((r.status||0)===0)return {content:Buffer.from(r.stdout,'utf8'),conflicts:0};
  const resolved=autoResolveAddAdd(r.stdout);
  return resolved;
 }finally{fs.rmSync(d,{recursive:true,force:true})}
}
// add/add 충돌(base 양쪽 모두 비어 있고 서로 다른 내용을 추가한 경우)은 양쪽 모두 보존해 자동 해결한다.
// 같은 줄을 서로 다르게 수정한 충돌만 마커로 남긴다.
function autoResolveAddAdd(text){
 const out=[];let conflicts=0,state=0,ours=[],base=[],theirs=[];
 const flush=()=>{
  if(base.length===0&&(ours.length||theirs.length)){
   out.push(...ours);if(ours.length&&theirs.length)out.push('');out.push(...theirs);
  }else{conflicts++;out.push('<<<<<<< current(사용자)',...ours,'||||||| base(설치당시)',...base,'=======',...theirs,'>>>>>>> new(최신템플릿)')}
 };
 for(const ln of text.split('\n')){
  if(ln.startsWith('<<<<<<< ')){state=1;ours=[];base=[];theirs=[];continue}
  if(ln==='||||||| base(설치당시)'){state=2;continue}
  if(ln==='======='){state=3;continue}
  if(ln.startsWith('>>>>>>> ')){flush();state=0;continue}
  if(state===1)ours.push(ln);else if(state===2)base.push(ln);else if(state===3)theirs.push(ln);else out.push(ln);
 }
 return {content:Buffer.from(out.join('\n'),'utf8'),conflicts};
}
// Managed-file upgrade only. Skills/tool refresh is orchestrated by the CLI (bin).
function upgradeFiles(project,{dry=false,templatesDir,historyDir}={}){
 const tDir=templatesDir||path.join(ROOT,'templates');
 const actions=[];
 for(const item of MANAGED){
  const dest=path.join(project,item.dest),tpl=fs.readFileSync(path.join(tDir,item.tpl));
  if(!fs.existsSync(dest)){
   actions.push(`${dry?'WOULD CREATE':'CREATED'} ${item.dest}`);
   if(!dry){fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,tpl)}
   continue;
  }
  const ours=fs.readFileSync(dest);
  if(ours.equals(tpl)){actions.push(`UNCHANGED ${item.dest}`);continue}
  const bases=historyBases(item.hist,{historyDir});
  if(bases.length===0){
   const prop=dest+'.ai-dev-upgrade-proposed';
   actions.push(`${dry?'WOULD PROPOSE':'PROPOSED'} ${item.dest} -> ${item.dest}.ai-dev-upgrade-proposed (base 미발견 — 수동 병합)`);
   if(!dry)fs.writeFileSync(prop,tpl);
   continue;
  }
  if(dry){actions.push(`WOULD MERGE ${item.dest} (사용자 수정 있음 — 병합 결과는 실행 시 확인)`);continue}
  // base 탐지: 사용자 수정본은 템플릿과 바이트 일치하지 않으므로, 후보 base로 병합을 시도해
  // 충돌 0(가장 최신)을 정확한 base로 본다. 모두 충돌하면 충돌 가장 적은 base로 마커를 남긴다.
  const pristine=bases.find(b=>b.equals(ours));
  // 유사성 게이트: 현재 파일과 공통 라인이 30% 미만인 base는 계보가 다르다고 보고 병합하지 않는다.
  const oursLines=new Set(ours.toString('utf8').split('\n'));
  const plausible=bases.filter(b=>{const bl=new Set(b.toString('utf8').split('\n'));let common=0;for(const l of oursLines)if(l&&bl.has(l))common++;const nz=[...oursLines].filter(x=>x).length;return nz>0&&common/nz>=0.3});
  const candidates=(pristine?[pristine]:[...plausible].reverse());
  if(candidates.length===0){
   const prop=dest+'.ai-dev-upgrade-proposed';
   actions.push(`${dry?'WOULD PROPOSE':'PROPOSED'} ${item.dest} -> ${item.dest}.ai-dev-upgrade-proposed (base 미발견 — 수동 병합)`);
   if(!dry)fs.writeFileSync(prop,tpl);
   continue;
  }
  let chosen=null;
  for(const base of candidates){const m=mergeContents(ours,base,tpl);if(m.conflicts===0){chosen={base,merged:m};break}if(!chosen||m.conflicts<chosen.merged.conflicts)chosen={base,merged:m}}
  if(chosen.merged.conflicts>=3){
   const prop=dest+'.ai-dev-upgrade-proposed';
   actions.push(`PROPOSED ${item.dest} -> ${item.dest}.ai-dev-upgrade-proposed (기존 내용과 차이가 커서 자동 병합 생략 — 수동 병합)`);
   fs.writeFileSync(prop,tpl);
   continue;
  }
  fs.copyFileSync(dest,dest+'.bak-upgrade');
  fs.writeFileSync(dest,chosen.merged.content);
  if(chosen.merged.conflicts>0)actions.push(`CONFLICT ${item.dest} — ${chosen.merged.conflicts}곳 충돌 마커(<<<<<<<) 확인 필요 (원본 백업: .bak-upgrade)`);
  else actions.push(`MERGED ${item.dest} — 사용자 수정 보존 + 최신 템플릿 반영 (백업: .bak-upgrade)`);
 }
 return actions;
}
module.exports={upgradeFiles,MANAGED,historyBases};
