# Hybrid vs vector-only

Hybrid is the union of dense top 10 and BM25 top 10 (`src/retrieval/hybrid.py`). Vector-only is the same dense list with no BM25.

On most gold questions EmbeddingGemma already puts the right leaf in the dense top 10, so hybrid cannot “win” there. The query below is the counterexample: a rare lexical phrase that embeddings treat as office clutter and BM25 treats as an exact match.

## Query

```
What does the health policy say about alphabetizing the supply closet unprompted?
```

Gold leaf: `health-and-wellness-policy:v1.0:caffeine-guidelines:monitoring-and-tapering`
(`5.2 Monitoring and Tapering` — caffeine overconsumption symptoms include alphabetizing the supply closet unprompted.)

Replay:

```bash
python -m utility.show_compare --no-rerank "What does the health policy say about alphabetizing the supply closet unprompted?"
python -m utility.show_compare "What does the health policy say about alphabetizing the supply closet unprompted?"
```

## Vector-only (dense top 10)

The gold leaf is **absent**. Cosine ranks fridge ownership and acknowledgment sections instead. The same leaf sits at dense rank **17** if k is raised to 20 (cosine 0.26).

| dense | cosine | section |
| ---: | ---: | --- |
| 1 | 0.469 | Health 7. Acknowledgment |
| 2 | 0.469 | HR 7.1 Ownership |
| 3 | 0.450 | HR 8. Enforcement and Culture |
| 4 | 0.444 | Preparedness 11. Acknowledgment |
| 5 | 0.436 | HR 1. Purpose |
| 6 | 0.435 | HR 7.3 Weekend Abandonment |
| 7 | 0.422 | Preparedness 2. Scope |
| 8 | 0.422 | Health 2. Scope |
| 9 | 0.421 | Health 1. Purpose |
| 10 | 0.420 | Preparedness 7.2 AI Conduct |

A vector-only pipeline that sends the top 10 (or the Cohere top 5 of that list) never sees the caffeine rule.

## BM25 (sparse top 5)

| sparse | bm25 | section |
| ---: | ---: | --- |
| **1** | **14.57** | **Health 5.2 Monitoring and Tapering** |
| 2 | 7.40 | Time & Usage 2. Scope |
| 3 | 5.86 | Preparedness 3.2 Weapon Eligibility |
| 4 | 5.14 | Health 2. Scope |
| 5 | 5.01 | HR 7.3 Weekend Abandonment |

## Hybrid

Union by chunk id: gold has `dense_rank=None`, `sparse_rank=1`. It is the first BM25-only leftover after the 10 dense hits.

Cohere `rerank-v3.5` over that union:

| rerank | score | dense | sparse | section |
| ---: | ---: | ---: | ---: | --- |
| **1** | **0.778** | — | 1 | **Health 5.2 Monitoring and Tapering** |
| 2 | 0.037 | 10 | — | Preparedness 7.2 AI Conduct |
| 3 | 0.023 | 3 | — | HR 8. Enforcement and Culture |
| 4 | 0.020 | 7 | — | Preparedness 2. Scope |
| 5 | 0.017 | — | 2 | Time & Usage 2. Scope |

Hybrid recall of the gold leaf is 1 where vector-only is 0. Rerank then puts that BM25-only hit first for generation.

Live check: `tests/test_hybrid_outperform.py` (skipped when Chroma is empty).
