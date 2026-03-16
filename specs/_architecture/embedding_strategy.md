# 데이터 청킹 및 임베딩 전략서 (Chunking & Embedding Spec)

문서를 벡터화하여 데이터베이스에 저장하기 위한 전략과 규칙을 정의하며, 현재 `django_server`에 구현된 방식입니다.

## 1. 임베딩 모델

*   **모델 명:** BAAI/bge-m3
*   **특징:** 다국어 처리에 특화되어 있으며(한국어 질의 -> 영어 문서 검색 성능 탁월), 1024 차원의 벡터를 생성합니다.
*   **인프라 가속**: GPU(CUDA)가 사용 가능한 경우 자동으로 감지하여 가속을 활용합니다.

## 2. 청킹 및 문맥 유지 전략

단순 글자 수가 아닌, 의미가 유지되는 계층 구조 기반의 청킹을 수행합니다.

### 2.1 헤더 기반 분할
*   **MarkdownHeaderTextSplitter**: 마크다운 헤더(H1, H2, H3)를 기준으로 문서를 1차 분할합니다.
*   **계층 문맥 주입**: 각 분할된 섹션의 상단에 해당 섹션의 헤더 경로(예: `Context: Introduction > Section 1`)를 주입하여, 청크 자체만으로도 전체 문서 내 위치를 파악할 수 있도록 합니다.

### 2.2 재귀적 분할 (Recursive Splitting)
*   **Target Size**: 개별 청크의 크기는 약 800 문자(Character) 내외로 유지합니다.
*   **Overlap**: 청크 간 문맥 단절을 방지하기 위해 80 문자 내외의 중첩(Overlap) 구간을 허용합니다.
*   **코드 블록 보호**: `RecursiveCharacterTextSplitter`를 활용하여 줄바꿈(Newlines)과 공백을 존중하며 분할함으로써 코드 블록 중간이 잘리는 현상을 최소화합니다.

### 2.3 문서 메타데이터 주입
*   각 청크의 가장 상단에 문서 전체의 제목을 주입(예: `Document: Django ORM Cookbook`)하여 RAG 검색 시 모델이 전체 문서 맥락을 인지하도록 보강합니다.

## 3. 소스별 전략 및 처리 프로세스

*   **파일 파싱**: `python-frontmatter`를 사용하여 YAML Front Matter(버전, 카테고리 등)를 추출합니다.
*   **Upsert 로직**: `source_path`와 `target_version`을 기준으로 기존 적재 내역이 있으면 삭제 후 재생성함으로써 데이터 중복을 방지합니다.
*   **트랜잭션 관리**: 개별 파일 단위로 `transaction.atomic`을 적용하여, 적재 중 에러 발생 시 데이터 정합성을 보장(Rollback)합니다.
