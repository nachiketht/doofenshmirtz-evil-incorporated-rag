# Evaluation report

Scores are question-level hit rates over the gold set in `evaluation_harness/gold_set.json`.

## Final scores

| Metric | What it measures | Score |
| --- | --- | ---: |
| Retrieval recall (union) | Gold chunk(s) in the dense/BM25 pool | 11/11 (100.0%) |
| Retrieval recall (rerank@5) | Gold chunk in the Cohere top 5 sent to generation | 11/11 (100.0%) |
| Answer accuracy | Generated answer contains every expected key group | 11/11 (100.0%) |
| Router accuracy | Lane is current vs history as labeled | 11/11 (100.0%) |
| Average latency | Mean end-to-end time per question | 18.02s |

## Latency

**Final average latency: 18.02s per question** (total 198.24s over 11 questions).

Wall time in seconds. Retrieve is dense+BM25 union. Total is the sum of stages.

| Stage | Mean | Total |
| --- | ---: | ---: |
| route | 2.36s | 25.99s |
| retrieve | 1.15s | 12.59s |
| rerank | 0.25s | 2.80s |
| generate | 14.26s | 156.87s |
| end-to-end | 18.02s | 198.24s |

## Per-question results

| id | lane | union | rerank@5 | answer | total s | generate s |
| --- | --- | --- | --- | --- | ---: | ---: |
| gym-minimum | current (llm) | pass | pass | pass | 24.13 | 20.07 |
| intern-gym-exempt | current (llm) | pass | pass | pass | 16.91 | 13.04 |
| caffeine-limit | current (llm) | pass | pass | pass | 21.32 | 17.55 |
| dog-adoption-leave | current (llm) | pass | pass | pass | 15.86 | 12.24 |
| email-joke | current (llm) | pass | pass | pass | 21.37 | 17.78 |
| foosball-winner-tokens | current (llm) | pass | pass | pass | 17.02 | 13.22 |
| token-allocation-current | current (llm) | pass | pass | pass | 19.94 | 16.13 |
| token-allocation-history | history (llm) | pass | pass | pass | 17.18 | 13.64 |
| hazmat-suit | current (llm) | pass | pass | pass | 14.05 | 10.29 |
| nuclear-shelter | current (llm) | pass | pass | pass | 14.04 | 10.32 |
| nuclear-history-wait | history (llm) | pass | pass | pass | 16.42 | 12.60 |
