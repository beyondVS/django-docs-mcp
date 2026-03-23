# 기술 조사 (Research)

## 1. 부분 클론(Sparse Checkout)을 통한 특정 폴더(`docs`) 다운로드 방식

- **결정(Decision)**: Git의 `sparse-checkout` 기능을 사용하여 `stable/5.2.x` 브랜치의 `docs/` 디렉터리만 `.temp/django_src`에 클론합니다.
- **근거(Rationale)**: 전체 Django 저장소를 클론하는 것은 시간과 디스크 공간을 낭비합니다. `sparse-checkout`을 활용하면 문서 폴더만 효율적으로 가져올 수 있어 CI/CD 및 로컬 실행 속도가 향상됩니다.
- **고려된 대안(Alternatives considered)**: 
  - `git clone --depth 1`: 전체 트리를 가져오지 않아 빠르지만, 여전히 불필요한 코드 소스가 포함됩니다.
  - GitHub API 또는 원시(Raw) 파일 다운로드: 개별 파일마다 요청이 발생해 속도 제한(Rate Limit)에 걸릴 위험이 큽니다.

## 2. `docutils`를 활용한 RST -> Markdown 변환

- **결정(Decision)**: `docutils`의 파서를 사용하여 RST를 분석하고, 파이썬 생태계에 존재하는 마크다운 Writer (예: `docutils` 기본 지원 또는 추가 구현)를 통해 변환합니다. 변환 과정에서 마크다운 포맷팅 정제가 필요한 경우 정규식이나 `markdownify` 등을 보조적으로 활용합니다.
- **근거(Rationale)**: RST는 표준 파서인 `docutils`를 사용해야 구조가 깨지지 않고 정확한 파싱이 가능합니다. 외부 시스템 의존성(Pandoc 등)을 피하고 파이썬 라이브러리만으로 처리하기 위함입니다.
- **고려된 대안(Alternatives considered)**:
  - `pypandoc`: 가장 깔끔한 마크다운을 생성하지만 시스템에 Pandoc이 설치되어 있어야 하므로 컨테이너/개발 환경 구성이 복잡해집니다.
  - 직접 정규식 처리: RST 문법이 방대하여 엣지 케이스 처리가 불가능합니다.
