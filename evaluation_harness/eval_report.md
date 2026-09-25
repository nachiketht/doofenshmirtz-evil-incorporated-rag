# Evaluation report

Scores are question-level hit rates over the gold set in `evaluation_harness/gold_set.json`.

## Final scores

| Metric | What it measures | Score |
| --- | --- | ---: |
| Retrieval recall (union) | Gold chunk(s) in the dense/BM25 pool | 11/11 (100.0%) |
| Retrieval recall (rerank@5) | Gold chunk in the Cohere top 5 sent to generation | 11/11 (100.0%) |
| Answer accuracy | Generated answer contains every expected key group | 11/11 (100.0%) |
| Router accuracy | Lane is current vs history as labeled | 11/11 (100.0%) |

## Per-question results

| id | lane | union | rerank@5 | answer |
| --- | --- | --- | --- | --- |
| gym-minimum | current (llm) | pass | pass | pass |
| intern-gym-exempt | current (llm) | pass | pass | pass |
| caffeine-limit | current (llm) | pass | pass | pass |
| dog-adoption-leave | current (llm) | pass | pass | pass |
| email-joke | current (llm) | pass | pass | pass |
| foosball-winner-tokens | current (llm) | pass | pass | pass |
| token-allocation-current | current (llm) | pass | pass | pass |
| token-allocation-history | history (llm) | pass | pass | pass |
| hazmat-suit | current (llm) | pass | pass | pass |
| nuclear-shelter | current (llm) | pass | pass | pass |
| nuclear-history-wait | history (llm) | pass | pass | pass |
