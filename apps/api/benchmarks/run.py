"""Retrieval benchmark for candidate embedding models.

Measures how often each model retrieves a chunk that actually answers the question.
This is retrieval only — no LLM is involved, so nothing here measures answer quality.

Run from `apps/api`:

    uv run python benchmarks/run.py

Add documents to `benchmarks/corpus/*.txt` and labelled questions to
`benchmarks/questions.jsonl`. See `benchmarks/README.md`.
"""

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

HERE = Path(__file__).resolve().parent
API_ROOT = HERE.parent
sys.path.insert(0, str(API_ROOT))

from app.ai.chunking import chunk_text  # noqa: E402

CACHE_DIR = Path(os.environ.get("BENCH_MODEL_CACHE", str(API_ROOT / "models")))
RERANKER_REPO = "cross-encoder/ms-marco-MiniLM-L-6-v2"
SIMILARITY_THRESHOLD = 0.45
CANDIDATE_POOL = 20


@dataclass(frozen=True)
class Candidate:
    name: str
    repo: str
    query_prefix: str = ""


# The query prefix is per model on purpose. Getting it wrong makes the comparison
# unfair, so check each model card before trusting these numbers.
CANDIDATES: tuple[Candidate, ...] = (
    Candidate("bge-m3", "BAAI/bge-m3"),
    Candidate(
        "medembed-large",
        "abhinand/MedEmbed-large-v0.1",
        query_prefix="Represent this sentence for searching relevant passages: ",
    ),
    Candidate("pubmedbert-msmarco", "pritamdeka/S-PubMedBert-MS-MARCO"),
)


