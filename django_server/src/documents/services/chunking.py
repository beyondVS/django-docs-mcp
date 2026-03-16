from typing import Any

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


class ChunkingService:
    """
    마크다운 문서를 헤더 기반으로 분할하고, 청킹(Chunking)을 수행하는 서비스 클래스.

    헤더(H1~H3) 계층을 인식하여 문맥을 유지하며,
    코드 블록을 최대한 보존하면서 지정된 크기로 문서를 분할합니다.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 80):
        """
        ChunkingService를 초기화합니다.

        Args:
            chunk_size (int): 개별 청크의 최대 문자 길이. 기본값 800.
            chunk_overlap (int): 청크 간 중첩되는 문자 길이. 기본값 80.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 분할 기준 헤더 설정
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on, strip_headers=False
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def split_markdown(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        마크다운 텍스트를 헤더와 크기 기준으로 분할합니다.

        코드 블록이 중간에 끊기지 않도록 최대한 시도하며,
        각 청크의 상단에 문서 제목 및 헤더 경로 정보를 주입하여 문맥을 보존합니다.

        Args:
            text (str): 분할할 전체 마크다운 텍스트.
            metadata (Optional[Dict[str, Any]]): 문서 제목 등 추가 메타데이터.

        Returns:
            list[dict[str, Any]]: 분할된 청크 데이터 리스트.
                각 요소는 'content'와 'metadata'를 포함합니다.
        """
        if metadata is None:
            metadata = {}

        # 1. 헤더 기반 1차 분할
        sections = self.header_splitter.split_text(text)

        chunks = []
        for section in sections:
            # 헤더 계층 구조를 문맥 문자열로 결합 (예: H1 > H2 > H3)
            header_context = " > ".join(
                [
                    section.metadata.get(h, "")
                    for _, h in self.headers_to_split_on
                    if h in section.metadata
                ]
            )

            # 2. 섹션이 너무 클 경우 추가 분할
            sub_chunks = self._split_preserving_code_blocks(section.page_content)

            for i, content in enumerate(sub_chunks):
                # 청크 상단에 문서/헤더 컨텍스트 정보 주입
                full_content = content
                if header_context:
                    full_content = f"Context: {header_context}\n\n{content}"
                if metadata.get("title"):
                    full_content = f"Document: {metadata['title']}\n{full_content}"

                chunks.append(
                    {
                        "content": full_content,
                        "metadata": {
                            **section.metadata,
                            "header_context": header_context,
                            "chunk_index": i,
                            "token_count": len(full_content.split()),  # 대략적인 토큰 수 추정
                        },
                    }
                )

        return chunks

    def _split_preserving_code_blocks(self, text: str) -> list[str]:
        """
        코드 블록을 최대한 유지하면서 텍스트를 분할합니다.

        Args:
            text (str): 분할할 텍스트.

        Returns:
            List[str]: 분할된 하위 텍스트 리스트.
        """
        # 줄바꿈을 존중하는 RecursiveCharacterTextSplitter 사용
        return self.text_splitter.split_text(text)


def get_chunking_service() -> ChunkingService:
    """
    ChunkingService 인스턴스를 가져오는 헬퍼 함수.

    Returns:
        ChunkingService: 초기화된 청킹 서비스.
    """
    return ChunkingService()
