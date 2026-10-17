
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    NameObject,
    DictionaryObject
)
from pathlib import Path

# Folder containing ex1.pdf to ex17.pdf
folder = Path("Oh_shit")

name = input("Enter student name: ")
enrollment = input("Enter enrollment number: ")

output = Path("Student_Final.pdf")

# Find PDFs in numerical order
pdf_files = sorted(
    folder.glob("ex*.pdf"),
    key=lambda p: int(p.stem[2:])
)

if not pdf_files:
    print("No PDF files found!")
else:
    writer = PdfWriter()

    for pdf in pdf_files:
        print("Processing:", pdf.name)

        if pdf.stem == "ex1":
            reader = PdfReader(str(pdf))
            page = reader.pages[0]

            # Create overlay page
            temp = PdfWriter()
            overlay = temp.add_blank_page(
                width=float(page.mediabox.width),
                height=float(page.mediabox.height)
            )

            # Bold built-in font
            font = DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"):
                    NameObject("/Helvetica-Bold")
            })

            overlay[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({
                    NameObject("/F1"): font
                })
            })

            def safe(text):
                return (
                    text.replace("\\", "\\\\")
                    .replace("(", "\\(")
                    .replace(")", "\\)")
                )

            # White box + new details
            # Coordinates may need adjustment for your PDF
            content = f"""
q
1 1 1 rg
384 744 205 40 re f
Q
BT /F1 8.4 Tf 0 0 0 rg
386.95 773 Td (Name :- {safe(name)}) Tj ET
BT /F1 8.4 Tf 0 0 0 rg
386.95 761 Td (Enrollment No :- {safe(enrollment)}) Tj ET
""".encode("latin-1")

            stream = DecodedStreamObject()
            stream.set_data(content)
            overlay[NameObject("/Contents")] = (
                temp._add_object(stream)
            )

            # Apply overlay to ex1 first page
            page.merge_page(overlay)
            writer.add_page(page)

            # Preserve any additional pages in ex1
            for extra_page in reader.pages[1:]:
                writer.add_page(extra_page)

        else:
            # Append ex2, ex3 ... in numerical order
            writer.append(str(pdf))

    with open(output, "wb") as file:
        writer.write(file)

    writer.close()

    print("All PDFs merged successfully!")
    print("Total PDFs:", len(pdf_files))
    print("Output:", output.resolve())
