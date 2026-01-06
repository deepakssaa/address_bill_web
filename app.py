from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
import io
import re

app = Flask(__name__)

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 10 * mm
PADDING = 10  # 10px padding
COLUMN_WIDTH = 65 * mm  # width of each label column


# ---------- TEXT WRAP ----------
def wrap_text(text, font, size, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + (" " if current else "") + word
        if stringWidth(test, font, size) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


# ---------- MEASURE BLOCK HEIGHT ----------
def measure_block_height(name, address_lines, max_width):
    body_size = 11
    line_height = body_size + 4

    lines = wrap_text(name, "Helvetica-Bold", body_size + 2, max_width)
    for line in address_lines:
        lines += wrap_text(line, "Helvetica", body_size, max_width)

    return len(lines) * line_height + 20  # spacing


# ---------- DRAW BLOCK ----------
def draw_block(c, x, y, name, address_lines):
    content_width = COLUMN_WIDTH - 2 * PADDING

    body_size = 11
    line_height = body_size + 4

    y_cursor = y - PADDING

    # Name
    name_lines = wrap_text(name, "Helvetica-Bold", body_size + 2, content_width)
    for line in name_lines:
        c.setFont("Helvetica-Bold", body_size + 2)
        c.drawString(x + PADDING, y_cursor, line)
        y_cursor -= line_height

    # Address
    for line in address_lines:
        wrapped = wrap_text(line, "Helvetica", body_size, content_width)
        for w in wrapped:
            c.setFont("Helvetica", body_size)
            c.drawString(x + PADDING, y_cursor, w)
            y_cursor -= line_height


# ---------- ROUTES ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    raw = request.form.get("addresses", "").strip()

    blocks_raw = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
    blocks = []

    for block in blocks_raw:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if len(lines) >= 2:
            blocks.append((lines[0], lines[1:]))

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    x = MARGIN
    y = PAGE_HEIGHT - MARGIN

    for name, address_lines in blocks:
        block_height = measure_block_height(
            name,
            address_lines,
            COLUMN_WIDTH - 2 * PADDING
        )

        # New column
        if y - block_height < MARGIN:
            x += COLUMN_WIDTH
            y = PAGE_HEIGHT - MARGIN

        # New page
        if x + COLUMN_WIDTH > PAGE_WIDTH - MARGIN:
            c.showPage()
            x = MARGIN
            y = PAGE_HEIGHT - MARGIN

        # Border
        c.rect(x, y - block_height, COLUMN_WIDTH, block_height)

        # Content
        draw_block(c, x, y, name, address_lines)

        y -= block_height + 10  # spacing between labels

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
