# 02 - Serve: load test + saturation reading

Host `Linux-x86_64` · llama.cpp `b10488` ·
`--parallel 4` · `ctx=2048` · `threads=8` ·
`ngl=0`

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 23 | 0.37 | 22000 | 34000 | 42000 | 8.5 | 0.0% |
| 50 | 23 | 0.36 | 20000 | 63000 | 63000 | 10.0 | 0.0% |

*Effective concurrency = RPS x average latency (Little's Law) -- how many requests were
really in flight, regardless of how many users locust simulated. It counts queued requests
too, so the occupancy/slot ratio can legitimately exceed 1.0; it is occupancy, not
utilisation. For true slot utilisation use the server's own gauges (`make metrics`).*

## What these two runs say

| Going from 10 to 50 users | |
|:--|--:|
| Offered load | 5x |
| Throughput actually delivered | **1.00x** (20% of linear) |
| P95 latency | **1.85x** |
| Effective concurrency at 50 users | 10.0 vs `--parallel 4` slots (occupancy/slot ratio 2.50) |

**Saturated.** Throughput delivered only 1.00x for 5x the offered load, and effective concurrency (10.0) is at or above all 4 decode slots. These are saturation signals at the tested load. Two short runs do not locate the exact saturation threshold or separate queue time from compute time; corroborate queueing with the server's deferred-request gauges.


## Your reading

Tăng từ 10 lên 50 users, RPS gần như giữ nguyên (0.37 và 0.36), còn P95 tăng từ 34 lên 63 giây. Cùng với 4 slot bận và 46 request deferred, đây là dấu hiệu bão hòa. Mỗi lượt chỉ hoàn tất 23 request nên chưa xác định chính xác ngưỡng bão hòa. Tôi sẽ thử giảm TPOT bằng quant nhỏ hơn trước; GPU offload cần kiểm tra runtime thấy GPU.
