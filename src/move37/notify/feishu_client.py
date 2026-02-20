"""Feishu bot app client."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import requests

from .errors import FeishuAPIError, NetworkError

LOGGER = logging.getLogger(__name__)


class FeishuClient:
    """Feishu API client using app_id/app_secret authentication."""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        chat_receive_id: str,
        chat_receive_id_type: str = "chat_id",
        timeout: float = 30.0,
        base_url: str = "https://open.feishu.cn",
    ) -> None:
        self.app_id = app_id.strip()
        self.app_secret = app_secret.strip()
        self.chat_receive_id = chat_receive_id.strip()
        self.chat_receive_id_type = chat_receive_id_type.strip() or "chat_id"
        self.timeout = float(timeout)
        self.base_url = base_url.strip().rstrip("/") or "https://open.feishu.cn"

    def _post_json(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise NetworkError(f"HTTP request failed: {exc}") from exc

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise FeishuAPIError(
                f"Feishu API returned non-JSON response (status={response.status_code})."
            ) from exc

        if not isinstance(response_payload, dict):
            raise FeishuAPIError(
                "Feishu API response payload is not a dictionary."
            )
        return response_payload

    def _get_tenant_access_token(self) -> str:
        auth_url = f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        response_payload = self._post_json(auth_url, payload)

        code = int(response_payload.get("code", -1))
        if code != 0:
            msg = response_payload.get("msg", "")
            raise FeishuAPIError(f"Feishu auth failed: code={code}, msg={msg}")

        token = str(response_payload.get("tenant_access_token") or "").strip()
        if not token:
            raise FeishuAPIError("Feishu auth response missing tenant_access_token.")
        return token

    def send_message(self, content: str) -> Dict[str, Any]:
        """Send a text message to Feishu chat."""
        message = str(content or "").strip()
        if not message:
            return {
                "success": False,
                "message": "Message content is empty.",
                "response": None,
            }

        try:
            tenant_access_token = self._get_tenant_access_token()

            send_url = (
                f"{self.base_url}/open-apis/im/v1/messages"
                f"?receive_id_type={self.chat_receive_id_type}"
            )
            headers = {
                "Authorization": f"Bearer {tenant_access_token}",
                "Content-Type": "application/json; charset=utf-8",
            }
            payload = {
                "receive_id": self.chat_receive_id,
                "msg_type": "text",
                "content": json.dumps({"text": message}, ensure_ascii=False),
            }
            response_payload = self._post_json(send_url, payload, headers=headers)

            code = int(response_payload.get("code", -1))
            if code != 0:
                msg = response_payload.get("msg", "")
                return {
                    "success": False,
                    "message": f"Feishu send failed: code={code}, msg={msg}",
                    "response": response_payload,
                }

            data = response_payload.get("data")
            message_id = ""
            if isinstance(data, dict):
                message_id = str(data.get("message_id") or "").strip()

            success_message = "Feishu message sent successfully."
            if message_id:
                success_message = f"Feishu message sent successfully. message_id={message_id}"
            LOGGER.info(
                "Feishu message sent, receive_id_type=%s receive_id=%s",
                self.chat_receive_id_type,
                self.chat_receive_id,
            )
            return {
                "success": True,
                "message": success_message,
                "response": response_payload,
            }
        except (NetworkError, FeishuAPIError) as exc:
            LOGGER.error("Failed to send Feishu message: %s", exc)
            return {
                "success": False,
                "message": str(exc),
                "response": None,
            }
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Unexpected Feishu client error")
            return {
                "success": False,
                "message": f"Unexpected error: {type(exc).__name__}: {exc}",
                "response": None,
            }
