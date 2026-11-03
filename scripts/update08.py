"""v0.8.0 template changes; repeatable on a clean v0.7.0 asset bundle."""
from pathlib import Path
p=Path(__file__).resolve().parent.parent/'src/teamdev/assets'
append='''## Runtime Audit and Skill Evidence (v0.8)
- 새 세션 시작 시 `teamdev --root . startup`과 필요 시 `teamdev --root . audit` 실행. 설정/스킬 파일/추천 스킬을 구분해 출력한다.
- `teamdev audit --strict`는 설정 누락 시 실패한다. 그러나 실제 LLM Worker 파견이나 스킬 로드의 E2E 증거를 대체하지 않는다.
- Worker가 네이티브 스킬을 호출한 근거를 원본 파일로 저장한 경우에 한해 `teamdev skill-record TASK --skill NAME --role ROLE --session-id SESSION --evidence FILE` 사용. 단, 이 기록은 에이전트 신고이며 독립 검증된 자동 후킹 기록이 아니다.
- 네이티브 도구 호출 증거가 없으면 `NOT_VERIFIED` 그대로 보고하고 추측하지 않는다.
- 외부 스킬은 실제 파일이 확인되어도 자동 로드된 것으로 간주하지 않는다. RTK 훅과 CRG graph.db 최신성도 각각 검증 전 상태를 유지한다.
- 작업 시작 전 `teamdev new` 실행. 계획 승인 전 소스 구현 금지. 승인 후 실제 native task 호출 및 반환 증거를 확보한다.
- 일반 shell 권한 허용과 사용자 계획/완료 승인은 별개의 정책이다. 도구 권한 설정을 승인 증거로 사용하지 않는다.
'''
for rel in ('AGENTS.md','.opencode/agents/coordinator.md','.claude/agents/coordinator.md'):
 f=p/rel
 t=f.read_text()
 if '## Runtime Audit and Skill Evidence (v0.8)' not in t:
  f.write_text(t.rstrip()+'\n\n'+append)
f=p/'docs/RUNTIME-AUDIT.md'
f.write_text('''# 프레임워크 종합 운영 진단 (v0.8)

## 기본 확인

```sh
teamdev startup
teamdev audit
teamdev audit --json
teamdev audit --strict
```

- `PASS`: 로컬 설정 파일 검사를 통과함. **실제 에이전트 실행 성공이 아님**.
- `CONFIG_ONLY`: 역할 설정 파일은 있으나 Worker 호출 여부 미검증.
- `NOT_VERIFIED`: 에이전트 세션의 네이티브 스킬 로드·실제 호출을 확인할 수 없음.
- 외부 선택 스킬: 프로젝트와 알려진 사용자별 스킬 디렉터리에서 `SKILL.md` 존재 여부만 확인. 설치 여부를 모르면 추측하지 않음.
- `RTK`: CLI 존재와 훅 적용은 다름. `CRG`: CLI, graph.db 존재, graph freshness는 세 가지 별개.

## 실행 근거 보존

Worker/Coordinator가 실제 도구 호출 출력 파일을 `docs/tasks/TASK/evidence/`에 남겼다면:

```sh
teamdev skill-record TASK-001 --skill code-graph-analysis --role coordinator --session-id sess-1 --evidence skill-call.log
teamdev skill-events TASK-001
```

이벤트는 파일 SHA-256 및 역할·단계·세션을 기록하지만 **에이전트 신고값**이다. 네이티브 런타임의 스킬 도구를 자동 감청하거나 실행 성공을 증명하지 않는다. 민감정보를 증거 파일에 저장하지 않는다.

## 실제 E2E 수락 기준

1. OpenCode/Claude/Codex별 첫 세션에서 Coordinator 정책 적용을 실제 확인
2. `teamdev new` → Spec/Plan → 승인 전 파견 차단 검증
3. 인간이 계획 승인한 뒤 Implementer 네이티브 호출과 반환 확인
4. 별도 Verifier, Reviewer 호출 + 원본 검증 로그 확인
5. 최종 인간 승인 후 active → completed 자동 아카이브 확인
6. Session Rotation 시 이전 Worker 종료 후 동일 TASK/worktree에서 새 세션 재개
7. RTK 자동 훅·CRG 그래프 최신성은 각 사용 환경에서 실제 확인

이 항목들은 로컬 단위 테스트만으로 PASS로 표시하지 않는다.
''',encoding='utf-8')
print('Templates updated')
