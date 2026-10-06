# 01 - Measure: latency baseline

Model `Gemma 4 E2B` · host `Linux-x86_64` · llama.cpp `b10488`
Settings: `threads=8` `ngl=0` `ctx=2048`
`max_tokens=64` · warm-up discarded
Completed requests: `UD-Q4_K_XL` 10/10 · `UD-Q2_K_XL` 10/10

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 53954 | 447 / 502 | 94.9 / 100.5 | 6353 / 6780 / 6780 | 10.5 |
| UD-Q2_K_XL | 2.24 | 44838 | 484 / 568 | 64.5 / 69.6 | 4493 / 4797 / 4797 | 15.5 |

- **TTFT** = prefill. Short prompts keep it small; long-context RAG is where it explodes.
- **TPOT** = per-output-token decode cost, bounded by memory bandwidth. `decode tok/s = 1000 / TPOT_p50`.
- `UD-Q2_K_XL` decodes **1.48x faster** than `UD-Q4_K_XL` here, for 0.73 GB less on disk.

## Your observation

Lần chạy lại CPU-only, 8 threads: UD-Q4_K_XL đạt 10.5 tok/s, UD-Q2_K_XL đạt 15.5 tok/s (tỷ lệ compare/primary 1.48×). TPOT P50 lần lượt 94.94 và 64.49 ms; bản compare nhỏ hơn 0.73 GiB. Kết quả phù hợp với giả thuyết decode chịu ảnh hưởng của lưu lượng bộ nhớ, nhưng không đo trực tiếp bandwidth hoặc chi phí dequantization. Đã thử cùng prompt ở cả hai quantization; transcript bên dưới. Một câu hỏi chưa đủ kết luận chất lượng suy giảm. Giữ 4-bit cho serving theo lựa chọn đã ghi trong REFLECTION; cần kiểm tra chất lượng trước khi đổi.

## Same-prompt quality check

Prompt: Explain in two sentences how goodput@SLO differs from raw throughput. Mention TTFT and TPOT targets.

**UD-Q4_K_XL**

> Goodput@SLO measures the actual data delivered to the user within a specific Service Level Objective (SLO), whereas raw throughput is the total volume of data processed. Goodput@SLO is often evaluated in the context of latency targets like Time to First Byte (TTFT) and Time to Process (TPOT) to ensure both speed and data delivery meet service expectations.

**UD-Q2_K_XL**

> Goodput@SLO measures the *effective* throughput achieved by a system under specific Service Level Objectives (SLOs), focusing on the quality and reliability of the delivered service. Raw throughput, on the other hand, is a more fundamental metric measuring the sheer volume of data processed or transferred, irrespective of service quality.

Cùng temperature=0, seed=42, max_tokens=96, CPU-only, 8 threads. Một prompt chỉ là kiểm tra minh họa, không phải phép đánh giá chất lượng tổng quát. Raw request/response: `01-quality-comparison.json`.

Quan sát ở prompt này: Q4 viết sai tên TTFT (Time to First Byte) và TPOT (Time to Process); trong lab, chúng là Time to First Token và Time per Output Token. Q2 không nhắc TTFT/TPOT như prompt yêu cầu. Cả hai kết thúc bình thường (`finish_reason=stop`), nên các thiếu sót này không do hết ngân sách 96 token. Một ví dụ chưa xác lập chất lượng tương đối giữa hai quantization.
