# 01 - Measure: latency baseline

Model `Gemma 4 E2B` · host `Linux-x86_64` · llama.cpp `b10488`
Settings: `threads=8` `ngl=0` `ctx=2048`
`max_tokens=64` · warm-up discarded
Completed requests: `UD-Q4_K_XL` 10/10 · `UD-Q2_K_XL` 10/10

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 63826 | 461 / 620 | 116.2 / 136.9 | 7682 / 9247 / 9247 | 8.6 |
| UD-Q2_K_XL | 2.24 | 48368 | 558 / 745 | 90.5 / 99.2 | 6199 / 6889 / 6889 | 11.0 |

- **TTFT** = prefill. Short prompts keep it small; long-context RAG is where it explodes.
- **TPOT** = per-output-token decode cost, bounded by memory bandwidth. `decode tok/s = 1000 / TPOT_p50`.
- `UD-Q2_K_XL` decodes **1.28x faster** than `UD-Q4_K_XL` here, for 0.73 GB less on disk.

## Your observation

Trên phần cứng máy thí nghiệm (AMD Ryzen 7 7435HS 8 cores/16 threads, CPU inference):
- **Tốc độ Decode (TPOT):** Bản `UD-Q2_K_XL` (2-bit) đạt tốc độ giải mã 11.0 tok/s so với 8.6 tok/s của `UD-Q4_K_XL` (4-bit), tăng tốc xấp xỉ **1.28x (28% speedup)**. Điều này hoàn toàn khớp với lý thuyết: giai đoạn decode của LLM có arithmetic intensity rất thấp (memory-bandwidth bound). Việc nén trọng số từ 4-bit xuống 2-bit giúp giảm 24.6% dung lượng dữ liệu cần chuyển từ RAM vào CPU cache ở mỗi token sinh ra, trực tiếp giảm TPOT từ 116.2 ms xuống 90.5 ms.
- **Thời gian khởi động (Load Time):** Bản 2-bit nhẹ hơn 0.73 GB (2.24 GB so với 2.97 GB) nên thời gian nạp model vào RAM giảm từ 63.8s xuống 48.4s (nhanh hơn ~24%).
- **Độ trễ TTFT (Prefill):** Giai đoạn prefill phụ thuộc nhiều hơn vào năng lực tính toán FLOPs (compute bound). TTFT của bản 2-bit cao hơn nhẹ (P50 558 ms so với 461 ms) do chi phí giải nén/dequantization trọng số 2-bit phức tạp hơn về mặt toán tử CPU.
- **Đánh đổi chất lượng (Quantization Trade-off):** Mặc dù bản 2-bit nhanh hơn và tiết kiệm dung lượng, độ phân giải 2-bit gây suy giảm perplexity và độ chính xác ngữ nghĩa rõ rệt hơn so với bản 4-bit (UD-Q4_K_XL). Đối với mô hình phục vụ tương tác thực tế hoặc RAG, bản 4-bit mang lại sự cân bằng tối ưu giữa tốc độ (8.6 tok/s đủ cho tốc độ đọc người dùng) và độ chính xác của câu trả lời.
