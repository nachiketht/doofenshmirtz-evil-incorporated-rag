# Evaluation report

Scores are question-level hit rates over the gold set in `evaluation_harness/gold_set.json`.

## Final scores

| Metric | What it measures | Score |
| --- | --- | ---: |
| Retrieval recall (union) | Gold chunk(s) in the dense/BM25 pool | 11/11 (100.0%) |
| Retrieval recall (rerank@5) | Gold chunk in the Cohere top 5 sent to generation | 10/10 (100.0%) |
| Answer accuracy | Generated answer contains every expected key group | 11/11 (100.0%) |
| Router accuracy | Lane is current vs history as labeled | 11/11 (100.0%) |
| Average latency | Mean end-to-end time per question | 13.33s |

## Latency

**Final average latency: 13.33s per question** (total 146.58s over 11 questions).

Wall time in seconds. Retrieve is dense+BM25 union. Total is the sum of stages.

| Stage | Mean | Total |
| --- | ---: | ---: |
| route | 0.82s | 9.07s |
| retrieve | 0.36s | 4.01s |
| rerank | 1.83s | 18.29s |
| generate | 10.47s | 115.21s |
| end-to-end | 13.33s | 146.58s |

## Per-question results

| id | lane | union | rerank@5 | answer | total s | generate s |
| --- | --- | --- | --- | --- | ---: | ---: |
| gym-minimum | current (llm) | pass | pass | pass | 20.59 | 15.88 |
| intern-gym-exempt | current (llm) | pass | skip | pass | 10.93 | 9.78 |
| caffeine-limit | current (llm) | pass | pass | pass | 15.67 | 14.66 |
| dog-adoption-leave | current (llm) | pass | pass | pass | 14.58 | 13.61 |
| email-joke | current (llm) | pass | pass | pass | 11.52 | 10.54 |
| foosball-winner-tokens | current (llm) | pass | pass | pass | 7.49 | 6.55 |
| token-allocation-current | current (llm) | pass | pass | pass | 8.67 | 7.36 |
| token-allocation-history | history (llm) | pass | pass | pass | 10.80 | 9.73 |
| hazmat-suit | current (llm) | pass | pass | pass | 27.58 | 10.15 |
| nuclear-shelter | current (llm) | pass | pass | pass | 8.83 | 7.89 |
| nuclear-history-wait | history (llm) | pass | pass | pass | 9.93 | 9.07 |
