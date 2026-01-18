from flask import Flask, render_template, request, send_file
from weasyprint import HTML
from datetime import datetime, timedelta, timezone
import io
import re
import os

app = Flask(__name__)

# ---------- ADDRESS PARSING ----------
def parse_addresses(raw):
    blocks_raw = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
    blocks = []

    for block in blocks_raw:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            continue

        first_line = lines[0]

        # ✅ Detect FROM
        if first_line.lower().startswith("from"):
            label = "FROM,"
            name = lines[1]
            address = lines[2:]
        else:
            label = "TO,"
            name = lines[0]
            address = lines[1:]

        blocks.append({
            "label": label,
            "name": name,
            "address": address
        })

    return blocks



# ---------- HTML GENERATOR (SAME ALIGNMENT MODEL) ----------
def build_html(blocks):
    return render_template(
        "pdf.html",
        blocks=blocks
    )


# ---------- ROUTES ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/preview", methods=["POST"])
def preview():
    raw = request.form.get("addresses", "")
    blocks = parse_addresses(raw)

    html = build_html(blocks)
    pdf = HTML(string=html, base_url=request.root_url).write_pdf()

    return send_file(
        io.BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=False
    )


@app.route("/generate", methods=["POST"])
def generate():
    raw = request.form.get("addresses", "")
    blocks = parse_addresses(raw)

    html = build_html(blocks)
    pdf = HTML(string=html, base_url=request.root_url).write_pdf()

    IST = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(IST)
    filename = f"labels_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"

    return send_file(
        io.BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":
    app.run(debug=True)
