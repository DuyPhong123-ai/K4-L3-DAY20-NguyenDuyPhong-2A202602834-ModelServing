# 01 - Tune: thread-count sweep

Model `gemma-4-E2B-it-UD-Q4_K_XL.gguf` · host `Linux-x86_64` · llama.cpp `b10488`
CPU: **8 physical · 16 logical** cores · `ngl=0` · metric `tg128`

| threads (-t) | tg128 (tok/s) | vs best |
|:--|--:|--:|
| 1 | 6.2 | 51% |
| 4 | 11.9 | 98% |
| 8 | 12.2 | 100% |
| 16 | 3.3 | 27% |
| 32 | 1.2 | 10% |

**Best**: `-t 8` at 12.2 tok/s
**Slowest tested**: `-t 32` at 1.2 tok/s (10.12x spread)
**Against the physical-core default** (`-t 8`, 12.2 tok/s): 1.00x

Use this in your run:

```bash
LAB_N_THREADS=8 make bench
```

## Your explanation

Sweep đo tg128; cấu hình tốt nhất trong grid là 8 threads (12.15 tok/s), so với baseline 8 threads (12.15 tok/s): 1.00×.

Giả thuyết đã ghi trong REFLECTION là giới hạn bandwidth, tranh chấp cache và chi phí đồng bộ. Đây là các cơ chế có thể giải thích đường cong; chưa có hardware counters để phân biệt chúng. Không suy ra băng thông DDR5 bão hòa hoàn toàn hoặc mức tăng RPS serving từ sweep decode đơn lẻ. Log nguyên bản ở submission/logs/tune.txt.
