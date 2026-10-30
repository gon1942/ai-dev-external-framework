#!/usr/bin/env python3
"""Shared file-based gates for externally installed AI coding skills."""
import argparse, pathlib, json, datetime, hashlib, subprocess, sys, shutil, re
ROOT=pathlib.Path(__file__).resolve().parent.parent
BASE=ROOT/'docs'/'exec-plans'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def get(task):
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{1,79}',task):raise ValueError('invalid task ID')
 for state in ['active','completed']:
  p=BASE/state/task
  if p.is_dir() and (p/'status.json').is_file():return p
 raise ValueError(f'unknown task: {task}')
def meta(p):return json.loads((p/'status.json').read_text())
def save(p,data):(p/'status.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def digest():
 h=hashlib.sha256()
 skip={'.git','.agents','.opencode','.claude','node_modules','.venv','venv','.pytest_cache','__pycache__','.external-skills-lock.json'}
 for f in sorted(ROOT.rglob('*')):
  if not f.is_file() or any(c in skip for c in f.relative_to(ROOT).parts):continue
  rel=f.relative_to(ROOT).as_posix()
  if rel.startswith('docs/exec-plans/') or rel.startswith('docs/generated/') or rel.startswith('docs/ai-workflow/') or rel.startswith('scripts/'):continue
  h.update(rel.encode());h.update(hashlib.sha256(f.read_bytes()).digest())
 return h.hexdigest()
def acmap(p):
 try:
  data=json.loads((p/'ac-tests.json').read_text());assert isinstance(data,dict) and data
  for k,v in data.items():assert re.fullmatch(r'AC-[0-9]+',k) and isinstance(v,list) and bool(v) and all(isinstance(x,str) and x.strip() for x in v)
  return data
 except (ValueError,AssertionError,OSError) as e:raise ValueError('ac-tests.json must contain AC IDs mapped to nonempty command descriptions') from e
def proof(p):
 records=[json.loads(line) for line in (p/'evidence.jsonl').read_text().splitlines()] if (p/'evidence.jsonl').exists() else []
 mapping=acmap(p);d=digest();issues=[]
 for ac in mapping:
  if not any(x.get('ac')==ac and x.get('exit_code')==0 and x.get('source_digest')==d and x.get('log_file') and (p/x['log_file']).is_file() and x.get('command') in [v.split() for v in mapping[ac]] and not x.get('source_changed_during_test',False) for x in records):issues.append(ac+': missing current successful recorded execution')
 return issues
def gate(p,stage):
 s=meta(p)
 if stage=='implement':
  if not (s.get('approved') is True or bool(s.get('approved_by'))):raise ValueError('plan is not human-approved')
  if not (p/'spec.md').read_text().strip() or not (p/'plan.md').read_text().strip():raise ValueError('missing spec/plan')
  acmap(p)
 elif stage in ['review','complete']:
  gate(p,'implement')
  issues=proof(p)
  if issues:raise ValueError('; '.join(issues))
  if stage=='complete':
   r=s.get('review',{})
   if r.get('verdict')!='PASS' or r.get('source_digest')!=digest():raise ValueError('missing PASS review for current source')
 else:raise ValueError('unknown stage')
def main():
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='cmd',required=True)
 sub.add_parser('status');sub.add_parser('next');se=sub.add_parser('session');se.add_argument('--json',action='store_true');se.add_argument('--all',action='store_true',help='Include completed tasks (default active only)');n=sub.add_parser('new');n.add_argument('--id',required=True);n.add_argument('--title',required=True)
 for action in ['approve','gate','run','review','complete']:
  a=sub.add_parser(action);a.add_argument('--id',required=True)
  if action in ['approve','complete']:a.add_argument('--user-confirmed',action='store_true',help='Agent attests explicit user approval in current conversation; not identity authentication')
  if action=='gate':a.add_argument('--stage',choices=['implement','review','complete'],required=True)
  if action=='run':a.add_argument('--ac',required=True);a.add_argument('command',nargs=argparse.REMAINDER)
  if action=='review':a.add_argument('--verdict',choices=['PASS','FAIL'],required=True);a.add_argument('--notes-file',required=True)
 args=parser.parse_args()
 if args.cmd=='session':
  # Read-only snapshot for a fresh agent session; do not infer approvals from chat.
  tasks=[];problems=[]
  states=['active','completed'] if args.all else ['active']
  for state in states:
   for sf in sorted((BASE/state).glob('*/status.json')):
    q=sf.parent
    try:
     d=meta(q);phase='COMPLETED' if state=='completed' else 'PLAN_APPROVAL_REQUIRED';issue=''
     if state=='active':
      if not d.get('approved') and not d.get('approved_by'):
       # A newly created task may have no meaningful plan yet.
       phase='PLAN_DRAFT' if not (q/'ac-tests.json').is_file() or (q/'ac-tests.json').read_text().strip()=='{}' else 'PLAN_APPROVAL_REQUIRED'
      else:
       try:gate(q,'review');phase='INDEPENDENT_REVIEW_REQUIRED'
       except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:phase='IMPLEMENT_OR_VERIFY';issue=str(e)
       if d.get('review',{}).get('verdict')=='PASS':
        try:gate(q,'complete');phase='COMPLETION_APPROVAL_REQUIRED';issue=''
        except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:phase='REVERIFY_OR_REVIEW';issue=str(e)
     tasks.append({'id':q.name,'title':d.get('title',''), 'phase':phase,'path':str(q.relative_to(ROOT)),'created_at':d.get('created_at',''),'issue':issue})
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:
     problems.append({'path':str(q.relative_to(ROOT)),'error':str(e)})
  for state in states:
   if (BASE/state).is_dir():
    for d in sorted((BASE/state).iterdir()):
     if d.is_dir() and not (d/'status.json').is_file():problems.append({'path':str(d.relative_to(ROOT)),'error':'orphan folder without status.json'})
  if (BASE/'active').is_dir() and (BASE/'completed').is_dir():
   for d in sorted((BASE/'active').iterdir()):
    if d.is_dir() and (BASE/'completed'/d.name).is_dir():problems.append({'path':str(d.relative_to(ROOT)),'error':'task folder exists in both active and completed'})
  order={'REVERIFY_OR_REVIEW':0,'IMPLEMENT_OR_VERIFY':1,'INDEPENDENT_REVIEW_REQUIRED':2,'PLAN_DRAFT':3,'PLAN_APPROVAL_REQUIRED':4,'COMPLETION_APPROVAL_REQUIRED':5,'COMPLETED':6}
  tasks.sort(key=lambda d:(order.get(d['phase'],99), d['id']))
  payload={'project':str(ROOT),'active_count':sum(t['phase']!='COMPLETED' for t in tasks),'tasks':tasks,'warnings':problems}
  if args.json:print(json.dumps(payload,indent=2,ensure_ascii=False));return
  print('=== AI WORK SESSION STATUS ===')
  print('Project:',ROOT)
  print('Active tasks:',payload['active_count'])
  if not tasks:print('No tracked active tasks. For a new user request, create a task; do not create one merely because a session started.')
  for t in tasks:
   print(f"- {t['id']} | {t['phase']} | {t['title']}")
   print('  files:',t['path'])
   if t['issue']:print('  attention:',t['issue'])
  for err in problems:print('WARNING:',err['path'],err['error'])
  print('Next: Read relevant active task files; report current status before new coding. Do not infer user approval.')
  return
 if args.cmd=='next':
  tasks=[]
  for state in ['active','completed']:
   for sf in sorted((BASE/state).glob('*/status.json')):
    q=sf.parent;d=meta(q);phase='COMPLETED' if state=='completed' else 'PLAN_APPROVAL_REQUIRED'
    if state=='active' and d.get('approved') is True:
     try:gate(q,'review');phase='INDEPENDENT_REVIEW_REQUIRED'
     except (ValueError,OSError):phase='IMPLEMENT_OR_VERIFY'
     if d.get('review',{}).get('verdict')=='PASS':
      try:gate(q,'complete');phase='COMPLETION_APPROVAL_REQUIRED'
      except (ValueError,OSError):phase='REVERIFY_OR_REVIEW'
    tasks.append({'id':q.name,'title':d.get('title'),'phase':phase,'directory':str(q.relative_to(ROOT))})
  print(json.dumps({'tasks':tasks},indent=2,ensure_ascii=False));return
 if args.cmd=='status':
  for state in ['active','completed']:
   for p in sorted((BASE/state).glob('*/status.json')):
    d=json.loads(p.read_text());print(state,p.parent.name,d.get('title'), 'approved='+str(d.get('approved') is True or bool(d.get('approved_by'))),'review='+str(d.get('review',{}).get('verdict')))
  return
 if args.cmd=='new':
  task=args.id
  if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{1,79}',task):raise ValueError('invalid task ID')
  if any((BASE/st/task).exists() for st in ['active','completed']):raise ValueError('task exists')
  p=BASE/'active'/task;p.mkdir(parents=True)
  (p/'analysis.md').write_text('# Analysis\n\n');(p/'spec.md').write_text('# Spec / Acceptance Criteria\n\n');(p/'plan.md').write_text('# Execution plan / Task graph\n\n');(p/'ac-tests.json').write_text('{}\n')
  save(p,{'id':task,'title':args.title,'created_at':now(),'approved':False,'review':{}});print('CREATED',p);return
 p=get(args.id);s=meta(p)
 if args.cmd=='approve':
  if not args.user_confirmed:raise ValueError('explicit user approval required; agent must pass --user-confirmed only after user authorizes plan')
  if p.parent.name!='active':raise ValueError('completed task')
  if not (p/'spec.md').read_text().strip() or not (p/'plan.md').read_text().strip():raise ValueError('missing spec/plan')
  acmap(p)
  adapter_file=ROOT/'.ai-dev/spec-adapter.json'
  if adapter_file.exists():
   adapter=json.loads(adapter_file.read_text())
   if adapter.get('mode')=='openspec':
    change=s.get('openspec_change_id')
    if not change or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,100}',change) or not (ROOT/adapter.get('source','openspec/changes')/change).is_dir():raise ValueError('valid openspec_change_id pointing to existing change directory required')
  s.pop('approved_by',None);s['approved']=True;s['approved_at']=now();save(p,s);print('APPROVED',p.name);return
 if args.cmd=='gate':gate(p,args.stage);print('PASS',args.stage,p.name);return
 if args.cmd=='run':
  gate(p,'implement');mapping=acmap(p)
  if args.ac not in mapping:raise ValueError('unknown AC')
  cmd=args.command
  if cmd and cmd[0]=='--':cmd=cmd[1:]
  if not cmd:raise ValueError('command required after --')
  if cmd not in [v.split() for v in mapping[args.ac]]:raise ValueError('command is not declared for this AC in ac-tests.json')
  if cmd[0].startswith('-'):raise ValueError('command must begin with executable')
  before=digest();proc=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  after=digest();logs=p/'logs';logs.mkdir(exist_ok=True)
  tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');name='logs/'+tag+'-'+args.ac+'.log'
  (p/name).write_text('$ '+' '.join(cmd)+'\n'+proc.stdout)
  row={'timestamp':now(),'ac':args.ac,'command':cmd,'exit_code':proc.returncode,'source_digest':after,'source_changed_during_test':before!=after,'log_file':name}
  if before!=after:row['exit_code']=999
  with (p/'evidence.jsonl').open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
  print('RECORDED',args.ac,'exit',proc.returncode,'source_changed',before!=after,'log',p/name)
  sys.exit(1 if before!=after else proc.returncode)
 if args.cmd=='review':
  gate(p,'review');notes=pathlib.Path(args.notes_file).resolve()
  if not notes.is_file() or not notes.read_text().strip():raise ValueError('review notes required')
  reviewdir=p/'reviews';reviewdir.mkdir(exist_ok=True);dest=reviewdir/('review-'+now().replace(':','-')+'.md');shutil.copyfile(notes,dest)
  s['review']={'verdict':args.verdict,'at':now(),'notes':str(dest.relative_to(p)),'source_digest':digest()};save(p,s);print('REVIEW',args.verdict);return
 if args.cmd=='complete':
  if not args.user_confirmed:raise ValueError('explicit user completion approval required; agent must pass --user-confirmed only after user authorizes completion')
  gate(p,'complete')
  if p.parent.name!='active':raise ValueError('already completed')
  s.pop('completed_by',None);s['completed_at']=now();save(p,s);dst=BASE/'completed'/p.name;p.rename(dst);print('COMPLETED',dst)
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,json.JSONDecodeError) as e:print('BLOCK:',e,file=sys.stderr);sys.exit(2)
