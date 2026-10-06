# 02 - Serve: load test + saturation reading

Host `Linux-x86_64` · llama.cpp `b10488` ·
`--parallel 4` · `ctx=2048` · `threads=8` ·
`ngl=0`

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 13 | 0.23 | 25000 | 53000 | 53000 | 6.7 | 0.0% |
| 50 | 21 | 0.38 | 32000 | 51000 | 56000 | 11.9 | 0.0% |

*Effective concurrency = RPS x average latency (Little's Law) -- how many requests were
really in flight, regardless of how many users locust simulated. It counts queued requests
too, so the occupancy/slot ratio can legitimately exceed 1.0; it is occupancy, not
utilisation. For true slot utilisation use the server's own gauges (`make metrics`).*

## What these two runs say

| Going from 10 to 50 users | |
|:--|--:|
| Offered load | 5x |
| Throughput actually delivered | **1.60x** (32% of linear) |
| P95 latency | **0.96x** |
| Effective concurrency at 50 users | 11.9 vs `--parallel 4` slots (occupancy/slot ratio 2.97) |

**Saturated.** Throughput delivered only 1.60x for 5x the offered load, and effective concurrency (11.9) is at or above all 4 decode slots. Saturation sets in somewhere at or below 50 users; the load you added beyond that point became queue time rather than throughput.

P95 grew no faster than throughput (0.96x vs 1.60x), so this server still has headroom at 50 users.

> **Small sample.** Only 13 requests completed in the
> shorter run, so these percentiles are indicative rather than solid. Note also that
> locust averages only *completed* requests: when the run ends with requests still
> queued, effective concurrency is an **under**-estimate. Trust the throughput-scaling
> row over the concurrency row here, and run longer (`-t 3m`) if you want firmer numbers.

## Your reading

- **Điểm bão hòa và Bằng chứng số liệu (Saturation Evidence):**
  1. Khi tăng tải từ 10 lên 50 người dùng (tăng **5.0x offered load**), throughput thực tế của hệ thống chỉ tăng từ 0.23 RPS lên 0.38 RPS (**tăng 1.60x**, chỉ đạt 32% mức tăng tuyến tính lý tưởng).
  2. Áp dụng định luật Little ($L = \lambda \times W$), số lượng request đồng thời trong hệ thống (Effective Concurrency) tại 50 users là **11.9 requests**, trong khi server chỉ có tối đa `--parallel 4` slot xử lý song song. Tỷ lệ occupancy/slot đạt **2.97**, chứng minh rõ ràng hệ thống đã bão hòa tài nguyên tính toán ngay từ ngưỡng dưới 50 users. Lượng tải dư thừa bị dồn vào hàng đợi (queueing delay), khiến độ trễ trung vị P50 tăng từ 25.0s lên 32.0s.
- **Biện pháp nâng cao Goodput@SLO:**
  - Knob cần can thiệp đầu tiên là **tăng tốc độ giải mã (TPOT) bằng mô hình lượng tử hóa nhẹ hơn (chuyển sang `UD-Q2_K_XL`) hoặc offload GPU (`-ngl`)**: Vì server bị nghẽn ở giai đoạn decode của 4 slots hiện tại, giảm TPOT giúp mỗi slot hoàn thành và giải phóng nhanh hơn, trực tiếp nâng trần RPS và giảm hàng đợi tồn đọng mà không làm tràn bộ nhớ KV cache như việc tăng `--parallel` thuần túy trên CPU.
