'use strict';
const fs=require('node:fs');const path=require('node:path');const cp=require('node:child_process');
const PATHS={opencode:'.opencode/skills',codex:'.agents/skills',claude:'.claude/skills'};
function targets(agents){const a=agents==='all'?Object.keys(PATHS):agents.split(',');if(a.some(x=>!PATHS[x]))throw Error('Unknown agent(s) '+agents);return a}
function inspect(project,{agents='all'}={}){
 const selected=targets(agents),base=path.join(project,'.ai-dev','playwright');
 const cli=path.join(base,'node_modules','.bin','playwright-cli');
 const installed={};for(const agent of selected){const p=path.join(project,PATHS[agent],'playwright-cli','SKILL.md');installed[agent]=fs.existsSync(p)&&!!fs.readFileSync(p,'utf8').trim()}
 return {installed:fs.existsSync(cli)&&Object.values(installed).every(Boolean),cli:fs.existsSync(cli),skills:installed,browserVerified:false};
}
function install(project,{agents='all',dry=false,runner=cp.spawnSync}={}){
 const selected=targets(agents),before=inspect(project,{agents});if(before.installed)return ['PLAYWRIGHT ALREADY INSTALLED'];
 const base=path.join(project,'.ai-dev','playwright'),exe=path.join(base,'node_modules','.bin','playwright-cli');
 const actions=[];const run=(cmd,args,cwd)=>{actions.push([cmd,...args].join(' '));if(dry)return;const r=runner(cmd,args,{cwd,encoding:'utf8',timeout:240000});if(r.error||r.status!==0)throw Error('Playwright installation failed: '+[cmd,...args].join(' ')+'\n'+(r.stderr||r.error?.message||''))};
 if(!before.cli){if(!dry){fs.mkdirSync(base,{recursive:true});if(!fs.existsSync(path.join(base,'package.json')))fs.writeFileSync(path.join(base,'package.json'),JSON.stringify({name:'ai-dev-playwright-runtime',private:true,version:'1.0.0'},null,2)+'\n')}
 run('npm',['install','--no-audit','--no-fund','--save-exact','@playwright/cli@latest'],base)}
 // Installer writes its official skills into .agents and .claude. Preserve existing directories.
 const official=selected.includes('opencode')?['codex',...selected.filter(x=>x!=='opencode')]:selected;
 const needAgents=official.includes('codex')&&!before.skills.codex;
 const needClaude=official.includes('claude')&&!before.skills.claude;
 if(needAgents)run(exe,['install','--skills=agents'],project);
 if(needClaude)run(exe,['install','--skills=claude'],project);
 if(selected.includes('opencode')&&!before.skills.opencode){
  actions.push('COPY official playwright-cli skill to .opencode/skills/playwright-cli');
  if(!dry){const source=path.join(project,'.agents/skills/playwright-cli'),dest=path.join(project,'.opencode/skills/playwright-cli');if(!fs.existsSync(path.join(source,'SKILL.md')))throw Error('Official Playwright skill was not created: '+source);if(fs.existsSync(dest))throw Error('Refusing to overwrite existing skill: '+dest);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.cpSync(source,dest,{recursive:true,force:false,errorOnExist:true})}}
 if(!dry){const after=inspect(project,{agents});if(!after.installed)throw Error('Playwright not fully installed: '+JSON.stringify(after));const record=path.join(project,'.ai-dev','playwright-install.json');fs.writeFileSync(record,JSON.stringify({agents:selected,cli:exe,installedAt:new Date().toISOString(),browserVerified:false},null,2)+'\n')}
 return actions;
}
module.exports={inspect,install,targets};
