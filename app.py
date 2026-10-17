
from flask import Flask, render_template, request, send_file, jsonify
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    NameObject, DictionaryObject, DecodedStreamObject
)
from io import BytesIO
from pathlib import Path
import re

app = Flask(__name__)

PDF_FOLDER = Path(__file__).parent / "Oh_shit"


def safe_pdf_text(value):
    """Make text safe for a basic PDF text command."""
    value = value.encode("latin-1", errors="replace").decode("latin-1")
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def add_student_details(page, name, enrollment):
    """Cover the old details on the first page and draw new details."""
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)

    overlay_writer = PdfWriter()
    overlay_page = overlay_writer.add_blank_page(
        width=width, height=height
    )

    # Basic built-in bold font
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica-Bold"),
    })

    resources = DictionaryObject()
    resources[NameObject("/Font")] = DictionaryObject({
        NameObject("/F1"): font
    })
    overlay_page[NameObject("/Resources")] = resources

    # NOTE: These coordinates are approximate.
    # Adjust the white rectangle to cover the old name/enrollment only.
    content = f"""
q
1 1 1 rg
384 744 205 40 re f
Q
BT
/F1 8.4 Tf
0 0 0 rg
386.95 773 Td
(Name :- {safe_pdf_text(name)}) Tj
ET
BT
/F1 8.4 Tf
0 0 0 rg
386.95 761 Td
(Enrollment No :- {safe_pdf_text(enrollment)}) Tj
ET
""".encode("latin-1")

    stream = DecodedStreamObject()
    stream.set_data(content)
    overlay_page[NameObject("/Contents")] = stream

    overlay_buffer = BytesIO()
    overlay_writer.write(overlay_buffer)
    overlay_buffer.seek(0)

    overlay_reader = PdfReader(overlay_buffer)
    page.merge_page(overlay_reader.pages[0])


def create_student_pdf(name, enrollment):
    pdf_files = sorted(
        PDF_FOLDER.glob("ex*.pdf"),
        key=lambda file: int(file.stem[2:])
        if file.stem[2:].isdigit() else 999999
    )

    if len(pdf_files) != 17:
        raise ValueError(
            "Server par ex1.pdf thi ex17.pdf sudhi badhi 17 files hovi joie."
        )

    if not (PDF_FOLDER / "ex1.pdf").exists():
        raise ValueError("ex1.pdf file mali nathi.")

    writer = PdfWriter()

    for pdf_path in pdf_files:
        reader = PdfReader(str(pdf_path))

        if pdf_path.name == "ex1.pdf":
            for page_number, page in enumerate(reader.pages):
                if page_number == 0:
                    add_student_details(page, name, enrollment)
                writer.add_page(page)
        else:
            for page in reader.pages:
                writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/generate")
def generate():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    enrollment = str(data.get("enrollment", "")).strip()

    if not name or not enrollment:
        return jsonify(error="Name ane Enrollment No. banne bharo."), 400

    if len(name) > 100 or len(enrollment) > 40:
        return jsonify(error="Name athva Enrollment No. ghanu lambo chhe."), 400

    try:
        pdf_buffer = create_student_pdf(name, enrollment)
        filename = re.sub(
            r"[^A-Za-z0-9_-]+", "_", enrollment
        ) or "student"

        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"TempServices_{filename}.pdf"
        )
    except (ValueError, OSError) as error:
        app.logger.exception("PDF generation failed")
        return jsonify(error=str(error)), 500
    except Exception:
        app.logger.exception("Unexpected PDF generation error")
        return jsonify(
            error="PDF generate na thai. Server files ane PDF format check karo."
        ), 500


if __name__ == "__main__":
    app.run(debug=True)
