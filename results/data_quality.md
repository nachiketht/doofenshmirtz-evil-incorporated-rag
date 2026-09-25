# Data quality diagnosis

The corpus includes outdated duplicates: v1 PDFs sit next to v2 DOCX files for the same policy. The files disagree on material rules. Naive RAG retrieves both, so the model hedges. That is a **source-data** problem, not a retrieval or generation bug.

Mitigation: the router sends “current rule” questions to in-force leaves only (`change_status != stale`) and “what changed / old version” questions to the full history pool.

## Primary: Preparedness nuclear protocol


|           | `Preparedness Policy v1.0.pdf`                                                                          | `Preparedness Policy v2.0.docx`                                  |
| --------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Shelter   | Under the desk (`4.1 Shelter Position`). Called the only sanctioned position.                           | Break-room industrial refrigerator (`4.1 Shelter Location`).     |
| All-clear | Employees may go outside after **two hours** (`4.2 All-Clear Timing`). Radiation is assumed acceptable. | Remain indoors for **two weeks** (`4.3 Duration of Sheltering`). |


A question such as “when can I go outside after a blast?” matches both sections. Without a version filter, both chunks look live. The answer becomes two hours, two weeks, or an ambiguous mix. Chunking, embeddings, and the generator are doing what they should with conflicting excerpts.

## Secondary: Time & Usage token allocation


|            | `Time and Usage Policy v1.0.pdf`                  | `Time and Usage Policy v2.0.docx`              |
| ---------- | ------------------------------------------------- | ---------------------------------------------- |
| Allocation | **1,000,000** tokens each six-hour cycle (`5.1`). | **500,000** tokens (`6.1 Allocation Amount`).  |
| Transfers  | Gifting and pooling prohibited (`8.1`).           | Winner-takes-tokens foosball transfer (`4.2`). |


Same pattern: “how many tokens do I get?” retrieves both numbers unless stale v1 is dropped.

## Why this is not a pipeline bug

1. Both versions are real files in `docs/` and both are ingested on purpose.
2. The questions are semantically identical across versions, so dense search ranks both.
3. Once both excerpts are in the prompt, a grounded model should surface the conflict rather than invent a third number.
4. After ingest, v1 nuclear and token leaves are marked `stale` and v2 `added`. The router is a retrieve-time filter on that metadata. It does not rewrite the PDFs.



## What the router does

- **Current** (default): drop `stale`. “Where should I shelter?” → refrigerator / two weeks. “How many tokens per cycle?” → 500,000.
- **History** (what changed, old version, comparison): keep v1. State previously … / now … (two hours → two weeks; 1,000,000 → 500,000).

Eval cases `nuclear-shelter`, `nuclear-history-wait`, `token-allocation-current`, and `token-allocation-history` check both lanes.