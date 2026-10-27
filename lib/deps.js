'use strict';
const fs=require('node:fs');const path=require('node:path');
const {installSkills}=require('./install');const {installCrg}=require('./crg');const playwright=require('./playwright');
const NAMES=['grill-with-docs','to-spec','to-tickets','implement','implement-spec','code-review','retro','diagnosing-bugs','brainstorming','writing-plans','test-driven-development','systematic-debugging','verification-before-completion','requesting-code-review','receiving-code-review','using-git-worktrees','subagent-driven-development','ponytail','using-superpowers'];
const DIRS={opencode:'.opencode/skills',codex:'.agents/skills',claude:'.claude/skills'};
function inspect(project,{agents='all'}={}){
 const selected=agents==='all'?Object.keys(DIRS):agents.split(',');for(const a of selected)if(!DIRS[a])throw Error('Unknown agent: '+a);
 const missing={};for(const a of selected){missing[a]=NAMES.filter(n=>{const p=path.join(project,DIRS[a],n,'SKILL.md');return !fs.existsSync(p)||!fs.readFileSync(p,'utf8').trim()})}
 const crgRecord=path.join(project,'.ai-dev','crg-install.json');const crgExe=path.join(project,'.ai-dev','crg-venv','bin','code-review-graph');
 let crgValid=false,recordAgents=[];try{const obj=JSON.parse(fs.readFileSync(crgRecord,'utf8'));recordAgents=obj.agents||[];crgValid=fs.existsSync(crgExe)&&selected.every(a=>recordAgents.includes(a))}catch{}
 return {agents:selected,missing,playwright:playwright.inspect(project,{agents}),crg:{installed:crgValid,record:fs.existsSync(crgRecord),executable:fs.existsSync(crgExe),missingAgents:selected.filter(a=>!recordAgents.includes(a))},healthy:Object.values(missing).every(a=>!a.length)&&crgValid&&playwright.inspect(project,{agents}).installed};
}
function repair(project,{agents='all',sourceDir,pins,dry=false,skipCrg=false,skipPlaywright=false}={}){
 const before=inspect(project,{agents}),actions=[];
 for(const [agent,missing] of Object.entries(before.missing))if(missing.length){actions.push(`${dry?'WOULD REPAIR':'REPAIR'} ${agent}: ${missing.join(', ')}`);if(!dry)installSkills(project,{agents:agent,sourceDir,pins})}
 if(!skipCrg&&!before.crg.installed){actions.push(`${dry?'WOULD REPAIR':'REPAIR'} CRG`);if(!dry)actions.push(...installCrg(project,{agents}));}
 if(!skipPlaywright&&!before.playwright.installed){actions.push(`${dry?'WOULD REPAIR':'REPAIR'} Playwright CLI`);actions.push(...playwright.install(project,{agents,dry}));}
 const after=dry?before:inspect(project,{agents});if(!dry&&!skipCrg&&!skipPlaywright&&!after.healthy)throw Error('Dependencies still incomplete after repair: '+JSON.stringify(after));
 return {before,after,actions};
}
module.exports={NAMES,DIRS,inspect,repair};
