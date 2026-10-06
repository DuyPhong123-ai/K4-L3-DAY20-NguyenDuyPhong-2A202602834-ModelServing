"""Build a labelled HTML viewer from verbatim successful command logs.

Capture these pages with a browser; no terminal output is invented or drawn.
"""
from pathlib import Path
import html

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['01-hardware-probe', '02-bench', '03-serve-and-smoke',
         '04-locust-10', '05-locust-50']

def generate_all():
    out = ROOT / 'submission' / 'evidence'
    out.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        source = ROOT / 'submission' / 'logs' / (name + '.txt')
        text = source.read_text(encoding='utf-8')
        if 'Exit code: 0' not in text:
            raise RuntimeError(f'Command has not completed successfully: {source}')
        if name.startswith(('04-', '05-')):
            lines = text.splitlines()
            # Keep the final Locust summary and percentiles, omit repeated interim tables.
            headers = [i for i, line in enumerate(lines) if line.startswith('Type') and '# fails' in line]
            if headers:
                text = '\n'.join(lines[:7] + ['[Verbatim final summary; interim output omitted. See full source log.]'] + lines[headers[-1]:])
        elif name == '02-bench':
            lines = text.splitlines()
            start = next(i for i, line in enumerate(lines) if line.startswith('# 01 - Measure'))
            end = next(i for i, line in enumerate(lines) if line.startswith('## Your observation'))
            text = '\n'.join(lines[:5] + ['[Verbatim result section; per-request output remains in the source log.]'] + lines[start:end] + ['Exit code: 0'])
        if name == '03-serve-and-smoke':
            server = (ROOT / 'submission' / 'logs' / 'server.txt').read_text(encoding='utf-8')
            selected = [line for line in server.splitlines() if 'Command:' in line or 'listening' in line]
            text = '\n'.join(selected) + '\n\n' + text
        page = ('<!doctype html><meta charset="utf-8"><title>Lab run evidence</title>'
                '<style>body{margin:24px;background:#101827;color:#e5e7eb;font:15px monospace}'
                'h1{font:22px sans-serif}p{font:15px sans-serif;color:#a5d6ff}'
                'pre{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.45;'
                'border:1px solid #475569;padding:18px}</style><h1>' + html.escape(name) + '</h1>'
                '<p>Actual command log · local WSL2 · browser evidence viewer (not a terminal screenshot)</p>'
                '<p>Source: submission/logs/' + html.escape(source.name) + '</p><pre>'
                + html.escape(text) + '</pre>')
        target = out / (name + '.html')
        target.write_text(page, encoding='utf-8')
        print(target)

if __name__ == '__main__':
    generate_all()
