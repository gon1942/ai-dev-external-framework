"use strict";
const fs=require('node:fs');const path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
function upgrade(project,{dry=false}={}){
 const changes=[];
 for(const rel of ['docs/ai-workflow/PROJECT-RULES.md','docs/ai-workflow/ENVIRONMENT.md']){
  const source=fs.readFileSync(path.join(ROOT,'templates',rel));const target=path.join(project,rel);
  if(fs.existsSync(target)){changes.push('PRESERVED '+rel);continue;}
  changes.push((dry?'WOULD_CREATE ':'CREATED ')+rel);
  if(!dry){fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,source);}
 }
 const dest=path.join(project,'AGENTS.md');const wanted=fs.readFileSync(path.join(ROOT,'templates','AGENTS.md'));
 if(!fs.existsSync(dest)){
  changes.push((dry?'WOULD_CREATE ':'CREATED ')+'AGENTS.md');if(!dry)fs.writeFileSync(dest,wanted);
 }else if(fs.readFileSync(dest).equals(wanted))changes.push('UNCHANGED AGENTS.md');
 else{
  // Do not overwrite unknown project modifications or legacy managed blocks.
  const proposal=dest+'.ai-dev-v1.0.4-proposed';
  if(fs.existsSync(proposal)&&!fs.readFileSync(proposal).equals(wanted))throw Error('Existing proposal conflict: '+proposal);
  changes.push((dry?'WOULD_PROPOSE ':'PROPOSED ')+'AGENTS.md.ai-dev-v1.0.4-proposed (original preserved)');
  if(!dry)fs.writeFileSync(proposal,wanted);
 }
 return changes;
}
module.exports={upgrade};
