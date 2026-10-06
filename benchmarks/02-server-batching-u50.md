# 02 - Continuous batching under load (u50)

Host `Linux-x86_64` · `--parallel 4` · 29 samples over
60s at 2.0s intervals · raw CSV: `02-server-metrics-u50.csv`

| Gauge | Peak observed |
|:--|--:|
| `n_busy_slots_per_decode` (avg/decode) | 3.84 of 4 slots (96%) |
| `requests_processing` | 4 |
| `requests_deferred` | 46 |
| `kv_cache_usage_ratio` | n/a — not exported by llama.cpp `b10488` |
| `tokens_predicted_total` (final) | 1859 |

Highest sampled value was **3.84 of 4** slots. Note this gauge is llama.cpp's *average* busy slots per decode step, so the number below is the highest average we sampled, not an instantaneous maximum batch width. A peak near 1 means
requests were served one at a time -- either the load was too light to overlap, or
they arrived too far apart. A peak approaching `--parallel` means the scheduler was
genuinely packing concurrent requests into shared decode steps.
`requests_deferred` went above zero: more requests arrived than there were slots, so some waited. That wait is the queue time in your P95.

## Your observation

- **Độ rộng Batch cực đại (Peak Batch Width):** Chỉ số `n_busy_slots_per_decode` ghi nhận giá trị đỉnh **3.84 / 4 slots** (đạt 96% công suất tối đa). Cùng lúc đó, metric nội tại của server ghi nhận `requests_processing = 4` (toàn bộ 4 slot đều đang bận) và `requests_deferred = 46` (46 request phải chờ trong hàng đợi). Điều này cung cấp bằng chứng thực nghiệm rõ ràng rằng **Continuous Batching đang hoạt động hiệu quả**, scheduler của llama.cpp liên tục gom các request đồng thời vào cùng một bước giải mã.
- **So sánh với Effective Concurrency (Little's Law):**
  - Trong `02-server-results.md`, Effective Concurrency đo được là **11.9**, trong khi `n_busy_slots_per_decode` là **3.84**.
  - Hai con số này không hề mâu thuẫn mà phản ánh hai góc độ của hệ thống:
    - `3.84` (server gauge) đo số lượng request **thực sự đang được tính toán (compute in flight)** trong các slot decode tại một thời điểm. Con số này bị chặn trên bởi giới hạn phần cứng `--parallel 4`.
    - `11.9` (Little's Law) đo **tổng số lượng request đang tồn tại trong hệ thống (system residency)**, bao gồm cả compute time (xử lý ở 4 slot) VÀ queue time (nằm chờ trong hàng đợi 46 requests deferred).
  - Cả hai số liệu đều hoàn toàn đáng tin cậy: số liệu server gauge cho biết hiệu suất khai thác phần cứng (slot utilization = 96%), còn số liệu từ Little's Law vạch rõ tình trạng tắc nghẽn hàng đợi khi quá tải.
