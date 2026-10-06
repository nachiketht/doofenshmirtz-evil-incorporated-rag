# Workflow: current RAG structure

This is the pipeline as implemented on `feat/enterprise-upgrade` (`src/rag/pipeline.py`, `src/rag/retrieve.py`, `src/rag/ingest.py`). `ARCHITECTURE-RAG.md` describes the earlier Chroma-only v1.

## Question answering

```mermaid
flowchart TD
    Q[Question] --> G[Access gate<br/>parse_access]
    G -->|strip 6-letter phrase| E[Embed query<br/>embeddinggemma 768-d]
    E --> C[Load catalog for access level]
    C --> Cache{Semantic cache hit?<br/>same level + corpus fingerprint}
    Cache -->|yes| Out[Return cached answer]
    Cache -->|no| R[Router gemma3:4b<br/>lookup or compare + optional policy/version]
    R -->|compare| Cmp[Search older + newer versions<br/>pair by heading]
    R -->|lookup| MQ[Multi-query rewrite]
    MQ --> Search[Dense ANN + BM25 fused with RRF]
    Search --> MRL{RAG_MRL_DIMS set?}
    MRL -->|yes| S1[First pass: truncated-vector index]
    S1 --> S2[Rescore shortlist with full vectors]
    S2 --> RR
    MRL -->|no| RR[Rerank Cohere / local / ensemble]
    RR --> MMR[MMR diversity]
    MMR --> Low{Low cosine or rerank score?}
    Low -->|named policy miss| Broad[Broaden to all latest documents]
    Broad --> Low
    Low -->|still low| SC[Rewrite query once]
    SC --> Search
    Low -->|ok| LIM[Lost-in-the-middle reorder]
    Cmp --> Gen
    LIM --> Gen[Generate gemma3:12b + citations]
    Gen --> V[Lexical verify]
    V --> Store[Cache store<br/>restricted stays in memory]
    Store --> Out
```

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
        Cohere[Cohere rerank-v3.5]
    end
    subgraph stores
        Chroma[Chroma policies]
        PC[Pinecone doofenshmirtz-policies<br/>ns=dev + dev__documents]
        MRL[Optional mrl256 / mrl512 index]
    end
    Emb --> Chroma
    Emb --> PC
    Emb --> MRL
    Route --> PC
    Cohere --> Ans
```

| Command | Role |
| --- | --- |
| `python -m rag.ingest` | Read `docs/`, write the configured store |
| `python -m rag.retrieve "…"` | Answer one question |
| `python -m rag.trace "…"` | Same path, plus per-step latency / tokens / cost |
| `python -m rag.admin list\|retire\|restore\|purge` | Document lifecycle |
| `python -m rag.feedback up\|down` | Rate the last answer |

Switch backend with `RAG_DB_BACKEND=chroma|pinecone` and Matryoshka with `RAG_MRL_DIMS=0|128|256|512`. After changing MRL dims, ingest again so the sibling index is filled.
