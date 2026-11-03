# 작업 유형별 TDD 정책 (v0.9.0)

| 작업 유형 | 모드 | 검증 |
| --- | --- | --- |
| feature, bugfix, behavior_change, api, business_logic | required | RED 실패(의도한 원인), GREEN 통과, REFACTOR 검토 및 회귀 통과 |
| ui_visual | alternative | 시각·접근성 검증 결과 및 원본 로그 |
| configuration | alternative | 설정/스모크 검증 및 원본 로그 |
| refactoring | alternative | 회귀 검증 및 원본 로그 |
| documentation | exempt | 문서 검증(예: 링크/lint) 및 원본 로그 |

`teamdev new TASK "제목" --type bugfix` 또는 계획 승인 전 `teamdev tdd-set TASK --type bugfix --actor coordinator`.
유형은 계획 승인 시 고정됩니다. 누락되거나 변경된 정책/증거는 report/verify/completion에서 차단합니다.

Worker는 `docs/tasks/TASK/evidence/tdd-manifest.json` 및 모든 실행 로그를 report.evidence에 포함해야 합니다.

required 예시:
```json
{"task":"TASK-001","type":"feature","mode":"required","cycles":[{"red":{"command":"npm test","exit_code":1,"log":"red.log","expected_failure":"로그인 실패 케이스 미구현"},"green":{"command":"npm test","exit_code":0,"log":"green.log"},"refactor":{"command":"npm test","exit_code":0,"log":"refactor.log","review":"리팩터링 불필요 검토 완료"}}]}
```

alternative 예시:
```json
{"task":"TASK-002","type":"ui_visual","mode":"alternative","strategy":"visual_accessibility","rationale":"시각 변경은 스크린샷 및 접근성 검사로 검증","checks":[{"command":"npm run test:ui","exit_code":0,"log":"ui.log"}]}
```

exempt는 `mode: exempt`, `rationale`, `checks` 필요. `strategy`는 불필요합니다.
각 로그는 실제 실행에서 수집해야 합니다. 파일/해시 검사는 진짜 실행 여부를 증명하지 않으므로 독립 검증 및 CI를 유지합니다.
