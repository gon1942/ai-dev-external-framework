# 외부 원본 스킬 안내 (필요 시 설치)

원본 출처:
- Matt Pocock: https://github.com/mattpocock/skills
- Superpowers: https://github.com/obra/superpowers
- Ponytail: https://github.com/DietrichGebert/ponytail

대표적인 단계별 적용 예시(실제 활성 배정은 `.ai-dev/stage-skills.json` 참조):

- **분석(Analyze):** `grill-with-docs`, `diagnosing-bugs`, `systematic-debugging`, `brainstorming`
- **계획(Plan):** `to-spec`, `to-tickets`, `writing-plans`
- **구현(Implement):** `implement`, `implement-spec`, `test-driven-development`, `using-git-worktrees`, `subagent-driven-development`, `ponytail`(최소 구현 지침)
- **검증(Verify):** `verification-before-completion`
- **리뷰(Review):** `code-review`, `requesting-code-review`, `receiving-code-review`, `retro`

**주의:** 원본 스킬에 따라 추가 기능·플러그인·이슈 추적 도구·하위 에이전트가 필요할 수 있다. 이 패키지는 원본 스킬 디렉터리만 설치한다. Ponytail의 호스트 전용 플러그인 활성화, 모드 전환, 수명주기 훅은 설치하지 않는다. 완전한 Ponytail 기능이 필요하면 README에 안내된 공식 호스트 플러그인 설치 절차를 따른다. 하위 에이전트나 백그라운드 실행이 지원되지 않으면 사용 불가로 보고하고 순차 실행으로 대체한다. 이 패키지는 CRG 자체를 설치하거나 수정하지 않는다.
