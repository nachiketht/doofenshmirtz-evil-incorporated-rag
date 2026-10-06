# Doofenshmirtz Evil Inc RAG

Question answering over the Doofenshmirtz Evil Incorporated handbook: 100
versioned policies, FAQs, minutes, incident reports and a handful of
top-secret documents (`docs/`, PDF / DOCX / Markdown). Answers cite the policy,
version and section they came from, and every run can print a per-step
latency / token / cost trace.

## Setup

Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"            # core + tests
pip install -e ".[pinecone]"       # optional: Pinecone backend
pip install -e ".[local-rerank]"   # optional: local cross-encoder reranker
pip install -e ".[corpus]"         # optional: regenerate docs/ (python-docx, reportlab)
cp .env.example .env               # then fill in what you use
```

For live answers you need Ollama and, for the default reranker, a Cohere key:

```bash
ollama pull embeddinggemma:latest
ollama pull gemma3:4b
ollama pull gemma3:12b
```

The clients use `OLLAMA_HOST` (default `http://127.0.0.1:11434`). From a
container, Ollama usually lives at `http://host.docker.internal:11434`.

Everything is configured through environment variables or the gitignored
`.env`; `.env.example` lists every setting with its default.

## Quick start

```bash
python scripts/demo.py                       # offline tour, no models or keys needed
python scripts/compare_chunkers.py -q "How big must a self-destruct button be?"
python -m rag.ingest                         # read docs/, write ./chroma
python -m rag.retrieve "How big must a self-destruct button be?"
python -m rag.trace "What changed about password length between Password and Access Policy v1 and v3?"
python -m rag.trace "How many days of pet leave for a platypus?" --json
python -m rag.server                         # policy desk at http://127.0.0.1:8000
```

`python -m rag.trace` prints the answer, then a table with one row per pipeline
step (latency, share of total, input/output tokens, external calls, cost in
USD, models) and a total row. `--json` prints the same data as JSON, and
`--no-cache` bypasses the semantic cache. Prices come from
`src/rag/model_costs.json` (local Ollama models cost $0).

## Compare chunkers

Same question through every ready chunker (`structural`, `recursive`,
`parent_child`, `contextual`, `table_aware`). Prints chunk count, search
latency, generate latency, total, answer kind, and the top hit. Cache is off.
Offline (default) uses a hashing embedder and a temp Chroma store per
strategy. `--live` uses Ollama and the configured reranker but still writes
**local Chroma**, so Pinecone is not overwritten. Generate usually dominates
`--live` totals; the search column is the chunker effect.

```bash
python scripts/compare_chunkers.py
python scripts/compare_chunkers.py "How big must a self-destruct button be?"
python scripts/compare_chunkers.py -q "What colour is Agent P?"
python scripts/compare_chunkers.py --question "How many days of pet leave for a platypus?"
python scripts/compare_chunkers.py -q "How big must a self-destruct button be?" \
  --strategy structural --strategy recursive
python scripts/compare_chunkers.py --live -q "How big must a self-destruct button be?"
python scripts/compare_chunkers.py --live --keep .rag/chunker-demo --force \
  -q "How big must a self-destruct button be?"
```

Pass the query as a positional argument or with `-q` / `--question`. Repeat
`--strategy` to subset chunkers. `--keep DIR` reuses one Chroma subdir per
strategy; `--force` re-ingests those stores. `--docs` defaults to `docs/`.

## Policy desk (HTTP server)

Same pipeline as `python -m rag.trace`, served as a page and a small JSON API.
Ingest first so the store exists. From this container, set `OLLAMA_HOST` the
same way as the CLI.

```bash
python -m rag.server                         # http://127.0.0.1:8000
python -m rag.server --host 0.0.0.0 --port 8000
python -m rag.server --host 127.0.0.1 --port 8080
```

Open the printed URL in a browser. Type a question (prefix the access phrase
for top-secret docs, e.g. `ABCDEF: What colour is Agent P?`). The page shows
the answer, cited sections, and the latency / token / cost
trace. Useful / Off records the same vote as `python -m rag.feedback`.

```bash
curl -s http://127.0.0.1:8000/health
# {"ok": true}

curl -s http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"How big must a self-destruct button be?"}'

curl -s http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"ABCDEF: What colour is Agent P?","no_cache":true}'

curl -s http://127.0.0.1:8000/feedback \
  -H 'Content-Type: application/json' \
  -d '{"vote":"up"}'
# after an answer: {"ok": true, "vote": "up"}
```

