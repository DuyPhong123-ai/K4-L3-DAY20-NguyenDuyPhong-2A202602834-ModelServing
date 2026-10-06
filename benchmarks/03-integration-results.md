# 03 - Integrate: RAG pipeline run

Host `Linux-x86_64` · llama.cpp `b10488` ·
retrieval backend: **keyword overlap** · 3 queries

| Query | Contexts retrieved | embed (ms) | retrieve (ms) | llm (ms) | total (ms) |
|:--|--:|--:|--:|--:|--:|
| Why is goodput more useful than raw throughp... | goodput, paged, radix | 0.0 | 0.1 | 6293.4 | 6293.6 |
| What problem does PagedAttention actually so... | paged, radix, disagg | 0.0 | 0.1 | 4411.5 | 4411.7 |
| When does splitting prefill and decode help?... | disagg, radix, batching | 0.0 | 0.1 | 3824.5 | 3824.6 |

Mean per stage (ms): embed **0.0** · retrieve **0.1** ·
llm **4843.1** · total **4843.3**
Dominant stage: **llm** (100% of total)

## Answers returned

**Why is goodput more useful than raw throughput?**

> Goodput@SLO counts only the requests per second that met the TTFT and TPOT targets. Throughput at saturation ignores SLOs.

**What problem does PagedAttention actually solve?**

> PagedAttention stores the KV cache in non-contiguous pages, which removes the internal fragmentation that wasted most GPU memory.

**When does splitting prefill and decode help?**

> Splitting prefill and decode helps because prefill is compute-bound and decode is memory-bandwidth-bound.


## Which N16-N19 pieces are real

N16 Cloud/IaC: stub, không triển khai cloud. N17 Data pipeline: stub, TOY_DOCS. N18 Lakehouse: stub, danh sách in-memory. N19 Vector + features: stub, keyword overlap, không dùng embedding model/vector database. N20 Serving: real, HTTP tới llama-server.

Mean: embed 0.0 ms, retrieve 0.1 ms, llm 4843.1 ms, total 4843.3 ms. LLM chiếm gần toàn bộ thời gian trong pipeline toy này; không khái quát sang RAG có retrieval thật. Ưu tiên đo thử GPU offload hoặc caching trên prefix thực sự trùng nhau. Chưa đo mức giảm 2×; streaming cải thiện thời gian nhìn thấy token đầu tiên, không giảm thời gian hoàn tất.
