# Reflection — Day 20 Lab (Personal Report)

> **Đây là báo cáo cá nhân.** Số liệu của bạn **không** so sánh được với bạn cùng lớp
> — chỉ so **before vs after trên chính máy bạn**. Rubric chấm độ rõ ràng của setup,
> đo lường và **lập luận**, không chấm tốc độ tuyệt đối.
>
> `make verify` sẽ fail nếu còn placeholder chưa điền. Đó là cố ý.

**Họ Tên:** Nguyễn Duy Phong
**MSSV:** 2A202602834
**Cohort:** K4
**Ngày submit:** 2026-10-06

---

## 1. Hardware & runtime  *(rubric 1, 2 — 10 điểm)*

> Từ `make probe`. Paste output hoặc điền tay.

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
_(Nếu dùng cloud fallback: nói rõ vì sao — RAM < 8 GB, setup fail, v.v. Không mất điểm.)_

**Setup story** (≤ 80 chữ): điều gì cần thay đổi để lab chạy trên máy bạn? Có bước
nào fail rồi phải workaround không?

Do Smart App Control trên Windows 11 chặn nạp DLL của server (mã lỗi 4551), tôi chuyển sang Ubuntu WSL 2. Lần kiểm tra lại dùng CPU-only (`LAB_N_GPU_LAYERS=0`), 8 threads, ctx 2048, 4 slots, cổng 8090. WSL được cấp 7.7 GB RAM nên probe khuyến nghị Qwen nhỏ hơn; tôi giữ Gemma đã tải và ghi nhận kết quả chạy thực tế.

---

## 2. Đo lường  *(rubric 3, 4, 5 — 20 điểm)*

> Paste bảng từ `benchmarks/01-quickstart-results.md` (`make bench` tự sinh).

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 53954 | 447 / 502 | 94.9 / 100.5 | 6353 / 6780 / 6780 | 10.5 |
| UD-Q2_K_XL | 2.24 | 44838 | 484 / 568 | 64.5 / 69.6 | 4493 / 4797 / 4797 | 15.5 |

**Quan sát** (≤ 60 chữ): 2-bit nhanh hơn bao nhiêu, và **có đáng không**? Bạn đã thử
hỏi cùng một câu trên cả hai (`make serve` vs `.venv/bin/python labs/02-serve/serve.py --compare`)
chưa? Chất lượng khác nhau thế nào?

2-bit decode nhanh 1.48×, nhỏ hơn 0.73 GiB. Với cùng prompt, Q4 giải thích sai tên TTFT/TPOT; Q2 bỏ hai chỉ số. Một câu hỏi chưa đủ so chất lượng. Tôi giữ 4-bit làm baseline serving và sẽ kiểm tra thêm trước khi đổi.

---

## 3. Serving under load  *(rubric 8, 9, 10 — 20 điểm)*

> Từ `benchmarks/02-server-results.md` (`make load-report`).

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 23 | 0.37 | 22000 | 34000 | 42000 | 8.5 | 0.0% |
| 50 | 23 | 0.36 | 20000 | 63000 | 63000 | 10.0 | 0.0% |

- **Offered load tăng 5×, throughput thực tăng:** 1.00×
- **P95 thay đổi:** 1.85×
- **Effective concurrency ở 50 users:** 10.0 so với 4 slots

**Peak `llamacpp:n_busy_slots_per_decode`** (từ `make metrics` khi `make load-50` đang
chạy): 4.00 / 4 slots (peak của trung bình mỗi decode step)

**Saturation reading** (≤ 80 chữ): server của bạn bão hoà ở đâu, và **bằng chứng nào**
thuyết phục bạn? Nếu P95 tăng nhanh hơn RPS thì phần latency thêm đó là queue time hay
compute time — bạn biết bằng cách nào? Nếu bạn phải nâng goodput@SLO, bạn sẽ đổi knob
nào **trước**, và vì sao knob đó?

