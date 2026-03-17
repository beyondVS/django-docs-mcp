# 조사 보고서: 마크다운 코드 블록 보호 및 논리적 청킹 전략 (003-improve-markdown-chunking)

## 결정 사항 (Decisions)

### 1. 2단계 파이프라인 연결 전략
- **선택**: `MarkdownHeaderTextSplitter.split_text` → `MarkdownTextSplitter.split_documents`
- **근거**: `split_documents` 메서드를 사용하면 1단계에서 추출된 헤더 메타데이터가 2단계로 분할된 모든 하위 청크에 자동으로 상속됩니다. 이는 수동으로 메타데이터를 복사하는 로직을 제거하여 복잡도를 낮춥니다.

### 2. 하위 호환성 유지 및 데이터 순수성 (FR-004, FR-005)
- **선택**: `ChunkingService.split_markdown()`의 반환 타입(`list[dict]`)을 유지하되, `content` 필드에서 강제 텍스트 주입(Context:, Document:)을 제거합니다.
- **근거**: `IngestionService`가 이미 `metadata["header_context"]`를 참조하여 DB의 `Section`을 관리하고 있으므로, 인터페이스 변경 없이 내부 데이터 정제만으로 요구사항을 충족할 수 있습니다.

### 3. 코드 블록 보호 메커니즘
- **선택**: `MarkdownTextSplitter`의 기본 구분자(Separators) 활용 및 적정 `chunk_size` 설정.
- **근거**: `MarkdownTextSplitter`는 코드 블록 시작/종료 기호(`\n```\n`)를 분할 지점으로 인식하도록 설계되어 있어, 일반 `RecursiveCharacterTextSplitter`보다 코드 블록 내부 절단 확률이 현저히 낮습니다.

## 고려된 대안 (Alternatives Considered)

### 대안 1: 사용자 정의 토크나이저 기반 분할
- **평가**: 정합성은 높으나 프로젝트의 실용주의 원칙(헌법 I-1)에 따라 추가적인 라이브러리 의존성 및 복잡도 증가를 피하기 위해 거부되었습니다.
- **결정**: 문자 수 기반 분할(SYS-001)을 유지합니다.

### 대안 2: 본문 내 헤더 정보 유지
- **평가**: 검색 결과에서 문맥 확인이 용이할 수 있으나, 임베딩 모델의 노이즈가 될 수 있고 FR-005(데이터 순수성)에 위배됩니다.
- **결정**: 모든 컨텍스트 정보는 메타데이터로 이동시킵니다.

## 미해결 사항 (Open Questions / Needs Clarification)

- [x] **질문**: `chunk_size`를 2500자로 상향 조정 시 임베딩 모델(bge-m3)의 성능 저하 우려가 없는가?
    - **답변**: bge-m3는 최대 8192 토큰을 지원하므로 2500자(약 600~800 토큰)는 충분히 안전한 범위 내에 있습니다.
- [x] **질문**: 오버랩(`chunk_overlap`) 설정이 코드 블록 기호(```)를 중복 생성하여 마크다운 렌더링을 깨뜨릴 가능성은?
    - **답변**: `MarkdownTextSplitter`는 문장/블록 단위로 분할을 시도하므로, 오버랩 지점이 블록 중간일 경우에만 발생합니다. 적절한 구분자 우선순위 설정을 통해 이를 최소화합니다.
