# Gemini Context

## 1. 전역 지침 참조 (필수)
작업 시작 전, 다음 공통 문서들을 반드시 읽고 컨텍스트를 확보하십시오.
1. **원칙 및 표준:** [.specify/memory/constitution.md](.specify/memory/constitution.md)
2. **에이전트 역할 및 지침:** [AGENTS.md](AGENTS.md)

## 2. 우선순위 및 Gemini 특화 규칙
- **우선순위:** `constitution.md` > `AGENTS.md` > `GEMINI.md`
- **커스텀 커맨드:** 프로젝트 설계 및 구현 워크플로우를 위해 `.gemini/commands/speckit.*.toml` 명령어를 적극 활용하십시오.
- **컨텍스트 최적화:** `data_sources/` 디렉터리에는 대량의 데이터가 포함될 수 있습니다. 전체 프로젝트 대상 검색(`grep`, `glob`) 시 불필요한 토큰 낭비를 막기 위해 이 폴더는 가급적 검색 대상에서 제외하고, 테스트 데이터 생성 등 **필요한 경우에만 특정 파일을 명시적으로 지정하여 읽으십시오.**
