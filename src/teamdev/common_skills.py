"""Deterministic project-local skill distribution, no network or silent overwrites."""
from __future__ import annotations
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from . import core

TARGETS = {"codex": ".agents/skills", "opencode": ".opencode/skills", "claude": ".claude/skills"}

def _hash(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def _lock(root):
    p=root/'.ai-dev/skills.lock.json'
    if not p.is_file():
        raise core.WorkflowError('공통 스킬 잠금 파일이 없습니다. teamdev upgrade-skills --apply 필요')
    return core.json_read(p)

def status(root:Path):
    root=root.resolve()
    lock=_lock(root)
    rows=[]
    for name,spec in sorted(lock['skills'].items()):
        expected=spec['sha256']
        paths={}
        for runtime,rel in TARGETS.items():
            p=root/rel/name/'SKILL.md'
            actual=_hash(p)
            paths[runtime]={'status':'OK' if actual==expected else ('MISSING' if actual is None else 'MISMATCH'), 'sha256': actual}
        rows.append({'name':name,'provenance':spec['provenance'],'runtimes':paths})
    problems=[{'skill':r['name'],'runtime':runtime,'status':entry['status']} for r in rows for runtime,entry in r['runtimes'].items() if entry['status']!='OK']
    return {'version':lock.get('version'),'total':len(rows),'runtimes':{k:sum(r['runtimes'][k]['status']=='OK' for r in rows) for k in TARGETS},'skills':rows,'issues':problems,'ok':not problems,'runtime_loaded':'NOT_VERIFIED'}

def sync(root:Path,apply=False,force=False):
    root=root.resolve()
    lock=_lock(root)
    actions=[]
    conflicts=[]
    for name,spec in sorted(lock['skills'].items()):
        source=root/'.agents/skills'/name/'SKILL.md'
        if _hash(source)!=spec['sha256']:
            conflicts.append(f'{name}: canonical missing or modified');continue
        # canonical source already checked; copy *whole* skill directory for companion files.
        for runtime in ('opencode','claude'):
            dest=root/TARGETS[runtime]/name
            cur=_hash(dest/'SKILL.md')
            if cur==spec['sha256']:continue
            if cur is not None and not force:
                conflicts.append(f'{runtime}/{name}: modified; explicit --force required');continue
            actions.append({'runtime':runtime,'skill':name,'action':'replace' if cur else 'install'})
            if apply:
                if dest.exists():shutil.rmtree(dest)
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copytree(source.parent,dest)
    return {'applied':apply,'actions':actions,'conflicts':conflicts,'status':status(root)}

def _package_bytes(rel):
    path=core.TEMPLATE_DIR/rel
    if path.is_file():
        return path.read_bytes()
    with zipfile.ZipFile(core.TEMPLATE_DIR/'bundle.zip') as archive:
        return archive.read(rel)

def upgrade(root:Path,apply=False):
    """Preflight all conflicts before changing a project; never overwrite custom skills."""
    root=root.resolve()
    original=core.TEMPLATE_DIR
    files=['.ai-dev/skills.lock.json','.ai-dev/skills.json','docs/COMMON-SKILLS.md']
    actions=[];conflicts=[]
    lock=json.loads(_package_bytes(files[0]).decode('utf8'))
    for name,spec in sorted(lock['skills'].items()):
        rel=f'.agents/skills/{name}'
        target=root/rel
        cur=_hash(target/'SKILL.md')
        if cur==spec['sha256']: continue
        if cur is not None:
            conflicts.append(f'{rel}: existing content differs; review before migration')
        else:
            actions.append({'action':'install','target':rel})
    for rel in files:
        source=original/rel;target=root/rel
        if not target.is_file() or target.read_bytes()!=_package_bytes(rel):
            actions.append({'action':'update-policy','target':rel})
    if conflicts:
        return {'applied':False,'actions':actions,'conflicts':conflicts,'sync':None,'ok':False}
    if apply:
        for action in actions:
            rel=action['target'];src=original/rel;target=root/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            if action['action']=='install':
                target.mkdir(parents=True,exist_ok=True)
                (target/'SKILL.md').write_bytes(_package_bytes(rel+'/SKILL.md'))
            else:
                if target.exists():
                    backup=target.with_name(target.name+'.pre-v013.bak')
                    if not backup.exists():shutil.copy2(target,backup)
                target.write_bytes(_package_bytes(rel))
        synced=sync(root,apply=True)
    else:
        synced=None
    return {'applied':apply,'actions':actions,'conflicts':conflicts,'sync':synced,'ok':not conflicts and (synced is None or synced['status']['ok'])}
