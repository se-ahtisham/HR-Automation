# Reads an uploaded CV or job post file (PDF, Word, .md or .txt) and gives back its text
from io import BytesIO
from pathlib import Path

from markitdown import MarkItDown

MAX_SIZE_MB = 5

converter = MarkItDown()


# One clear error type, so a page can show the message to the user
class FileProblem(Exception):
    pass


def upload_to_text(file_name, data, allowed_types):
    suffix = Path(file_name).suffix.lower()
    if suffix not in allowed_types:
        raise FileProblem(f"Wrong file type: {suffix}. Allowed: {', '.join(allowed_types)}")
    if len(data) > MAX_SIZE_MB * 1024 * 1024:
        raise FileProblem(f"File is too big. The limit is {MAX_SIZE_MB} MB.")
    # A real PDF starts with "%PDF", and a real Word file starts with "PK". Anything else is a fake or broken file
    if (suffix == ".pdf" and not data.startswith(b"%PDF")) or (suffix == ".docx" and not data.startswith(b"PK")):
        raise FileProblem("Needs Manual Review: the file could not be read.")

    # MarkItDown reads the file straight from memory. A broken or locked file can't be read, so a human must check it
    try:
        return converter.convert_stream(BytesIO(data), file_extension=suffix).text_content
    except Exception as error:
        if "Password" in str(error):
            raise FileProblem("Needs Manual Review: the PDF is locked with a password.")
        raise FileProblem("Needs Manual Review: the file could not be read.")
