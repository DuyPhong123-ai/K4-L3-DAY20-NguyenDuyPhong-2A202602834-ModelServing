# 02 - Continuous batching under load (u50)

Host `Linux-x86_64` · `--parallel 4` · 29 samples over
60s at 2.0s intervals · raw CSV: `02-server-metrics-u50.csv`

| Gauge | Peak observed |
|:--|--:|
| `n_busy_slots_per_decode` (avg/decode) | 4.00 of 4 slots (100%) |
| `requests_processing` | 4 |
| `requests_deferred` | 46 |
| `kv_cache_usage_ratio` | n/a — not exported by llama.cpp `b10488` |
| `tokens_predicted_total` (final) | 993 |

Highest sampled value was **4.00 of 4** slots. Note this gauge is llama.cpp's *average* busy slots per decode step, so the number below is the highest average we sampled, not an instantaneous maximum batch width. A peak near 1 means
requests were served one at a time -- either the load was too light to overlap, or
they arrived too far apart. A peak approaching `--parallel` means the scheduler was
genuinely packing concurrent requests into shared decode steps.
`requests_deferred` went above zero: more requests arrived than there were slots, so some waited. These samples do not isolate how much queue time contributed to P95.

## Your observation

Peak của trung bình busy slots/decode là 4.00/4, processing peak 4, deferred peak 46. Gauge busy > 1 là bằng chứng gom nhiều request vào decode. Effective concurrency 10.0 tính từ request hoàn tất bao gồm thời gian chờ; khác với trung bình slot bận mỗi bước decode. Không gọi tỷ lệ này là mức sử dụng CPU/GPU hay batch width tức thời. Raw samples nằm trong CSV; metrics chạy chồng với load-50.
