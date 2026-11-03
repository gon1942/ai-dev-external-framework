import argparse
import json
import sys
import time
from pathlib import Path
from . import core, orchestrator, migration, integrations, monitor, overview, startup, audit, skill_events, tdd, lifecycle, common_skills, progress, coordinator_session, improvements


def main(argv=None):
    parser = argparse.ArgumentParser(prog="teamdev", description="멀티 에이전트 팀 개발 워크플로")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="프로젝트 루트")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="프로젝트 기본 구조 설치 (기존 파일 보존)")
    init.add_argument("--force", action="store_true", help="템플릿 파일 덮어쓰기 (주의)")
    create = sub.add_parser("new", help="작업/Spec/Plan 생성")
    create.add_argument("task")
    create.add_argument("title")
    create.add_argument("--type", choices=tdd.TYPES, default="feature", help="작업 유형: 기본 feature(TDD 필수)")
    ts = sub.add_parser("tdd-set", help="계획 승인 전 작업 유형 변경")
    ts.add_argument("task")
    ts.add_argument("--type", choices=tdd.TYPES, required=True)
    ts.add_argument("--actor", required=True)
    tc = sub.add_parser("tdd-check", help="승인된 TDD 정책 및 증거 검사")
    tc.add_argument("task")
    for cmd in ("status", "plan-ready", "dispatch"):
        p = sub.add_parser(cmd)
        p.add_argument("task")
        if cmd != "status":
            p.add_argument("--actor", required=True)
    ap = sub.add_parser("approve")
    ap.add_argument("task")
    ap.add_argument("--scope", choices=("plan", "completion"), required=True)
    ap.add_argument("--actor", required=True)
    ap.add_argument("--confirm", required=True)
    tpl = sub.add_parser('report-template', help='구현 Worker 입력 JSON 템플릿 생성 (기본 출력만, 증거 조작 없음)')
    tpl.add_argument('task'); tpl.add_argument('--worker', default='implementer')
    tpl.add_argument('--output', type=Path, help='출력 JSON 경로; 기존 파일은 덮어쓰지 않음')
    chk = sub.add_parser('report-check', help='등록 전에 입력 JSON·TDD·증거 파일 검사 (읽기 전용)')
    chk.add_argument('task'); chk.add_argument('--file', type=Path, required=True)
    for cmd in ("report", "verify", "review"):
        p = sub.add_parser(cmd)
        p.add_argument("task")
        p.add_argument("--actor", required=True)
        p.add_argument("--file", type=Path, required=True)
    rot = sub.add_parser("rotate-request", help="Worker context handoff event (not worker_done)")
    rot.add_argument("task")
    for option in ("actor", "session-id", "worktree", "next-action", "reason", "completed"):
        rot.add_argument("--" + option, required=True)
    for option in ("changed-files", "verification", "blockers"):
        rot.add_argument("--" + option, default="none")
    resume = sub.add_parser("rotate-resume", help="Validate handoff and produce short next-session bootstrap")
    resume.add_argument("task")
    resume.add_argument("--actor", required=True)
    resume.add_argument("--new-session-id", required=True)
    resume.add_argument("--previous-session-stopped", action="store_true")
    ch = sub.add_parser('coordinator-handoff', help='Orca Coordinator 새 메인 세션 인계 준비; UI 자동 생성 아님')
    ch.add_argument('task')
    ch.add_argument('--session-id', required=True)
    ch.add_argument('--next-action', required=True)
    ch.add_argument('--reason', required=True)
    ch.add_argument('--summary', default='참조: TASK 정본/증거')
    ch.add_argument('--blockers', default='none')
    cr = sub.add_parser('coordinator-resume', help='새 메인 Coordinator에서 정본 검증 후 인계 복구')
    cr.add_argument('task')
    cr.add_argument('--new-session-id', required=True)
    cr.add_argument('--old-session-stopped', action='store_true')
    cs = sub.add_parser('coordinator-session', help='Coordinator 인계/세션 상태 조회')
    cs.add_argument('task')
    run = sub.add_parser("drive", help="승인된 TASK를 실제 워커 CLI로 순차 실행 (실행 전에는 preview)")
    run.add_argument("task")
    run.add_argument("--runtime", choices=("opencode", "claude", "codex"), default="opencode")
    run.add_argument("--execute", action="store_true", help="실제 외부 코딩 에이전트 프로세스 실행")
    run.add_argument("--max-rotations", type=int, default=5)
    route = sub.add_parser("next", help="현재 작업에 필요한 다음 Coordinator 동작 확인")
    route.add_argument("task")
    upgrade = sub.add_parser("upgrade-routing", help="기존 프로젝트에 v0.3 실행 어댑터 안전 병합 (백업)")
    upgrade.add_argument("--apply", action="store_true", help="변경 사항 적용; 기존 파일 백업")
    ut = sub.add_parser("upgrade-tools", help="기존 프로젝트에 RTK/CRG 정책과 브리지 스킬 추가")
    ut.add_argument("--apply", action="store_true")
    um = sub.add_parser("upgrade-monitor", help="기존 프로젝트에 모니터 지침과 스킬 안전 추가")
    um.add_argument("--apply", action="store_true")
    sub.add_parser("tools-status", help="RTK/CRG 설치와 그래프 파일 상태 확인")
    st = sub.add_parser("tools-setup", help="RTK/CRG 도구별 hook/MCP 초기화 (기본 미리보기)")
    st.add_argument("--tool", choices=("rtk", "crg"), required=True)
    st.add_argument("--runtime", choices=("opencode", "claude", "codex"))
    st.add_argument("--apply", action="store_true")
    bg = sub.add_parser("crg-build", help="CRG 그래프 생성/갱신 (기본 미리보기)")
    bg.add_argument("--apply", action="store_true")
    cg = sub.add_parser("crg-auto", help="소스/CRG 그래프 상태 자동 판별; --apply 시 필요할 때만 빌드")
    cg.add_argument("--apply", action="store_true")
    pg = sub.add_parser("progress", help="TASK 단계별 진행률·사용자 조치·Worker 활동 간결 표시 (읽기 전용)")
    pg.add_argument("--task", help="특정 TASK만 조회")
    pg.add_argument("--json", action="store_true")
    mon = sub.add_parser("monitor", help="모든 TASK의 최신 상태와 Worker 활동 이벤트 조회")
    mon.add_argument("--task", help="단일 TASK 조회")
    mon.add_argument("--watch", action="store_true", help="지정 간격으로 반복 조회 (Ctrl+C 종료)")
    mon.add_argument("--interval", type=float, default=3, help="watch 갱신 주기 초")
    mon.add_argument("--stale-seconds", type=int, default=120, help="heartbeat 지연 경고 임계값")
    mon.add_argument("--json", action="store_true", help="구조화된 JSON 출력")
    wp = sub.add_parser('worker-prepare', help='승인 확인 후 IMPLEMENT dispatch 전이 및 Worker 상태 준비 (실행은 하지 않음)')
    wp.add_argument('task')
    wp.add_argument('--role', choices=monitor.ROLES, required=True)
    wp.add_argument('--actor', default='coordinator')
    wr = sub.add_parser('worker-return', help='동기 네이티브 Task가 실제 반환된 경우 활동 이력 기록 (자기신고)')
    wr.add_argument('task')
    wr.add_argument('--role', choices=monitor.ROLES, required=True)
    wr.add_argument('--session-id', required=True)
    wr.add_argument('--status', choices=('FINISHED', 'FAILED', 'STOPPED'), required=True)
    wr.add_argument('--actor', default='coordinator')
    ws = sub.add_parser("worker-start", help="네이티브 서브에이전트 실행 이벤트 등록")
    ws.add_argument("task")
    ws.add_argument("--role", choices=monitor.ROLES, required=True)
    ws.add_argument("--session-id", required=True)
    ws.add_argument("--actor", default="coordinator")
    hb = sub.add_parser("worker-heartbeat", help="활성 워커 heartbeat 기록")
    hb.add_argument("task")
    hb.add_argument("--session-id", required=True)
    we = sub.add_parser("worker-stop", help="워커 종료 활동 기록")
    we.add_argument("task")
    we.add_argument("--session-id", required=True)
    we.add_argument("--status", choices=('FINISHED', 'FAILED', 'STOPPED'), required=True)
    legacy = sub.add_parser("archive-completed", help="이전 버전 완료 작업의 active 계획 아카이브")
    legacy.add_argument("task")
    legacy.add_argument("--apply", action="store_true")
    summary = sub.add_parser("session-summary", help="새 세션에서 TASK/상태/사용자 조치 대시보드")
    summary.add_argument("--json", action="store_true")
    sh = sub.add_parser("skill-history", help="전체 TASK 단계별 스킬 사용 기록과 증거 무결성")
    sh.add_argument("--task", help="해당 TASK만 조회")
    sh.add_argument("--json", action="store_true")
    perms = sub.add_parser("upgrade-permissions", help="OpenCode shell 명령 승인 설정을 안전 병합")
    perms.add_argument("--apply", action="store_true")
    proj = sub.add_parser("upgrade-lifecycle", help="완료 아카이브 및 세션 시작 정책을 기존 프로젝트에 안전 추가")
    proj.add_argument("--apply", action="store_true")
    boot = sub.add_parser("startup", help="실행 구조·단계별 스킬·현재 TASK 시작 안내 (읽기 전용)")
    boot.add_argument("--json", action="store_true")
    launcher = sub.add_parser("launch", help="안내 화면을 출력한 뒤 선택한 코딩 에이전트 실행")
    launcher.add_argument("runtime", choices=("opencode", "claude", "codex"))
    boot_upgrade = sub.add_parser("upgrade-startup", help="시작 안내 및 Coordinator 문서 작성 권한을 안전 병합")
    boot_upgrade.add_argument("--apply", action="store_true")
    diag = sub.add_parser("audit", help="에이전트/스킬/도구/작업 상태 종합 진단 (읽기 전용)")
    diag.add_argument("--json", action="store_true")
    diag.add_argument("--strict", action="store_true", help="설정 누락/작업 오류가 있으면 exit 2")
    sr = sub.add_parser("skill-record", help="스킬 사용 선언과 원본 호출 증거 파일을 기록 (실제 로드 검증은 아님)")
    sr.add_argument("task")
    sr.add_argument("--skill", required=True)
    sr.add_argument("--role", choices=("coordinator","implementer","verifier","reviewer"), required=True)
    sr.add_argument("--session-id", required=True)
    sr.add_argument("--evidence", required=True)
    se = sub.add_parser("skill-events", help="TASK의 스킬 사용 선언과 증거 무결성 조회")
    se.add_argument("task")
    au = sub.add_parser("upgrade-audit", help="기존 프로젝트에 종합 진단 지침을 비파괴적으로 추가")
    au.add_argument("--apply", action="store_true")
    utdd = sub.add_parser("upgrade-tdd", help="기존 프로젝트에 작업 유형별 TDD 정책 안전 병합")
    utdd.add_argument("--apply", action="store_true")
    lc = sub.add_parser("lifecycle-check", help="Spec/Task/Plan 위치와 승인·해시 불일치 검사 (읽기 전용)")
    lc.add_argument("--json", action="store_true")
    lc.add_argument("--strict", action="store_true", help="불일치 발견 시 exit 2")
    ui = sub.add_parser("upgrade-lifecycle-integrity", help="기존 프로젝트에 정본 경로/일치성 검사 지침을 비파괴적으로 반영")
    ui.add_argument("--apply", action="store_true")
    uc = sub.add_parser("upgrade-crg-auto", help="기존 프로젝트에 CRG 자동 판단 정책/스킬 안전 추가")
    uc.add_argument("--apply", action="store_true")
    uc16 = sub.add_parser('upgrade-coordinator-recovery', help='기존 프로젝트에 Orca Coordinator 인계·복구 정책 안전 추가')
    uc16.add_argument('--apply', action='store_true')
    cp = sub.add_parser("upgrade-coordinator-permissions", help="Coordinator의 Spec/Plan/TASK 문서 편집 권한 경로 규칙 안전 수정")
    cp.add_argument("--apply", action="store_true")
    upg = sub.add_parser("upgrade-progress", help="기존 프로젝트에 단계별 Coordinator 진행 보고 지침을 비파괴적으로 추가")
    upg.add_argument("--apply", action="store_true")
    uv = sub.add_parser("upgrade-visibility", help="기존 프로젝트에 시작 현황·스킬 기록 지침 비파괴 병합")
    uv.add_argument("--apply", action="store_true")
    ss = sub.add_parser("skills-status", help="모든 에이전트의 공통 스킬 해시·누락 검사")
    ss.add_argument("--strict", action="store_true")
    sy = sub.add_parser("skills-sync", help="잠금 파일 기준 누락 스킬 동기화 (기본 미리보기)")
    sy.add_argument("--apply", action="store_true")
    sy.add_argument("--force", action="store_true", help="로컬에서 수정된 에이전트 사본 강제 복구")
    us = sub.add_parser("upgrade-skills", help="기존 프로젝트에 공통 스킬 및 잠금 정책 안전 적용")
    us.add_argument("--apply", action="store_true")
    uwd = sub.add_parser('upgrade-worker-dispatch', help='기존 프로젝트에 Worker 준비/모니터 순서 지침 추가')
    uwd.add_argument('--apply', action='store_true')
    urc = sub.add_parser('upgrade-report-contract', help='기존 프로젝트에 Worker JSON 보고서 계약 비파괴 병합 (미리보기 기본)')
    urc.add_argument('--apply', action='store_true')
    uoc = sub.add_parser("upgrade-opencode-config", help="프로젝트 OpenCode 설정을 권장 기본값으로 안전 병합 (미리보기 기본)")
    uoc.add_argument("--apply", action="store_true")
    uds = sub.add_parser("upgrade-document-sources", help="기존 프로젝트에 설계/참고 문서 경로와 선택적 참조 지침 추가 (기본 미리보기)")
    uds.add_argument("--apply", action="store_true")
    ip = sub.add_parser('improve-propose', help='자가개선 후보와 ANALYZE 작업 생성 (정책 미변경)')
    ip.add_argument('task'); ip.add_argument('title'); ip.add_argument('--problem', required=True)
    ist = sub.add_parser('improve-stage', help='승인된 계획의 개선 파일을 격리 스테이징 (정책 미변경)')
    ist.add_argument('task'); ist.add_argument('--target', required=True); ist.add_argument('--file', type=Path, required=True)
    ich = sub.add_parser('improve-check', help='독립 검증/리뷰/사용자 최종 승인/해시 확인')
    ich.add_argument('task')
    ia = sub.add_parser('improve-apply', help='최종 승인 완료된 스테이징을 공식 정책에 반영 (기본 미리보기)')
    ia.add_argument('task'); ia.add_argument('--actor', default=''); ia.add_argument('--confirm', default='')
    ia.add_argument('--apply', action='store_true')
    iu = sub.add_parser('upgrade-self-improvement', help='자가개선 정책을 기존 프로젝트에 비파괴적으로 추가')
    iu.add_argument('--apply', action='store_true')
    sub.add_parser("doctor")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        # Frozen Coordinator handoff: cooperating CLI workflow mutations cannot advance.
        if args.command in {'tdd-set', 'plan-ready', 'approve', 'dispatch', 'report', 'verify',
                            'review', 'rotate-request', 'rotate-resume', 'worker-prepare', 'worker-start',
                            'worker-heartbeat', 'worker-stop', 'skill-record', 'improve-stage', 'improve-apply'}:
            coordinator_session.require_ready(root, args.task)
        if args.command == 'improve-propose':
            out = improvements.propose(root, args.task, args.title, args.problem)
        elif args.command == 'improve-stage':
            out = improvements.stage(root, args.task, args.target, args.file)
        elif args.command == 'improve-check':
            out = improvements.inspect(root, args.task)
        elif args.command == 'improve-apply':
            out = improvements.apply(root, args.task, args.actor, args.confirm, args.apply)
        elif args.command == 'upgrade-self-improvement':
            out = migration.upgrade_self_improvement(root, args.apply)
        elif args.command == "init":
            out = {"created_or_overwritten": core.copy_assets(root, args.force), "root": str(root)}
        elif args.command == "new":
            out = core.create_task(root, args.task, args.title, args.type)
        elif args.command == "tdd-set":
            out = tdd.set_type(root, args.task, args.type, args.actor)
        elif args.command == "tdd-check":
            out = tdd.check(root, args.task)
        elif args.command == "plan-ready":
            out = core.plan_ready(root, args.task, args.actor)
        elif args.command == "approve":
            out = core.approve(root, args.task, args.actor, args.scope, args.confirm)
        elif args.command == "dispatch":
            out = core.dispatch(root, args.task, args.actor)
        elif args.command == 'report-template':
            out = core.report_template(root, args.task, args.worker, args.output)
        elif args.command == 'report-check':
            out = core.report_check(root, args.task, args.file)
        elif args.command == "report":
            out = core.register_report(root, args.task, args.actor, args.file)
        elif args.command == "verify":
            out = core.verify(root, args.task, args.actor, args.file)
        elif args.command == "review":
            out = core.review(root, args.task, args.actor, args.file)
        elif args.command == "rotate-request":
            out = core.rotation_request(root, args.task, args.actor, args.session_id,
                Path(args.worktree), args.next_action, args.reason, args.completed,
                args.changed_files, args.verification, args.blockers)
        elif args.command == "rotate-resume":
            out = core.rotation_resume(root, args.task, args.actor,
                args.previous_session_stopped, args.new_session_id)
        elif args.command == 'coordinator-handoff':
            out = coordinator_session.prepare(root, args.task, args.session_id, args.next_action, args.reason, args.summary, args.blockers)
        elif args.command == 'coordinator-resume':
            out = coordinator_session.resume(root, args.task, args.new_session_id, args.old_session_stopped)
        elif args.command == 'coordinator-session':
            out = coordinator_session.status(root, args.task)
        elif args.command == "drive":
            out = orchestrator.drive(root, args.task, args.runtime, execute=args.execute, max_rotations=args.max_rotations)
        elif args.command == 'upgrade-report-contract':
            out = migration.upgrade_report_contract(root, args.apply)
        elif args.command == 'upgrade-opencode-config':
            out = migration.upgrade_opencode_config(root, args.apply)
        elif args.command == 'upgrade-document-sources':
            out = migration.upgrade_document_sources(root, args.apply)
        elif args.command == 'upgrade-worker-dispatch':
            out = migration.upgrade_worker_dispatch(root, args.apply)
        elif args.command == "upgrade-routing":
            out = migration.upgrade_routing(root, args.apply)
        elif args.command == "upgrade-tools":
            out = migration.upgrade_tools(root, args.apply)
        elif args.command == "upgrade-monitor":
            out = migration.upgrade_monitor(root, args.apply)
        elif args.command == "tools-status":
            out = integrations.tool_status(root)
        elif args.command == "tools-setup":
            out = integrations.setup_tool(root, args.tool, args.runtime, apply=args.apply)
        elif args.command == "crg-build":
            out = integrations.build_graph(root, apply=args.apply)
        elif args.command == "crg-auto":
            out = integrations.auto_graph(root, apply=args.apply)
        elif args.command == "skills-status":
            out=common_skills.status(root)
            print(json.dumps(out,ensure_ascii=False,indent=2))
            return 2 if args.strict and not out['ok'] else 0
        elif args.command == "skills-sync":
            out=common_skills.sync(root,args.apply,args.force)
            print(json.dumps(out,ensure_ascii=False,indent=2))
            return 2 if out['conflicts'] or (args.apply and not out['status']['ok']) else 0
        elif args.command == "upgrade-skills":
            out=common_skills.upgrade(root,args.apply)
            print(json.dumps(out,ensure_ascii=False,indent=2))
            return 2 if out['conflicts'] or (args.apply and not out['ok']) else 0
        elif args.command == 'upgrade-coordinator-recovery':
            out = migration.upgrade_coordinator_recovery(root, args.apply)
        elif args.command == "upgrade-coordinator-permissions":
            out = migration.upgrade_coordinator_permissions(root, args.apply)
        elif args.command == "upgrade-progress":
            out = migration.upgrade_progress(root, args.apply)
        elif args.command == "upgrade-visibility":
            out = migration.upgrade_visibility(root, args.apply)
        elif args.command == "upgrade-crg-auto":
            out = migration.upgrade_crg_auto(root, args.apply)
        elif args.command == "progress":
            data = progress.snapshot(root, args.task)
            print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else progress.render(data))
            return 0
        elif args.command == "monitor":
            if args.interval <= 0 or args.stale_seconds <= 0:
                raise core.WorkflowError("interval 및 stale-seconds는 양수여야 합니다")
            def snapshot():
                return ([monitor.one(root, args.task, stale_seconds=args.stale_seconds)]
                        if args.task else monitor.all_tasks(root, stale_seconds=args.stale_seconds))
            if args.watch:
                try:
                    while True:
                        rows = snapshot()
                        if sys.stdout.isatty():
                            print("\033[2J\033[H", end="")
                        print(json.dumps(rows, ensure_ascii=False, indent=2) if args.json else monitor.render(rows), flush=True)
                        time.sleep(args.interval)
                except KeyboardInterrupt:
                    return 0
            else:
                rows = snapshot()
                print(json.dumps(rows, ensure_ascii=False, indent=2) if args.json else monitor.render(rows))
                return 0
        elif args.command == "archive-completed":
            out = core.archive_legacy_completed(root, args.task, apply=args.apply)
        elif args.command == "session-summary":
            out = overview.dashboard(root)
            if not args.json:
                print('해야 할 작업 {pending}건 | 완료 {completed}건 | 승인 대기 {approval_waiting}건 | 차단 {blocked}건'.format(**out['counts']))
                print('TASK | 단계 | 상태 | 사용자 조치 | 다음 실행 | Worker / 활동')
                for t in out['tasks']:
                    print('{task} | {stage} | {status} | {user_action} | {next_action} | {worker} / {activity}'.format(**t))
                return 0
        elif args.command == "skill-history":
            out = skill_events.history(root, args.task)
            if not args.json:
                print('스킬 사용 신고 {count}건 | 증거 불일치 {integrity_errors}건'.format(**out))
                for stage, events in out['by_stage'].items():
                    if events:
                        print(stage + ':')
                        for e in events:
                            print('  {task} | {skill} | {role} | {at} | {integrity}'.format(**e))
                print(out['note'])
                return 0
        elif args.command == "upgrade-permissions":
            out = migration.upgrade_permissions(root, args.apply)
        elif args.command == "upgrade-lifecycle":
            out = migration.upgrade_lifecycle(root, args.apply)
        elif args.command == 'worker-prepare':
            out = orchestrator.prepare_worker(root, args.task, args.role, args.actor)
        elif args.command == 'worker-return':
            out = monitor.observe_return(root, args.task, args.role, args.session_id, args.status, actor=args.actor)
        elif args.command == "worker-start":
            out = monitor.start(root, args.task, args.role, args.session_id, actor=args.actor)
        elif args.command == "worker-heartbeat":
            out = monitor.heartbeat(root, args.task, args.session_id)
        elif args.command == "worker-stop":
            out = monitor.stop(root, args.task, args.session_id, args.status)
        elif args.command == "startup":
            info = startup.snapshot(root)
            print(json.dumps(info, ensure_ascii=False, indent=2) if args.json else startup.render(info))
            return 0
        elif args.command == "lifecycle-check":
            data = lifecycle.check(root)
            print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else lifecycle.render(data))
            return 2 if args.strict and not data['ok'] else 0
        elif args.command == "audit":
            data = audit.audit(root)
            print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else audit.render(data))
            return 2 if args.strict and any(i["severity"] == "ERROR" for i in data["issues"]) else 0
        elif args.command == "upgrade-lifecycle-integrity":
            out = migration.upgrade_lifecycle_integrity(root, args.apply)
        elif args.command == "upgrade-tdd":
            out = migration.upgrade_tdd(root, args.apply)
        elif args.command == "upgrade-audit":
            out = migration.upgrade_audit(root, args.apply)
        elif args.command == "skill-record":
            out = skill_events.record(root, args.task, args.skill, args.role, args.session_id, args.evidence)
        elif args.command == "skill-events":
            out = skill_events.list_events(root, args.task)
        elif args.command == "launch":
            return startup.launch(root, args.runtime)
        elif args.command == "upgrade-startup":
            out = migration.upgrade_startup(root, args.apply)
        elif args.command == "next":
            out = orchestrator.next_step(root, args.task)
        elif args.command == "status":
            out = core.status(root, args.task)
        else:
            out = core.doctor(root)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    except (core.WorkflowError, OSError, KeyError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