| Method | Path | Body |
| --- | --- | --- |
| `GET` | `/` | HTML policy desk |
| `GET` | `/health` | process is up |
| `POST` | `/ask` | `{"question": "...", "no_cache": false}` — same JSON as `rag.trace --json` |
| `POST` | `/feedback` | `{"vote": "up"\|"down", "note": "..."}` — rates the last answer |

The first `/ask` loads models and the vector store; later requests reuse them.
Requests are handled one at a time. Embedding vectors are never sent on the
wire. The access phrase is stripped before models, the cache, or feedback see
the question.

## Restricted documents

Top-secret documents (Perry the Platypus countermeasures, Agent P sightings,
the escape blimp protocol, the master plan ledger) are only searchable when the
question starts with the six-letter access phrase:

```bash
# .env
RAG_ACCESS_PHRASE=ABCDEF        # exactly 6 letters, case-sensitive; empty = locked
```

```bash
python -m rag.retrieve "ABCDEF: What is the current Perry trap program code name?"
```

The phrase must be the first word and match exactly; it may be followed by a
space, `:` or `,`. It is stripped before the question reaches the router, the
models, the cache, the logs or the feedback file. Access is enforced with a
metadata filter in the vector store and re-checked on every hit, never by
prompting. Cached answers are partitioned by access level, and restricted
answers are kept in memory only (never written to `.rag/`).

## Ingest and document lifecycle

```bash
python -m rag.ingest [docs] [chroma] [--force] [--chunker contextual]
python -m rag.admin list | retire POLICY VERSION | restore POLICY VERSION | purge POLICY VERSION --yes
python -m rag.chunking stats --strategy table_aware
```

* Files must be named `Doofenshmirtz Evil Inc - <Title> v<N.N>.<pdf|docx|md>`.
  `docs/manifest.json` adds department, document type, classification and
  effective dates; a `TOP SECRET` banner always forces top-secret.
* Ingest is incremental: unchanged files (same bytes, chunker, extractor,
  embedding model and Matryoshka setting) are skipped, changed ones replace
  only their own chunks. Everything is embedded before the first write, so a
  failed embed leaves the store untouched. Each document write is retried
  twice. Newer versions automatically supersede older ones (`is_latest`,
  effective-to dates).
* A file removed from `docs/` is deleted from the store on the next ingest,
  and the whole semantic cache is cleared. Retired versions that are still on
  disk drop out of normal lookups but stay available for compares; `purge`
  deletes them and clears the cache the same way. A status set with
  `rag.admin retire|restore` overrides the manifest's `status` and survives
  re-ingest.
* Backends: `RAG_DB_BACKEND=chroma` (default, local) or `pinecone`
  (`PINECONE_API_KEY`, `PINECONE_INDEX`, `PINECONE_NAMESPACE`).

## Retrieval pipeline and algorithms

```
access gate -> embed -> semantic cache -> catalog -> route (lookup/compare)
  -> query rewrite (multi-query) -> dense ANN per query -> BM25 -> RRF fusion
  -> rerank -> MMR -> self-correction -> lost-in-the-middle ordering
  -> parent expansion -> generate -> cache store
```

| Technique | Where | Setting |
| --- | --- | --- |
| Chunkers: structural, recursive (token budget + overlap), parent-child, contextual (document/section prefix), table-aware | `rag/chunking.py` | `RAG_CHUNKER` |
| Metadata extraction (clause type, entities; heuristic or LLM) | `rag/extract.py` | `RAG_METADATA_EXTRACTOR` |
| Hybrid search: dense ANN plus BM25 over every chunk the filter allows, fused with reciprocal rank fusion | `rag/retrieve.py` | `RAG_CANDIDATE_K`, `RAG_FUSE_N`, `RAG_RRF_K` |
| Multi-query rewriting, fused with RRF | `rag/retrieve.py` | `RAG_MULTI_QUERY`, `RAG_NUM_QUERIES` |
| Rerankers: Cohere, local cross-encoder (bge-reranker), ensemble, automatic fallback | `rag/rerankers.py` | `RAG_RERANKER` |
| Maximal marginal relevance (diversity) | `rag/algorithms.py` | `RAG_MMR`, `RAG_MMR_LAMBDA` |
| Self-correcting retrieval: low relevance -> one rewrite -> "not found" | `rag/retrieve.py` | `RAG_SELF_CORRECT`, `RAG_MIN_COSINE`, `RAG_MIN_RERANK_SCORE` |
| Version targeting: any two versions ("v1 vs v3"), retired versions allowed | `rag/algorithms.py` | — |
| Point-in-time answers ("on 2024-06-01") from effective dates | `rag/lifecycle.py` | `RAG_AS_OF` |
| Metadata filters (department, clause type, document type, entity) | `RetrievalOptions` | — |
| Lost-in-the-middle context ordering | `rag/algorithms.py` | `RAG_LOST_IN_MIDDLE` |
| Parent-section expansion for generation | `rag/pipeline.py` | `RAG_EXPAND_PARENTS` |
| Matryoshka two-stage search (truncated-vector prefetch, full-vector rescoring) | `rag/matryoshka.py` | `RAG_MRL_DIMS`, `RAG_MRL_PREFETCH` |
| Semantic cache: 24h TTL, 256-entry LRU, full clear on delete | `rag/cache.py` | `RAG_CACHE`, `RAG_CACHE_MAX`, `RAG_CACHE_TTL`, `RAG_CACHE_THRESHOLD` |
| Tracing: per-step latency, tokens, cost | `rag/tracing.py` | `RAG_COST_TABLE` |

