"""Parse and check source invariants with a per-case wall budget (Linux)."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import time
import traceback

from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.semantic import check_program
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.analysis.semantics import prepare_program

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=30)
    args = parser.parse_args()
    rows = []
    for item in json.loads((ROOT / 'inventory.json').read_text()):
        source = ROOT / item['source']
        row = {'id': item['id'], 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
        start = time.monotonic()

        def expired(signum, frame):
            row['timeout_stack'] = ''.join(traceback.format_stack(frame))
            raise TimeoutError('source invariant check exceeded wall budget')

        signal.signal(signal.SIGALRM, expired)
        signal.alarm(args.seconds)
        try:
            cfg = build_cfg(check_program(parse_file(source)))
            row.update(parse='ok', locations=len(cfg.locations))
            evidence = prepare_program(cfg)
            row.update(semantics='proved', ordinary_locations=len(evidence.locations) - 2)
        except TimeoutError as exc:
            row.update(semantics='timeout', error=str(exc))
        except Exception as exc:
            row.update(semantics='error', error=f'{type(exc).__name__}: {exc}')
        finally:
            signal.alarm(0)
        row['seconds'] = time.monotonic() - start
        rows.append(row)
        (ROOT / 'preflight.json').write_text(json.dumps(rows, indent=2) + '\n')
        print(item['id'], row.get('parse'), row['semantics'], flush=True)


if __name__ == '__main__':
    main()