def load_corpus(corpus_dir: Path) -> list[dict[str, str]]:
    documents = []

    for path in sorted(corpus_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()

        if text:
            documents.append({"id": path.stem, "text": text})

    return documents


def build_chunks(documents: list[dict[str, str]]) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []

    for document in documents:
        for chunk in chunk_text(document["text"]):
            chunks.append(
                {
                    "document": document["id"],
                    "index": chunk.index,
                    "content": chunk.content,
                }
            )

    return chunks


def load_questions(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []

    questions: list[dict[str, object]] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if line and not line.startswith("#"):
            questions.append(json.loads(line))

    return questions


def is_relevant(chunk: dict[str, object], markers: list[str]) -> bool:
    content = str(chunk["content"]).lower()

    return any(marker.lower() in content for marker in markers)


def recall_at(rankings: list[list[int]], chunks: list[dict[str, object]], k: int) -> float:
    hits = 0

    for ranking, markers in rankings:
        if any(is_relevant(chunks[index], markers) for index in ranking[:k]):
            hits += 1

    return hits / len(rankings)


def mrr_at(rankings: list[list[int]], chunks: list[dict[str, object]], k: int) -> float:
    reciprocal: list[float] = []

    for ranking, markers in rankings:
        for position, index in enumerate(ranking[:k], start=1):
            if is_relevant(chunks[index], markers):
                reciprocal.append(1 / position)
                break
        else:
            reciprocal.append(0.0)

    return statistics.fmean(reciprocal)


def directory_size_mb(path: Path) -> float:
    if not path.exists():
        return 0.0

    # Hugging Face keeps real files in blobs/ and symlinks them into snapshots/,
    # sometimes from the parent cache dir, so deduplicate by resolved path.
    seen: set[Path] = set()
    total = 0

    for item in path.rglob("*"):
        if not item.is_file():
            continue

        resolved = item.resolve()

        if resolved in seen:
            continue

        seen.add(resolved)
        total += resolved.stat().st_size

    return round(total / (1024 * 1024), 1)


def evaluate(
    candidate: Candidate,
    chunks: list[dict[str, object]],
    questions: list[dict[str, object]],
    reranker: CrossEncoder | None,
) -> dict[str, object]:
    started = time.perf_counter()
    model = SentenceTransformer(candidate.repo, cache_folder=str(CACHE_DIR))
    model_load_seconds = time.perf_counter() - started

    # One throwaway encode, so the timings below do not absorb lazy initialisation.
    model.encode(["warm up"], normalize_embeddings=True)

    started = time.perf_counter()
    chunk_vectors = model.encode(
        [str(chunk["content"]) for chunk in chunks],
        normalize_embeddings=True,
        batch_size=8,
        show_progress_bar=False,
    )
    corpus_seconds = time.perf_counter() - started

    answerable = [row for row in questions if row.get("answerable")]
    unanswerable = [row for row in questions if not row.get("answerable")]

    rankings: list[tuple[list[int], list[str]]] = []
    reranked: list[tuple[list[int], list[str]]] = []
    query_seconds: list[float] = []
    abstained: list[float] = []

    for row in questions:
        text = f"{candidate.query_prefix}{row['question']}"

        started = time.perf_counter()
        query_vector = model.encode([text], normalize_embeddings=True)[0]
        scores = chunk_vectors @ query_vector
        query_seconds.append(time.perf_counter() - started)

        order = list(np.argsort(-scores)[:CANDIDATE_POOL])
        markers = list(row.get("expect") or [])

        if not row.get("answerable"):
            abstained.append(float(scores[order[0]]) if order else 0.0)
            continue
        rankings.append((order, markers))

        if reranker is not None:
            pairs = [(str(row["question"]), str(chunks[index]["content"])) for index in order]
            scores_by_pair = reranker.predict(pairs)
            reranked.append(([order[i] for i in np.argsort(-scores_by_pair)], markers))

    result: dict[str, object] = {
        "model": candidate.name,
        "repo": candidate.repo,
        "dimensions": int(chunk_vectors.shape[1]),
        "chunks": len(chunks),
        "answerable_questions": len(answerable),
        "unanswerable_questions": len(unanswerable),
        "recall@5": round(recall_at(rankings, chunks, 5), 4),
        "recall@10": round(recall_at(rankings, chunks, 10), 4),
        "recall@20": round(recall_at(rankings, chunks, CANDIDATE_POOL), 4),
        "mrr@10": round(mrr_at(rankings, chunks, 10), 4),
        "model_load_seconds": round(model_load_seconds, 2),
        "corpus_embed_seconds": round(corpus_seconds, 2),
        "query_median_ms": round(statistics.median(query_seconds) * 1000, 1),
        "query_p95_ms": round(
            sorted(query_seconds)[max(0, int(len(query_seconds) * 0.95) - 1)] * 1000, 1
        ),
        "vector_index_mb": round(len(chunks) * int(chunk_vectors.shape[1]) * 4 / (1024 * 1024), 2),
        "model_on_disk_mb": directory_size_mb(
            CACHE_DIR / f"models--{candidate.repo.replace('/', '--')}"
        ),
    }

    if reranked:
        result["recall@5_after_rerank"] = round(recall_at(reranked, chunks, 5), 4)
        result["mrr@10_after_rerank"] = round(mrr_at(reranked, chunks, 10), 4)

    if abstained:
        leaked = [value for value in abstained if value >= SIMILARITY_THRESHOLD]
        result["abstention_accuracy"] = round(1 - len(leaked) / len(abstained), 4)
        result["highest_unanswerable_similarity"] = round(max(abstained), 4)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=HERE / "corpus")
    parser.add_argument("--questions", type=Path, default=HERE / "questions.jsonl")
    parser.add_argument("--only", default=None, help="run a single candidate by name")
    parser.add_argument("--rerank", action="store_true", help="also score Recall@5 after reranking")
    parser.add_argument("--out", type=Path, default=HERE / "results" / "latest.json")
    args = parser.parse_args()

    documents = load_corpus(args.corpus)
    questions = load_questions(args.questions)

    if not documents:
        raise SystemExit(f"No .txt documents found in {args.corpus}")
    if not questions:
        raise SystemExit(f"No questions found in {args.questions}")

    chunks = build_chunks(documents)

    answerable_total = sum(1 for row in questions if row.get("answerable"))

    print(f"corpus   : {len(documents)} documents -> {len(chunks)} chunks")
    print(
        f"questions: {len(questions)} ({answerable_total} answerable, "
        f"{len(questions) - answerable_total} unanswerable)"
    )
    print(f"cache    : {CACHE_DIR}")
    print()

    if len(chunks) <= CANDIDATE_POOL:
        print(
            f"WARNING: only {len(chunks)} chunks, so recall@{CANDIDATE_POOL} will be 1.0 "
            "for every model. The harness works, but these numbers cannot choose a model."
        )
        print()

    reranker = None

    if args.rerank:
        print(f"loading reranker {RERANKER_REPO} ...")
        reranker = CrossEncoder(RERANKER_REPO, cache_folder=str(CACHE_DIR))

    results: list[dict[str, object]] = []

    for candidate in CANDIDATES:
        if args.only and candidate.name != args.only:
            continue

        print(f"running {candidate.name} ({candidate.repo}) ...")
        result = evaluate(candidate, chunks, questions, reranker)
        results.append(result)

        for key, value in result.items():
            if key not in {"model", "repo"}:
                print(f"  {key:34} {value}")
        print()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"wrote {args.out}")
    print()
    print("These numbers measure retrieval only. They are not answer accuracy,")
    print("and a small gap on a small question set is not meaningful.")


if __name__ == "__main__":
    main()
