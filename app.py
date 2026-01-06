from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io
import re

app = Flask(__name__)

# --- Page & label settings for 4x4 grid ---
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 10 * mm
COLUMNS = 4  # 4 columns
ROWS = 4     # 4 rows
LABEL_WIDTH = (PAGE_WIDTH - 2 * MARGIN) / COLUMNS
LABEL_HEIGHT = (PAGE_HEIGHT - 2 * MARGIN) / ROWS


# --- Draw a single label ---
def draw_single_label(c, col, row, name, address_lines):
    x = MARGIN + col * LABEL_WIDTH
    y = PAGE_HEIGHT - MARGIN - (row + 1) * LABEL_HEIGHT

    # --- Draw label border ---
    c.setStrokeColorRGB(0.6, 0.6, 0.6)  # light gray
    c.setLineWidth(0.5)
    c.rect(x, y, LABEL_WIDTH, LABEL_HEIGHT)

    c.saveState()
    c.translate(x + LABEL_WIDTH / 2, y + LABEL_HEIGHT / 2)
    c.rotate(90)

    base_x = -LABEL_HEIGHT / 2 + 8 * mm
    base_y = LABEL_WIDTH / 2 - 8 * mm

    # TO,
    c.setFont("Helvetica-Bold", 11)
    c.drawString(base_x, base_y, "TO,")

    indent = 24

    # Name
    c.setFont("Helvetica-Bold", 13)
    c.drawString(base_x + indent, base_y - 18, name)

    # Address lines (any number)
    c.setFont("Helvetica", 11)
    for i, line in enumerate(address_lines):
        c.drawString(base_x + indent, base_y - 36 - i * 14, line)

    c.restoreState()



# --- Home page ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# --- Generate PDF ---
@app.route("/generate", methods=["POST"])
def generate():
    raw = request.form.get("addresses", "").strip()

    # --- Robust splitting: any empty line separates addresses ---
    raw_blocks = [b.strip() for b in re.split(r'\n\s*\n', raw) if b.strip()]

    blocks = []
    for block in raw_blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        name = lines[0]
        address_lines = lines[1:]
        blocks.append((name, address_lines))

    # --- PDF setup ---
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    index = 0
    for name, address_lines in blocks:
        row = (index // COLUMNS) % ROWS
        col = index % COLUMNS

        # Start new page when needed
        if index > 0 and index % (COLUMNS * ROWS) == 0:
            c.showPage()

        draw_single_label(c, col, row, name, address_lines)
        index += 1

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="address_labels.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)
