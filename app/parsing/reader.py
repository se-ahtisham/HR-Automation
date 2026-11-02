
# refuse wrong file types and files that are too big.
from pathlib import Path

ALLOWED_TYPES = [".pdf", ".docx"]
MAX_SIZE_MB = 5



from markitdown import MarkItDown

converter = MarkItDown()


def read_resume(file_path):
    result = converter.convert(file_path)
    return result.text_content


def check_file(file_path):
    path = Path(file_path)
    size_mb = path.stat().st_size / (1024 * 1024)

    if path.suffix.lower() not in ALLOWED_TYPES:
        return "Wrong file type"
    if size_mb > MAX_SIZE_MB:
        return "File is too big"
    return "OK"