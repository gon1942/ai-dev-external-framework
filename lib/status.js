'use strict';
const fs=require('node:fs'); const path=require('node:path');
function sessionStatus(root){
 const base=path.join(root,'docs','exec-plans','active');let items=[],warnings=[];
 if(fs.existsSync(base))for(const ent of fs.readdirSync(base,{withFileTypes:true}).filter(x=>x.isDirectory()).sort((a,b)=>a.name.localeCompare(b.name))){
  const file=path.join(base,ent.name,'status.json');if(!fs.existsSync(file))continue;
  try {const s=JSON.parse(fs.readFileSync(file,'utf8')); const hasPlan=['spec.md','plan.md','ac-tests.json'].every(x=>fs.existsSync(path.join(base,ent.name,x)));let phase='PLAN_DRAFT';
   if(s.approved===true||Boolean(s.approved_by)){phase=s.review?.verdict==='PASS'?'REVERIFY_OR_COMPLETION_CHECK':'IMPLEMENT_OR_VERIFY';}
   else if(hasPlan){const ac=JSON.parse(fs.readFileSync(path.join(base,ent.name,'ac-tests.json'),'utf8'));if(Object.keys(ac).length)phase='PLAN_APPROVAL_REQUIRED';}
   items.push({id:ent.name,title:s.title||'',phase,path:`docs/exec-plans/active/${ent.name}`});
  }catch(e){warnings.push(`${ent.name}: ${e.message}`)}
 }
 return {project:root,active_count:items.length,tasks:items,warnings};
}
function formatStatus(s){const lines=['=== AI WORK SESSION STATUS ===',`Project: ${s.project}`,`Active tasks: ${s.active_count}`]; if(!s.tasks.length)lines.push('No active tasks. Do not auto-create work at session start.');for(const t of s.tasks)lines.push(`${t.id} | ${t.phase} | ${t.title}\n  ${t.path}`);for(const w of s.warnings)lines.push(`WARNING: ${w}`);lines.push('Read existing task files before starting new work. Show this summary to the user.');return lines.join('\n');}
module.exports={sessionStatus,formatStatus};
