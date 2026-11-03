# 자가개선 승인 및 반영 정책 (v0.18.2)

## 목적
에이전트는 반복 오류, 누락된 규칙, 비효율, 설계 충돌 등의 개선을 **제안**할 수 있다. 발견했다는 이유만으로 AGENTS.md, 에이전트/스킬/도구 설정, .ai-dev 정책, 기존 프로젝트 규칙을 직접 변경하거나 활성화해서는 안 된다.

## 두 번의 사용자 승인
1. ANALYZE: 관찰 사실/재현 로그, 근본 원인, 기존 정책과 중복·충돌 여부를 기록한다. 무분별한 개선 후보 양산 금지.
2. PLAN: 변경 전/후, 범위, 대상 정본 경로(정확한 상대 경로를 Plan 목록 `- AGENTS.md` 형식으로 기록), 위험, 검증/회귀/롤백, 예상 영향 명시. `teamdev plan-ready TASK --actor coordinator` 후 **사용자 계획 승인** 없이는 구현 금지.
3. IMPLEMENT: 승인된 Plan에 목록으로 기록된 경로에 한해, **승인 후 파견된 IMPLEMENT 단계에서 격리된 작업공간**의 개선안만 작성한다. 정본에 바로 덮어쓰지 않는다. `teamdev improve-stage TASK --target AGENTS.md --file /path/to/staged.md` 등으로 스테이징한다.
4. VERIFY: 별도 검증자가 실행 결과와 기존 게이트/회귀/권한 정책의 영향을 확인하고 원본 증거를 기록한다.
5. REVIEW: 별도 리뷰어가 지침 중복/순환 참조/정본 충돌/보안 영향/CLI 동작 일치 여부를 검토한다.
6. 최종 승인: `teamdev approve TASK --scope completion --actor USER --confirm APPROVE`는 기존 workflow의 최종 사용자 승인 단계이며, 실제 정본 반영을 의미하지 않는다.
7. **정식 반영:** `teamdev improve-check TASK`, `teamdev improve-apply TASK` 미리보기 후 사람의 반영 확인 `teamdev improve-apply TASK --actor USER --confirm APPLY --apply`를 실행한다. 대상 정본 해시가 달라졌거나 증거가 부족하면 차단한다. 백업과 이력 보존.

## 보장과 한계
- `teamdev improve-propose TASK "제목" --problem "문제 재현 설명 ..."`은 `docs/agent-improvements/candidates/TASK/`와 기존 Spec/Plan/TASK를 생성한다. 실제 정책 반영 없음.
- `improve-stage`는 계획 승인 후만 허용되며 승인된 범위를 준수해야 한다. 승인 대상 및 변경 내용의 정합성은 독립 검토 대상으로 남는다.
- 완료 후에도 자동 반영하지 않는다. 반영 명령은 `COMPLETED`/계획·최종 승인/검증·리뷰/스테이징 내용 및 대상 원본 SHA-256 확인 필요.
- 기존 설계 문서와 참고자료를 참조할 때 `docs/DOCUMENT-SOURCES.md` 적용. 새 규칙은 해당 작업과 관련된 정본 문서에만 위치시킨다. AGENTS.md에는 광범위한 공통 불변 원칙만 둔다.
- CLI의 `--actor` 및 `--confirm`은 **사용자 인증 수단이 아니다**. 실제 사용자 승인 주체는 Orca/팀 운영 규칙에서 별도로 확인해야 한다. 직접 파일 편집·bash 우회는 CLI가 방지할 수 없으므로 별도 접근 제어가 필요하다.
- 승인된 개선 스테이징을 되돌리기 위한 원본은 후보별 `backups/`에 보존한다. 변경 결과는 별도 빌드/검증을 거쳐 배포해야 한다.
