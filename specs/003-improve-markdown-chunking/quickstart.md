# 퀵스타트 가이드: 마크다운 논리적 청킹 (003-improve-markdown-chunking)

## 개요
이 가이드는 `langchain-text-splitters`를 활용한 새로운 2단계 청킹 파이프라인을 적용하고 검증하는 방법을 설명합니다.

## 개발 준비 (Setup)

1. **의존성 확인**: `langchain-text-splitters` 패키지가 설치되어 있는지 확인합니다.
   ```bash
   uv pip list | grep langchain-text-splitters
   ```

2. **환경 설정**: `chunk_size` 기본값이 요구사항(SYS-001)에 맞게 설정되었는지 확인합니다 (기본 2500자).

## 테스트 방법 (Testing)

### 1. 단위 테스트 실행 (추천)
새로운 청킹 로직을 검증하기 위한 전용 테스트를 실행합니다.
```bash
cd django_server
uv run pytest tests/test_chunking.py
```

### 2. 코드 블록 보호 검증
테스트 시나리오에는 반드시 다음과 같은 긴 코드 블록이 포함되어야 합니다:
- **Given**: 3000자 이상의 파이썬 코드 블록이 포함된 마크다운.
- **When**: `ChunkingService.split_markdown()` 실행.
- **Then**: 결과 청크 내에서 코드 블록 시작(` ```python `)과 종료(` ``` `)가 짝을 이루는지 확인.

## 주요 변경 사항 요약 (Key Changes)

| 대상 | 기존 방식 | 변경 방식 |
|------|-----------|-----------|
| **Splitter 2단계** | `RecursiveCharacterTextSplitter` | `MarkdownTextSplitter` |
| **데이터 순수성** | `content`에 헤더 텍스트 주입 | `content`는 순수 마크다운만 포함 |
| **메타데이터** | 수동 복사 및 관리 | `split_documents`를 통한 자동 상속 |
| **크기 제한** | 1000자 | 2500자 (bge-m3 최적화) |

## 트러블슈팅

- **헤더 계층이 누락됨**: `MarkdownHeaderTextSplitter`의 `headers_to_split_on` 설정을 확인하십시오.
- **코드 블록이 잘림**: `chunk_size`가 너무 작거나, 코드 블록 내부의 빈 줄이 너무 많아 `MarkdownTextSplitter`가 분할 지점으로 오인했을 수 있습니다. 구분자(Separators) 설정을 점검하십시오.
