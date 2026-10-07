# Workflow: current RAG structure

Pipeline as implemented now (`src/rag/pipeline.py`, `src/rag/retrieve.py`, `src/rag/ingest.py`). Setup, env vars, and commands are in README.md. This checkout answers from Pinecone (`doofenshmirtz-policies`, namespace `dev`) with Matryoshka prefetch at 512 dimensions. `RAG_TOP_N` is 5.

## Question answering

```mermaid
flowchart TD
    Q[Question] --> G[Access gate<br/>parse_access]
    G -->|strip 6-letter phrase| E[Embed query<br/>embeddinggemma 768-d]
    E --> C[Load catalog for access level]
    C --> Cache{Semantic cache hit?<br/>same level + corpus fingerprint<br/>+ same content words}
    Cache -->|yes| Out[Return cached answer]
    Cache -->|no| R[Router gemma3:4b<br/>temperature 0, JSON<br/>lookup or compare]
    R -->|compare, policy in catalog| Cmp[Search the two versions<br/>pair by heading, rerank, top 5]
    R -->|compare, unknown policy| Look
    R -->|lookup| AsOf{Question or RAG_AS_OF names a date?}
    AsOf -->|yes| PIT[Documents in force that day<br/>narrowed when the router named a policy]
    AsOf -->|no| Scope{Question names a version<br/>and the router named that policy?}
    Scope -->|yes| Pin[That policy and version only<br/>invented versions are ignored]
    Scope -->|no| All[Latest version of every visible document]
    Pin --> MQ
    All --> MQ
    PIT --> MQ[Multi-query rewrite]
    MQ --> Search[Dense ANN + BM25 fused with RRF]
    Search --> MRL{RAG_MRL_DIMS set?}
    MRL -->|yes| S1[Prefetch truncated vectors]
    S1 --> S2[Rescore shortlist with full vectors]
    S2 --> RR
    MRL -->|no| RR[Rerank Cohere / local / ensemble]
    RR --> MMR[MMR, keep top 5]
    MMR --> Low{Cosine under 0.3<br/>or rerank under 0.1?}
    Low -->|yes| SC[Rewrite the query once]
    SC --> Search
    Low -->|still low or no hits| NF[Not found<br/>no answer is generated]
    Low -->|ok| Sib[Lookup only: add other chunks<br/>from the same sections]
    Cmp --> Gen
    Sib --> Par[Expand to parent section text]
    Par --> LIM[Lost-in-the-middle reorder]
    LIM --> Gen[Generate gemma3:12b<br/>answer plus citation lines]
    Gen --> Store[Cache store<br/>restricted stays in memory<br/>not-found is not cached]
    Store --> Out
    NF --> Out
```

A lookup does not trust the router to pick the document. The router still decides lookup versus compare, and it still names the policy for a compare and for a version the question itself names ("what did HR Policy 1.0 say"). "What changed between the current and previous version" stays on the compare path: no version numbers means previous versus latest.

After retrieval, section siblings can make the prompt longer than 5 chunks. The policy desk (`python -m rag.server`) shows at most 5 citation cards, in the order the passages were given to the model. The page is read from disk on each request. The server process keeps the Python it imported at startup, so restart it after a code change.

Access levels: without the phrase, only `public` / `internal`. With `RAG_ACCESS_PHRASE` as the first word, `top-secret` is included. The phrase never reaches the router, models, cache, or feedback file.

## Ingest

```mermaid
flowchart TD
    Docs[docs/ PDF DOCX MD + manifest.json] --> Hash[SHA-256 of bytes + chunker + extractor + MRL tag]
    Hash --> Skip{Same hash in store?}
    Skip -->|yes| Meta[Metadata-only update if manifest changed]
    Skip -->|no| Read[Read + chunk + extract + validate]
    Read --> Emb[Embed all pending documents first]
    Emb --> Del[Delete that policy+version only]
    Del --> Up[Upsert chunks]
    Up --> Cat[put_document catalog row]
    Cat --> Life[lifecycle: is_latest, effective_to]
    Meta --> Life
    Life --> Gone{File missing from docs/?}
    Gone -->|yes| Drop[Delete that policy+version and clear the whole cache]
    Life --> Store[(Chroma collection or<br/>Pinecone index + namespace)]
    Store --> MRL{MRL on?}
    MRL -->|yes| Small[(Sibling store of truncated vectors<br/>policies_mrlN or index-mrlN)]
```

Failed embeds abort before any delete. `admin retire|restore` writes `admin_status`, which survives re-ingest.

## Stores and models

```mermaid
flowchart LR
    subgraph models
        Emb[embeddinggemma]
        Route[gemma3:4b]
        Ans[gemma3:12b]
        Judge[gemma3:27b<br/>eval --judge only]
        Cohere[Cohere rerank-v3.5]
    end
    subgraph stores
        Chroma[Chroma policies]
        PC[Pinecone doofenshmirtz-policies<br/>ns=dev + dev__documents]
        MRL[Optional mrl128 / mrl256 / mrl512]
    end
    Emb --> Chroma
    Emb --> PC
    Emb --> MRL
    Route --> PC
    Cohere --> Ans
```

From this container, Ollama is at `OLLAMA_HOST=http://host.docker.internal:11434`.

| Command | Role |
| --- | --- |
| `python -m rag.ingest` | Read `docs/`, write the configured store |
| `python -m rag.retrieve "…"` | Answer one question |
| `python -m rag.trace "…"` | Same path, plus per-step latency / tokens / cost |
| `python -m rag.server` | Policy desk at http://127.0.0.1:8000 |
| `python -m rag.admin list\|retire\|restore\|purge` | Document lifecycle |
| `python -m rag.feedback up\|down` | Rate the last answer |
| `python scripts/run_eval.py` | Offline eval |
| `python scripts/run_eval.py --live` | Live eval, writes `results/result.json` |

Switch backend with `RAG_DB_BACKEND=chroma|pinecone` and Matryoshka with `RAG_MRL_DIMS=0|128|256|512`. After changing MRL dims, ingest again so the sibling index is filled.

## Eval

`tests/eval_set.py` is the fixed set: original handbook, new documents, named-version lookups, compares, restricted questions, and leak checks. Recall, MRR, and nDCG are scored on the reranked retrieval list, before siblings are inserted and before lost-in-the-middle reorders the prompt. Answer checks use word boundaries, so a comma after a word still counts and `1,000` does not match inside `1,000,000`.

Last live run (`results/result.json`, k=5): recall 1.000, MRR 0.947, nDCG 0.960, accuracy 1.000, citation 1.000, routing 1.000, leaks 0. Median latency 22.3s, p95 29.0s.
