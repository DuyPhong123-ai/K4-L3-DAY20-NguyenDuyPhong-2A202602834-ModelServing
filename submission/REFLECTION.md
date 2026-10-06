# Reflection — Day 20 Lab (Personal Report)

**Họ Tên:** Nguyễn Duy Phong
**MSSV:** 2A202602834
**Cohort:** K4
**Ngày submit:** 2026-10-06

---

## 1. Hardware & runtime

- **OS:** Ubuntu trong WSL 2 trên Windows; hardware.json là probe WSL của lần chạy lại.
- **CPU:** AMD Ryzen 7 7435HS
- **Cores:** 8 physical / 16 logical
- **CPU extensions:** AVX2
- **RAM:** 7.7 GB (WSL) / 16 GB physical
- **Accelerator:** NVIDIA GeForce RTX 3050 Laptop GPU (4096 MiB)
- **llama.cpp asset đã tải:** llama-b10488-bin-ubuntu-vulkan-x64.tar.gz
- **Model đã dùng:** Gemma 4 E2B (đọc từ `models/active.json`)
- **Quantization:** UD-Q4_K_XL + UD-Q2_K_XL (từ `models/active.json`)

**Chạy ở đâu:** laptop của tôi

**Setup:**

Windows chặn DLL của server nên tôi chuyển sang WSL 2. Tôi dùng CPU, 8 threads, ctx 2048 và 4 slots ở cổng 8090. WSL có 7.7 GB RAM; dù probe khuyên dùng Qwen nhỏ hơn, Gemma đã tải vẫn chạy được.

---

## 2. Đo lường

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 53954 | 447 / 502 | 94.9 / 100.5 | 6353 / 6780 / 6780 | 10.5 |
| UD-Q2_K_XL | 2.24 | 44838 | 484 / 568 | 64.5 / 69.6 | 4493 / 4797 / 4797 | 15.5 |

**Nhận xét:**

2-bit decode nhanh 1.48×, nhỏ hơn 0.73 GiB. Với cùng prompt, Q4 giải thích sai tên TTFT/TPOT; Q2 bỏ hai chỉ số. Một câu hỏi chưa đủ so chất lượng. Tôi giữ 4-bit làm baseline serving và sẽ kiểm tra thêm trước khi đổi.

---

## 3. Serving under load

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 23 | 0.37 | 22000 | 34000 | 42000 | 8.5 | 0.0% |
| 50 | 23 | 0.36 | 20000 | 63000 | 63000 | 10.0 | 0.0% |

- **Offered load tăng 5×, throughput thực tăng:** 1.00×
- **P95 thay đổi:** 1.85×
- **Effective concurrency ở 50 users:** 10.0 so với 4 slots

**Peak `llamacpp:n_busy_slots_per_decode`** (từ `make metrics` khi `make load-50` đang
chạy): 4.00 / 4 slots (peak của trung bình mỗi decode step)

**Nhận xét:**

Tải tăng 5×, RPS tăng 1.00×; P95 thay đổi 1.85×. Concurrency 10.0, peak deferred 46 cho thấy có queue. Mẫu hoàn tất ít, chưa xác định chính xác ngưỡng bão hòa. Tôi sẽ thử giảm TPOT bằng quant nhỏ hơn hoặc GPU offload; chưa đo hiệu quả.

---

## 4. Integration

| Day | Piece | Real hay stub? |
|---|---|---|
| N16 Cloud/IaC | không triển khai cloud/IaC | stub |
| N17 Data pipeline | TOY_DOCS, không ingestion thật | stub |
| N18 Lakehouse | danh sách tài liệu in-memory | stub |
| N19 Vector + features | keyword overlap, không embedding/vector DB | stub |
| N20 Serving | `llama-server` | real |

**Latency split** (mean của 3 query, từ output của `pipeline.py`):

- embed: 0.0 ms
- retrieve: 0.1 ms
- llm: 4843.1 ms
- **stage chiếm nhiều nhất:** llm (100% của total)

**Nhận xét:**

LLM chiếm gần toàn bộ latency của pipeline toy. Tôi sẽ đo thử caching trên prefix trùng và GPU offload; chưa chứng minh giảm 2×. Retrieval đang stub nên kết quả không đại diện cho RAG có embedding/vector database thật.

---

## 5. The single change that mattered most

**Change:** Đổi từ UD-Q4_K_XL sang UD-Q2_K_XL trong benchmark; serving vẫn dùng 4-bit.

```
before:  10.5 tok/s (UD-Q4_K_XL, 8 threads)
after:   15.5 tok/s (UD-Q2_K_XL, 8 threads)
speedup: 1.48×
```

**Giải thích:**

Đổi sang 2-bit giúp decode tăng từ 10.5 lên 15.5 tok/s. Model nhỏ hơn 0.73 GiB, TPOT giảm từ 94.94 xuống 64.49 ms. Tôi cho rằng ít dữ liệu trọng số phải đọc từ RAM góp phần làm decode nhanh hơn, nhưng chưa đo bandwidth để xác nhận.

Tuning không cải thiện baseline: 8 threads vẫn tốt nhất ở 12.15 tok/s; 32 threads chỉ còn 1.20 tok/s. Thêm threads có thể làm tăng tranh chấp bộ nhớ và chi phí đồng bộ. Vì vậy, đổi quantization là thay đổi có tác động rõ nhất trong các phép đo của tôi.

---

## 6. Bonus

Không làm bonus; tuning thuộc base track.

---

## 8. Self-check trước khi push

- [x] `hardware.json` committed
- [x] `models/active.json` committed
- [x] `benchmarks/01-quickstart-results.md` committed (`make bench`)
- [x] `benchmarks/01-tuning-tg128.md` committed (`make tune`)
- [x] `benchmarks/02-server-results.md` committed (`make load-report`)
- [x] `benchmarks/02-server-batching-u50.md` hoặc `-metrics-u50.csv` committed (`make metrics`)
- [x] `benchmarks/locust-10_stats.csv` + `locust-50_stats.csv` committed (`make load-10` / `load-50`)
- [x] `benchmarks/03-integration-results.md` committed (`make pipeline`)
- [x] Mọi section **"required — replace this line"** trong các file `benchmarks/*.md`
      đã được thay bằng nhận xét của bạn
- [x] 5 screenshots trong `submission/screenshots/`
- [x] `make verify` → **exit 0**
- [x] Repo tên đúng mẫu `K4-L3-DAY20-HoVaTen-MSSV-ModelServing` (xem `docs/SUBMISSION.md`)
- [x] Repo GitHub ở chế độ **public** (đã kiểm tra qua GitHub API)
- [ ] Đã push và paste public URL vào VinUni LMS **trước 23:59 (UTC+7) ngày làm lab**
- [x] **Không** commit `models/*.gguf`, `runtime/` hay `.env` (đã có trong `.gitignore`)

---

## 9. Khai báo sử dụng AI  *(xem `docs/RULES.md` §3)*

- Công cụ: Antigravity AI Assistant; OpenAI Codex.
- Mục đích: Hỗ trợ xử lý lỗi, chạy các phép đo, đối chiếu số liệu và rút gọn báo cáo. Ảnh là ảnh chụp trang hiển thị log thật, có ghi rõ nguồn; không phải ảnh terminal. Giải thích về bandwidth/cache là giả thuyết, chưa được đo trực tiếp.
