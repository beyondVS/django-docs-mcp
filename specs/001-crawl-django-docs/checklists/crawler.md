# 요구사항 품질 체크리스트: Django Cookbook Crawler

**목적**: 크롤러 요구사항의 완전성, 명확성 및 데이터 품질 검증 (에이전트 자가 검증용)
**생성일**: 2026-03-15
**기능**: [Django 관련 문서 RAG 데이터 소스 크롤링](../spec.md)

## 요구사항 완전성 (Completeness)

- [ ] CHK001 - 모든 일반적인 네트워크 예외 상황(Timeout, Connection Refused 등)에 대한 처리 및 로깅 요구사항이 정의되었습니까? [완전성, Spec §FR-008]
- [ ] CHK002 - 수집 성공, 실패 및 재시도 횟수를 포함한 실행 결과 요약 리포트 형식이 명시되었습니까? [공백]
- [ ] CHK003 - YAML Front Matter에 포함될 필수 필드(`source_url`, `target_version`, `collected_at`)가 모두 정의되었습니까? [완전성, Spec §FR-004]

## 요구사항 명확성 (Clarity)

- [ ] CHK004 - "파이썬 코드 블록 보존"이 들여쓰기, 주석, 빈 줄 유지를 포함하는 것으로 구체적으로 정의되었습니까? [명확성, Spec §FR-007, Q2-B 반영]
- [ ] CHK005 - 메타데이터의 `collected_at` 필드에 대한 표준 시간대(예: UTC) 및 ISO 8601 규격이 명시되었습니까? [명확성, Data Model §2]
- [ ] CHK006 - 수집 대상 도메인을 벗어나는 외부 링크(Out-of-bound)에 대한 무시 정책이 명확하게 서술되었습니까? [명확성, Spec §FR-008]

## 요구사항 일관성 (Consistency)

- [ ] CHK007 - `orm_cookbook.py`가 공통 유틸리티(`utils/`)를 사용하여 설계된 데이터 저장 구조를 엄격히 따르고 있습니까? [일관성, Plan §Project Structure]
- [ ] CHK008 - YAML Front Matter의 필드명이 데이터 모델과 명세서 간에 충돌 없이 정렬되었습니까? [일관성, Spec vs Data Model]

## 수락 기준 품질 (Success Criteria)

- [ ] CHK009 - "코드 블록 손상 없음(95% 이상)"이라는 성공 기준을 객관적으로 검증할 수 있는 샘플링 검사 기준이 명시되었습니까? [측정 가능성, Spec §SC-002]
- [ ] CHK010 - "단일 명령으로 전체 워크플로우 완료" 기준에 오류 발생 시의 리포트 생성 완료 시점이 포함되었습니까? [명확성, Spec §SC-004]

## 시나리오 커버리지 (Coverage)

- [ ] CHK011 - 서버에서 본문 내용이 없는 빈 페이지(404가 아닌 정상 응답이나 비어있는 경우)를 반환할 때의 처리 요구사항이 있습니까? [커버리지, 예외 케이스]
- [ ] CHK012 - 차후 피드백 반영을 위해 수집된 데이터의 품질을 기록하고 보고하는 "사후 검토(Post-Crawl Review)" 시나리오가 요구사항에 포함되었습니까? [공백, Q3 답변 반영]

## 종속성 및 가정 (Dependencies & Assumptions)

- [ ] CHK013 - Python 3.14 환경에서 `lxml` 및 `readability-lxml` 빌드 실패 시의 대체 의존성 또는 빌드 환경 가정이 문서화되었습니까? [가정, Plan §Technical Context]
- [ ] CHK014 - 대상 사이트(Agiliq)의 정적 HTML 구조가 크롤링 도중 변경되지 않는다는 가정이 명시되었습니까? [가정]
