"""The limiter key must be the real client, and a client must not choose its own key."""

from types import SimpleNamespace

import pytest

from app.core import rate_limit
from app.core.rate_limit import _parse_networks, get_client_ip


def _request(peer, xff=None):
    headers = {"x-forwarded-for": xff} if xff is not None else {}
    return SimpleNamespace(client=SimpleNamespace(host=peer), headers=headers)


@pytest.fixture(autouse=True)
def docker_trust(monkeypatch):
    monkeypatch.setattr(rate_limit, "_TRUSTED_NETWORKS", _parse_networks("127.0.0.1,::1,172.16.0.0/12"))


def test_nginx_in_another_container_gives_one_key_for_each_client():
    a = get_client_ip(_request("172.20.0.4", "198.51.100.10"))
    b = get_client_ip(_request("172.20.0.4", "203.0.113.20"))
    assert (a, b) == ("198.51.100.10", "203.0.113.20")


def test_loopback_proxy_still_works():
    assert get_client_ip(_request("127.0.0.1", "198.51.100.10")) == "198.51.100.10"


def test_client_cannot_choose_its_key_by_sending_a_header():
    # Nginx appends the real address at the end. The forged left part is ignored.
    assert get_client_ip(_request("172.20.0.4", "1.2.3.4, 198.51.100.10")) == "198.51.100.10"


def test_chain_of_trusted_proxies_is_skipped_from_the_right():
    assert get_client_ip(_request("172.20.0.4", "198.51.100.10, 172.20.0.9")) == "198.51.100.10"


def test_untrusted_peer_cannot_set_the_address():
    assert get_client_ip(_request("198.51.100.99", "1.2.3.4")) == "198.51.100.99"


def test_trusted_peer_without_header_uses_the_peer():
    assert get_client_ip(_request("172.20.0.4")) == "172.20.0.4"


def test_invalid_trusted_entry_is_ignored():
    assert len(_parse_networks("127.0.0.1, not-an-ip, 10.0.0.0/8")) == 2
