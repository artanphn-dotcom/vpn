from pydantic import BaseModel, IPvAnyAddress, validator
import ipaddress

PHASE1_PROPOSALS = ["aes256-sha256", "aes256-sha384", "aes128-sha256"]
PHASE2_PROPOSALS = ["aes256-sha256", "aes256gcm"]
DH_GROUPS = ["14", "19", "20"]

class VPNRequest(BaseModel):
    tunnel_name: str
    interface: str
    remote_gw: IPvAnyAddress
    psk: str
    phase1_proposal: str
    phase2_proposal: str
    dhgrp: str
    local_subnet: str
    remote_subnet: str
    local_endpoint: str = "10.10.10.50"  # Reverse rule endpoint
    local_port: str = "ALL"               # Reverse rule port/service
    mode: str = "fortigate"               # Default mode

    @validator("phase1_proposal")
    def p1_valid(cls, v):
        if v not in PHASE1_PROPOSALS:
            raise ValueError("Invalid Phase1 proposal")
        return v

    @validator("phase2_proposal")
    def p2_valid(cls, v):
        if v not in PHASE2_PROPOSALS:
            raise ValueError("Invalid Phase2 proposal")
        return v

    @validator("dhgrp")
    def dh_valid(cls, v):
        if v not in DH_GROUPS:
            raise ValueError("Invalid DH Group")
        return v

    @validator("local_subnet", "remote_subnet")
    def subnet_valid(cls, v):
        ipaddress.ip_network(v)
        return v
