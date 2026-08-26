"""Mechanical tools used by the Resume Agent."""
import io
import re

import PyPDF2
import docx

def extract_text_from_file(file_path: str, mime_type: str) -> str:
    """
    Extracts text mechanically from PDF or DOCX. No LLM involved here.
    This guarantees we read the pure text layer without parsing ambiguity.
    """
    text = ""
    try:
        if mime_type == "application/pdf" or file_path.endswith(".pdf"):
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        
        elif "wordprocessingml" in mime_type or file_path.endswith(".docx"):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            raise ValueError("Unsupported format for pure text extraction")
    except Exception as e:
        raise RuntimeError(f"Mechanical text extraction failed: {str(e)}")
        
    return text


# Hardcoded Master Skill Map acting as an internal DB for lab 2
# In production, this would query the `skills` table from pgvector
MASTER_SKILL_MAP = {
    "react": "React.js",
    "reactjs": "React.js",
    "react.js": "React.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "python3": "Python",
    "py": "Python",
    "js": "JavaScript",
    "java8": "Java",
    "c++11": "C++",
    "cpp": "C++",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
    "ml": "Machine Learning",
}

def normalize_skill_name(raw_skill: str) -> str:
    """
    Deterministic skill normalization tool. 
    Maps raw resume mentions to the canonical taxonomy.
    """
    if not raw_skill:
        return ""
    
    clean = raw_skill.strip().lower()
    
    # Simple direct mapping
    if clean in MASTER_SKILL_MAP:
        return MASTER_SKILL_MAP[clean]
        
    # If no mapping found, Title Case it as a fallback standard
    return raw_skill.strip().title()
