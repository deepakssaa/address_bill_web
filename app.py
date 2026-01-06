from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
import io
import re

app = Flask(__name__)

# ---------- PAGE SETTINGS ----------
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 40
PADDING = 10                 # TRUE padding on all sides
COLUMN_WIDTH = 260           # label width
GAP = 10                     # space between labels


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


# ---------- MEASURE LABEL HEIGHT ----------
def measure_label_height(name, address_lines, content_width):
    body_size = 11
    line_height = body_size + 4

    lines = ["TO,"]
    lines += wrap_text(name, "Helvetica-Bold", body_size + 2, content_width)

    for line in address_lines:
        lines += wrap_text(line, "Helvetica", body_size, content_width)

    return len(lines) * line_height + 2 * PADDING


# ---------- DRAW LABEL ----------
def draw_label(c, x, y, name, address_lines):
    content_width = COLUMN_WIDTH - 2 * PADDING
    body_size = 11
    line_height = body_size + 4

    cursor_y = y - PADDING

    # TO,
    c.setFont("Helvetica-Bold", body_size)
    c.drawString(x + PADDING, cursor_y, "TO,")
    cursor_y -= line_height

    # Name
    for line in wrap_text(name, "Helvetica-Bold", body_size + 2, content_width):
        c.setFont("Helvetica-Bold", body_size + 2)
        c.drawString(x + PADDING, cursor_y, line)
        cursor_y -= line_height

    # Address
    c.setFont("Helvetica", body_size)
    for line in address_lines:
        for wrapped in wrap_text(line, "Helvetica", body_size, content_width):
            c.drawString(x + PADDING, cursor_y, wrapped)
            cursor_y -= line_height


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
        label_height = measure_label_height(
            name,
            address_lines,
            COLUMN_WIDTH - 2 * PADDING
        )

        # Move to next column
        if y - label_height < MARGIN:
            x += COLUMN_WIDTH + GAP
            y = PAGE_HEIGHT - MARGIN

        # New page
        if x + COLUMN_WIDTH > PAGE_WIDTH - MARGIN:
            c.showPage()
            x = MARGIN
            y = PAGE_HEIGHT - MARGIN

        # Border (optional)
        c.rect(x, y - label_height, COLUMN_WIDTH, label_height)

        # Draw content
        draw_label(c, x, y, name, address_lines)

        y -= label_height + GAP

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
