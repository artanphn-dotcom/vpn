from pydantic import BaseModel, IPvAnyAddress, validator, root_validator
import ipaddress
from typing import Optional

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
    vendor: Optional[str] = "fortigate"
    # Vendor-specific optional fields
    tunnel_local_ip: Optional[str] = None
    tunnel_remote_ip: Optional[str] = None

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

    @root_validator(skip_on_failure=True)
    def vendor_specific_checks(cls, values):
        vendor = values.get('vendor') or values.get('mode') or 'fortigate'
        tunnel_local = values.get('tunnel_local_ip')
        tunnel_remote = values.get('tunnel_remote_ip')
        if vendor in ('paloalto', 'cisco'):
            if not tunnel_local or not tunnel_remote:
                raise ValueError('Vendor "paloalto" and "cisco" require tunnel_local_ip and tunnel_remote_ip')
            # validate tunnel_local as network/CIDR
            ipaddress.ip_network(tunnel_local)
            # validate tunnel_remote as address
            ipaddress.ip_address(tunnel_remote)
        return values
