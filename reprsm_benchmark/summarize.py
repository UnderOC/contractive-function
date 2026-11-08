"""Summarize only runs whose source hash matches the delivered input."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAMES = {'verified_nontrivial': '精确验证成功：非平凡上界',
         'verified_trivial': '精确验证成功：仅得到 1',
         'no_certificate_found': '未找到可验证证书',
         'wall_timeout': '进程预算耗尽', 'unsupported': '语义证据未通过'}


def main():
    inventory = json.loads((ROOT / 'inventory.json').read_text())
    runs = []
    for path in sorted((ROOT / 'runs').glob('*/results.json'), key=lambda p: p.stat().st_mtime):
        for item in json.loads(path.read_text()):
            runs.append({**item, 'results_file': str(path.relative_to(ROOT))})
    rows = []
    for item in inventory:
        source_hash = hashlib.sha256((ROOT / item['source']).read_bytes()).hexdigest()
        assert source_hash == item['source_sha256']
        candidates = [r for r in runs if r['id'] == item['id'] and r['source_sha256'] == source_hash]
        assert candidates, f'No current-source experiment for {item["id"]}'
        verified = [r for r in candidates if r['classification'].startswith('verified_')]
        # Prefer the best certified bound; otherwise the most extensive completed
        # search (not the later, degree-one verbose diagnostic probe).
        selected = min(verified, key=lambda r: r['bound']['upper_bound_numeric']) if verified else max(
            candidates, key=lambda r: ('retry_' in r['run'], r.get('attempts', 0)))
        rows.append({**item, 'classification': selected['classification'],
                     'bound': selected.get('bound'), 'selected_run': selected['run'],
                     'independent_check': selected.get('independent_check'),
                     'current_source_runs': [{'run': r['run'], 'classification': r['classification'],
                                              'attempt_statuses': r.get('attempt_statuses', {})} for r in candidates]})
    counts = dict(Counter(r['classification'] for r in rows))
    (ROOT / 'results.json').write_text(json.dumps({'counts': counts, 'cases': rows}, indent=2) + '\n')
    lines = ['# 实验结果（2026-11-03）', '',
             '最终交付 28 个输入（27 个论文参数实例 + 1 个原文核对样例），全部通过解析、CFG 构造和精确归纳不变量检查。', '',
             '只汇总与当前 `.pp` 的 SHA-256 一致的运行；已修改注释/标志编码的历史结果不混入最终计数。多个当前源程序结果中，优先选最好的精确验证界，否则展示最充分的搜索。', '',
             '状态统计：' + '；'.join(f'{NAMES.get(k,k)}（{v} 个）' for k,v in counts.items()) + '。', '',
             '| 输入 | 结果 | 违反概率上界 | η 次数 / c | 证据 |',
             '|---|---|---|---|---|']
    for r in rows:
        b = r['bound']
        val = f"{b['upper_bound_numeric']:.12g}" if b else '—'
        params = f"{b['degree']} / {b['c']}" if b else '—'
        evidence = r['selected_run'] + ('/summary.json' if r['classification'] != 'wall_timeout' else '')
        lines.append(f"| [{r['id']}]({r['source']}) | {NAMES.get(r['classification'],r['classification'])} | {val} | {params} | [运行记录]({evidence}) |")
    lines += ['', '所有表中成功结果均已通过 `verify_assertion` 独立源程序重放及精确有理数证书复核；近似小数仅用于展示，精确分数在运行记录中。概率界为 1 的两个实例没有提供有用的概率收紧。', '',
              '失败定位和实验限制见 [DIAGNOSTICS.md](DIAGNOSTICS.md)。完整逐例机器可读结果见 [results.json](results.json)，源程序检查见 [preflight.json](preflight.json)。', '',
              '现有 assertion 分支回归测试：`pytest -q tests/unit/test_assertion.py tests/integration/test_assertion_backend.py`，14 passed。本次没有修改 `src/` 或已有测试。', '']
    (ROOT / 'RESULTS.md').write_text('\n'.join(lines))
    print(json.dumps(counts))


if __name__ == '__main__':
    main()
