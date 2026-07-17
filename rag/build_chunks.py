# things to do:
# create an object that looks like: chunk_id, file_name, title, category, section, chunk_text, embedding
# Use sentence transformer MiniLM to convert the documents in knowledge base to chunks
# loop through each file and convert each section in the file to a chunk_id
# Use regex to identify sections (split by section headings)
# Create an embedding per section
# store the embedding plus all the aforementioned data together

from pathlib import Path 
import re

KNOW_BASE_DIR = Path("knowledge_base")

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", text.lower()).strip(_)