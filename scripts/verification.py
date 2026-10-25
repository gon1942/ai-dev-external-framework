#!/usr/bin/env python3
"""Declarative, project-owned verification profiles; never execute undocumented commands."""
import argparse, json, pathlib, fnmatch, subprocess, datetime, hashlib, sys

def load(project):
    f=project/'.ai-dev/verification-profiles.json'
    if not f.exists():raise ValueError(f'Missing verification profiles: {f}')
    cfg=json.loads(f.read_text())
    if not isinstance(cfg.get('profiles'),dict):raise ValueError('profiles object required')
    for name,profile in cfg['profiles'].items():
        if not isinstance(profile.get('patterns'),list) or not isinstance(profile.get('checks'),dict):raise ValueError('invalid profile '+name)
        for check,cmd in profile['checks'].items():
            if not isinstance(cmd,list) or not cmd or not all(isinstance(s,str) and s for s in cmd):raise ValueError('checks must be argv lists')
    return cfg

def decide(cfg,files):
    found={}
    for name,profile in cfg['profiles'].items():
        matching=[f for f in files if any(fnmatch.fnmatch(f,pat) for pat in profile['patterns'])]
        if matching:found[name]={'files':matching,'checks':profile['checks']}
    return found

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project',default='.');ap.add_argument('--files',nargs='+',required=True);ap.add_argument('--run',action='store_true');args=ap.parse_args()
    project=pathlib.Path(args.project).resolve();cfg=load(project);found=decide(cfg,args.files)
    if not found:print(json.dumps({'profiles':{},'warning':'NO_MATCHING_PROFILE: manual verification plan required'},indent=2));return 2
    if not args.run:print(json.dumps({'profiles':found,'note':'Preview only: choose appropriate AC mappings before execution'},indent=2));return 0
    logs=project/'docs/generated/verification';logs.mkdir(parents=True,exist_ok=True)
    results=[]
    for name,data in found.items():
        for check,cmd in data['checks'].items():
            r=subprocess.run(cmd,cwd=project,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            key=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            f=logs/(key+'-'+name+'-'+check+'.log');f.write_text(r.stdout)
            results.append({'profile':name,'check':check,'command':cmd,'exit_code':r.returncode,'log':str(f.relative_to(project)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    print(json.dumps({'results':results},indent=2))
    return 1 if any(x['exit_code'] for x in results) else 0
if __name__=='__main__':
 try:sys.exit(main())
 except (ValueError,OSError,json.JSONDecodeError) as e:print('BLOCK:',e,file=sys.stderr);sys.exit(2)
