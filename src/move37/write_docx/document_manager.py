"""Document manager for wiki/docx hierarchy operations."""

from __future__ import annotations

import logging

from .errors import DocumentOperationError, FeishuAPIError, NetworkError
from .feishu_client import FeishuAPIClient

LOGGER = logging.getLogger(__name__)


class DocumentManager:
    """Manage main and sub documents in Feishu wiki."""

    def __init__(self, feishu_client: FeishuAPIClient, space_id: str) -> None:
        self.feishu_client = feishu_client
        self.space_id = str(space_id).strip()

    def create_main_document(self, title: str, parent_node_token: str) -> str:
        """Create target-date main document under configured parent node."""
        try:
            return self.feishu_client.create_wiki_node(
                space_id=self.space_id,
                parent_node_token=parent_node_token,
                title=title,
            )
        except (FeishuAPIError, NetworkError) as exc:
            raise DocumentOperationError(f"Failed to create main document `{title}`: {exc}") from exc

    def create_sub_document(
        self,
        parent_node_token: str,
        title: str,
        content: str = "",
    ) -> str:
        """Create a sub-document and optionally write content."""
        try:
            doc_token = self.feishu_client.create_wiki_node(
                space_id=self.space_id,
                parent_node_token=parent_node_token,
                title=title,
            )
            if content:
                self.feishu_client.write_document_content(doc_token, content)
            return doc_token
        except (FeishuAPIError, NetworkError) as exc:
            raise DocumentOperationError(f"Failed to create sub document `{title}`: {exc}") from exc

    def write_document_content(self, document_token: str, content: str) -> None:
        """Write document content with unified error mapping."""
        try:
            self.feishu_client.write_document_content(document_token, content)
        except (FeishuAPIError, NetworkError) as exc:
            raise DocumentOperationError(
                f"Failed to write content to document `{document_token}`: {exc}"
            ) from exc

    @staticmethod
    def build_document_url(document_token: str) -> str:
        """Build a user-facing URL for a document token."""
        return FeishuAPIClient.build_doc_url(document_token)
