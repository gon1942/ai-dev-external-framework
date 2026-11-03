'use strict';
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const os = require('node:os');
const VERSION = require('../package.json').version;
const wheel = path.join(__dirname, '../vendor', `team_ai_dev_framework-${VERSION}-py3-none-any.whl`);
const marker = '.teamdev-npx';
function run(exe, args, opts = {}) {
  const res = cp.spawnSync(exe, args, { encoding: 'utf8', stdio: opts.stdio || 'inherit', ...opts });
  if (res.error) throw new Error(`${exe}: ${res.error.message}`);
  if (res.status !== 0) throw new Error(`${exe}: 종료코드 ${res.status}`);
  return res;
}
function pythonBinary() {
  for (const name of [process.env.TEAMDEV_PYTHON, 'python3', 'python'].filter(Boolean)) {
    const p = cp.spawnSync(name, ['-c', 'import sys; assert sys.version_info >= (3,10)'], { stdio: 'ignore' });
    if (!p.error && p.status === 0) return name;
  }
  throw new Error('Python 3.10 이상이 필요합니다. Python 설치 후 다시 실행하세요.');
}
function venvBin(root) {
  return path.join(root, '.ai-dev', '.runtime', process.platform === 'win32' ? 'Scripts' : 'bin');
}
function runtimePath(root) {
  return path.join(venvBin(root), process.platform === 'win32' ? 'python.exe' : 'python');
}
function ensureRuntime(root) {
  if (!fs.existsSync(wheel)) throw new Error(`번들 WHL 누락: ${wheel}`);
  const py = runtimePath(root);
  const versionFile = path.join(root, '.ai-dev', '.runtime', marker);
  const installed = fs.existsSync(py) && fs.existsSync(versionFile) && fs.readFileSync(versionFile, 'utf8').trim() === VERSION;
  if (installed) return py;
  const venv = path.join(root, '.ai-dev', '.runtime');
  // Existing runtime is private to this npx wrapper; do not modify a user's system Python.
  if (!fs.existsSync(py)) run(pythonBinary(), ['-m', 'venv', venv]);
  run(py, ['-m', 'pip', 'install', '--no-index', '--no-deps', '--force-reinstall', wheel]);
  fs.writeFileSync(versionFile, `${VERSION}\n`, 'utf8');
  return py;
}
function teamdev(root, args) {
  const py = ensureRuntime(root);
  run(py, ['-m', 'teamdev', '--root', root, ...args]);
}
function isTeamdevProject(root) {
  return fs.existsSync(path.join(root, '.ai-dev', 'policy.json')) &&
    fs.existsSync(path.join(root, 'docs', 'WORKFLOW.md'));
}
function isLegacyProject(root) {
  return fs.existsSync(path.join(root, 'scripts', 'workflow.py')) ||
    fs.existsSync(path.join(root, '.ai-dev', 'stage-skills.json'));
}
function changes(root) {
  return [
    'upgrade-report-contract',
    'upgrade-document-sources', 'upgrade-opencode-config', 'upgrade-self-improvement',
    'upgrade-worker-dispatch', 'upgrade-coordinator-recovery', 'upgrade-skills'
  ].map(command => ({ command, root }));
}
function configureIgnore(root) {
  const ignorePath = path.join(root, '.gitignore');
  const rule = '.ai-dev/.runtime/';
  const old = fs.existsSync(ignorePath) ? fs.readFileSync(ignorePath, 'utf8') : '';
  if (!old.split(/\r?\n/).includes(rule)) fs.appendFileSync(ignorePath, `${old.endsWith('\n') || !old ? '' : '\n'}${rule}\n`);
}
function usage() {
  process.stdout.write(`Team AI Dev Framework ${VERSION}\n\n` +
    '  team-ai-dev init <project> [--dry-run]\n' +
    '  team-ai-dev upgrade --project . [--dry-run | --apply]\n' +
    '  team-ai-dev adopt --project . [--dry-run | --apply]   (기존 별도 프레임워크는 별도 이관 검토)\n' +
    '  team-ai-dev doctor --project .\n' +
    '  team-ai-dev cli --project . <teamdev command...>\n');
}
function parse(argv) {
  const cmd = argv[0];
  let dir = null, project = null, dryRun = false, apply = false, extra = [];
  const sep = argv.indexOf('--');
  if (sep >= 0) { extra = argv.slice(sep + 1); argv = argv.slice(0, sep); }
  for (let i = 1; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--project') { if (!argv[i + 1]) throw new Error('--project 경로가 필요합니다'); project = argv[++i]; }
    else if (arg === '--dry-run') dryRun = true;
    else if (arg === '--apply') apply = true;
    else if (arg.startsWith('-')) throw new Error(`지원하지 않는 옵션: ${arg}`);
    else if (!dir) dir = arg;
    else throw new Error(`예상하지 못한 인자: ${arg}`);
  }
  if (apply && dryRun) throw new Error('--apply 와 --dry-run 은 동시에 사용할 수 없습니다');
  return { cmd, dir, project, dryRun, apply, extra };
}
function main(argv = process.argv.slice(2)) {
  const a = parse(argv);
  if (!a.cmd || a.cmd === '--help' || a.cmd === 'help') return usage();
  const root = path.resolve(a.project || a.dir || '.');
  if (a.cmd === 'init') {
    if (!a.project && !a.dir) throw new Error('init 뒤에 프로젝트 이름/경로를 지정하세요');
    if (a.dryRun) return console.log(JSON.stringify({ action: 'init', project: root, apply: false }, null, 2));
    fs.mkdirSync(root, { recursive: true });
    teamdev(root, ['init']); // never --force; keep existing files
    configureIgnore(root);
    return console.log(`[완료] ${root}\n사용: npx --yes @gon1942/team-ai-dev-framework@${VERSION} cli --project . startup`);
  }
  if (a.cmd === 'adopt') {
    if (isLegacyProject(root)) throw new Error('기존 ai-dev-external-framework 감지: 상태/정책 이관은 자동 수행하지 않습니다. 별도 마이그레이션 계획과 사용자 승인이 필요합니다.');
    if (isTeamdevProject(root)) throw new Error('이미 Team AI Dev 프로젝트입니다. upgrade를 사용하세요.');
    if (a.dryRun || !a.apply) return console.log(JSON.stringify({ action:'adopt', project:root, apply:false, warning:'사용자 파일 보존; 새 teamdev 구조만 추가' }, null, 2));
    if (!fs.existsSync(root)) throw new Error('기존 프로젝트가 없습니다');
    teamdev(root, ['init']);
    configureIgnore(root);
    return console.log('[완료] 비파괴 초기 설치. 기존 프로젝트 정책과 신규 정책의 충돌은 직접 검토하세요.');
  }
  if (a.cmd === 'upgrade') {
    if (!fs.existsSync(root)) throw new Error(`프로젝트를 찾을 수 없습니다: ${root}`);
    if (isLegacyProject(root)) throw new Error('다른 프레임워크(ai-dev-external-framework)가 감지됐습니다. 자동 덮어쓰기/이관을 중단했습니다.');
    if (!isTeamdevProject(root)) throw new Error('Team AI Dev Framework 프로젝트가 아닙니다. adopt를 사용하거나 기존 구조를 확인하세요.');
    if (!a.apply) return console.log(JSON.stringify({ action: 'upgrade', project: root, apply: false, changes: changes(root), note:'각 업그레이드 명령은 내부에서 별도 미리보기를 제공합니다' }, null, 2));
    // Preserve existing project settings and tasks; each upgrade runs own safety checks.
    for (const { command } of changes(root)) teamdev(root, [command, '--apply']);
    configureIgnore(root);
    return console.log('[완료] 지원되는 정책 업그레이드 적용. doctor 및 수동 충돌 검토를 권장합니다.');
  }
  if (a.cmd === 'doctor') return teamdev(root, ['doctor']);
  if (a.cmd === 'cli') {
    if (!a.extra.length) throw new Error('cli 뒤에 teamdev 명령을 지정하세요. 예: cli --project . -- startup');
    return teamdev(root, a.extra);
  }
  throw new Error(`알 수 없는 명령: ${a.cmd}`);
}
module.exports = { main, parse, isLegacyProject, isTeamdevProject, changes, ensureRuntime };
