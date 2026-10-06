# 01 - Tune: thread-count sweep

Model `gemma-4-E2B-it-UD-Q4_K_XL.gguf` · host `Linux-x86_64` · llama.cpp `b10488`
CPU: **8 physical · 16 logical** cores · `ngl=0` · metric `tg128`

| threads (-t) | tg128 (tok/s) | vs best |
|:--|--:|--:|
| 1 | 6.0 | 53% |
| 4 | 11.2 | 100% |
| 8 | 9.6 | 86% |
| 16 | 3.3 | 29% |
| 32 | 1.2 | 11% |

**Best**: `-t 4` at 11.2 tok/s
**Slowest tested**: `-t 32` at 1.2 tok/s (9.33x spread)
**Against the physical-core default** (`-t 8`, 9.6 tok/s): 1.16x

Use this in your run:

```bash
LAB_N_THREADS=4 make bench
```

## Your explanation

- **Vị trí của điểm uốn (Knee of the curve):** Hiệu năng decode đạt đỉnh cực đại tại **`-t 4` (11.2 tok/s)**, sau đó giảm dần ở `-t 8` (9.6 tok/s), sụp đổ mạnh ở `-t 16` (3.3 tok/s), và chạm đáy ở `-t 32` (1.2 tok/s). Chênh lệch giữa cấu hình tốt nhất và tệ nhất lên tới **9.33x**.
- **Giải thích cơ chế (Mechanism):**
  1. **Memory-Bandwidth Saturation:** Quá trình sinh token (decode) có tỷ lệ tính toán trên dung lượng nhớ (arithmetic intensity) cực thấp. Với mỗi token mới sinh ra, toàn bộ trọng số mô hình (~2.97 GB) phải được nạp liên tục từ bộ nhớ RAM vào cache CPU. Trên kiến trúc CPU AMD Ryzen 7 7435HS (kênh nhớ dual-channel DDR5), chỉ cần 4 luồng thực thi song song là đã bão hòa hoàn toàn băng thông đọc của bộ điều khiển bộ nhớ (memory bus).
  2. **Inter-core Contention & Cache Thrashing:** Khi tăng lên 8 luồng, các core vật lý bắt đầu cạnh tranh nhau về dung lượng L3 cache và băng thông bộ nhớ, đồng thời chi phí đồng bộ luồng (synchronization overhead) tăng lên, làm giảm tốc độ từ 11.2 tok/s xuống 9.6 tok/s.
  3. **Tác động tiêu cực của Hyperthreading/SMT (`-t 16`):** Khi kích hoạt 16 luồng (bao gồm cả logical cores), hai luồng logic trên cùng một nhân vật lý phải chia sẻ bộ nhớ đệm L1/L2 và pipeline thực thi. Trong tác vụ memory-bound, điều này không mang lại thêm năng lực tính toán mà ngược lại gây ra hiện tượng cache thrashing nghiêm trọng và kẹt tài nguyên bus, khiến throughput giảm tới 71% (xuống còn 3.3 tok/s).
  4. **Oversubscription (`-t 32`):** Ở mức 32 luồng, hệ điều hành phải liên tục thực hiện context switching, dẫn đến sụp đổ hiệu năng hoàn toàn (chỉ còn 1.2 tok/s).
- **Kết luận tinh chỉnh:** Cấu hình tối ưu nhất cho serving và inference trên máy này là **`LAB_N_THREADS=4`** (đạt 11.2 tok/s, mang lại speedup 1.16x so với mặc định 8 physical cores).
