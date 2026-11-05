# Turns an uploaded file into text, so the agents can read it
import os
import tempfile
from pathlib import Path

from fastapi import HTTPException

from app.parsing.reader import MAX_SIZE_MB, read_resume


def upload_to_text(upload, allowed_types):
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Wrong file type: {suffix}. Allowed: {', '.join(allowed_types)}")

    data = upload.file.read()
    if len(data) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File is too big. The limit is {MAX_SIZE_MB} MB.")

    # A .md or .txt file is already text
    if suffix in [".md", ".txt"]:
        return data.decode("utf-8", errors="ignore")

    # MarkItDown reads from a file path, so I save the upload to a temporary file first
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_file.write(data)
        temp_path = temp_file.name

    # A broken or locked file can't be read, so a human must check it
    try:
        return read_resume(temp_path)
    except Exception as error:
        if "Password" in str(error):
            raise HTTPException(status_code=422, detail="Needs Manual Review: the PDF is locked with a password.")
        raise HTTPException(status_code=422, detail="Needs Manual Review: the file could not be read.")
    finally:
        os.remove(temp_path)
