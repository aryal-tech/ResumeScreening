
from pathlib import Path
from typing import List
from pypdf import PdfReader

UPLOAD_ROOT   = Path("uploads")
JD_FILE_PATH  = UPLOAD_ROOT / "job_description.pdf"     
RESUMES_DIR   = UPLOAD_ROOT / "resumes"                  


def extract_text(pdf_path: Path) -> str:
    """Read a PDF from *pdf_path* and return its full text."""
    reader = PdfReader(str(pdf_path))
    return "".join(page.extract_text() or "" for page in reader.pages)


def get_job_text() -> str:
    """Return the text of the (latest) uploaded job‑description PDF."""
    if not JD_FILE_PATH.exists():
        raise FileNotFoundError(
            "No job description found — did you upload jd_file in index.html?"
        )
    job_text = extract_text(JD_FILE_PATH)
    print("Job Description (first 500 chars):\n", job_text[:500])
    return job_text


def get_resume_texts() -> List[str]:
    """Return a list of texts for every PDF sitting in uploads/resumes/."""
    if not RESUMES_DIR.exists():
        raise FileNotFoundError(
            "No resumes directory found — did you upload resume_files in index.html?"
        )

    resume_paths = sorted(RESUMES_DIR.glob("*.pdf"))
    if not resume_paths:
        raise FileNotFoundError("No resumes were uploaded.")

    texts = []
    for idx, path in enumerate(resume_paths, start=1):
        txt = extract_text(path)
        print(f"\nResume {idx} ({path.name}) first 300 chars:\n", txt[:300])
        texts.append(txt)
    return texts
