from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_home():
    r = client.get("/")
    assert r.status_code == 200
    assert "Generated Configuration" not in r.text  # homepage


def test_generate_valid():
    form = {
        "tunnel_name": "test-tunnel",
        "interface": "wan1",
        "remote_gw": "203.0.113.1",
        "psk": "secretPSK",
        "phase1_proposal": "aes256-sha256",
        "phase2_proposal": "aes256-sha256",
        "dhgrp": "14",
        "local_subnet": "192.0.2.0/24",
        "remote_subnet": "198.51.100.0/24",
        # fortigate mode by default; include optional fields
        "local_endpoint": "10.10.10.50",
        "local_port": "ALL",
    }

    r = client.post("/generate", data=form)
    assert r.status_code == 200
    # Should render a generated configuration block
    assert "Generated Configuration" in r.text or "Generated Configuration (fortigate)" in r.text
    # basic check that the tunnel name appears in output template
    assert "test-tunnel" in r.text