A cached answer is reused when the new question is at least `RAG_CACHE_THRESHOLD`
(0.95) cosine-similar, has the same content words, numbers, versions and dates
(stopwords and word order can differ), was asked at the same access level, and
is aimed at the same corpus fingerprint. Non-restricted answers are stored in
`.rag/semantic_cache.json` and keep aging from the time they were written,
including across process restarts.

```bash
python -m rag.cache purge
```

* Each entry lives **24 hours** (`RAG_CACHE_TTL=86400`). `0` turns the time
  limit off. An expired entry is a miss and is removed on the next lookup.
* The cache holds at most **256** answers (`RAG_CACHE_MAX`). Past that, the
  least recently used entry is dropped.
* `python -m rag.cache purge` clears every entry, in memory and on disk.
  Removing a file from `docs/` (on the next ingest) or `rag.admin purge` does
  the same. A content re-ingest changes the corpus fingerprint, so earlier
  answers stop matching and age out on their own.
* Restricted answers stay in memory only and end when the process exits.
  Restart `rag.server` after a delete so it drops the copy it loaded at startup.

## Feedback

Every answer is saved to `.rag/last_answer.json`. Rate it:

```bash
python -m rag.feedback up
python -m rag.feedback down --note "cited the old version"
python -m rag.feedback candidates      # thumbs-down questions, shaped as eval cases
python -m rag.feedback stats
```

Votes go to `.rag/feedback.jsonl` (gitignored) with the question, retrieved
chunks and answer. The access phrase is never stored, and text from top-secret
chunks is redacted.

## Tests and evaluation

```bash
env -u OLLAMA_HOST pytest                  # unit + integration, no network
python scripts/run_eval.py                 # offline eval: hashing embedder, heuristic router
python scripts/run_eval.py --live          # live eval: Ollama + Cohere, writes results/result.json
ollama pull gemma3:27b                    # judge only; larger than the gemma3:12b answerer
python scripts/run_eval.py --judge         # offline answers, then local judge
python scripts/run_eval.py --live --judge  # Ollama answers, then local judge
```

`--judge` asks local `gemma3:27b` through Ollama whether the generated prose
answers the question. It does not see the retrieved passages or the citation
block. Use `--live --judge` when the answers come from `gemma3:12b`. The
report adds a `jdg` column and a `judge=` total. The offline CI command does
not pass `--judge`.

The eval set (`tests/eval_set.py`) covers the original handbook, the new
documents, named-version lookups, compares between any two versions, restricted
questions that need the access phrase and leak checks that ask the same
questions without it. Reported metrics: recall@k, MRR, nDCG@k, answer accuracy
(required / banned phrases), citation accuracy, routing accuracy, leaks, p50 /
p95 latency and total cost, overall and per group. Restricted cases run only
when `RAG_ACCESS_PHRASE` is set (the offline harness uses its own test phrase).

The offline eval measures retrieval plumbing with deterministic fakes, not
model quality; use `--live` for real numbers. CI runs ruff (pinned) on `src`,
`tests` and `scripts`, the test suite, the offline eval with minimum recall /
accuracy and zero leaks, and checks the committed live results.

## Regenerating the corpus

```bash
pip install -e ".[corpus]"
python scripts/generate_corpus.py           # rewrites the generated docs + manifest
python scripts/generate_corpus.py --check   # verify docs/ matches the generator
python -m rag.chunking export            # rewrites chunks.json
```
