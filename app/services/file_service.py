from PyPDF2 import PdfReader

def read_file(file_path: str) -> str: 
    reader = PdfReader(file_path)

    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    
    # print(f"file content:\n{text}")
    return text