# Evaluation report

Scores are question-level hit rates over the gold set in `evaluation_harness/gold_set.json`.

## Final scores

| Metric | What it measures | Score |
| --- | --- | ---: |
| Retrieval recall (union) | Gold chunk(s) in the dense/BM25 pool | 11/11 (100.0%) |
| Retrieval recall (rerank@5) | Gold chunk in the Cohere top 5 sent to generation | 11/11 (100.0%) |
| Answer accuracy | Generated answer contains every expected key group | 11/11 (100.0%) |
| Router accuracy | Lane is current vs history as labeled | 11/11 (100.0%) |
| Average latency | Mean end-to-end time per question | 17.71s |

## Latency

**Final average latency: 17.71s per question** (total 194.77s over 11 questions).

Wall time in seconds. Retrieve is dense+BM25 union. Total is the sum of stages.

| Stage | Mean | Total |
| --- | ---: | ---: |
| route | 2.31s | 25.46s |
| retrieve | 1.12s | 12.32s |
| rerank | 0.24s | 2.60s |
| generate | 14.04s | 154.39s |
| end-to-end | 17.71s | 194.77s |

## Per-question results

| id | lane | union | rerank@5 | answer | total s | generate s |
| --- | --- | --- | --- | --- | ---: | ---: |
| gym-minimum | current (llm) | pass | pass | pass | 23.97 | 20.71 |
| intern-gym-exempt | current (llm) | pass | pass | pass | 15.12 | 11.08 |
| caffeine-limit | current (llm) | pass | pass | pass | 18.64 | 15.11 |
| dog-adoption-leave | current (llm) | pass | pass | pass | 20.14 | 15.71 |
| email-joke | current (llm) | pass | pass | pass | 18.34 | 14.78 |
| foosball-winner-tokens | current (llm) | pass | pass | pass | 18.62 | 15.32 |
| token-allocation-current | current (llm) | pass | pass | pass | 16.34 | 12.65 |
| token-allocation-history | history (llm) | pass | pass | pass | 16.23 | 12.59 |
| hazmat-suit | current (llm) | pass | pass | pass | 17.15 | 13.33 |
| nuclear-shelter | current (llm) | pass | pass | pass | 14.93 | 11.39 |
| nuclear-history-wait | history (llm) | pass | pass | pass | 15.29 | 11.73 |
