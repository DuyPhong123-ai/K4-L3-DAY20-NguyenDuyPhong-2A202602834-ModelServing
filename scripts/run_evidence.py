"""Re-run base measurements in WSL and preserve verbatim command output."""
import datetime
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / 'lib'))
import labkit

OUT = ROOT / 'submission' / 'logs'
OUT.mkdir(parents=True, exist_ok=True)
os.environ.update(LAB_N_THREADS='8', LAB_N_GPU_LAYERS='0', LAB_PARALLEL='4',
                  LAB_N_CTX='2048', LAB_MAX_TOKENS='64', LAB_SERVER_PORT='8090',
                  LAB_RUNTIME_ENV='local-wsl2', PYTHONUNBUFFERED='1')

def run(name, args):
    env = os.environ.copy()
    prefix = {'04-locust-10': 'benchmarks/locust-10',
              '05-locust-50': 'benchmarks/locust-50'}.get(name)
    if prefix:
        env['LAB_FINAL_CSV'] = prefix
    with (OUT / (name + '.txt')).open('w', encoding='utf-8') as log:
        log.write(f'Captured at: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n')
        log.write('Command: ' + shlex.join(args) + '\n')
        log.write('Environment: threads=8 ngl=0 ctx=2048 parallel=4 port=8090\n\n')
        if prefix:
            log.write('LAB_FINAL_CSV=' + prefix + ' (final shutdown snapshot)\n\n')
        log.flush()
        print('RUN', name, flush=True)
        result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, env=env)
        log.write(f'\nExit code: {result.returncode}\n')
    if result.returncode:
        raise RuntimeError(f'{name} failed; see {OUT / (name + ".txt")}')
    if prefix:
        final = Path(prefix + '_final_stats.csv')
        if not final.exists():
            raise RuntimeError('Final Locust snapshot missing: ' + str(final))
        final.replace(Path(prefix + '_stats.csv'))

if __name__ == '__main__':
    py = sys.executable
    if '--tune-only' in sys.argv:
        run('tune', [py, 'labs/01-measure/tune.py', '--reps', '2'])
        sys.exit(0)
    if '--quality-only' in sys.argv:
        run('quality', [py, __file__, '--quality-worker'])
        sys.exit(0)
    if '--quality-worker' in sys.argv:
        import httpx
        active = labkit.load_active()
        prompt = ('Explain in two sentences how goodput@SLO differs from raw throughput. '
                  'Mention TTFT and TPOT targets.')
        payload = {'model': 'local', 'messages': [{'role': 'user', 'content': prompt}],
                   'max_tokens': 96, 'temperature': 0, 'seed': 42}
        results = []
        for key in ('primary', 'compare'):
            model = str(ROOT / active[key + '_model'])
            with labkit.serve_bg(model):
                response = httpx.post(labkit.base_url() + '/v1/chat/completions',
                                      json=payload, timeout=300)
                response.raise_for_status()
                body = response.json()
                answer = body['choices'][0]['message']['content']
                print(active[key + '_quant'] + ': ' + answer, flush=True)
                results.append({'quant': active[key + '_quant'], 'model_file': Path(model).name,
                                'response': body})
        target = ROOT / 'benchmarks/01-quality-comparison.json'
        target.write_text(json.dumps({'request': payload, 'results': results},
                                     ensure_ascii=False, indent=2), encoding='utf-8')
        print('Saved ' + str(target), flush=True)
        sys.exit(0)
    if '--serve-only' not in sys.argv:
        run('01-hardware-probe', [py, 'labs/00-setup/detect-hardware.py'])
        run('02-bench', [py, 'labs/01-measure/benchmark.py'])
    with (OUT / 'server.txt').open('w', encoding='utf-8') as log:
        cmd = labkit.server_cmd(str(ROOT / labkit.load_active()['primary_model']))
        log.write('Command: ' + shlex.join(cmd) + '\n')
        log.flush()
        server = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        try:
            if not labkit.wait_healthy(timeout=240, proc=server):
                raise RuntimeError('Server failed to become healthy; see server.txt')
            run('03-serve-and-smoke', [py, 'labs/02-serve/smoke-test.py'])
            locust = [py, '-m', 'locust', '-f', 'labs/02-serve/load-test.py',
                      '--headless', '-r', '5', '-t', '60s', '--host', labkit.base_url()]
            run('04-locust-10', locust + ['-u', '10'])
            # Restart to exclude the 10-user run's metrics and queued requests.
            server.terminate()
            server.wait(timeout=30)
            server = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            if not labkit.wait_healthy(timeout=240, proc=server):
                raise RuntimeError('Server restart failed')
            with (OUT / 'metrics.txt').open('w', encoding='utf-8') as metrics_log:
                metrics = subprocess.Popen([py, 'labs/02-serve/record-metrics.py',
                                            '--duration', '60', '--label', 'u50'],
                                           stdout=metrics_log, stderr=subprocess.STDOUT)
                run('05-locust-50', locust + ['-r', '25', '-u', '50'])
                if metrics.wait(timeout=90):
                    raise RuntimeError('Metrics recording failed')
            run('load-report', [py, 'labs/02-serve/load-report.py'])
            # Fresh server so unfinished load-test requests do not bias pipeline latency.
            server.terminate()
            server.wait(timeout=30)
            server = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            if not labkit.wait_healthy(timeout=240, proc=server):
                raise RuntimeError('Pipeline server restart failed')
            run('pipeline', [py, 'labs/03-integrate/pipeline.py'])
        finally:
            if server.poll() is None:
                server.terminate()
                server.wait(timeout=30)
    run('tune', [py, 'labs/01-measure/tune.py', '--reps', '2'])
    print('All evidence commands completed.', flush=True)
