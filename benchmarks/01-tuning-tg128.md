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

8 threads tốt nhất: 12.15 tok/s, gần với 11.86 tok/s ở 4 threads. Tăng lên 16 và 32 threads làm tốc độ giảm còn 3.28 và 1.20 tok/s. Tôi nghĩ tranh chấp bộ nhớ và chi phí đồng bộ góp phần gây giảm tốc, nhưng chưa đo trực tiếp. Tuning không cải thiện baseline 8 threads.
