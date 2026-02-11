# FortiGate IPsec Configuration Generator

Created by Artan V.

A small Flask web application that generates FortiGate and FortiManager IPsec VPN configuration snippets from user-provided VPN parameters. It provides a simple web form and Jinja2 templates to render device-specific configuration blocks that can be copied into device CLI or management consoles.

Features
- Web-based form to collect IPsec parameters (phase1/phase2 settings, peer addresses, subnets, pre-shared keys, etc.)
- Template-driven output using Jinja2 to produce FortiGate and FortiManager configuration snippets
- Lightweight single-file Flask app for local use

Prerequisites
- Python 3.8+ installed on Windows, macOS or Linux
- A virtual environment is recommended

Installation (Windows PowerShell)
1. Create and activate a virtual environment:

   python -m venv venv
   .\venv\Scripts\Activate.ps1

2. Install dependencies:

   pip install -r requirements.txt

3. Run the application:

   python app.py

The app listens on http://127.0.0.1:5000 by default. Open this URL in a browser to access the generator UI.

Installation (Ubuntu WSL)
1. Open the Ubuntu shell (WSL). If you don't have WSL installed, follow Microsoft's WSL installation guide first.

2. (Optional) Install system packages required for Python virtual environments (only needed if not already present):

   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip

3. Create and activate a virtual environment:

   python3 -m venv venv
   source venv/bin/activate

4. Install dependencies:

   pip install -r requirements.txt

5. Run the application:

   python app.py

Notes:
- On WSL2 the Flask app listens on http://127.0.0.1:5000 and can be opened from a browser on Windows at the same address.
- If you need the app to be reachable from other machines on your network, run the server bound to all interfaces (for example via `flask run --host=0.0.0.0` or by modifying `app.py` to use app.run(host='0.0.0.0')).

Usage
- Open the web UI and fill the form with your VPN parameters (local/remote subnets, peer IPs, PSK, Phase 1/2 profiles).
- Select whether you want FortiGate or FortiManager output.
- The app will render a configuration snippet using the corresponding Jinja2 template (`templates/fortigate_ipsec.j2` and `templates/fortimanager_ipsec.j2`).
- Copy the generated snippet into your device or manager.

Project Structure
- `app.py` — Flask application and routing logic.
- `models.py` — Python data models used to validate/organize form input.
- `templates/` — Jinja2 templates that render the final device configuration:
  - `fortigate_ipsec.j2` — FortiGate CLI-style configuration template.
  - `fortimanager_ipsec.j2` — FortiManager-style configuration template.
  - `index.html` — Main UI that hosts the form.
- `static/` — Static assets for the UI:
  - `style.css` — Basic styling.
  - `wizard.js` — Client-side form behaviour and validation.
- `requirements.txt` — Python dependencies for the project.

Extending and Customizing
- Modify or add Jinja2 templates in `templates/` to match your device firmware/CLI version or to support other devices.
- Extend `models.py` to add validation or additional fields.
- Add authentication or persistence if you need to store configurations securely.

Security Notes
- This tool is intended for local, offline use. Do not run it exposed to the public internet without adding authentication and secure transport (HTTPS).
- Pre-shared keys and secrets are entered in plain text in the browser—handle outputs carefully.

License
- This repository does not include a license file. Add an appropriate LICENSE if you plan to distribute the code.

Contributing
- Contributions and fixes are welcome. Open issues or pull requests with clear descriptions of the problem and proposed changes.

Contact
- For questions or improvements, open an issue in the project repository or update the README with repository/contact details.

Author
- Created by Artan V.

Improvements and roadmap
- Validation & security
  - Strengthen input validation in `models.py` (more precise IP/subnet checks, PSK strength rules).
  - Never log or persist PSKs; add UI/server option to redact secrets in outputs and logs.
  - Add support for .env configuration (use python-dotenv) and document secure deployment practices.

- Developer experience
  - Split the app into a package (move to `app/__init__.py` and use Blueprints) for easier testing and extension.
  - Add unit tests (see `tests/`) and a GitHub Actions workflow for CI (`.github/workflows/ci.yml`).
  - Provide a Dockerfile for reproducible runs and a `Makefile` or simple scripts for common tasks.

- UX & features
  - Add copy-to-clipboard and download-as-file buttons in the UI (templates already include a basic copy button).
  - Offer presets for common FortiOS versions and allow selecting multiple phase proposals.
  - Improve frontend validation and responsive styling in `static/`.

- Documentation
  - Add a `CONTRIBUTING.md`, `LICENSE` and `ISSUE_TEMPLATE.md`.
  - Expand README with Quick Start examples, Troubleshooting and WSL/Ubuntu instructions.

Quick next steps I implemented for you
- Added a basic unit test at `tests/test_app.py` to validate homepage and generation flow.
- Added a GitHub Actions CI workflow at `.github/workflows/ci.yml` to run tests and linting.
- Added a `Dockerfile` to run the application with Uvicorn in a container.

If you'd like, I can:
- Add more tests (validation edge cases, template outputs).
- Convert the app into a package structure and update imports.
- Create `CONTRIBUTING.md`, `LICENSE` and issue templates.

To run the tests locally (PowerShell):
1. Create and activate venv:
   python -m venv venv
   .\venv\Scripts\Activate.ps1
2. Install deps and pytest:
   pip install -r requirements.txt
   pip install pytest
3. Run tests:
   pytest -q

To build and run the Docker image (PowerShell):
1. Build image:
   docker build -t fortigate-ipsec-generator .
2. Run container:
   docker run -p 8000:8000 fortigate-ipsec-generator

source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
Browser: http://127.0.0.1:8000

Additional recommendations
- Add unit tests that validate template outputs for each vendor (assert presence of key blocks and correct fields).
- Add a Docker Compose setup for local dev environments with a small static web UI or test harness.
- Add frontend validation for IP/subnet formats (use a library or regex) and helpful inline hints for vendor-specific fields.
- Consider encrypting PSKs if you plan to persist them or adding an option to store configs locally encrypted.
- Provide example presets for common FortiOS/PAN-OS/Cisco versions to reduce user input and errors.# vpn 
# Artan V.
# vpn
# Test