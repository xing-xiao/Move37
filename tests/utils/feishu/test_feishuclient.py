"""Tests for move37.utils.feishu.feishuclient."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from move37.utils.feishu.feishuclient import (
    FeishuAuthError,
    FeishuClient,
    FeishuClientError,
    FeishuDocxContentError,
    FeishuDocxError,
    FeishuMessageError,
    FeishuVerificationError,
)


class _FakeRaw:
    def __init__(self, payload: Dict[str, Any], status_code: int = 200) -> None:
        self.content = json.dumps(payload).encode("utf-8")
        self.status_code = status_code


class _FakeResponse:
    def __init__(
        self,
        payload: Dict[str, Any],
        *,
        ok: bool = True,
        code: int | None = 0,
        msg: str | None = "ok",
        log_id: str = "log_id_test",
        status_code: int = 200,
    ) -> None:
        self.raw = _FakeRaw(payload, status_code=status_code)
        self._ok = ok
        self.code = code
        self.msg = msg
        self._log_id = log_id

    def success(self) -> bool:
        return self._ok

    def get_log_id(self) -> str:
        return self._log_id


def _install_fake_sdk(
    monkeypatch: pytest.MonkeyPatch,
    response: _FakeResponse | list[_FakeResponse],
) -> Dict[str, Any]:
    state: Dict[str, Any] = {}
    responses = response if isinstance(response, list) else [response]

    class _FakeBaseRequestBuilder:
        def __init__(self) -> None:
            self._request: Dict[str, Any] = {}

        def http_method(self, value: str) -> "_FakeBaseRequestBuilder":
            self._request["http_method"] = value
            return self

        def uri(self, value: str) -> "_FakeBaseRequestBuilder":
            self._request["uri"] = value
            return self

        def body(self, value: Dict[str, Any]) -> "_FakeBaseRequestBuilder":
            self._request["body"] = value
            return self

        def headers(self, value: Dict[str, str]) -> "_FakeBaseRequestBuilder":
            self._request["headers"] = value
            return self

        def build(self) -> Dict[str, Any]:
            return dict(self._request)

    class _FakeBaseRequest:
        @staticmethod
        def builder() -> _FakeBaseRequestBuilder:
            return _FakeBaseRequestBuilder()

    class _FakeClient:
        def request(self, request: Dict[str, Any]) -> _FakeResponse:
            request_history = state.setdefault("requests", [])
            request_history.append(request)
            state["request"] = request
            if not responses:
                raise RuntimeError("No fake response configured.")
            return responses.pop(0)

    class _FakeClientBuilder:
        def app_id(self, value: str) -> "_FakeClientBuilder":
            state["app_id"] = value
            return self

        def app_secret(self, value: str) -> "_FakeClientBuilder":
            state["app_secret"] = value
            return self

        def timeout(self, value: int) -> "_FakeClientBuilder":
            state["timeout"] = value
            return self

        def domain(self, value: str) -> "_FakeClientBuilder":
            state["domain"] = value
            return self

        def log_level(self, value: Any) -> "_FakeClientBuilder":
            state["log_level"] = value
            return self

        def build(self) -> _FakeClient:
            return _FakeClient()

    class _FakeClientType:
        @staticmethod
        def builder() -> _FakeClientBuilder:
            return _FakeClientBuilder()

    fake_sdk = SimpleNamespace(
        Client=_FakeClientType,
        BaseRequest=_FakeBaseRequest,
        HttpMethod=SimpleNamespace(POST="POST", GET="GET", PATCH="PATCH"),
        LogLevel=SimpleNamespace(WARNING="WARNING"),
    )
    monkeypatch.setitem(sys.modules, "lark_oapi", fake_sdk)
    return state


def test_init_requires_app_id_and_app_secret() -> None:
    with pytest.raises(ValueError):
        FeishuClient(app_id="", app_secret="secret")
    with pytest.raises(ValueError):
        FeishuClient(app_id="cli_test", app_secret="")


def test_missing_sdk_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "lark_oapi", raising=False)

    original_import_module = importlib.import_module

    def _fake_import_module(name: str, package: str | None = None) -> Any:
        if name == "lark_oapi":
            raise ModuleNotFoundError("No module named 'lark_oapi'")
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", _fake_import_module)

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuClientError, match="lark-oapi is required"):
        client.get_tenant_access_token()


def test_get_tenant_access_token_success(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 0,
                "msg": "ok",
                "tenant_access_token": "t-test-token",
                "expire": 7200,
            }
        ),
    )

    client = FeishuClient(
        app_id="cli_test",
        app_secret="secret_test",
        timeout=15,
        base_url="https://open.feishu.cn",
    )
    token = client.get_tenant_access_token()

    assert token == "t-test-token"
    assert state["app_id"] == "cli_test"
    assert state["app_secret"] == "secret_test"
    assert state["timeout"] == 15
    assert state["domain"] == "https://open.feishu.cn"
    assert state["request"]["http_method"] == "POST"
    assert state["request"]["uri"] == FeishuClient.TENANT_ACCESS_TOKEN_URI
    assert state["request"]["body"]["app_id"] == "cli_test"
    assert client.tenant_access_token == "t-test-token"


def test_get_tenant_access_token_raises_when_sdk_response_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {"code": 999, "msg": "request failed"},
            ok=False,
            code=999,
            msg="request failed",
            log_id="log_abc",
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuAuthError, match="code=999"):
        client.get_tenant_access_token()


def test_get_tenant_access_token_raises_when_api_code_not_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 91663,
                "msg": "app invalid",
                "tenant_access_token": "",
            }
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuAuthError, match="code=91663"):
        client.get_tenant_access_token()


def test_get_tenant_access_token_raises_when_token_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 0,
                "msg": "ok",
                "tenant_access_token": "",
            }
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuAuthError, match="missing tenant_access_token"):
        client.get_tenant_access_token()


def test_get_tenant_verification_info_success(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 0,
                "msg": "ok",
                "data": {
                    "status": "verified",
                    "type": "company",
                    "tenant_name": "Move37",
                    "certification_url": "https://open.feishu.cn/example",
                },
            }
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    info = client.get_tenant_verification_info("t-test-token")

    assert info["status"] == "verified"
    assert info["tenant_name"] == "Move37"
    assert state["request"]["http_method"] == "GET"
    assert state["request"]["uri"] == FeishuClient.TENANT_VERIFICATION_URI
    assert state["request"]["headers"]["Authorization"] == "Bearer t-test-token"


def test_get_tenant_verification_info_raises_when_sdk_response_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {"code": 999, "msg": "request failed"},
            ok=False,
            code=999,
            msg="request failed",
            log_id="log_abc",
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuVerificationError, match="code=999"):
        client.get_tenant_verification_info("t-test-token")


def test_get_tenant_verification_info_raises_when_api_code_not_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 91684,
                "msg": "invalid tenant_access_token",
            }
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuVerificationError, match="code=91684"):
        client.get_tenant_verification_info("t-invalid-token")


def test_get_tenant_verification_info_raises_when_data_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 0,
                "msg": "ok",
            }
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuVerificationError, match="missing data object"):
        client.get_tenant_verification_info("t-test-token")


def test_create_docx_success(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 0,
                "msg": "ok",
                "data": {
                    "node": {"node_token": "wikcn_node"},
                    "obj_token": "doccn_obj",
                    "wiki_node_url": "https://example.feishu.cn/wiki/wikcn_node",
                },
            }
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    result = client.create_docx(
        space_id="7600000000000000000",
        node_name="origin",
        parent_node_token="wikcn_parent",
        title="2026-02-26",
        tenant_access_token="t-test-token",
    )

    assert result["obj_token"] == "doccn_obj"
    assert state["request"]["http_method"] == "POST"
    assert (
        state["request"]["uri"]
        == FeishuClient.WIKI_DOCX_CREATE_URI_TEMPLATE.format(space_id="7600000000000000000")
    )
    assert state["request"]["body"]["parent_node_token"] == "wikcn_parent"
    assert state["request"]["body"]["obj_type"] == "docx"
    assert state["request"]["body"]["node_type"] == "origin"
    assert state["request"]["body"]["title"] == "2026-02-26"
    assert state["request"]["headers"]["Authorization"] == "Bearer t-test-token"


def test_create_docx_uses_auto_token_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install_fake_sdk(
        monkeypatch,
        [
            _FakeResponse(
                {
                    "code": 0,
                    "msg": "ok",
                    "tenant_access_token": "t-fetched-token",
                }
            ),
            _FakeResponse(
                {
                    "code": 0,
                    "msg": "ok",
                    "data": {
                        "node": {"node_token": "wikcn_node"},
                        "obj_token": "doccn_obj",
                        "wiki_node_url": "https://example.feishu.cn/wiki/wikcn_node",
                    },
                }
            ),
        ],
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    result = client.create_docx(space_id="7600000000000000000", title="auto-token-title")

    assert result["obj_token"] == "doccn_obj"
    assert len(state["requests"]) == 2
    assert state["requests"][0]["uri"] == FeishuClient.TENANT_ACCESS_TOKEN_URI
    assert (
        state["requests"][1]["uri"]
        == FeishuClient.WIKI_DOCX_CREATE_URI_TEMPLATE.format(space_id="7600000000000000000")
    )
    assert state["requests"][1]["headers"]["Authorization"] == "Bearer t-fetched-token"


def test_create_docx_raises_when_api_code_not_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 90001,
                "msg": "permission denied",
            }
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuDocxError, match="code=90001"):
        client.create_docx(
            space_id="7600000000000000000",
            title="test-doc",
            tenant_access_token="t-test-token",
        )


def test_create_docx_raises_when_data_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 0,
                "msg": "ok",
            }
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuDocxError, match="missing data object"):
        client.create_docx(
            space_id="7600000000000000000",
            title="test-doc",
            tenant_access_token="t-test-token",
        )


def test_create_docx_failure_message_uses_raw_payload_when_code_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 99991663,
                "msg": "invalid parent node",
            },
            ok=False,
            code=None,
            msg=None,
            status_code=400,
            log_id="log_from_gateway",
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(
        FeishuDocxError,
        match="code=99991663, msg=invalid parent node, http_status=400, log_id=log_from_gateway",
    ):
        client.create_docx(
            space_id="7600000000000000000",
            title="test-doc",
            tenant_access_token="t-test-token",
        )


def test_write_docx_content_success(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 0,
                "msg": "ok",
                "data": {"document_revision_id": 3},
            }
        ),
    )
    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    result = client.write_docx_content(
        document_id="PDlqd7vFloeAzIxlaQUc3Zdrnfb",
        block_id="doxcn_root_block",
        children=[
            {
                "block_type": 2,
                "paragraph": {
                    "elements": [{"text_run": {"content": "hello"}}],
                },
            }
        ],
        tenant_access_token="t-test-token",
    )

    assert result["document_revision_id"] == 3
    assert state["request"]["http_method"] == "POST"
    assert (
        state["request"]["uri"]
        == FeishuClient.DOCX_DESCENDANT_CREATE_URI_TEMPLATE.format(
            document_id="PDlqd7vFloeAzIxlaQUc3Zdrnfb",
            block_id="doxcn_root_block",
        )
    )
    assert state["request"]["body"]["children"][0]["paragraph"]["elements"][0]["text_run"]["content"] == "hello"
    assert state["request"]["headers"]["Authorization"] == "Bearer t-test-token"


def test_write_docx_content_uses_auto_token_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install_fake_sdk(
        monkeypatch,
        [
            _FakeResponse(
                {
                    "code": 0,
                    "msg": "ok",
                    "tenant_access_token": "t-fetched-token",
                }
            ),
            _FakeResponse(
                {
                    "code": 0,
                    "msg": "ok",
                    "data": {"document_revision_id": 4},
                }
            ),
        ],
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    result = client.write_docx_content(
        document_id="PDlqd7vFloeAzIxlaQUc3Zdrnfb",
        block_id="doxcn_root_block",
        children=[
            {
                "block_type": 2,
                "paragraph": {
                    "elements": [{"text_run": {"content": "auto token"}}],
                },
            }
        ],
    )

    assert result["document_revision_id"] == 4
    assert len(state["requests"]) == 2
    assert state["requests"][0]["uri"] == FeishuClient.TENANT_ACCESS_TOKEN_URI
    assert (
        state["requests"][1]["uri"]
        == FeishuClient.DOCX_DESCENDANT_CREATE_URI_TEMPLATE.format(
            document_id="PDlqd7vFloeAzIxlaQUc3Zdrnfb"
            ,
            block_id="doxcn_root_block",
        )
    )


def test_write_docx_content_raises_when_api_code_not_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 90001,
                "msg": "no permission",
            }
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuDocxContentError, match="code=90001"):
        client.write_docx_content(
            document_id="PDlqd7vFloeAzIxlaQUc3Zdrnfb",
            block_id="doxcn_root_block",
            children=[
                {
                    "block_type": 2,
                    "paragraph": {
                        "elements": [{"text_run": {"content": "failed"}}],
                    },
                }
            ],
            tenant_access_token="t-test-token",
        )


def test_write_docx_content_raises_when_data_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 0,
                "msg": "ok",
            }
        ),
    )

    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuDocxContentError, match="missing data object"):
        client.write_docx_content(
            document_id="PDlqd7vFloeAzIxlaQUc3Zdrnfb",
            block_id="doxcn_root_block",
            children=[
                {
                    "block_type": 2,
                    "paragraph": {
                        "elements": [{"text_run": {"content": "failed"}}],
                    },
                }
            ],
            tenant_access_token="t-test-token",
        )


def test_send_group_notify_text_success(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 0,
                "msg": "ok",
                "data": {"message_id": "om_123"},
            }
        ),
    )
    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    payload = client.send_group_notify(
        content="hello",
        receive_id="oc_chat_123",
        msg_type="text",
        receive_id_type="chat_id",
        tenant_access_token="t-test-token",
    )

    assert payload["data"]["message_id"] == "om_123"
    assert state["request"]["http_method"] == "POST"
    assert (
        state["request"]["uri"]
        == f"{FeishuClient.IM_MESSAGES_URI}?receive_id_type=chat_id"
    )
    assert state["request"]["body"]["receive_id"] == "oc_chat_123"
    assert state["request"]["body"]["msg_type"] == "text"
    assert state["request"]["headers"]["Authorization"] == "Bearer t-test-token"


def test_send_group_notify_raises_when_api_code_not_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sdk(
        monkeypatch,
        _FakeResponse(
            {
                "code": 90001,
                "msg": "permission denied",
            }
        ),
    )
    client = FeishuClient(app_id="cli_test", app_secret="secret_test")
    with pytest.raises(FeishuMessageError, match="code=90001"):
        client.send_group_notify(
            content="failed",
            receive_id="oc_chat_123",
            msg_type="text",
            receive_id_type="chat_id",
            tenant_access_token="t-test-token",
        )
