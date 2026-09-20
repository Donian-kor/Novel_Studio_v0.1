from __future__ import annotations

import socket
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from novel_studio.ai.providers import base
from novel_studio.ai.providers.base import AIProvider, CONNECT_TIMEOUT


class _ProbeProvider(AIProvider):
    def _chat_impl(self, *args, **kwargs):
        return ""

    def _chat_stream_impl(self, *args, **kwargs):
        return iter(())


class _DelayedHandler(BaseHTTPRequestHandler):
    """첫 응답(헤더)을 늦게 보내 모델 로딩 중 상황을 재현한다."""

    delay = 2.5

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        time.sleep(type(self).delay)
        body = b'{"choices": [{"message": {"content": "ok"}}]}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def _start_server(delay: float):
    handler = type("_Delayed", (_DelayedHandler,), {"delay": delay})
    server = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _post_request(port: int):
    return urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=b"{}", headers={"Content-Type": "application/json"}, method="POST")


def test_slow_first_response_is_not_connection_failure(qtbot=None):
    """모델 로딩처럼 첫 응답이 느려도 연결 실패로 끊기지 않아야 한다.

    회귀 배경: urlopen(timeout=1초)이 응답 헤더 대기까지 끊어버려 첫 응답이 늦으면
    재요청이 반복되고, LM Studio에서 모델 로드/언로드가 반복되며 결국 연결 실패가 났다.
    """
    server = _start_server(delay=2.5)
    try:
        provider = _ProbeProvider({})
        started = time.monotonic()
        resp = provider._check_urlopen(_post_request(server.server_address[1]), 60)
        elapsed = time.monotonic() - started
        try:
            assert resp.status == 200
            assert elapsed >= 2.0  # 응답을 끝까지 기다려 받았다
        finally:
            resp.close()
    finally:
        server.shutdown()
        server.server_close()


def test_short_timeout_still_waits_for_first_response():
    """timeout이 CONNECT_TIMEOUT(1초)이어도 첫 응답 대기는 끊기지 않는다."""
    server = _start_server(delay=1.6)
    try:
        provider = _ProbeProvider({})
        resp = provider._check_urlopen(_post_request(server.server_address[1]), CONNECT_TIMEOUT)
        try:
            assert resp.status == 200
        finally:
            resp.close()
    finally:
        server.shutdown()
        server.server_close()


def test_server_down_is_detected_fast():
    """서버가 꺼져 있으면 연결 판정은 빠르게 실패해야 한다."""
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/models")
    provider = _ProbeProvider({})
    started = time.monotonic()
    with pytest.raises(Exception):
        provider._check_urlopen(req, 60)
    assert time.monotonic() - started < 5.0


def test_post_connect_timeout_relaxes_short_limits():
    """연결 후 대기 상한은 1초 이하이면 무제한으로 완화된다(취소는 abort/폴링)."""

    class _Sock:
        def __init__(self):
            self.value = "unset"

        def settimeout(self, value):
            self.value = value

    sock = _Sock()
    base._post_connect_timeout(sock, CONNECT_TIMEOUT)
    assert sock.value is None
    base._post_connect_timeout(sock, 60.0)
    assert sock.value == 60.0
