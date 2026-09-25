# Evaluation report

Scores are question-level hit rates over the gold set in `evaluation_harness/gold_set.json`.

## Final scores

| Metric | What it measures | Score |
| --- | --- | ---: |
| Retrieval recall (union) | Gold chunk(s) in the dense/BM25 pool | 11/11 (100.0%) |
| Retrieval recall (rerank@5) | Gold chunk in the Cohere top 5 sent to generation | 11/11 (100.0%) |
| Answer accuracy | Generated answer contains every expected key group | 11/11 (100.0%) |
| Router accuracy | Lane is current vs history as labeled | 11/11 (100.0%) |
| Average latency | Mean end-to-end time per question | 17.00s |

## Latency

**Final average latency: 17.00s per question** (total 187.00s over 11 questions).

Wall time in seconds. Retrieve is dense+BM25 union. Total is the sum of stages.

| Stage | Mean | Total |
| --- | ---: | ---: |
| route | 2.40s | 26.37s |
| retrieve | 1.17s | 12.85s |
| rerank | 0.20s | 2.20s |
| generate | 13.23s | 145.59s |
| end-to-end | 17.00s | 187.00s |

## Per-question results

| id | lane | union | rerank@5 | answer | total s | generate s |
| --- | --- | --- | --- | --- | ---: | ---: |
| gym-minimum | current (llm) | pass | pass | pass | 24.88 | 20.36 |
| intern-gym-exempt | current (llm) | pass | pass | pass | 13.87 | 10.07 |
| caffeine-limit | current (llm) | pass | pass | pass | 20.13 | 16.29 |
| dog-adoption-leave | current (llm) | pass | pass | pass | 15.73 | 12.29 |
| email-joke | current (llm) | pass | pass | pass | 16.82 | 13.30 |
| foosball-winner-tokens | current (llm) | pass | pass | pass | 13.70 | 10.10 |
| token-allocation-current | current (llm) | pass | pass | pass | 18.08 | 14.57 |
| token-allocation-history | history (llm) | pass | pass | pass | 17.59 | 13.32 |
| hazmat-suit | current (llm) | pass | pass | pass | 14.95 | 11.38 |
| nuclear-shelter | current (llm) | pass | pass | pass | 14.99 | 11.31 |
| nuclear-history-wait | history (llm) | pass | pass | pass | 16.25 | 12.60 |
