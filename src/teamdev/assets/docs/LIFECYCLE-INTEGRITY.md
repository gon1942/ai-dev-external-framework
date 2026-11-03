# 작업 정본 및 아카이브 무결성

**정본 경로:** Spec은 `docs/product-specs/TASK-ID.md`, 실행 상태·최종 승인·증거는 `docs/tasks/TASK-ID/`에 고정합니다.

Plan은 작업 중 `docs/exec-plans/active/TASK-ID/`에 두고, **사용자 최종 승인** 이후 실행 계획 디렉터리 전체를 `docs/exec-plans/completed/TASK-ID/`로 이동합니다. 다른 폴더를 임의 이동하지 않습니다.

## 검증 명령

```bash
teamdev lifecycle-check
teamdev lifecycle-check --strict
teamdev lifecycle-check --json
teamdev session-summary
teamdev audit --strict
```

검사는 읽기 전용입니다. Plan 중복, 파일 누락, 작업 ID 불일치, 완료 승인 누락, 승인 후 Spec·Plan 변경, 완료 상태와 Plan 위치 불일치를 오류로 표시합니다. `--strict`는 오류 발견 시 종료코드 2를 반환합니다. `teamdev next` 역시 불일치 시 다음 작업을 중단합니다.

구버전에서 승인 완료되었으나 `active/`에 Plan이 남아 있는 경우 **검토 후** 다음을 실행합니다.

```bash
teamdev archive-completed TASK-ID
teamdev archive-completed TASK-ID --apply
```

이 도구의 검사는 로컬 파일 일치성만 확인합니다. 최종 승인자의 신원이나 실제 테스트 실행 여부까지 입증하지는 않습니다. 두 개 이상의 컴퓨터가 공유 저장소를 수정하는 경우 단일 호스트 파일 잠금만으로 동시성 안전성을 보장할 수 없습니다.
