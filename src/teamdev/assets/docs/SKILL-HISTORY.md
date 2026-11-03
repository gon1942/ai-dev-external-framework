# 단계별 스킬 사용 기록

`teamdev skill-history`는 `docs/tasks/TASK-ID/skill-events.json`을 모아 단계별로 보여줍니다.
스킬 호출 이후 TASK evidence/에 호출 근거를 저장하고 `teamdev skill-record TASK-ID --skill SKILL --role ROLE --session-id SID --evidence logs/call.log`로 기록합니다.
기록은 호출 신고 및 증거 파일의 SHA-256 무결성 확인이며 도구 내부 로드를 독립적으로 증명하지 않습니다.
`teamdev session-summary`는 전체 TASK/단계/상태/사용자 조치/다음 실행/Worker 관측 상태를 출력합니다.
