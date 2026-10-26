'use strict';
const readline=require('node:readline/promises');
const {stdin:input,stdout:output}=require('node:process');
const {load,manage,validate,STAGES,DEFAULT}=require('./skill-manager');
const MODES=['required','recommended','optional','conditional'];
const LABELS={analyze:'분석',plan:'계획',implement:'구현',verify:'검증',review:'리뷰',complete:'완료'};
function render(p){
 console.log(`\n=== AI Dev Skill Manager | 정책 ${p.policyVersion} | 등록 ${Object.keys(p.skills).length}개 ===`);
 for(const st of STAGES){
  console.log(`\n[${st.toUpperCase()} / ${LABELS[st]}] ${p.stages[st].length}개`);
  p.stages[st].forEach((a,i)=>console.log(`  ${String(i+1).padStart(2)}. ${a.id} [${a.mode}] ${p.skills[a.id].enabled?'✓':'비활성'} (${p.skills[a.id].kind})`));
 }
}
async function run({file=DEFAULT}={}){
 if(!input.isTTY)throw Error('대화형 관리는 터미널(TTY)에서 실행해야 합니다. 에이전트는 ai-dev skill 명령을 사용하세요.');
 const rl=readline.createInterface({input,output});
 const ask=async prompt=>(await rl.question(prompt)).trim();
 const choose=async(label,choices)=>{choices.forEach((v,i)=>console.log(` ${i+1}. ${v}`));const a=await ask(`${label} [번호, 0 취소] > `);if(a==='0'||!a)return null;const n=Number(a);if(!Number.isInteger(n)||n<1||n>choices.length)throw Error('올바른 번호를 선택하세요');return choices[n-1];};
 const apply=async(action,args)=>{
  console.log(`\n변경 미리 보기: ${action} ${args.join(' ')}`);
  console.log('중앙 정책만 변경합니다. 설치 파일 삭제 및 npm 배포는 수행하지 않습니다.');
  if((await ask('이 변경을 승인합니까? [yes] > ')).toLowerCase()!=='yes'){console.log('변경 취소');return}
  console.log('적용:',manage({file,action,args}));validate(load(file));console.log('검증 PASS | 이전 정책 백업:',file+'.bak');
 };
 try{
  for(;;){
   const p=load(file);render(p);
   const top=await choose('작업 선택',['단계별 스킬 구성 변경','새 외부 Git 스킬 등록','스킬 전체 활성화/비활성화','정책 검증','종료']);
   if(!top||top==='종료')break;
   try{
    if(top==='정책 검증'){validate(p);console.log('정책 구조 검증 PASS');continue}
    if(top==='새 외부 Git 스킬 등록'){
     const id=await ask('스킬 ID: '),url=await ask('원본 저장소 HTTPS .git URL: '),sha=await ask('고정 commit SHA (40자리): '),path=await ask('원본 skills/ 경로 (비우면 기본값): ');
     await apply('add',[id,url,sha,...(path?[path]:[])]);continue;
    }
    if(top==='스킬 전체 활성화/비활성화'){
     const id=await choose('스킬 선택',Object.keys(p.skills));if(id)await apply(p.skills[id].enabled?'disable':'enable',[id]);continue;
    }
    const selected=await choose('개발 단계 선택',STAGES.map(s=>`${s} (${LABELS[s]})`));if(!selected)continue;
    const st=selected.split(' ')[0],items=p.stages[st];
    console.log(`\n선택한 단계: ${st}`);
    for(const item of items)console.log(` - ${item.id} (${item.mode})`);
    const op=await choose('단계 관리',['스킬 추가','스킬 제외','스킬 교체','사용 정책 변경','돌아가기']);
    if(!op||op==='돌아가기')continue;
    if(op==='스킬 추가'){
     const ids=Object.keys(p.skills).filter(id=>p.skills[id].enabled&&!items.some(x=>x.id===id));if(!ids.length){console.log('추가 가능한 스킬 없음');continue}
     const id=await choose('추가할 스킬',ids);if(!id)continue;
     const mode=await choose('사용 정책',MODES);if(mode)await apply('stage-add',[st,id,mode]);
    }else{
     if(!items.length){console.log('이 단계의 스킬이 없습니다');continue}
     const id=await choose('대상 스킬',items.map(x=>x.id));if(!id)continue;
     if(op==='스킬 제외')await apply('stage-remove',[st,id]);
     else if(op==='스킬 교체'){
      const ids=Object.keys(p.skills).filter(x=>p.skills[x].enabled&&!items.some(y=>y.id===x));if(!ids.length){console.log('교체 가능한 스킬 없음');continue}
      const next=await choose('대체 스킬',ids);if(next)await apply('stage-replace',[st,id,next]);
     }else if(op==='사용 정책 변경'){
      const mode=await choose('변경할 정책',MODES);if(mode)await apply('stage-mode',[st,id,mode]);
     }
    }
   }catch(e){console.log('오류:',e.message)}
  }
 }finally{rl.close()}
}
module.exports={run,render};
