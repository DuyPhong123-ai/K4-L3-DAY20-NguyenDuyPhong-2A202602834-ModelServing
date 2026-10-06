"""Synchronize report tables from measured JSON/CSV, without editing measurements."""
import csv
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'benchmarks'

def read(name):
    return json.loads((B / name).read_text(encoding='utf-8'))

def section(name, heading, body):
    path = B / name
    text = path.read_text(encoding='utf-8')
    text = text.split('\n## ' + heading)[0]
    path.write_text(text + '\n## ' + heading + '\n\n' + body + '\n', encoding='utf-8')

def table(text):
    return '\n'.join(line for line in text.splitlines() if line.startswith('|'))

def main():
    data = read('01-quickstart-results.json')
    a, b = data['primary'], data['compare']
    ratio = b['decode_tok_s'] / a['decode_tok_s']
    observation = (f"Lần chạy lại CPU-only, 8 threads: {a['quant']} đạt {a['decode_tok_s']} tok/s, "
                   f"{b['quant']} đạt {b['decode_tok_s']} tok/s (tỷ lệ compare/primary {ratio:.2f}×). "
                   f"TPOT P50 lần lượt {a['tpot_p50']:.2f} và {b['tpot_p50']:.2f} ms; "
                   f"bản compare nhỏ hơn {a['size_gb'] - b['size_gb']:.2f} GiB. "
                   "Kết quả phù hợp với giả thuyết decode chịu ảnh hưởng của lưu lượng bộ nhớ, "
                   "nhưng không đo trực tiếp bandwidth hoặc chi phí dequantization. "
                   "Chưa có bằng chứng đối chiếu chất lượng cùng câu hỏi; không kết luận chất lượng suy giảm. "
                   "Giữ 4-bit cho serving theo lựa chọn đã ghi trong REFLECTION; cần kiểm tra chất lượng trước khi đổi.")
    section('01-quickstart-results.md', 'Your observation', observation)
    quality_path = B / '01-quality-comparison.json'
    if quality_path.exists():
        quality = json.loads(quality_path.read_text(encoding='utf-8'))
        path = B / '01-quickstart-results.md'
        text = path.read_text(encoding='utf-8')
        text = text.replace('Chưa có bằng chứng đối chiếu chất lượng cùng câu hỏi; không kết luận chất lượng suy giảm.',
                            'Đã thử cùng prompt ở cả hai quantization; transcript bên dưới. Một câu hỏi chưa đủ kết luận chất lượng suy giảm.')
        text += '\n## Same-prompt quality check\n\nPrompt: ' + quality['request']['messages'][0]['content'] + '\n\n'
        for result in quality['results']:
            answer = result['response']['choices'][0]['message']['content'].strip()
            text += '**' + result['quant'] + '**\n\n> ' + answer.replace('\n', '\n> ') + '\n\n'
        text += 'Cùng temperature=0, seed=42, max_tokens=96, CPU-only, 8 threads. Một prompt chỉ là kiểm tra minh họa, không phải phép đánh giá chất lượng tổng quát. Raw request/response: `01-quality-comparison.json`.\n'
        text += '\nQuan sát ở prompt này: Q4 viết sai tên TTFT (Time to First Byte) và TPOT (Time to Process); trong lab, chúng là Time to First Token và Time per Output Token. Q2 không nhắc TTFT/TPOT như prompt yêu cầu. Cả hai kết thúc bình thường (`finish_reason=stop`), nên các thiếu sót này không do hết ngân sách 96 token. Một ví dụ chưa xác lập chất lượng tương đối giữa hai quantization.\n'
        path.write_text(text, encoding='utf-8')
    load = read('02-server-results.json')
    low, high = load['runs']
    path = B / '02-server-results.md'
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'Saturation sets in somewhere at or below .*?became queue time rather than throughput\.',
                  'These are saturation signals at the tested load. Two short runs do not locate the exact saturation threshold or separate queue time from compute time; corroborate queueing with the server\'s deferred-request gauges.', text)
    path.write_text(text, encoding='utf-8')
    path = B / '02-server-batching-u50.md'
    text = path.read_text(encoding='utf-8').replace('That wait is the queue time in your P95.',
                    'These samples do not isolate how much queue time contributed to P95.')
    path.write_text(text, encoding='utf-8')
    rps_ratio = high['rps'] / low['rps']
    p95_ratio = high['p95_ms'] / low['p95_ms']
    conc = high['rps'] * high['avg_ms'] / 1000
    with (B / '02-server-metrics-u50.csv').open(encoding='utf-8', newline='') as f:
        metrics = list(csv.DictReader(f))
    def peak(key):
        return max(float(row.get('llamacpp:' + key) or 0) for row in metrics)
    busy = peak('n_busy_slots_per_decode')
    deferred = peak('requests_deferred')
    reading = (f"Tải mô phỏng tăng 5×, RPS tăng {rps_ratio:.2f}×; P95 thay đổi {p95_ratio:.2f}×. "
               f"Effective concurrency ở 50 users là {conc:.1f}, so với 4 slots. "
               f"Server ghi nhận peak trung bình busy slots/decode {busy:.2f}/4 và "
               f"peak deferred {deferred:.0f}. Hai peak có thể ở các thời điểm khác nhau. "
               "Request phải xếp hàng khi deferred > 0; không suy ra ranh giới bão hòa chính xác chỉ từ hai mức tải. "
               f"Chỉ có {low['requests']} và {high['requests']} request hoàn tất; "
               "percentile chưa phản ánh các request còn chờ lúc dừng. "
               "Theo lựa chọn đã ghi trong REFLECTION, hướng thử tiếp là giảm TPOT bằng quant nhỏ hơn "
               "hoặc GPU offload sau khi xác minh runtime thấy GPU. Chưa đo goodput@SLO riêng.")
    section('02-server-results.md', 'Your reading', reading)
    section('02-server-batching-u50.md', 'Your observation',
            f"Peak của trung bình busy slots/decode là {busy:.2f}/4, "
            f"processing peak {peak('requests_processing'):.0f}, deferred peak {deferred:.0f}. "
            "Gauge busy > 1 là bằng chứng gom nhiều request vào decode. "
            f"Effective concurrency {conc:.1f} tính từ request hoàn tất bao gồm thời gian chờ; "
            "khác với trung bình slot bận mỗi bước decode. Không gọi tỷ lệ này là mức sử dụng CPU/GPU "
            "hay batch width tức thời. Raw samples nằm trong CSV; metrics chạy chồng với load-50.")
    integration = read('03-integration-results.json')
    avg = integration['mean_ms']
    section('03-integration-results.md', 'Which N16-N19 pieces are real',
            "N16 Cloud/IaC: stub, không triển khai cloud. N17 Data pipeline: stub, TOY_DOCS. "
            "N18 Lakehouse: stub, danh sách in-memory. N19 Vector + features: stub, keyword overlap, "
            "không dùng embedding model/vector database. N20 Serving: real, HTTP tới llama-server.\n\n"
            f"Mean: embed {avg['embed']} ms, retrieve {avg['retrieve']} ms, "
            f"llm {avg['llm']} ms, total {avg['total']} ms. "
            "LLM chiếm gần toàn bộ thời gian trong pipeline toy này; không khái quát sang RAG có retrieval thật. "
            "Ưu tiên đo thử GPU offload hoặc caching trên prefix thực sự trùng nhau. "
            "Chưa đo mức giảm 2×; streaming cải thiện thời gian nhìn thấy token đầu tiên, không giảm thời gian hoàn tất.")
    tune = read('01-tuning-tg128.json')
    best = tune['best']
    baseline = next(row for row in tune['rows'] if row['threads'] == tune['cores']['physical'])
    speedup = best['tok_s'] / baseline['tok_s']
    section('01-tuning-tg128.md', 'Your explanation',
            f"Sweep đo tg128; cấu hình tốt nhất trong grid là {best['threads']} threads "
            f"({best['tok_s']:.2f} tok/s), so với baseline {baseline['threads']} threads "
            f"({baseline['tok_s']:.2f} tok/s): {speedup:.2f}×.\n\n"
            "Giả thuyết đã ghi trong REFLECTION là giới hạn bandwidth, tranh chấp cache và chi phí đồng bộ. "
            "Đây là các cơ chế có thể giải thích đường cong; chưa có hardware counters để phân biệt chúng. "
            "Không suy ra băng thông DDR5 bão hòa hoàn toàn hoặc mức tăng RPS serving từ sweep decode đơn lẻ. "
            "Log nguyên bản ở submission/logs/tune.txt.")
    path = ROOT / 'submission/REFLECTION.md'
    text = path.read_text(encoding='utf-8')
    # Replace only the measured table within each section.
    def replace_table(match, value):
        return re.sub(r'(?m)^\|[^\n]*\n(?:\|[^\n]*\n)*', value + '\n', match, count=1)
    start2, start3, start4, start5, start6 = [text.index('\n## ' + str(i) + '.') for i in range(2, 7)]
    s2 = replace_table(text[start2:start3], table((B / '01-quickstart-results.md').read_text(encoding='utf-8')))
    s2 = re.sub(r'So sánh tốc độ được cập nhật theo lần benchmark mới bên trên\.|2-bit đạt [^\n]*?×\.',
                f"2-bit đạt {b['decode_tok_s']} so với {a['decode_tok_s']} tok/s, tỷ lệ {ratio:.2f}×.", s2)
    if quality_path.exists():
        s2 = re.sub(r'2-bit (?:đạt|decode nhanh)[^\n]+',
                    f"2-bit decode nhanh {ratio:.2f}×, nhỏ hơn {a['size_gb'] - b['size_gb']:.2f} GiB. "
                    'Với cùng prompt, Q4 giải thích sai tên TTFT/TPOT; Q2 bỏ hai chỉ số. '
                    'Một câu hỏi chưa đủ so chất lượng. Tôi giữ 4-bit làm baseline serving và sẽ kiểm tra thêm trước khi đổi.', s2)
    load_md = (B / '02-server-results.md').read_text(encoding='utf-8')
    first_table = load_md.split('\n\n*Effective')[0]
    s3 = replace_table(text[start3:start4], table(first_table))
    s3 = re.sub(r'(?m)^- \*\*Offered load.*$', f'- **Offered load tăng 5×, throughput thực tăng:** {rps_ratio:.2f}×', s3)
    s3 = re.sub(r'(?m)^- \*\*P95 tăng:.*$', f'- **P95 thay đổi:** {p95_ratio:.2f}×', s3)
    s3 = re.sub(r'(?m)^- \*\*Effective concurrency.*$', f'- **Effective concurrency ở 50 users:** {conc:.1f} so với 4 slots', s3)
    s3 = re.sub(r'chạy\): [^\n]+', f'chạy): {busy:.2f} / 4 slots (peak của trung bình mỗi decode step)', s3)
    s3 = re.sub(r'(?:Server bão hòa ở 50 users:|Tải tăng 5×, RPS tăng)[^\n]+',
                f'Tải tăng 5×, RPS tăng {rps_ratio:.2f}×; P95 thay đổi {p95_ratio:.2f}×. '
                f'Concurrency {conc:.1f}, peak deferred {deferred:.0f} cho thấy có queue. '
                'Mẫu hoàn tất ít, chưa xác định chính xác ngưỡng bão hòa. Tôi sẽ thử giảm TPOT bằng quant nhỏ hơn hoặc GPU offload; chưa đo hiệu quả.', s3)
    s4 = text[start4:start5]
    for key in ('embed', 'retrieve', 'llm'):
        s4 = re.sub(rf'(?m)^- {key}: [^\n]+', f'- {key}: {avg[key]} ms', s4)
    s4 = s4.replace('Bottleneck 100% nằm ở LLM, khớp với kỳ vọng vì decode autoregressive tuần tự. Để giảm 2x độ trễ, tôi sẽ dùng prompt caching để bỏ qua prefill và offload GPU để tăng tốc độ giải mã.',
                    'LLM chiếm gần toàn bộ latency của pipeline toy. Tôi sẽ đo thử caching trên prefix trùng và GPU offload; chưa chứng minh giảm 2×. Retrieval đang stub nên kết quả không đại diện cho RAG có embedding/vector database thật.')
    s5 = text[start5:start6]
    s5 = re.sub(r'\*\*Change:\*\*[^\n]+', f'**Change:** Chọn {best["threads"]} threads thay baseline {baseline["threads"]} threads theo sweep tg128.', s5)
    s5 = re.sub(r'before:[^\n]+', f'before:  {baseline["tok_s"]:.2f} tok/s (-t {baseline["threads"]})', s5)
    s5 = re.sub(r'after:[^\n]+', f'after:   {best["tok_s"]:.2f} tok/s (-t {best["threads"]})', s5)
    s5 = re.sub(r'speedup:[^\n]+', f'speedup: {speedup:.2f}×', s5)
    s5 = re.sub(r'Đỉnh ở \d+ threads', f'Đỉnh ở {best["threads"]} threads', s5)
    s5 = re.sub(r'là \d+ threads tốt nhất', f'là {best["threads"]} threads tốt nhất', s5)
    if ratio > speedup:
        s5 = re.sub(r'\*\*Change:\*\*[^\n]+',
                    '**Change:** Đổi từ UD-Q4_K_XL sang UD-Q2_K_XL trong benchmark; serving vẫn dùng 4-bit.', s5)
        s5 = re.sub(r'before:[^\n]+', f'before:  {a["decode_tok_s"]:.1f} tok/s (UD-Q4_K_XL, 8 threads)', s5)
        s5 = re.sub(r'after:[^\n]+', f'after:   {b["decode_tok_s"]:.1f} tok/s (UD-Q2_K_XL, 8 threads)', s5)
        s5 = re.sub(r'speedup:[^\n]+', f'speedup: {ratio:.2f}×', s5)
        s5 = re.sub(r'Giả thuyết của tôi[^\n]+',
                    'Giả thuyết của tôi vẫn là decode chịu giới hạn băng thông bộ nhớ. '
                    f'Bản 2-bit nhỏ hơn {a["size_gb"] - b["size_gb"]:.2f} GiB và có TPOT P50 thấp hơn '
                    f'({b["tpot_p50"]:.2f} so với {a["tpot_p50"]:.2f} ms). '
                    'Giảm dữ liệu trọng số phải đọc có thể giải thích tốc độ cao hơn; '
                    'bài đo không có bộ đếm bandwidth/cache để chứng minh riêng cơ chế này.', s5)
        s5 = re.sub(r'Tranh chấp bus bộ nhớ[^\n]+',
                    'Tranh chấp bộ nhớ/cache và chi phí đồng bộ vẫn là giả thuyết cho đường cong threads. '
                    f'Lần sweep mới tốt nhất ở {best["threads"]} threads; tăng so với baseline '
                    f'{baseline["threads"]} threads là {speedup:.2f}×, nhỏ hơn mức đổi quantization. '
                    'Vì vậy tôi chọn quantization làm thay đổi có tác động lớn nhất đã đo. '
                    'Chưa đo tăng RPS serving hoặc kiểm định chất lượng trên một tập câu hỏi đủ lớn.', s5)
    text = text[:start2] + s2 + s3 + s4 + s5 + text[start6:]
    text = text.replace('- **OS:** Ubuntu 24.04 LTS on Windows 11 (WSL 2)',
                        '- **OS:** Ubuntu trong WSL 2 trên Windows; hardware.json là probe WSL của lần chạy lại.')
    path.write_text(text, encoding='utf-8')
    print('Updated report summaries and REFLECTION tables from measurement artifacts.')

if __name__ == '__main__':
    main()
