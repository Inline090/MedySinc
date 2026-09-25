# Embedding model retrieval benchmark

Measures one thing: **for each candidate model, how often does it retrieve a chunk
that actually answers the question?**

No LLM is involved. Nothing here measures answer quality, faithfulness or citation
correctness. Those depend on the prompt, not on the embedding model.

## Running it

```powershell
cd apps\api
uv run python benchmarks\run.py
uv run python benchmarks\run.py --rerank          # also score Recall@5 after the cross-encoder
uv run python benchmarks\run.py --only bge-m3     # one model
```

Results are written to `benchmarks/results/latest.json`.

## What is in here

```
corpus/          one .txt file per document
questions.jsonl  one labelled question per line
run.py           the runner
results/         output
```

## Adding your own data

**Documents** — drop `.txt` files into `corpus/`. Plain text, one file per document.
They get chunked by the same code the app uses (`app/ai/chunking.py`), so the chunk
size and overlap match production.

**Questions** — one JSON object per line in `questions.jsonl`:

```json
{"question": "what was my hba1c", "answerable": true, "expect": ["7.4 percent"]}
{"question": "what is my insurance number", "answerable": false, "expect": []}
```

`expect` is a list of text markers. A retrieved chunk counts as relevant if it
contains **any** of them, compared case-insensitively. Markers are used instead of
chunk ids so the labels survive a change to the chunk size.

`"answerable": false` means the right answer is "nothing found". Those rows are
**excluded from recall** and measured as abstention instead. Counting them as
retrieval misses would punish the system for behaving correctly.

## Metrics

| Metric | Meaning |
|---|---|
| `recall@5` `@10` `@20` | Share of answerable questions where a relevant chunk is in the top k, **before** reranking |
| `mrr@10` | Mean of `1 / rank` of the first relevant chunk, 0 if none in the top 10 |
| `recall@5_after_rerank` | Recall@5 after the cross-encoder re-scores the top 20 (with `--rerank`) |
| `abstention_accuracy` | Share of unanswerable questions whose best similarity stays below the threshold |
| `corpus_embed_seconds` | Time to embed the whole corpus |
| `query_median_ms` `query_p95_ms` | Per-question embedding time |
| `vector_index_mb` | Storage the vectors would take, at 4 bytes per dimension |
| `model_on_disk_mb` | Download size of the model |

**Why `recall@20` matters more than it looks.** The reranker can rescue a weak
embedding model — it re-scores the top 20 and can promote a chunk that the model had
ranked 14th. So `recall@5` alone can make two very different models look identical.
`recall@20` before reranking is where the embedding model's own contribution shows.

## Candidate models

Defined in `CANDIDATES` at the top of `run.py`:

| Name | Repository | Notes |
|---|---|---|
| `bge-m3` | `BAAI/bge-m3` | What MedSync currently uses |
| `medembed-large` | `abhinand/MedEmbed-large-v0.1` | Medical fine-tune, built on a BGE base model |
| `pubmedbert-msmarco` | `pritamdeka/S-PubMedBert-MS-MARCO` | Verify this checkpoint before quoting results |

**The query prefix is per model and it matters.** E5 models need `"query: "`, some BGE
variants want an instruction on the query only. Getting this wrong means you are
measuring your mistake rather than the model. Check each model card.

Two names from earlier discussions were deliberately left out. `zembed-1` only has a
vendor's own blog post claiming it wins — no model card, no independent benchmark.
`PubMedBERT` on its own is not a retrieval model; you need a specific
sentence-transformers checkpoint, which is why one is named above.

## Limits — read before quoting a number

**The sample corpus is scaffolding.** It exists to prove the harness runs end to end.
It produces roughly a handful of chunks, which means `recall@20` will come out at
`1.0` no matter which model you use. **Those numbers cannot choose a model.** Replace
the corpus and the questions with real ones first.

**This is exact search, not your pipeline.** Vectors are held in memory and compared
with a plain dot product, so HNSW approximation is not measured, and neither is
hybrid retrieval or Reciprocal Rank Fusion. It isolates the embedding model on
purpose — but it is not the same as the shipped system.

**A small question set cannot resolve a small difference.** With 40 questions, a gap
of one or two questions is noise. If two models come out close, the honest conclusion
is "comparable on this set", and the useful next step is to read which questions each
one gets wrong rather than to declare a winner.

**Build the question set to target the weak spots.** If every question is ordinary,
a general model and a medical model will score the same and you will learn nothing.
Include abbreviation queries (`b.i.d.` versus "twice a day"), synonym queries
(`Tylenol` versus "acetaminophen"), exact-term queries, cross-document queries, and
unanswerable ones.
