from pathlib import Path
import os
import re

from sentence_transformers import SentenceTransformer

from infrastructure.s3_storage import download_folder


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", text.lower()).strip("_")


def get_title(file: str, file_path: Path) -> str:
    title_pattern = r"^#\s+(.+)$"
    title = re.search(title_pattern, file, re.MULTILINE)

    if title:
        return title.group(1).strip()

    return file_path.stem.replace("_", " ").title()


def get_section(file: str, section_name: str) -> str:
    section_pattern = rf"^##\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##\s+|\Z)"
    section = re.search(
        section_pattern,
        file,
        re.MULTILINE | re.DOTALL,
    )

    if section:
        return section.group(1).strip()

    return ""


def chunk_file(file_path: Path) -> list[dict]:
    with file_path.open("r", encoding="utf-8") as file:
        content = file.read()

    title = get_title(content, file_path)
    category = get_section(content, "Category")
    subcategory = get_section(content, "Subcategory")

    sections = [
        "Symptoms",
        "Likely Causes",
        "Troubleshooting Steps",
        "Escalation Notes",
        "Suggested Ticket Comment",
    ]

    chunks = []

    for index, section in enumerate(sections):
        section_text = get_section(content, section)

        if not section_text:
            continue

        chunk_id = (
            f"{file_path.stem}__"
            f"{normalize(title)}__"
            f"{normalize(section)}__"
            f"{index}"
        )

        embedding_text = f"""
Title: {title}
Category: {category}
Subcategory: {subcategory}
Section: {section}

{section_text}
""".strip()

        chunks.append(
            {
                "chunk_id": chunk_id,
                "file_name": file_path.name,
                "file_path": str(file_path),
                "title": title,
                "category": category,
                "subcategory": subcategory,
                "section": section,
                "chunk_index": index,
                "chunk_text": section_text,
                "embedding_text": embedding_text,
            }
        )

    return chunks


def build_all_chunks(local_directory: Path) -> list[dict]:
    all_chunks = []

    for file_path in local_directory.rglob("*.md"):
        all_chunks.extend(chunk_file(file_path))

    return all_chunks


def build_embeddings(local_directory: Path) -> list[dict]:
    chunks = build_all_chunks(local_directory)

    if not chunks:
        raise RuntimeError(
            f"No chunks were created from Markdown files in {local_directory}"
        )

    print(f"Created {len(chunks)} chunks from {local_directory}")

    model = SentenceTransformer(MODEL_NAME)

    embeddings = model.encode(
        [chunk["embedding_text"] for chunk in chunks],
        normalize_embeddings=True,
    )

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()

    return chunks


def run_build_embeddings() -> None:
    bucket = os.environ["S3_BUCKET_NAME"]
    prefix = os.getenv(
        "KNOWLEDGE_BASE_PREFIX",
        "knowledge-base/",
    )
    local_directory = Path(
        os.getenv(
            "LOCAL_KB_DIR",
            "/tmp/knowledge-base",
        )
    )

    files = download_folder(
        bucket=bucket,
        prefix=prefix,
        local_directory=local_directory,
    )

    if not files:
        raise RuntimeError(
            f"No knowledge-base files found under s3://{bucket}/{prefix}"
        )

    chunks = build_embeddings(local_directory)
    first = chunks[0]

    print("\nFirst Chunk Info\n")
    print(f"Chunk ID: {first['chunk_id']}")
    print(f"File: {first['file_name']}")
    print(f"Title: {first['title']}")
    print(f"Category: {first['category']}")
    print(f"Subcategory: {first['subcategory']}")
    print(f"Section: {first['section']}")
    print(f"Embedding length: {len(first['embedding'])}")