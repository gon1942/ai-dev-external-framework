"use strict";
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const ROOT=path.resolve(__dirname,'..');
const VERSION='1.0.3';
const TAG='AI-DEV-STAGE-REPORTING';
const START=`<!-- ${TAG}:START -->`;
const END=`<!-- ${TAG}:END -->`;
const BLOCK=`${START}\n## AI 개발 단계별 사용자 보고 (프레임워크 관리 영역)\n\n각 개발 단계(Analyze, Plan, Implement, Verify, Review, Complete)가 끝나면 반드시 \`docs/ai-workflow/STAGE-REPORTING.md\`를 읽고, 수행 결과·검증 증거·미완료 작업·담당 주체·완료 조건·사용자 행동·다음 단계 진입 조건을 **사용자 대화에 한국어로** 보고한다. Verify는 AC별 PASS/FAIL/NOT_RUN과 증거, Review는 심각도별 발견 사항·수정·재검증·잔여 위험을 구분한다. 사용자 승인 전에는 구현 또는 완료 처리를 승인된 것으로 기록하지 않는다.\n${END}\n`.replaceAll('\`','`');
function sha(data){return createHash('sha256').update(data).digest('hex')}
function preview(project){
 const report=path.join(project,'docs/ai-workflow/STAGE-REPORTING.md');
 const src=path.join(ROOT,'templates/docs/ai-workflow/STAGE-REPORTING.md');
 const plans=path.join(project,'docs/PLANS.md');
 const agents=path.join(project,'AGENTS.md');
 if(!fs.existsSync(src))throw Error('Packaged reporting contract missing');
 const changes=[];
 const srcData=fs.readFileSync(src);
 if(!fs.existsSync(report))changes.push({kind:'create',target:report,content:srcData,reason:'missing reporting contract'});
 else if(!fs.readFileSync(report).equals(srcData))changes.push({kind:'conflict',target:report,reason:'existing reporting contract differs; will not overwrite'});
 for(const target of [agents,plans]){
  const old=fs.existsSync(target)?fs.readFileSync(target,'utf8'):'';
  if(old.includes(START)||old.includes(END)){
   if(!old.includes(START)||!old.includes(END)) {changes.push({kind:'conflict',target,reason:'incomplete managed markers'});continue;}
   const a=old.indexOf(START),b=old.indexOf(END,a);
   if(b<0||old.indexOf(START,a+1)!==-1||old.indexOf(END,b+END.length)!==-1){changes.push({kind:'conflict',target,reason:'duplicate or damaged managed markers'});continue;}
   const current=old.slice(a,b+END.length);
   const wanted=BLOCK.trimEnd();
   if(current===wanted){changes.push({kind:'unchanged',target});continue;}
   changes.push({kind:'update',target,content:old.slice(0,a)+wanted+old.slice(b+END.length),reason:'update framework-managed section only'});
  }else{
   changes.push({kind:fs.existsSync(target)?'update':'create',target,content:old+(old.endsWith('\n')||!old?'':'\n')+'\n'+BLOCK,reason:'append framework-managed reference'});
  }
 }
 return changes;
}
function upgrade(project,{dry=false}={}){
 const actions=preview(project);
 if(actions.some(x=>x.kind==='conflict'))throw Error(actions.filter(x=>x.kind==='conflict').map(x=>`${path.relative(project,x.target)}: ${x.reason}`).join('; '));
 const result=[];
 for(const c of actions){const rel=path.relative(project,c.target);
  if(c.kind==='unchanged'){result.push('UNCHANGED '+rel);continue}
  if(dry){result.push('WOULD_'+c.kind.toUpperCase()+' '+rel);continue}
  fs.mkdirSync(path.dirname(c.target),{recursive:true});
  if(fs.existsSync(c.target)){
   const backup=`${c.target}.before-ai-dev-stage-report-${VERSION}.bak`;
   if(fs.existsSync(backup)&&!fs.readFileSync(backup).equals(fs.readFileSync(c.target)))throw Error('Backup conflict: '+backup);
   if(!fs.existsSync(backup))fs.copyFileSync(c.target,backup,fs.constants.COPYFILE_EXCL);
  }
  fs.writeFileSync(c.target,c.content);
  result.push(c.kind.toUpperCase()+' '+rel);
 }
 return result;
}
module.exports={upgrade,preview,START,END};
