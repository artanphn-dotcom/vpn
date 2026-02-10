import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import VPNRequest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(debug=True)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request):
    try:
        form = dict(await request.form())
        # Determine mode
        if form.get("fortimanager_mode"):
            form["mode"] = "fortimanager"
        else:
            form["mode"] = "fortigate"

        data = VPNRequest(**form)
        template_file = "fortimanager_ipsec.j2" if data.mode == "fortimanager" else "fortigate_ipsec.j2"
        config = templates.get_template(template_file).render(**data.dict())

        return HTMLResponse(
            f"""
            <html>
            <head>
                <link rel="stylesheet" href="/static/style.css">
                <title>Generated Configuration</title>
            </head>
            <body>
                <div class="container">
                    <h2>Generated Configuration ({data.mode})</h2>
                    <pre id="config">{config}</pre>
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
