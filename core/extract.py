import re
from pypdf import PdfReader
from io import BytesIO

def extract_text(file_bytes):
    """Extract text from PDF file bytes."""
    reader = PdfReader(BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

def extract_exact_section(text, section_name):
    """Extract exact section content by heading using regex."""
    pattern = rf"(?i){section_name}\s*(.*?)(?=\n[A-Z][^\n]*\n|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return section_name + '\n' + match.group(1).strip()
    return ""

def boost_resume_sections(text):
    """Boost skills and experience sections for similarity scoring."""
    skills = extract_exact_section(text, "skills")
    experience = extract_exact_section(text, "experience")
    boosted_text = text + " " + (skills * 2) + " " + (experience * 2)
    return boosted_text

def extract_email(text):
    """Extract the first email address found in the text."""
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else ""