Tải tăng 5×, RPS tăng 1.00×; P95 thay đổi 1.85×. Concurrency 10.0, peak deferred 46 cho thấy có queue. Mẫu hoàn tất ít, chưa xác định chính xác ngưỡng bão hòa. Tôi sẽ thử giảm TPOT bằng quant nhỏ hơn hoặc GPU offload; chưa đo hiệu quả.

---

## 4. Integration  *(rubric 12, 13 — 15 điểm)*

> Từ `make pipeline`. Nói thật cái nào real, cái nào stub — stub **không** mất điểm.

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

**Reflection** (≤ 60 chữ): bottleneck ở đâu? Có khớp với kỳ vọng của bạn không? Nếu
phải giảm latency của pipeline này 2×, bạn sẽ tấn công vào đâu?

LLM chiếm gần toàn bộ latency của pipeline toy. Tôi sẽ đo thử caching trên prefix trùng và GPU offload; chưa chứng minh giảm 2×. Retrieval đang stub nên kết quả không đại diện cho RAG có embedding/vector database thật.

---

## 5. The single change that mattered most  *(rubric 11 — 10 điểm)*

> **Phần quan trọng nhất của report.** Không cần bonus track: `make tune` đã cho bạn
> một before/after thật (`benchmarks/01-tuning-tg128.md`). Đổi quantization,
> `LAB_N_CTX`, hay `--parallel` rồi đo lại cũng được.

**Change:** Đổi từ UD-Q4_K_XL sang UD-Q2_K_XL trong benchmark; serving vẫn dùng 4-bit.

```
before:  10.5 tok/s (UD-Q4_K_XL, 8 threads)
after:   15.5 tok/s (UD-Q2_K_XL, 8 threads)
speedup: 1.48×
```

**Tại sao nó work** (1–2 đoạn — đây là phần grader đọc kỹ nhất):

Giả thuyết của tôi vẫn là decode chịu giới hạn băng thông bộ nhớ. Bản 2-bit nhỏ hơn 0.73 GiB và có TPOT P50 thấp hơn (64.49 so với 94.94 ms). Giảm dữ liệu trọng số phải đọc có thể giải thích tốc độ cao hơn; bài đo không có bộ đếm bandwidth/cache để chứng minh riêng cơ chế này.

Tranh chấp bộ nhớ/cache và chi phí đồng bộ vẫn là giả thuyết cho đường cong threads. Lần sweep mới tốt nhất ở 8 threads; tăng so với baseline 8 threads là 1.00×, nhỏ hơn mức đổi quantization. Vì vậy tôi chọn quantization làm thay đổi có tác động lớn nhất đã đo. Chưa đo tăng RPS serving hoặc kiểm định chất lượng trên một tập câu hỏi đủ lớn.

---

## 6. Bonus  *(optional — tối đa 10 điểm)*

> Bỏ trống nếu không làm. Xem `docs/bonus/README.md`. Đừng làm hết — **một** finding sâu
> ăn điểm hơn năm bảng nông.

**Đã làm:** Không làm bonus; thread tuning thuộc base track.

**Numbers:**

```
Không có kết quả bonus.
```

**Điều này nói lên gì mà deck chưa nói:**

_(để trống nếu bạn không làm phần này)_

---

## 7. Điều làm bạn ngạc nhiên nhất  *(optional)*

_(1–2 câu. Không bắt buộc, nhưng grader đọc hết.)_

_(để trống nếu bạn không làm phần này)_

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

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Private → grader không
xem được → 0 điểm.

---

## 9. Khai báo sử dụng AI  *(xem `docs/RULES.md` §3)*

- Công cụ: Antigravity AI Assistant; OpenAI Codex.
- Mục đích: Hỗ trợ xử lý lỗi môi trường, kiểm tra repo, chạy lại benchmark/load test/pipeline, sửa đường dẫn đa nền tảng và lỗi kết luận trong load-report, đồng bộ số liệu và làm rõ giới hạn bằng chứng. Codex thay ảnh terminal dựng sẵn bằng ảnh chụp trình duyệt hiển thị log thực, có gắn nhãn nguồn. Phần giải thích cơ chế giữ giả thuyết đã có và bỏ các khẳng định chưa đo được.
