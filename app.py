import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import VPNRequest
from cryptography.fernet import Fernet
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(debug=True)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

KEY_FILE = os.path.join(BASE_DIR, '.secret.key')
STORAGE_DIR = os.path.join(BASE_DIR, 'storage')

def load_or_create_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        k = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(k)
        return k

FERNET_KEY = load_or_create_key()
FERNET = Fernet(FERNET_KEY)

def encrypt_psk(psk: str) -> str:
    return FERNET.encrypt(psk.encode()).decode()

def decrypt_psk(token: str) -> str:
    return FERNET.decrypt(token.encode()).decode()

def validate_config_for_vendor(config: str, vendor: str):
    """Return list of warning strings if expected blocks are missing for vendor."""
    issues = []
    lower = config.lower()
    if vendor == 'fortigate' or vendor == 'fortimanager':
        if 'config vpn ipsec phase1-interface' not in lower:
            issues.append('Missing Phase1 block (config vpn ipsec phase1-interface)')
        if 'config vpn ipsec phase2-interface' not in lower:
            issues.append('Missing Phase2 block (config vpn ipsec phase2-interface)')
        if 'config firewall policy' not in lower:
            issues.append('Missing firewall policy blocks')
    elif vendor == 'paloalto':
        if 'set network ike gateway' not in lower and 'set network ike gateway' not in config:
            issues.append('Missing IKE / Phase1 gateway commands (set network ike gateway)')
        if 'set network ipsec tunnel' not in lower:
            issues.append('Missing IPsec / Phase2 tunnel commands (set network ipsec tunnel)')
        # tunnel interface is optional if user provided no tunnel IPs but we still warn
        if 'set network interface tunnel' not in lower and 'tunnel local ip' not in lower:
            issues.append('Tunnel interface IP not configured (set network interface tunnel units X ip ...)')
    elif vendor == 'cisco':
        if 'crypto ikev2 proposal' not in lower and 'crypto ikev2 proposal' not in config.lower():
            issues.append('Missing IKEv2 proposal block (crypto ikev2 proposal)')
        if 'crypto ipsec transform-set' not in lower:
            issues.append('Missing IPsec transform-set (crypto ipsec transform-set)')
        if 'interface tunnel' not in lower and 'interface tunnel0' not in lower:
            issues.append('Missing Tunnel interface configuration (interface TunnelX)')
    else:
        # generic checks
        if 'phase1' not in lower and 'ike' not in lower:
            issues.append('Phase1/ike section not detected')
    return issues

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request):
    try:
        form = dict(await request.form())
        # Determine vendor/mode
        vendor = form.get("vendor", "fortigate")

        # map vendor to template
        mapping = {
            "fortigate": "fortigate_ipsec.j2",
            "fortimanager": "fortimanager_ipsec.j2",
            "paloalto": "paloalto_ipsec.j2",
            "cisco": "cisco_ipsec.j2",
        }

        # normalize older fortimanager checkbox
        if form.get("fortimanager_mode"):
            vendor = "fortimanager"
            form["vendor"] = vendor

        data = VPNRequest(**form)
        template_file = mapping.get(vendor, "fortigate_ipsec.j2")
        config = templates.get_template(template_file).render(**data.dict())

        # run validation on generated config
        validation_issues = validate_config_for_vendor(config, vendor)

        # redact PSK from rendered output when showing in browser
        safe_output = config.replace(data.psk, "<redacted-psk>") if data.psk else config

        # build warnings HTML if any
        warnings_html = ''
        if validation_issues:
            warnings_html = '<div class="validation-warnings"><h3>Validation warnings</h3><ul>' + ''.join(f'<li>{i}</li>' for i in validation_issues) + '</ul></div>'

        return HTMLResponse(
            f"""
            <html>
            <head>
                <link rel="stylesheet" href="/static/style.css">
                <title>Generated Configuration</title>
            </head>
            <body>
                <div class="container">
                    <h2>Generated Configuration ({vendor})</h2>
                    {warnings_html}
                    <pre id="config">{safe_output}</pre>
                    <button onclick="navigator.clipboard.writeText(
                        document.getElementById('config').innerText
                    )">Copy</button>
                    <br><br>
                    <a href="/">⬅ Back</a>
                </div>
            </body>
            </html>
            """
        )

    except Exception as e:
        return HTMLResponse(
            f"<h2>Internal Server Error</h2><pre>{str(e)}</pre>",
            status_code=500
        )

@app.post('/download')
async def download(request: Request):
    try:
        form = dict(await request.form())
        vendor = form.get('vendor', 'fortigate')
        if form.get('fortimanager_mode'):
            vendor = 'fortimanager'
            form['vendor'] = vendor

        data = VPNRequest(**form)
        mapping = {
            'fortigate': 'fortigate_ipsec.j2',
            'fortimanager': 'fortimanager_ipsec.j2',
            'paloalto': 'paloalto_ipsec.j2',
            'cisco': 'cisco_ipsec.j2',
        }
        template_file = mapping.get(vendor, 'fortigate_ipsec.j2')
        config = templates.get_template(template_file).render(**data.dict())

        include_psk = form.get('include_psk', '0') == '1'
        if not include_psk:
            config = config.replace(data.psk, '<redacted-psk>')

        return PlainTextResponse(content=config, media_type='text/plain')
    except Exception as e:
        return PlainTextResponse(content=str(e), status_code=500)

@app.post('/save')
async def save_config(request: Request):
    try:
        form = dict(await request.form())
        vendor = form.get('vendor', 'fortigate')
        if form.get('fortimanager_mode'):
            vendor = 'fortimanager'
            form['vendor'] = vendor

        include_psk = form.get('include_psk', '0') == '1'
        save_encrypted = form.get('save_encrypted', '0') in ('1', 'on', 'true')

        data = VPNRequest(**form)
        mapping = {
            'fortigate': 'fortigate_ipsec.j2',
            'fortimanager': 'fortimanager_ipsec.j2',
            'paloalto': 'paloalto_ipsec.j2',
            'cisco': 'cisco_ipsec.j2',
        }
        template_file = mapping.get(vendor, 'fortigate_ipsec.j2')
        config = templates.get_template(template_file).render(**data.dict())

        # Prepare storage
        os.makedirs(STORAGE_DIR, exist_ok=True)
        base_name = f"{vendor}_{data.tunnel_name}".replace(' ', '_')
        txt_path = os.path.join(STORAGE_DIR, base_name + '.txt')
        meta_path = os.path.join(STORAGE_DIR, base_name + '.json')

        # Optionally encrypt PSK
        encrypted_token = None
        if save_encrypted:
            encrypted_token = encrypt_psk(data.psk)
            stored_config = config.replace(data.psk, '<redacted-psk>')
        else:
            stored_config = config if include_psk else config.replace(data.psk, '<redacted-psk>')

        # Write files
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(stored_config)

        meta = {
            'vendor': vendor,
            'tunnel_name': data.tunnel_name,
            'file': os.path.basename(txt_path),
            'encrypted_psk': encrypted_token,
        }
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2)

        return PlainTextResponse(content=f"Saved: {txt_path}\nMetadata: {meta_path}")
    except Exception as e:
        return PlainTextResponse(content=str(e), status_code=500)
