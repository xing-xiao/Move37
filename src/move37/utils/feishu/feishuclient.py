"""Feishu API client utilities based on lark-oapi SDK."""

from __future__ import annotations

import importlib
import json
from typing import Any, Dict


class FeishuClientError(RuntimeError):
    """Raised when Feishu client setup or transport fails."""


class FeishuAuthError(FeishuClientError):
    """Raised when Feishu auth API returns an error response."""


class FeishuVerificationError(FeishuClientError):
    """Raised when Feishu tenant verification API returns an error response."""


class FeishuDocxError(FeishuClientError):
    """Raised when Feishu wiki docx creation API returns an error response."""


class FeishuDocxContentError(FeishuClientError):
    """Raised when Feishu wiki docx content update API returns an error response."""


class FeishuMessageError(FeishuClientError):
    """Raised when Feishu IM message API returns an error response."""


class FeishuClient:
    """Minimal Feishu SDK client for tenant access token retrieval."""

    TENANT_ACCESS_TOKEN_URI = "/open-apis/auth/v3/tenant_access_token/internal"
    TENANT_VERIFICATION_URI = "/open-apis/verification/v1/verification"
    WIKI_DOCX_CREATE_URI_TEMPLATE = "/open-apis/wiki/v2/spaces/{space_id}/nodes"
    DOCX_CHILDREN_CREATE_URI_TEMPLATE = (
        "/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children"
    )
    IM_MESSAGES_URI = "/open-apis/im/v1/messages"
    DEFAULT_BASE_URL = "https://open.feishu.cn"

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        timeout: float = 30.0,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self.app_id = str(app_id or "").strip()
        self.app_secret = str(app_secret or "").strip()
        if not self.app_id:
            raise ValueError("`app_id` is required.")
        if not self.app_secret:
            raise ValueError("`app_secret` is required.")

        try:
            resolved_timeout = float(timeout)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"`timeout` must be a positive number, got: {timeout!r}") from exc
        if resolved_timeout <= 0:
            raise ValueError("`timeout` must be greater than 0.")

        self.timeout = resolved_timeout
        self.base_url = str(base_url or self.DEFAULT_BASE_URL).strip().rstrip("/")
        if not self.base_url:
            self.base_url = self.DEFAULT_BASE_URL

        self.tenant_access_token = ""
        self._sdk_module: Any | None = None
        self._sdk_client: Any | None = None

    def _load_sdk(self) -> Any:
        if self._sdk_module is not None:
            return self._sdk_module
        try:
            self._sdk_module = importlib.import_module("lark_oapi")
        except ModuleNotFoundError as exc:
            raise FeishuClientError(
                "lark-oapi is required. Install with `pip install lark-oapi`."
            ) from exc
        return self._sdk_module

    def _build_sdk_client(self) -> Any:
        lark = self._load_sdk()
        builder = (
            lark.Client.builder()
            .app_id(self.app_id)
            .app_secret(self.app_secret)
            .timeout(int(self.timeout))
            .domain(self.base_url)
        )
        log_level = getattr(getattr(lark, "LogLevel", None), "WARNING", None)
        if log_level is not None and hasattr(builder, "log_level"):
            builder = builder.log_level(log_level)
        self._sdk_client = builder.build()
        return self._sdk_client

    def _get_sdk_client(self) -> Any:
        if self._sdk_client is None:
            return self._build_sdk_client()
        return self._sdk_client

    def _build_tenant_token_request(self, lark: Any) -> Any:
        return (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.POST)
            .uri(self.TENANT_ACCESS_TOKEN_URI)
            .body({"app_id": self.app_id, "app_secret": self.app_secret})
            .build()
        )

    def _build_tenant_verification_request(self, lark: Any, tenant_access_token: str) -> Any:
        request_builder = (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.GET)
            .uri(self.TENANT_VERIFICATION_URI)
        )
        if hasattr(request_builder, "headers"):
            request_builder = request_builder.headers(
                {"Authorization": f"Bearer {tenant_access_token}"}
            )
        return request_builder.build()

    def _build_docx_create_request(
        self,
        lark: Any,
        tenant_access_token: str,
        space_id: str,
        body: Dict[str, Any],
    ) -> Any:
        request_builder = (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.POST)
            .uri(self.WIKI_DOCX_CREATE_URI_TEMPLATE.format(space_id=space_id))
            .body(body)
        )
        if hasattr(request_builder, "headers"):
            request_builder = request_builder.headers(
                {
                    "Authorization": f"Bearer {tenant_access_token}",
                    "Content-Type": "application/json; charset=utf-8",
                }
            )
        return request_builder.build()

    def _build_docx_descendant_create_request(
        self,
        lark: Any,
        tenant_access_token: str,
        document_id: str,
        block_id: str,
        body: Dict[str, Any],
    ) -> Any:
        request_builder = (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.POST)
            .uri(
                self.DOCX_CHILDREN_CREATE_URI_TEMPLATE.format(
                    document_id=document_id,
                    block_id=block_id,
                )
            )
            .body(body)
        )
        if hasattr(request_builder, "headers"):
            request_builder = request_builder.headers(
                {
                    "Authorization": f"Bearer {tenant_access_token}",
                    "Content-Type": "application/json; charset=utf-8",
                }
            )
        return request_builder.build()

    def _build_group_notify_request(
        self,
        lark: Any,
        tenant_access_token: str,
        receive_id_type: str,
        body: Dict[str, Any],
    ) -> Any:
        request_builder = (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.POST)
            .uri(f"{self.IM_MESSAGES_URI}?receive_id_type={receive_id_type}")
            .body(body)
        )
        if hasattr(request_builder, "headers"):
            request_builder = request_builder.headers(
                {
                    "Authorization": f"Bearer {tenant_access_token}",
                    "Content-Type": "application/json; charset=utf-8",
                }
            )
        return request_builder.build()

    @staticmethod
    def _parse_payload(response: Any) -> Dict[str, Any]:
        raw = getattr(response, "raw", None)
        content = getattr(raw, "content", None)
        if isinstance(content, bytes):
            response_text = content.decode("utf-8")
        elif isinstance(content, str):
            response_text = content
        else:
            raise FeishuClientError("Feishu SDK response does not contain raw JSON content.")

        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise FeishuClientError("Failed to parse Feishu SDK JSON response.") from exc
        if not isinstance(payload, dict):
            raise FeishuClientError("Feishu SDK response JSON must be an object.")
        return payload

    @staticmethod
    def _extract_error_details(response: Any) -> tuple[str, str, str, str]:
        """Extract best-effort error details from SDK response."""
        code = str(getattr(response, "code", "") or "").strip()
        msg = str(getattr(response, "msg", "") or "").strip()

        log_id = ""
        get_log_id = getattr(response, "get_log_id", None)
        if callable(get_log_id):
            log_id = str(get_log_id() or "").strip()

        status_code = ""
        raw = getattr(response, "raw", None)
        if raw is not None:
            status_code = str(getattr(raw, "status_code", "") or "").strip()
            content = getattr(raw, "content", None)
            response_text = ""
            if isinstance(content, bytes):
                response_text = content.decode("utf-8", errors="replace")
            elif isinstance(content, str):
                response_text = content
            if response_text:
                try:
                    payload = json.loads(response_text)
                except json.JSONDecodeError:
                    payload = None
                if isinstance(payload, dict):
                    if not code:
                        code = str(payload.get("code", "") or "").strip()
                    if not msg:
                        msg = str(payload.get("msg", "") or "").strip()
        return code, msg, log_id, status_code

    def get_tenant_access_token(self) -> str:
        """Call auth/v3 API and return tenant_access_token."""

        lark = self._load_sdk()
        sdk_client = self._get_sdk_client()
        request = self._build_tenant_token_request(lark)

        try:
            response = sdk_client.request(request)
        except Exception as exc:  # noqa: BLE001
            raise FeishuClientError(f"Feishu SDK request failed: {type(exc).__name__}: {exc}") from exc

        if not callable(getattr(response, "success", None)):
            raise FeishuClientError("Feishu SDK response object is invalid: missing success().")
        if not response.success():
            code, msg, log_id, status_code = self._extract_error_details(response)
            message = f"Feishu auth request failed: code={code}, msg={msg or 'unknown'}"
            if status_code:
                message = f"{message}, http_status={status_code}"
            if log_id:
                message = f"{message}, log_id={log_id}"
            raise FeishuAuthError(message)

        payload = self._parse_payload(response)
        try:
            code = int(payload.get("code", -1))
        except (TypeError, ValueError):
            code = -1
        if code != 0:
            msg = str(payload.get("msg", "")).strip()
            raise FeishuAuthError(f"Feishu auth failed: code={code}, msg={msg or 'unknown'}")

        token = str(payload.get("tenant_access_token") or "").strip()
        if not token:
            raise FeishuAuthError("Feishu auth response missing tenant_access_token.")
        self.tenant_access_token = token
        return token

    def get_tenant_verification_info(self, tenant_access_token: str | None = None) -> Dict[str, Any]:
        """Call verification/v1 API and return structured tenant verification info."""

        token = str(tenant_access_token or self.tenant_access_token).strip()
        if not token:
            token = self.get_tenant_access_token()

        lark = self._load_sdk()
        sdk_client = self._get_sdk_client()
        request = self._build_tenant_verification_request(lark, token)

        try:
            response = sdk_client.request(request)
        except Exception as exc:  # noqa: BLE001
            raise FeishuClientError(f"Feishu SDK request failed: {type(exc).__name__}: {exc}") from exc

        if not callable(getattr(response, "success", None)):
            raise FeishuClientError("Feishu SDK response object is invalid: missing success().")
        if not response.success():
            code, msg, log_id, status_code = self._extract_error_details(response)
            message = f"Feishu verification request failed: code={code}, msg={msg or 'unknown'}"
            if status_code:
                message = f"{message}, http_status={status_code}"
            if log_id:
                message = f"{message}, log_id={log_id}"
            raise FeishuVerificationError(message)

        payload = self._parse_payload(response)
        try:
            code = int(payload.get("code", -1))
        except (TypeError, ValueError):
            code = -1
        if code != 0:
            msg = str(payload.get("msg", "")).strip()
            raise FeishuVerificationError(
                f"Feishu verification failed: code={code}, msg={msg or 'unknown'}"
            )

        data = payload.get("data")
        if not isinstance(data, dict):
            raise FeishuVerificationError("Feishu verification response missing data object.")
        return data

    def create_docx(
        self,
        space_id: str,
        node_name: str = "origin",
        parent_node_token: str | None = None,
        title: str | None = None,
        tenant_access_token: str | None = None,
        obj_type: str = "docx",
    ) -> Dict[str, Any]:
        """Create a wiki DOCX node and return structured response data."""

        normalized_space_id = str(space_id or "").strip()
        if not normalized_space_id:
            raise ValueError("`space_id` is required.")

        normalized_node_name = str(node_name or "origin").strip() or "origin"
        normalized_title = str(title or normalized_node_name).strip()
        if not normalized_title:
            raise ValueError("`title` is required.")
        if len(normalized_title) > 500:
            raise ValueError("`title` must be 500 characters or fewer.")

        token = str(tenant_access_token or self.tenant_access_token).strip()
        if not token:
            token = self.get_tenant_access_token()

        payload: Dict[str, Any] = {
            "obj_type": str(obj_type or "docx").strip() or "docx",
            "node_type": normalized_node_name,
            "title": normalized_title,
        }

        normalized_parent = str(parent_node_token or "").strip()
        if normalized_parent:
            payload["parent_node_token"] = normalized_parent

        lark = self._load_sdk()
        sdk_client = self._get_sdk_client()
        request = self._build_docx_create_request(
            lark,
            token,
            normalized_space_id,
            payload,
        )

        try:
            response = sdk_client.request(request)
        except Exception as exc:  # noqa: BLE001
            raise FeishuClientError(f"Feishu SDK request failed: {type(exc).__name__}: {exc}") from exc

        if not callable(getattr(response, "success", None)):
            raise FeishuClientError("Feishu SDK response object is invalid: missing success().")
        if not response.success():
            code, msg, log_id, status_code = self._extract_error_details(response)
            message = f"Feishu docx create request failed: code={code}, msg={msg or 'unknown'}"
            if status_code:
                message = f"{message}, http_status={status_code}"
            if log_id:
                message = f"{message}, log_id={log_id}"
            raise FeishuDocxError(message)

        response_payload = self._parse_payload(response)
        try:
            code = int(response_payload.get("code", -1))
        except (TypeError, ValueError):
            code = -1
        if code != 0:
            msg = str(response_payload.get("msg", "")).strip()
            raise FeishuDocxError(f"Feishu docx create failed: code={code}, msg={msg or 'unknown'}")

        data = response_payload.get("data")
        if not isinstance(data, dict):
            raise FeishuDocxError("Feishu docx create response missing data object.")
        return data

    def write_docx_content(
        self,
        document_id: str,
        block_id: str,
        children: list[Dict[str, Any]],
        tenant_access_token: str | None = None,
    ) -> Dict[str, Any]:
        """Create descendant blocks in a docx block."""

        normalized_document_id = str(document_id or "").strip()
        if not normalized_document_id:
            raise ValueError("`document_id` is required.")
        normalized_block_id = str(block_id or "").strip()
        if not normalized_block_id:
            raise ValueError("`block_id` is required.")
        if not isinstance(children, list) or not children:
            raise ValueError("`children` must be a non-empty list.")

        token = str(tenant_access_token or self.tenant_access_token).strip()
        if not token:
            token = self.get_tenant_access_token()

        payload: Dict[str, Any] = {"children": children}

        lark = self._load_sdk()
        sdk_client = self._get_sdk_client()
        request = self._build_docx_descendant_create_request(
            lark,
            token,
            normalized_document_id,
            normalized_block_id,
            payload,
        )

        try:
            response = sdk_client.request(request)
        except Exception as exc:  # noqa: BLE001
            raise FeishuClientError(f"Feishu SDK request failed: {type(exc).__name__}: {exc}") from exc

        if not callable(getattr(response, "success", None)):
            raise FeishuClientError("Feishu SDK response object is invalid: missing success().")
        if not response.success():
            code, msg, log_id, status_code = self._extract_error_details(response)
            message = f"Feishu docx content update request failed: code={code}, msg={msg or 'unknown'}"
            if status_code:
                message = f"{message}, http_status={status_code}"
            if log_id:
                message = f"{message}, log_id={log_id}"
            raise FeishuDocxContentError(message)

        response_payload = self._parse_payload(response)
        try:
            code = int(response_payload.get("code", -1))
        except (TypeError, ValueError):
            code = -1
        if code != 0:
            msg = str(response_payload.get("msg", "")).strip()
            raise FeishuDocxContentError(
                f"Feishu docx content update failed: code={code}, msg={msg or 'unknown'}"
            )

        data = response_payload.get("data")
        if not isinstance(data, dict):
            raise FeishuDocxContentError("Feishu docx content update response missing data object.")
        return data

    def send_group_notify(
        self,
        content: str,
        receive_id: str,
        msg_type: str = "interactive",
        receive_id_type: str = "chat_id",
        tenant_access_token: str | None = None,
    ) -> Dict[str, Any]:
        """Send Feishu IM group message and return full response payload."""

        normalized_content = str(content or "").strip()
        if not normalized_content:
            raise ValueError("`content` is required.")

        normalized_receive_id = str(receive_id or "").strip()
        if not normalized_receive_id:
            raise ValueError("`receive_id` is required.")

        normalized_receive_id_type = str(receive_id_type or "chat_id").strip() or "chat_id"
        normalized_msg_type = str(msg_type or "interactive").strip() or "interactive"
        if normalized_msg_type not in {"text", "post", "interactive"}:
            raise ValueError("`msg_type` must be one of: text, post, interactive.")

        token = str(tenant_access_token or self.tenant_access_token).strip()
        if not token:
            token = self.get_tenant_access_token()

        payload_content = normalized_content
        if normalized_msg_type == "text":
            payload_content = json.dumps({"text": normalized_content}, ensure_ascii=False)

        body: Dict[str, Any] = {
            "receive_id": normalized_receive_id,
            "msg_type": normalized_msg_type,
            "content": payload_content,
        }

        lark = self._load_sdk()
        sdk_client = self._get_sdk_client()
        request = self._build_group_notify_request(
            lark,
            token,
            normalized_receive_id_type,
            body,
        )

        try:
            response = sdk_client.request(request)
        except Exception as exc:  # noqa: BLE001
            raise FeishuClientError(f"Feishu SDK request failed: {type(exc).__name__}: {exc}") from exc

        if not callable(getattr(response, "success", None)):
            raise FeishuClientError("Feishu SDK response object is invalid: missing success().")
        if not response.success():
            code, msg, log_id, status_code = self._extract_error_details(response)
            message = f"Feishu message request failed: code={code}, msg={msg or 'unknown'}"
            if status_code:
                message = f"{message}, http_status={status_code}"
            if log_id:
                message = f"{message}, log_id={log_id}"
            raise FeishuMessageError(message)

        response_payload = self._parse_payload(response)
        try:
            code = int(response_payload.get("code", -1))
        except (TypeError, ValueError):
            code = -1
        if code != 0:
            msg = str(response_payload.get("msg", "")).strip()
            raise FeishuMessageError(f"Feishu message send failed: code={code}, msg={msg or 'unknown'}")
        return response_payload
