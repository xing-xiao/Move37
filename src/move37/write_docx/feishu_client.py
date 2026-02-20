"""Feishu API client for wiki node creation and docx block writing."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import requests

from .errors import FeishuAPIError, NetworkError

LOGGER = logging.getLogger(__name__)

WIKI_NODE_CREATE_DOC_URL = (
    "https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create"
)
DOCUMENT_BLOCK_CREATE_DOC_URL = (
    "https://open.feishu.cn/document/docs/docs/document-block/create-2"
)


def _backoff_seconds(attempt: int) -> float:
    return min(8.0, float(2**attempt))


class FeishuAPIClient:
    """Feishu client with app auth, retry, and wiki/docx APIs."""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        base_url: str = "https://open.feishu.cn",
    ) -> None:
        self.app_id = app_id.strip()
        self.app_secret = app_secret.strip()
        self.timeout = float(timeout)
        self.max_retries = max(1, int(max_retries))
        self.base_url = base_url.strip().rstrip("/") or "https://open.feishu.cn"
        self._tenant_access_token: Optional[str] = None

    def _post_json(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        last_error: Optional[str] = None

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                last_error = f"HTTP request failed: {exc}"
                if attempt == self.max_retries - 1:
                    raise NetworkError(last_error) from exc

                delay = _backoff_seconds(attempt)
                LOGGER.warning(
                    "Feishu HTTP request failed (attempt %s/%s), retry in %.1fs, error=%s",
                    attempt + 1,
                    self.max_retries,
                    delay,
                    exc,
                )
                time.sleep(delay)
                continue

            try:
                response_payload = response.json()
            except ValueError as exc:
                raise FeishuAPIError(
                    f"Feishu API returned non-JSON response (status={response.status_code})."
                ) from exc

            if not isinstance(response_payload, dict):
                raise FeishuAPIError("Feishu API response payload is not a dictionary.")

            code = int(response_payload.get("code", -1))
            if code != 0:
                msg = str(response_payload.get("msg", "")).strip()
                request_id = str(response_payload.get("request_id", "")).strip()
                raise FeishuAPIError(
                    f"Feishu API error: code={code}, msg={msg}, request_id={request_id}"
                )

            return response_payload

        raise NetworkError(last_error or "Unknown HTTP error")

    def _get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        last_error: Optional[str] = None

        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                last_error = f"HTTP request failed: {exc}"
                if attempt == self.max_retries - 1:
                    raise NetworkError(last_error) from exc

                delay = _backoff_seconds(attempt)
                LOGGER.warning(
                    "Feishu HTTP request failed (attempt %s/%s), retry in %.1fs, error=%s",
                    attempt + 1,
                    self.max_retries,
                    delay,
                    exc,
                )
                time.sleep(delay)
                continue

            try:
                response_payload = response.json()
            except ValueError as exc:
                raise FeishuAPIError(
                    f"Feishu API returned non-JSON response (status={response.status_code})."
                ) from exc

            if not isinstance(response_payload, dict):
                raise FeishuAPIError("Feishu API response payload is not a dictionary.")

            code = int(response_payload.get("code", -1))
            if code != 0:
                msg = str(response_payload.get("msg", "")).strip()
                request_id = str(response_payload.get("request_id", "")).strip()
                raise FeishuAPIError(
                    f"Feishu API error: code={code}, msg={msg}, request_id={request_id}"
                )

            return response_payload

        raise NetworkError(last_error or "Unknown HTTP error")

    def get_tenant_access_token(self, force_refresh: bool = False) -> str:
        """Get tenant access token with in-memory cache."""
        if self._tenant_access_token and not force_refresh:
            return self._tenant_access_token

        auth_url = f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        response_payload = self._post_json(auth_url, payload)

        token = str(response_payload.get("tenant_access_token") or "").strip()
        if not token:
            raise FeishuAPIError("Feishu auth response missing tenant_access_token.")

        self._tenant_access_token = token
        return token

    def _auth_headers(self) -> Dict[str, str]:
        token = self.get_tenant_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def create_wiki_node(
        self,
        space_id: str,
        parent_node_token: str,
        title: str,
    ) -> str:
        """Create a wiki node (docx) under given space/parent node."""
        create_url = f"{self.base_url}/open-apis/wiki/v2/spaces/{space_id}/nodes"
        parent_token = str(parent_node_token or "").strip()
        payload = {
            "parent_node_token": parent_token,
            "node_type": "origin",
            "obj_type": "docx",
            "title": title,
        }
        headers = self._auth_headers()

        try:
            response_payload = self._post_json(create_url, payload, headers=headers)
        except FeishuAPIError as exc:
            message = str(exc)
            should_try_resolve = (
                ("code=10003" in message or "code=131002" in message)
                and parent_token
                and not parent_token.startswith("wik")
            )
            if not should_try_resolve:
                raise FeishuAPIError(
                    f"{message}. Hint: FEISHU_WIKI_PARENT_NODE_TOKEN must be a wiki node token "
                    "under FEISHU_WIKI_SPACE_ID."
                ) from exc

            try:
                resolved_node_token = self.resolve_wiki_node_token(parent_token)
            except (FeishuAPIError, NetworkError) as resolve_exc:
                raise FeishuAPIError(
                    f"{message}. Also failed to resolve parent token `{parent_token}` as docx token: "
                    f"{resolve_exc}. Hint: use a wiki node token (usually starts with `wik`)."
                ) from exc

            LOGGER.warning(
                "Resolved parent token from obj token: %s -> %s",
                parent_token,
                resolved_node_token,
            )
            payload["parent_node_token"] = resolved_node_token
            response_payload = self._post_json(create_url, payload, headers=headers)

        data = response_payload.get("data")
        if not isinstance(data, dict):
            raise FeishuAPIError("Feishu wiki create response missing data object.")

        node_token = str(
            data.get("node_token")
            or data.get("wiki_token")
            or (data.get("node", {}) or {}).get("node_token")
            or ""
        ).strip()
        if not node_token:
            raise FeishuAPIError("Feishu wiki create response missing node_token.")

        LOGGER.info("Created wiki node title=%s node_token=%s", title, node_token)
        return node_token

    def resolve_wiki_node_token(self, token: str) -> str:
        """Resolve wiki node token from object token via get_node API."""
        obj_token = str(token or "").strip()
        if not obj_token:
            raise FeishuAPIError("Cannot resolve empty wiki/doc token.")

        get_node_url = f"{self.base_url}/open-apis/wiki/v2/spaces/get_node"
        headers = self._auth_headers()

        try:
            response_payload = self._get_json(
                get_node_url,
                params={"obj_type": "docx", "token": obj_token},
                headers=headers,
            )
        except FeishuAPIError as exc:
            raise FeishuAPIError(
                f"Failed to resolve wiki node token from token `{obj_token}` with obj_type=docx: {exc}"
            ) from exc

        data = response_payload.get("data")
        node = (data or {}).get("node") if isinstance(data, dict) else None
        if not isinstance(node, dict):
            raise FeishuAPIError(
                f"Failed to resolve wiki node token from token `{obj_token}` with obj_type=docx."
            )

        node_token = str(node.get("node_token") or "").strip()
        if node_token:
            return node_token

        raise FeishuAPIError(
            f"Failed to resolve wiki node token from token `{obj_token}` with obj_type=docx."
        )

    def write_document_content(self, document_token: str, content: str) -> None:
        """Write markdown-like text to a docx node via block create API."""
        block_url = (
            f"{self.base_url}/open-apis/docx/v1/documents/{document_token}"
            f"/blocks/{document_token}/children"
        )
        payload = {
            "index": 0,
            "children": self._build_text_blocks(content),
        }
        self._post_json(block_url, payload, headers=self._auth_headers())
        LOGGER.info("Wrote document content token=%s", document_token)

    @staticmethod
    def _build_text_blocks(content: str) -> List[Dict[str, Any]]:
        lines = [line.rstrip() for line in (content or "").splitlines()]
        if not lines:
            lines = [""]

        blocks: List[Dict[str, Any]] = []
        for line in lines:
            blocks.append(
                {
                    "block_type": 2,
                    "paragraph": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": line,
                                }
                            }
                        ]
                    },
                }
            )
        return blocks

    @staticmethod
    def build_doc_url(document_token: str) -> str:
        """Build user-facing document URL from token."""
        token = str(document_token).strip()
        if not token:
            return ""
        return f"https://open.feishu.cn/wiki/{token}"
