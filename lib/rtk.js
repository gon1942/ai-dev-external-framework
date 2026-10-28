'use strict';
// RTK (rtk-ai/rtk) — 22nd framework component. Compresses common dev command
// output (git/pytest/npm/...) before agents read it. Installs the official
// Rust binary from upstream releases (download only, never bundled) and
// registers per-agent hooks globally. Telemetry is OFF by default upstream.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),os=require('node:os');
const INSTALL_URL='https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh';
const AGENTS={opencode:true,codex:true,claude:true};
function targets(agents){const a=agents==='all'?Object.keys(AGENTS):agents.split(',');if(a.some(x=>!AGENTS[x]))throw Error('Unknown agent(s) '+agents);return a}
function findBinary(runner){
 for(const cmd of [process.env.RTK_BIN,path.join(os.homedir(),'.local','bin','rtk'),'rtk'].filter(Boolean)){
  try{const r=runner(cmd,['--version'],{encoding:'utf8',timeout:15000});if(!r.error&&r.status===0)return {path:cmd,version:String(r.stdout||'').trim()}}catch{}
 }
 return null;
}
function inspect(project,{agents='all',runner=cp.spawnSync}={}){
 const selected=targets(agents),binary=findBinary(runner);
 let recordAgents=[],recorded=false;
 try{const obj=JSON.parse(fs.readFileSync(path.join(project,'.ai-dev','rtk-install.json'),'utf8'));recordAgents=Array.isArray(obj.agents)?obj.agents:[];recorded=true}catch{}
 return {installed:Boolean(binary)&&recorded&&selected.every(a=>recordAgents.includes(a)),binary,record:recorded,missingAgents:selected.filter(a=>!recordAgents.includes(a))};
}
function versionAtLeast(ver,min){const a=String(ver).match(/(\d+)\.(\d+)\.(\d+)/);if(!a)return true;const c=(x,y)=>x[0]-y[0]||x[1]-y[1]||x[2]-y[2];return c([+a[1],+a[2],+a[3]],min)>=0}
function install(project,{agents='all',dry=false,runner=cp.spawnSync}={}){
 const selected=targets(agents),before=inspect(project,{agents,runner}),actions=[];
 if(before.installed)return ['RTK ALREADY INSTALLED'];
 const run=(cmd,args,timeout)=>{actions.push([cmd,...args].join(' '));if(dry)return;const r=runner(cmd,args,{encoding:'utf8',timeout:timeout||300000});if(r.error||r.status!==0)throw Error('RTK init failed: '+[cmd,...args].join(' ')+'\n'+(r.stderr||r.error?.message||''))};
 let bin=before.binary;
 if(!bin){
  if(os.platform()==='win32')throw Error('RTK auto-install on Windows is not supported; install manually with `winget install rtk-ai.rtk` then re-run');
  // Download installer to a local file and run it literally (no remote pipe).
  const script=path.join(os.tmpdir(),'ai-dev-rtk-install.sh');
  actions.push('curl -fsSL -o '+script+' '+INSTALL_URL);
  actions.push('sh '+script);
  if(!dry){
   const dl=runner('curl',['-fsSL','-o',script,INSTALL_URL],{encoding:'utf8',timeout:180000});
   if(dl.error||dl.status!==0)throw Error('RTK installer download failed: '+(dl.stderr||dl.error?.message||''));
   const ex=runner('sh',[script],{encoding:'utf8',timeout:600000});
   if(ex.error||ex.status!==0)throw Error('RTK installation failed: '+(ex.stderr||ex.error?.message||''));
   bin=findBinary(runner);
   if(!bin)throw Error('RTK binary not found after installation (is ~/.local/bin on PATH?)');
  }
 } else actions.push('RTK binary present: '+bin.version);
 const binCmd=bin?bin.path:'rtk';
 // Agent hook registration is global and idempotent.
 if(selected.includes('claude')){run(binCmd,['init','-g']);actions.push('NOTE claude: non-interactive `rtk init` skips the settings.json hook patch — apply the snippet it prints once')}
 if(selected.includes('opencode')){
  if(!dry&&bin){const v=runner('opencode',['--version'],{encoding:'utf8',timeout:15000});if(!v.error&&v.status===0&&!versionAtLeast(v.stdout,[1,18,29]))actions.push('WARN opencode '+String(v.stdout).trim()+' < 1.18.29 — the rtk plugin requires OpenCode 1.18.29+')}
  run(binCmd,['init','-g','--opencode']);
 }
 if(selected.includes('codex'))run(binCmd,['init','-g','--codex']);
 if(!dry){
  fs.mkdirSync(path.join(project,'.ai-dev'),{recursive:true});
  fs.writeFileSync(path.join(project,'.ai-dev','rtk-install.json'),JSON.stringify({agents:selected,binary:bin.path,version:bin.version,installedAt:new Date().toISOString()},null,2)+'\n');
  const after=inspect(project,{agents,runner});
  if(!after.installed)throw Error('RTK not fully installed: '+JSON.stringify(after));
 }
 return actions;
}
module.exports={inspect,install,targets};
