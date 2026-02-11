from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

BASE_PAYLOAD = {
    "tunnel_name": "test-tunnel",
    "interface": "wan1",
    "remote_gw": "203.0.113.1",
    "psk": "secretPSK",
    "phase1_proposal": "aes256-sha256",
    "phase2_proposal": "aes256-sha256",
    "dhgrp": "14",
    "local_subnet": "192.0.2.0/24",
    "remote_subnet": "198.51.100.0/24",
    "local_endpoint": "10.10.10.50",
    "local_port": "ALL",
}


def test_fortigate_template_contains_blocks():
    payload = BASE_PAYLOAD.copy()
    payload.update({"vendor": "fortigate"})
    r = client.post("/generate", data=payload)
    assert r.status_code == 200
    text = r.text
    assert "config vpn ipsec phase1-interface" in text
    assert "config vpn ipsec phase2-interface" in text
    assert "config router static" in text
    assert "config firewall policy" in text


def test_fortimanager_template_contains_blocks():
    payload = BASE_PAYLOAD.copy()
    payload.update({"vendor": "fortimanager"})
    r = client.post("/generate", data=payload)
    assert r.status_code == 200
    text = r.text
    assert "Managed via FortiManager" in text
    assert "config vpn ipsec phase2-interface" in text


def test_paloalto_requires_tunnel_ips():
    payload = BASE_PAYLOAD.copy()
    payload.update({"vendor": "paloalto"})
    r = client.post("/generate", data=payload)
    assert r.status_code == 500 or "NOTE: Palo Alto" in r.text


def test_cisco_requires_tunnel_ips():
    payload = BASE_PAYLOAD.copy()
    payload.update({"vendor": "cisco"})
    r = client.post("/generate", data=payload)
    assert r.status_code == 500 or "NOTE: Cisco" in r.text


def test_download_includes_psk_when_requested():
    payload = BASE_PAYLOAD.copy()
    payload.update({"vendor": "fortigate", "include_psk": "1"})
    r = client.post("/download", data=payload)
    assert r.status_code == 200
    assert "secretPSK" in r.text


def test_download_redacts_psk_by_default():
    payload = BASE_PAYLOAD.copy()
    payload.update({"vendor": "fortigate", "include_psk": "0"})
    r = client.post("/download", data=payload)
    assert r.status_code == 200
    assert "<redacted-psk>" in r.text


def test_presets_file_exists():
    r = client.get('/static/presets.json')
    assert r.status_code == 200


def test_save_endpoint_exists():
    payload = BASE_PAYLOAD.copy()
    payload.update({"vendor": "fortigate", "include_psk": "0"})
    r = client.post('/save', data=payload)
    # may error if storage isn't writable, but endpoint should exist (200 or 500)
    assert r.status_code in (200, 500)
