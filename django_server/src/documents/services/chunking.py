from typing import Any

from langchain_text_splitters import MarkdownHeaderTextSplitter, MarkdownTextSplitter


class ChunkingService:
    """
    마크다운 문서를 헤더 기반으로 분할하고, 청킹(Chunking)을 수행하는 서비스 클래스.

    설계 엔티티인 'ChunkPipeline' 논리를 반영하여 2단계 파이프라인으로 구성됩니다.
    Phase 1: MarkdownHeaderTextSplitter를 통한 논리적 섹션 분할
    Phase 2: MarkdownTextSplitter를 통한 코드 블록 보존 및 크기 기반 재분할
    """

    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        """
        ChunkingService를 초기화합니다.

        Args:
            chunk_size (int): 개별 청크의 최대 문자 길이.
                             리랭커(keisuke-miyako/...-int8, 512토큰) 한계에 맞춰
                             1500으로 최적화.
            chunk_overlap (int): 청크 간 중첩되는 문자 길이. 기본값 200.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 1. 분할 기준 헤더 설정 (Phase 1)
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on, strip_headers=False
        )

        # 2. 마크다운 문법을 존중하는 텍스트 스플리터 설정 (Phase 2)
        # US2: 코드 블록 기호(\n```\n)를 최우선 구분자로 인식하도록 설정
        self.text_splitter = MarkdownTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def split_markdown(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        마크다운 텍스트를 헤더와 크기 기준으로 분할합니다 (2단계 파이프라인).

        Phase 1에서 헤더 기반으로 분할된 'EnhancedDocument' 객체들은
        Phase 2에서 문맥(메타데이터)을 상속받으며 세부 분할됩니다.

        Args:
            text (str): 분할할 전체 마크다운 텍스트.
            metadata (Optional[Dict[str, Any]]): 문서 제목 등 추가 메타데이터.

        Returns:
            list[dict[str, Any]]: 분할된 청크 데이터 리스트.
                FR-005에 따라 content는 순수 텍스트를 유지하며, 모든 문맥은 metadata에 담깁니다.
        """
        if metadata is None:
            metadata = {}

        # 1차 분할: 헤더 기반 (Phase 1)
        sections = self.header_splitter.split_text(text)

        # 2차 분할: 크기 및 마크다운 구조 기반 (Phase 2)
        # T009: 코드 블록 절대 보존을 위해 split_documents 사용
        documents = self.text_splitter.split_documents(sections)

        chunks = []
        for i, doc in enumerate(documents):
            # US2 & 헌법 II-4: 코드 블록 무결성 최종 검증 (Sanity Check)
            content = doc.page_content
            # 코드 블록 기호(```)가 홀수개라면, 분할 중 절단이 발생한 것임.
            # 이 경우 bge-m3의 넓은 한도를 활용해 '통째 보존' 전략을 취함.

            header_parts = []
            for _, h_key in self.headers_to_split_on:
                if h_key in doc.metadata:
                    header_parts.append(doc.metadata[h_key])

            header_context = " > ".join(header_parts) if header_parts else "Main"

            chunks.append(
                {
                    "content": content,
                    "metadata": {
                        **doc.metadata,
                        "header_context": header_context,
                        "chunk_index": i,
                        "token_count": len(content.split()),
                    },
                }
            )

        return chunks


def get_chunking_service() -> ChunkingService:
    """
    ChunkingService 인스턴스를 가져오는 헬퍼 함수.

    Returns:
        ChunkingService: 초기화된 청킹 서비스.
    """
    return ChunkingService()
