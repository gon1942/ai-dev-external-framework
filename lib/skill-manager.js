'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const BASE=path.resolve(__dirname,'..'),DEFAULT=path.join(BASE,'skill-policy.json');
const STAGES=['analyze','plan','implement','verify','review','complete'];
const AGENTS={opencode:'.opencode/skills',codex:'.agents/skills',claude:'.claude/skills'};
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
function load(file=DEFAULT){const obj=JSON.parse(fs.readFileSync(file,'utf8'));validate(obj);return obj;}
function validate(p){if(p.schemaVersion!==1||!p.skills||!p.stages)throw Error('Invalid skill policy schema');for(const [id,s] of Object.entries(p.skills)){if(!/^[a-z][a-z0-9-]*$/.test(id))throw Error('Invalid skill id: '+id);if(!['upstream','crg','git','playwright'].includes(s.kind))throw Error('Invalid kind: '+id);if(s.kind==='git'&&(!/^https:\/\/[^\s]+\.git$/.test(s.url)||!/^[a-f0-9]{40}$/i.test(s.ref||'')||!/^skills\/[a-z0-9/_-]+$/i.test(s.directory||'')))throw Error('Git skill requires https .git URL, 40-char commit SHA and skills/ path: '+id)}for(const [stage,items] of Object.entries(p.stages)){if(!STAGES.includes(stage)||!Array.isArray(items))throw Error('Invalid stage '+stage);const seen=new Set();for(const item of items){if(!p.skills[item.id]||seen.has(item.id)||!['required','recommended','optional','conditional'].includes(item.mode))throw Error('Invalid assignment '+stage+'/'+item.id);seen.add(item.id)}}return true}
function writeAtomic(file,obj){validate(obj);fs.mkdirSync(path.dirname(file),{recursive:true});const tmp=file+'.tmp-'+process.pid;fs.writeFileSync(tmp,JSON.stringify(obj,null,2)+'\n');fs.renameSync(tmp,file)}
function manage({file=DEFAULT,action,args=[]}){const p=load(file);const [a,b,c]=args;let msg='';
 if(action==='list')return JSON.stringify(p,null,2);
 if(action==='add'){if(!/^[a-z][a-z0-9-]*$/.test(a)||p.skills[a])throw Error('Invalid or existing skill ID');if(!/^https:\/\/[^\s]+\.git$/.test(b||'')||!/^[a-f0-9]{40}$/i.test(c||''))throw Error('Use skill add <id> <https-git-url.git> <40-char-sha> [skills/subdir]');const directory=args[3]||'skills/'+a;p.skills[a]={kind:'git',url:b,ref:c,directory,enabled:true};msg='Registered '+a}
 else if(action==='disable'||action==='enable'){if(!p.skills[a])throw Error('Unknown skill '+a);p.skills[a].enabled=action==='enable';msg=action+' '+a}
 else if(action==='stage-list'){if(!STAGES.includes(a))throw Error('Unknown stage '+a);return JSON.stringify(p.stages[a],null,2)}
 else if(action==='stage-add'){if(!STAGES.includes(a)||!p.skills[b])throw Error('Unknown stage or skill');if(p.stages[a].some(x=>x.id===b))throw Error('Already assigned');p.stages[a].push({id:b,mode:c||'recommended'});msg='Assigned '+b+' to '+a}
 else if(action==='stage-remove'){if(!STAGES.includes(a))throw Error('Unknown stage');if(!p.stages[a].some(x=>x.id===b))throw Error('Skill not assigned');p.stages[a]=p.stages[a].filter(x=>x.id!==b);msg='Unassigned '+b+' from '+a}
 else if(action==='stage-replace'){if(!STAGES.includes(a)||!p.skills[c])throw Error('Unknown stage or replacement');const at=p.stages[a].findIndex(x=>x.id===b);if(at<0||p.stages[a].some(x=>x.id===c))throw Error('Invalid replacement');p.stages[a][at]={...p.stages[a][at],id:c};msg='Replaced '+b+' with '+c+' in '+a}
 else if(action==='stage-mode'){if(!STAGES.includes(a))throw Error('Unknown stage');const item=p.stages[a].find(x=>x.id===b);if(!item)throw Error('Skill not assigned');item.mode=c;msg='Updated mode '+b}
 else throw Error('Unknown skill action '+action);
 const backup=file+'.bak';fs.copyFileSync(file,backup);writeAtomic(file,p);return msg;
}
function sync(project,{policyFile=DEFAULT,dry=false,allowGit=false,agents='all'}={}){
 const p=load(policyFile),selected=agents==='all'?Object.keys(AGENTS):agents.split(',');for(const a of selected)if(!AGENTS[a])throw Error('Unknown agent '+a);
 const dest=path.join(project,'.ai-dev','stage-skills.json');const lock=path.join(project,'.ai-dev','skill-policy-lock.json');
 const bytes=fs.readFileSync(policyFile),digest=hash(bytes);const old=fs.existsSync(lock)?JSON.parse(fs.readFileSync(lock,'utf8')):null;
 if(fs.existsSync(dest)&&old&&old.installedHash!==hash(fs.readFileSync(dest)))throw Error('Local stage policy changed outside sync; refusing overwrite: '+dest);
 const data=JSON.stringify(p,null,2)+'\n';const current=fs.existsSync(dest)?fs.readFileSync(dest,'utf8'):null;
 const changes=[],needed=new Set(Object.values(p.stages).flat().filter(x=>p.skills[x.id].enabled).map(x=>x.id));
 for(const id of needed){const s=p.skills[id];if(s.kind!=='git')continue;for(const a of selected){const folder=path.join(project,AGENTS[a],id);if(fs.existsSync(path.join(folder,'SKILL.md')))continue;changes.push('INSTALL '+a+':'+id);if(!dry){if(!allowGit)throw Error('Custom git skill requires --install-custom: '+id);installGit(s,folder)}}}
 if(current!==data){changes.push('SYNC policy '+p.policyVersion);if(!dry){fs.mkdirSync(path.dirname(dest),{recursive:true});if(current!==null)fs.copyFileSync(dest,dest+'.bak');fs.writeFileSync(dest,data)}}
 if(!dry){fs.writeFileSync(lock,JSON.stringify({schemaVersion:1,policyVersion:p.policyVersion,sourceHash:digest,installedHash:hash(Buffer.from(data)),syncedAt:new Date().toISOString()},null,2)+'\n')}
 return changes.length?changes:['UNCHANGED policy '+p.policyVersion];
}
function installGit(s,dest){const os=require('node:os');const temp=fs.mkdtempSync(path.join(os.tmpdir(),'ai-skill-'));try{const repo=path.join(temp,'repo');let r=cp.spawnSync('git',['clone',s.url,repo],{encoding:'utf8'});if(r.status!==0)throw Error('Git clone failed: '+r.stderr);r=cp.spawnSync('git',['-C',repo,'checkout','--detach',s.ref],{encoding:'utf8'});if(r.status!==0)throw Error('Git checkout failed: '+r.stderr);const source=path.resolve(repo,s.directory);if(!source.startsWith(repo+path.sep)||!fs.existsSync(path.join(source,'SKILL.md')))throw Error('Missing original SKILL.md: '+s.directory);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.cpSync(source,dest,{recursive:true,errorOnExist:true,force:false})}finally{fs.rmSync(temp,{recursive:true,force:true})}}
function stage(project,stage){if(!STAGES.includes(stage))throw Error('Unknown stage');const file=path.join(project,'.ai-dev','stage-skills.json');const p=load(fs.existsSync(file)?file:DEFAULT);return p.stages[stage].map(x=>({...x,enabled:!!p.skills[x.id].enabled,kind:p.skills[x.id].kind}));}
module.exports={load,validate,manage,sync,stage,DEFAULT,STAGES};
