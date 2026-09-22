import sys
from pathlib import Path

from rag.chunker import chunk_path
from rag.database import Database
from rag.embeddings import Embedder
from rag.logutil import log
from rag.reader import read
from rag.validate import validate

SUFFIXES = {".pdf", ".docx"}


def ingest(directory, embedder, database, read_file=read, chunk_file=chunk_path):
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"missing directory: {directory}")
    files = sorted(
        path for path in directory.iterdir() if path.suffix.lower() in SUFFIXES
    )
    if not files:
        raise ValueError(f"no policy files: {directory}")
    log("ingest", f"directory={directory} files={len(files)}")
    pending = []
    for path in files:
        loaded = read_file(path)
        records = chunk_file(path, loaded["lines"])
        for record in records:
            error = validate(record)
            if error:
                log("ingest", "failed")
                return error
            pending.append(record)
    if pending:
        vectors = embedder.embed(
            [record["text"] for record in pending], task="document"
        )
        database.upsert(pending, vectors)
    log("ingest", "finished")
    return None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    directory = argv[0] if argv else "docs"
    db_path = argv[1] if len(argv) > 1 else "chroma"
    error = ingest(directory, embedder=Embedder(), database=Database(db_path))
    if error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
