'use strict';
const fs=require('node:fs');const path=require('node:path');const {spawnSync}=require('node:child_process');
const ROOT=path.resolve(__dirname,'..');
function walk(dir){const out=[];for(const e of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,e.name);if(e.isDirectory())out.push(...walk(p));else out.push(p)}return out;}
function put(file,data,dry,mode='managed'){
 if(fs.existsSync(file)){
  const old=fs.readFileSync(file);if(old.equals(Buffer.isBuffer(data)?data:Buffer.from(data)))return 'UNCHANGED';
  if(mode==='managed')throw Error(`Existing file differs: ${file} (refusing overwrite)`);return 'PRESERVED';
 }
 if(!dry){fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,data)}return dry?'WOULD_CREATE':'CREATED';
}
function mergeHooks(file, entry, dry){let obj={};if(fs.existsSync(file)){obj=JSON.parse(fs.readFileSync(file,'utf8'));if(!obj||Array.isArray(obj)||typeof obj!=='object')throw Error(`Invalid JSON: ${file}`)}
 obj.hooks??={};obj.hooks.SessionStart??=[];const sig=JSON.stringify(entry);if(obj.hooks.SessionStart.some(x=>JSON.stringify(x)===sig))return 'UNCHANGED';obj.hooks.SessionStart.push(entry);
 if(!dry){fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,JSON.stringify(obj,null,2)+'\n')}return dry?'WOULD_MERGE':'MERGED';
}
function setup(project,{dry=false,agents='all'}={}){
 const selected=agents==='all'?['opencode','codex','claude']:agents.split(',');for(const a of selected)if(!['opencode','codex','claude'].includes(a))throw Error(`Unknown agent ${a}`);
 const actions=[];const source=path.join(ROOT,'templates');for(const f of walk(source)){
  const rel=path.relative(source,f);if(rel==='AGENTS.md'&&fs.existsSync(path.join(project,rel))){actions.push(`PRESERVED ${rel} (manually merge the workflow guidance)`);continue}
  const target=path.join(project,rel); actions.push(`${put(target,fs.readFileSync(f),dry,'project')} ${rel}`);
 }
 // Install the command entrypoints into the *target project*, not only the framework source.
 // Project-local management uses the project's synced policy and does not change the central npm package.
 const commandSource=path.join(ROOT,'agent-commands','installed-skill-manager.md');
 for(const [agent,rel] of [['opencode','.opencode/commands/skill-manager.md'],['claude','.claude/commands/skill-manager.md']]){
  if(!selected.includes(agent))continue;
  actions.push(`${put(path.join(project,rel),fs.readFileSync(commandSource),dry,'project')} ${rel}`);
 }
 if(selected.includes('codex')){
  const rel='.codex/prompts/skill-manager.md';
  actions.push(`${put(path.join(project,rel),fs.readFileSync(commandSource),dry,'project')} ${rel}`);
 }
 for(const [from,to] of [['lib/skill-manager.js','.ai-dev/skill-manager-engine.cjs'],['templates/.ai-dev/skill-manager.cjs','.ai-dev/skill-manager.cjs']]){
  actions.push(`${put(path.join(project,to),fs.readFileSync(path.join(ROOT,from)),dry,'project')} ${to}`);
 }
 const py=path.join(ROOT,'scripts','workflow.py');
 // Installed copies are self-contained and never overwritten without explicit user review.
 actions.push(`${put(path.join(project,'scripts','workflow.py'),fs.readFileSync(py),dry)} scripts/workflow.py`);
 const entryScript=path.join(project,'.ai-dev','session-status.cjs');
 // The installed hook imports the exact same status engine used by `ai-dev status`.
 const statusEngine=path.join(project,'.ai-dev','status-engine.cjs');
 actions.push(`${put(statusEngine,fs.readFileSync(path.join(ROOT,'lib','status.js')),dry)} .ai-dev/status-engine.cjs`);
 const portable=`const path=require('node:path');\nconst {spawnSync}=require('node:child_process');\nconst health=spawnSync(process.execPath,[path.join(__dirname,'dependency-check.cjs')],{encoding:'utf8'});\nif(health.stdout)process.stdout.write(health.stdout);\nif(health.stderr)process.stderr.write(health.stderr);\nconst {sessionStatus,formatStatus}=require('./status-engine.cjs');\nprocess.stdout.write(formatStatus(sessionStatus(path.resolve(__dirname,'..')))+'\\n');\n`;
 actions.push(`${put(entryScript,portable,dry)} .ai-dev/session-status.cjs`);
 // hook command cwd is tool-defined; use absolute path resolved at setup, with robust JSON/shell quoting.
 const cmd=`node ${JSON.stringify(entryScript)}`;
 if(selected.includes('claude')){const target=path.join(project,'.claude','settings.json');actions.push(`${mergeHooks(target,{hooks:[{type:'command',command:cmd,timeout:15}]},dry)} .claude/settings.json (SessionStart)`)}
 if(selected.includes('codex')){const target=path.join(project,'.codex','hooks.json');actions.push(`${mergeHooks(target,{hooks:[{type:'command',command:cmd,timeout:15}]},dry)} .codex/hooks.json (SessionStart)`)}
 if(selected.includes('opencode')){
  const target=path.join(project,'.opencode','plugins','ai-dev-session.js');
  const script=`import { execFileSync } from 'node:child_process';\nexport const AiDevSession = async ({client}) => {\n const seen=new Set();\n return {event:async ({event})=>{\n  if(event.type!=='session.created')return;\n  const id=event.properties?.info?.id || event.properties?.sessionID; if(!id||seen.has(id))return;seen.add(id);\n  try{ const status=execFileSync('node',[${JSON.stringify(entryScript)}],{encoding:'utf8',timeout:15000});\n   await client.tui.showToast({body:{title:'AI work status',message:status.slice(0,900),variant:'info',duration:8000}});\n  }catch(e){console.warn('[ai-dev] session status unavailable:',String(e));}\n }};\n};\n`;
  actions.push(`${put(target,script,dry)} .opencode/plugins/ai-dev-session.js`);
 }
 return actions;
}
function installSkills(project,options={}){
 const args=[path.join(ROOT,'scripts','external-install.py'),'--project',project,'--agents',options.agents||'all'];if(options.sourceDir)args.push('--source-dir',options.sourceDir);if(options.dry)args.push('--dry-run');if(options.update)args.push('--update');if(options.pins)args.push('--pins',options.pins);
 const r=spawnSync('python3',args,{stdio:'inherit'});if(r.status!==0)throw Error(`Original upstream skill install failed (exit ${r.status})`);
}
module.exports={setup,installSkills};
