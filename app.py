from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
import io
import re

app = Flask(__name__)

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 40
PADDING = 10
INDENT = 24
GAP = 12

COLUMN_COUNT = 3
COLUMN_WIDTH = (PAGE_WIDTH - 2 * MARGIN - (COLUMN_COUNT - 1) * GAP) / COLUMN_COUNT


# ---------- HELPERS ----------
def wrap_text(text, font, size, max_width):
    words = text.split()
    lines, current = [], ""

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


def parse_addresses(raw):
    blocks_raw = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
    blocks = []

    for block in blocks_raw:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if len(lines) >= 2:
            blocks.append((lines[0], lines[1:]))

    return blocks


def measure_label_height(name, address_lines, content_width):
    body_size = 11
    line_height = body_size + 4
    lines = ["TO,"]

    lines += wrap_text(name, "Helvetica-Bold", body_size + 2, content_width - INDENT)
    for line in address_lines:
        lines += wrap_text(line, "Helvetica", body_size, content_width - INDENT)

    return len(lines) * line_height + 2 * PADDING


def draw_label(c, x, y, name, address_lines):
    body_size = 11
    line_height = body_size + 4
    content_width = COLUMN_WIDTH - 2 * PADDING

    height = measure_label_height(name, address_lines, content_width)
    c.rect(x, y - height, COLUMN_WIDTH, height)

    y_cursor = y - PADDING - line_height

    c.setFont("Helvetica-Bold", body_size)
    c.drawString(x + PADDING, y_cursor, "TO,")
    y_cursor -= line_height

    for line in wrap_text(name, "Helvetica-Bold", body_size + 2, content_width - INDENT):
        c.setFont("Helvetica-Bold", body_size + 2)
        c.drawString(x + PADDING + INDENT, y_cursor, line)
        y_cursor -= line_height

    c.setFont("Helvetica", body_size)
    for line in address_lines:
        for w in wrap_text(line, "Helvetica", body_size, content_width - INDENT):
            c.drawString(x + PADDING + INDENT, y_cursor, w)
            y_cursor -= line_height


def generate_pdf(blocks):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    x = MARGIN
    y = PAGE_HEIGHT - MARGIN

    for name, address_lines in blocks:
        height = measure_label_height(name, address_lines, COLUMN_WIDTH - 2 * PADDING)

        if y - height < MARGIN:
            x += COLUMN_WIDTH + GAP
            y = PAGE_HEIGHT - MARGIN

        if x + COLUMN_WIDTH > PAGE_WIDTH - MARGIN:
            c.showPage()
            x = MARGIN
            y = PAGE_HEIGHT - MARGIN

        draw_label(c, x, y, name, address_lines)
        y -= height + GAP

    c.save()
    buffer.seek(0)
    return buffer


# ---------- ROUTES ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/preview", methods=["POST"])
def preview():
    raw = request.form.get("addresses", "")
    blocks = parse_addresses(raw)
    pdf = generate_pdf(blocks)

    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=False
    )


@app.route("/generate", methods=["POST"])
def generate():
    raw = request.form.get("addresses", "")
    blocks = parse_addresses(raw)
    pdf = generate_pdf(blocks)

    return send_file(
        pdf,
        as_attachment=True,
        download_name="address_labels.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)
