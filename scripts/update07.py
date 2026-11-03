from pathlib import Path
import json
root=Path(__file__).resolve().parent.parent
assets=root/'src/teamdev/assets'
marker='## Startup Dashboard (v0.7)'
append_common='''## Startup Dashboard (v0.7)
- 첫 응답 전에 `teamdev --root . startup`을 실제 실행하고 실행 구조, 각 단계의 설치된 스킬, 진행 중/완료 TASK를 짧게 사용자에게 보여준다.
- 시작 명령 실행 실패 시 이유를 명시하고 성공한 척하지 않는다.
- 새 세션에서는 실행 중 Worker의 소유권 확인 없이 재개하지 않는다.
- `teamdev launch opencode|claude|codex`는 에이전트 시작 전 로컬 터미널에 확정적으로 안내를 출력한다. 일반 네이티브 실행은 에이전트 지침 적용 여부에 의존한다.
- 자동으로 모든 스킬을 호출하지 않는다. 역할/작업에 필요한 스킬만 로드하고 실제 사용 증거와 설치를 구분한다.
'''
for rel in ['AGENTS.md','.opencode/agents/coordinator.md','.claude/agents/coordinator.md']:
    p=assets/rel
    s=p.read_text()
    if rel == '.opencode/agents/coordinator.md':
        assert '  edit: ask\n' in s
        s=s.replace('  edit: ask\n','''  edit:
    "*": deny
    "docs/product-specs/**": allow
    "docs/exec-plans/active/**": allow
    "docs/tasks/**": allow
''',1)
    p.write_text(s.rstrip()+'\n\n'+append_common)
(assets/'docs/STARTUP-DASHBOARD.md').write_text('''# 세션 시작 화면 (v0.7)

`teamdev startup`은 읽기 전용으로 단계/스킬, 미완료/완료 TASK, RTK/CRG 발견 상태를 표시합니다.
`teamdev launch opencode` 또는 `teamdev launch claude|codex`는 실행 전에 터미널 배너를 보여줍니다.
일반 `opencode` 등으로 시작하는 경우 Coordinator가 `teamdev startup`을 호출하도록 지침을 제공하지만 네이티브 첫 화면의 자동 출력은 보장하지 않습니다.

스킬 표시는 프로젝트 번들 설치 여부에 기반하며 실제 로딩/성공과 다릅니다. 전역 스킬은 별도 확인해야 합니다.
권한: Coordinator는 OpenCode `edit` 도구로 Spec/Plan/상태 경로만 수정하도록 제한합니다. Shell 명령 자동 허용은 별개이므로 임의 명령을 통제하는 완전한 경계가 아닙니다.
''')
readme=root/'README.md'
s=readme.read_text()
s='''# Team AI Dev Framework v0.7.0 — Runtime Startup Dashboard

## 첫 화면 / 신규 설치

```bash
python3 -m pip install -e .
mkdir -p ~/work/demo && cd ~/work/demo
teamdev init
teamdev doctor
teamdev startup
teamdev launch opencode  # 안내 화면 출력 후 OpenCode 시작
```

Claude Code: `teamdev launch claude` / Codex: `teamdev launch codex`.
기본 `opencode` 실행 시에는 Coordinator 지침이 시작 요약을 출력하도록 요청하지만, 화면에 표시되는 것을 기술적으로 강제하지는 않습니다.

기존 v0.6 프로젝트 업그레이드:
```bash
teamdev upgrade-startup          # 변경 미리보기
teamdev upgrade-startup --apply  # 백업 후 적용, 사용자 편집 정책 충돌 시 차단
teamdev startup
```

Coordinator의 OpenCode `edit` 권한은 `docs/product-specs/**`, `docs/exec-plans/active/**`, `docs/tasks/**` 범위만 허용하도록 변경합니다. Shell의 광범위한 실행 허용은 별도의 위험이며, 정책의 완전한 강제는 아닙니다.

주의: 단계별 스킬은 **발견/설치** 기준으로 표시하며 호출 성공을 뜻하지 않습니다. 네이티브 Worker 실제 실행과 RTK hook/CRG graph 최신성은 별도 확인해야 합니다.

---

'''+s
readme.write_text(s)
