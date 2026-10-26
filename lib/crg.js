'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {spawnSync}=require('node:child_process');

// CRG is a Python program + MCP server, not a SKILL.md-only plugin.
// Install into a project-local virtualenv. Do not change the global Python environment.
function installCrg(project,{agents='all',dry=false,run=spawnSync}={}){
 const selected=agents==='all'?['opencode','codex','claude']:agents.split(',');
 for(const a of selected)if(!['opencode','codex','claude'].includes(a))throw Error('Unknown CRG agent: '+a);
 const envdir=path.join(project,'.ai-dev','crg-venv');
 const python=process.platform==='win32'?path.join(envdir,'Scripts','python.exe'):path.join(envdir,'bin','python');
 const cli=process.platform==='win32'?path.join(envdir,'Scripts','code-review-graph.exe'):path.join(envdir,'bin','code-review-graph');
 const commands=[];
 if(!fs.existsSync(python))commands.push(['python3',['-m','venv',envdir]]);
 commands.push([python,['-m','pip','install','code-review-graph']]);
 // CRG owns its native MCP/skill configuration. Avoid overwriting framework AGENTS and SessionStart hooks.
 for(const a of selected)commands.push([cli,['install','--platform',a==='claude'?'claude-code':a,'--no-hooks','--no-instructions']]);
 // Empty projects may not have code to index; build lazily at first analysis, not during init.
 if(dry)return commands.map(([cmd,args])=>`WOULD RUN ${[cmd,...args].join(' ')}`);
 for(const [cmd,args] of commands){
  const result=run(cmd,args,{cwd:project,stdio:'inherit'});
  if(result.error||result.status!==0)throw Error(`CRG installation failed: ${cmd} ${args.join(' ')} (exit ${result.status??'unknown'}${result.error?'; '+result.error.message:''}). To retry run: npx @gon1942/ai-dev-external-framework install-crg --project ${JSON.stringify(project)} --agents ${agents}`);
 }
 const metadata={tool:'code-review-graph',installed_at:new Date().toISOString(),agents:selected,python,cli,build_required:true};
 fs.mkdirSync(path.join(project,'.ai-dev'),{recursive:true});
 fs.writeFileSync(path.join(project,'.ai-dev','crg-install.json'),JSON.stringify(metadata,null,2)+'\n');
 return ['CRG MCP and skills installed for '+selected.join(', '),'CRG graph build: run '+JSON.stringify(cli)+' build after project source is present'];
}
module.exports={installCrg};
