#!/usr/bin/env python3
"""Install unmodified upstream agent skills for Codex, OpenCode and Claude Code."""
import argparse, json, shutil, subprocess, tempfile, pathlib, hashlib, datetime, sys

ROOT=pathlib.Path(__file__).resolve().parent.parent
CATALOG={
'mattpocock':('https://github.com/mattpocock/skills.git', ['grill-with-docs','to-spec','to-tickets','implement','implement-spec','code-review','retro','diagnosing-bugs']),
'superpowers':('https://github.com/obra/superpowers.git', ['brainstorming','writing-plans','test-driven-development','systematic-debugging','verification-before-completion','requesting-code-review','receiving-code-review','using-git-worktrees','subagent-driven-development','using-superpowers']),
'ponytail':('https://github.com/DietrichGebert/ponytail.git', ['ponytail']),
}

def run(args):
 p=subprocess.run(args,text=True,capture_output=True)
 if p.returncode: raise RuntimeError(f"{' '.join(args)}\n{p.stderr.strip()}")
 return p.stdout.strip()

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--project',required=True)
 ap.add_argument('--agents',choices=['all','codex','opencode','claude'],default='all')
 ap.add_argument('--source-dir',help='Optional offline folder containing mattpocock/, superpowers/ and ponytail/ checkouts')
 ap.add_argument('--dry-run',action='store_true')
 ap.add_argument('--pins',help='JSON mapping vendor names to exact commit SHA; required for reproducible team installs')
 ap.add_argument('--update',action='store_true',help='Only replace files owned by a prior install when upstream changes; never overwrite foreign modifications')
 args=ap.parse_args()
 project=pathlib.Path(args.project).expanduser().resolve()
 if not project.is_dir(): ap.error('project directory must exist')
 pins=json.loads(pathlib.Path(args.pins).read_text()) if args.pins else {}
 if pins and (set(pins)!=set(CATALOG) or any(not isinstance(v,str) or len(v)!=40 or any(c not in '0123456789abcdefABCDEF' for c in v) for v in pins.values())):
  raise RuntimeError('pins must map every vendor to a 40-character git SHA')
 agents=['codex','opencode','claude'] if args.agents=='all' else [args.agents]
 # OpenCode gets its own .opencode/skills; no implicit dependency on Codex
 dests={'codex':project/'.agents/skills','opencode':project/'.opencode/skills','claude':project/'.claude/skills'}
 manifest_path=project/'.external-skills-lock.json'
 old=json.loads(manifest_path.read_text()) if manifest_path.exists() else {'files':{}}
 new={'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':{},'files':dict(old.get('files',{}))}
 with tempfile.TemporaryDirectory() as td:
  src={}
  for vendor,(url,skills) in CATALOG.items():
   if args.source_dir:
    repo=pathlib.Path(args.source_dir).expanduser().resolve()/vendor
    if not repo.is_dir(): raise RuntimeError(f'Missing offline source: {repo}')
   else:
    repo=pathlib.Path(td)/vendor
    print(f'FETCH {url}',flush=True)
    run(['git','clone',url,str(repo)]) if vendor in pins else run(['git','clone','--depth','1',url,str(repo)])
    if vendor in pins:run(['git','-C',str(repo),'checkout','--detach',pins[vendor]])
   src[vendor]=repo
   try: revision=run(['git','-C',str(repo),'rev-parse','HEAD'])
   except RuntimeError: revision='local-unversioned'
   if vendor in pins and revision.lower()!=pins[vendor].lower():raise RuntimeError(f'Pin mismatch for {vendor}: {revision} != {pins[vendor]}')
   new['sources'][vendor]={'url':url,'revision':revision}
  changes=[]
  for vendor,(_,names) in CATALOG.items():
   repo=src[vendor]
   for name in names:
    matches=sorted(x for x in (repo/'skills').rglob('SKILL.md') if x.parent.name==name)
    if len(matches)!=1:
     raise RuntimeError(f'Missing or ambiguous REQUIRED skill {vendor}/{name}: expected 1 exact source, found {len(matches)}')
    source=matches[0].parent
    if not (source/'SKILL.md').is_file() or not (source/'SKILL.md').read_text(encoding='utf-8').strip():
     raise RuntimeError(f'Empty REQUIRED skill {vendor}/{name}')
    for agent in agents:
     # Namespace avoids collisions; upstream SKILL.md internal name remains unmodified
     dest=dests[agent]/name
     if dest.exists():
      # Compare entire directory contents before accepting or replacing
      existing={str(x.relative_to(dest)):sha(x.read_bytes()) for x in dest.rglob('*') if x.is_file()}
      incoming={str(x.relative_to(source)):sha(x.read_bytes()) for x in source.rglob('*') if x.is_file()}
      if existing==incoming:
       print(f'SKIP IDENTICAL {agent}:{name}'); continue
      previous={k[len(str(dest.relative_to(project)))+1:]:v for k,v in old['files'].items() if k.startswith(str(dest.relative_to(project))+'/')}
      if not(args.update and previous and previous==existing):
       raise RuntimeError(f'Collision: {dest}. Refusing to overwrite; backup/remove manually or use --update for unchanged managed files.')
     changes.append((source,dest,agent,vendor,name))
  for source,dest,agent,vendor,name in changes:
   print(f'{"WOULD INSTALL" if args.dry_run else "INSTALL"} {agent}: {vendor}/{name} -> {dest}')
   if args.dry_run: continue
   if dest.exists(): shutil.rmtree(dest)
   shutil.copytree(source,dest,symlinks=False)
  if not args.dry_run:
   for vendor,(_,names) in CATALOG.items():
    repo=src[vendor]
    for name in names:
     matches=[x for x in (repo/'skills').rglob('SKILL.md') if x.parent.name==name]
     if len(matches)!=1: continue
     for agent in agents:
      dest=dests[agent]/name
      if dest.exists():
       for f in dest.rglob('*'):
        if f.is_file(): new['files'][str(f.relative_to(project))]=sha(f.read_bytes())
   manifest_path.write_text(json.dumps(new,indent=2,ensure_ascii=False)+'\n')
  else: print('Dry-run complete: no files changed')
 print('NOTE: This installs skill files only. Ponytail skill is installed, but its native plugin, hooks, mode-switching and other runtime capabilities are NOT installed. See README. Other upstream plugins and runtimes are not installed.')

if __name__=='__main__':
 try: main()
 except (RuntimeError,OSError) as e:
  print(f'ERROR: {e}',file=sys.stderr);sys.exit(2)
