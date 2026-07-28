import PyPDF2

with open('sample_contract.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        print(f"=== PAGE {i+1} ===")
        print(text)
        print()
