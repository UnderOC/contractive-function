"""Rebuild the experiment tables from exact stored certificates (no solving)."""
import json
import os
from collections import Counter
from pathlib import Path

import sympy as sp

ROOT = Path(__file__).resolve().parent
ADAPTED = ROOT.parent / 'stochastic_affine_adapted_20261109'
FIELDS = ('integer', 'noninteger', 'reciprocal', 'overall')


def read(path):
    return json.loads(path.read_text())


def link(path):
    return os.path.relpath(path, ROOT)


def number(value):
    return str(sp.N(value, 7))


def bound(candidate, n):
    if not candidate:
        return '—'
    value = sp.Rational(candidate['prefactor_upper']) * sp.Rational(candidate['decay_upper']) ** n
    return number(min(sp.Integer(1), value))


def generate():
    lines = [
        '# 随机仿射控制系统：完整自动分析测试（2026-11-09）', '',
        '测试对象为新增的 S1–S5，另将目录内的 `reference/original.pp` 作为参考单独列出。'
        '原始文件与初始化适配副本分开统计。所有自动合成均未读取目录内提供的人工模板或 certificates.json。', '',
        '## 测试协议', '',
        '- 正幂总软预算 180 秒，其中直接多项式阶段 90 秒；倒数独立软预算 120 秒。',
        '- 倒数反馈上限 24 次、反馈时间上限 90 秒；这两项限制均在倒数分支内，不额外增加 90 秒总预算。',
        '- 正幂模板从二次起，最高四次，首个成功次数即停；c 搜索最多 12 点，单次数值求解 10 秒，修复 5 秒。',
        '- 完整流程依次包含直接多项式、固定模板 Cauchy、联合模板 Cauchy、Jensen 派生及倒数搜索；预算/支持范围允许时执行。',
        '- 基线倒数为一次模板、constant_sos；Cauchy 的 scalar_order=2、matrix_multiplier_degree=1。',
        '- 顺序运行，成功后另行调用公开 verify 命令，从源码重放精确证据；随后以独立 Fraction 解释器检查有限时域概率。',
        '- 外部分析超时 600 秒，独立验证超时 180 秒。预算为软限制，不能在所有符号构造或精确恢复操作中途硬中断。',
        '- n 表示已完成循环轮数，比较同一事件 P(K>n)，上界为 min(1,A q^n)。', '',
        '配置与逐例命令见 [protocol.json](protocol.json)、[results.json](results.json)。'
        '数值表由精确有理数 A、q 重算；非常小的数不会因双精度下溢而写成 0。', '',
        '## 原文件完整流程结果', '',
        '| 样例 | 结果 | 正整数幂候选 | 非整数幂候选 | 倒数候选 | 分析实耗/秒 | 独立验证 |',
        '|---|---|---:|---:|---:|---:|---|',
    ]
    base = read(ROOT / 'results.json')
    adapted = read(ADAPTED / 'results.json')
    for row in base:
        counts = row['candidate_counts']
        lines.append(f"| {row['name']} | {row['status']} | {counts.get('direct_polynomial', 0)} | "
                     f"{counts.get('positive_jensen', 0)} | {counts.get('reciprocal', 0)} | "
                     f"{row['wall_seconds']:.2f} | {row.get('verification', {}).get('status', '未进入')} |")
    lines += ['',
        '这里直接多项式的 η 本身是二次多项式，幂指数按 k=1 解释；模板次数 2 不等于幂指数 k=2。'
        '本轮成功的非整数幂来自已验证正幂证书的 Jensen 派生。Cauchy 分支的额外整数/非整数幂搜索没有产生有效尾界候选。', '',
        '## S4、S5：初始化适配与补充测试', '',
        '原文件均报告 `Program must initialize all state variables before control flow; missing [\'nx\', \'z\']`。'
        '两者在循环内都先写后读临时变量，程序本身不存在相应的未定义读取；这是当前分析前端要求预先初始化全部状态变量的限制。', '',
        '仅在生成目录中的副本前缀添加 `z := 0; nx := 0;`。原文件保持不变。'
        '用源码解释器对各概率分支做符号比较，证明任意实数 x,y 及任意旧 nx,z 下，整轮完整后继分布相同，且与旧临时变量无关；'
        'x,y 初值和循环 guard 也保持不变。证据见 [equivalence.json](../stochastic_affine_adapted_inputs_20261109/equivalence.json)。', '',
        '补充运行将模板变量指定为实际控制状态 x,y，并将倒数模板设为二次、scalar_strategy=sos；'
        '180+120 秒及 24 次反馈设置保持不变。临时变量仍参与程序语义和不变量认证。'
        '这是配置适配后的补充实验，不能表述为原文件在原默认配置下已通过。', '',
        '| 副本 | 结果 | 候选分布 | 分析实耗/秒 | 独立验证 |',
        '|---|---|---|---:|---|',
    ]
    for row in adapted:
        lines.append(f"| {row['name']} | {row['status']} | {row['candidate_counts']} | "
                     f"{row['wall_seconds']:.2f} | {row.get('verification', {}).get('status', '未进入')} |")
    lines += ['', '## 各例模板、尾界与阶段诊断', '']
    for root, rows, label in ((ROOT, base, '原文件'), (ADAPTED, adapted, '适配副本')):
        for row in rows:
            case = root / row['name']
            lines += [f"### {row['name']}（{label}）", '',
                      f"状态：`{row['status']}`；分析 {row['wall_seconds']:.2f} 秒。"
                      f"[完整测量与命令]({link(case / 'measurement.json')})。", '']
            if row.get('diagnostic'):
                lines += [f"诊断：`{row['diagnostic']}`。", '']
            if row['comparisons']:
                lines += ['| n | 正整数幂 | 正非整数幂 | 倒数 | 总体最小值 |',
                          '|---:|---:|---:|---:|---:|']
                for comparison in row['comparisons']:
                    n = comparison['n']
                    lines.append(f"| {n} | " + ' | '.join(bound(comparison.get(f), n) for f in FIELDS) + ' |')
                lines += ['', '以下列出在上述比较点被选中的所有模板；系数为实际精确证书中的值。', '']
                chosen = {}
                for comparison in row['comparisons']:
                    for field in FIELDS:
                        c = comparison.get(field)
                        if c:
                            chosen.setdefault(c['id'], c)
                for c in chosen.values():
                    lines += [f"**{c['id']}**（{c['method']}，k={c['k']}）：", '',
                              '```text', f"eta = {c['eta']}", f"A = {c['prefactor_upper']}",
                              f"q = {c['decay_upper']}", '```', '',
                              f"A ≈ {number(sp.Rational(c['prefactor_upper']))}，q ≈ {number(sp.Rational(c['decay_upper']))}。", '']
            lines += ['阶段记录：', ''] if row['stages'] else []
            for stage in row['stages']:
                details = []
                for key in ('reason', 'stop_reason'):
                    if stage.get(key):
                        details.append(f"{key}={stage[key]}")
                if stage.get('artifact') and stage['stage'] != 'direct_polynomial':
                    path = case / 'run' / stage['artifact']
                    data = read(path)
                    for key in ('stop_reason', 'feedback_stop_reason'):
                        if data.get(key):
                            details.append(f"{key}={data[key]}")
                    reasons = Counter()
                    for attempt in data.get('attempts', []):
                        if attempt.get('reason'):
                            reasons[attempt['reason']] += 1
                        for sub in attempt.get('stages', []):
                            if sub.get('reason'):
                                reasons[f"{sub.get('kind')}:{sub['reason']}"] += 1
                        history = attempt.get('exponent_history', [])
                        if history and all(h.get('status') == 'no_contraction' for h in history):
                            reasons['所有已测 k 均未得到收缩界'] += 1
                    if reasons:
                        details.append(str(dict(reasons)))
                timing = f"，{stage['elapsed_seconds']:.2f} 秒" if 'elapsed_seconds' in stage else ''
                lines.append(f"- {stage['stage']}: `{stage['status']}`{timing}；" + '；'.join(details))
            if row.get('reciprocal_search'):
                lines += ['', f"倒数搜索记录：`{row['reciprocal_search']}`。"]
            if root == ADAPTED and row['name'].startswith('S5_'):
                lines += ['',
                    'S5 的失败位置不是编译或不变量认证。7 个初始参数点中，5 个完成分母、c、r0、D 的精确认证，'
                    '但所测 k 的 q 上界都不小于 1；自适应搜索给出 `nonnegative_initial_derivative` 数值诊断，'
                    '没有生成有效衰减候选。另 2 个点分别在 D 或分母的精确恢复阶段失败。'
                    '随后 24 次反馈的分母模型均返回数值 infeasible，最终因次数上限停止（耗时约 55 秒，未用满 120 秒）。'
                    '这些结果不能证明所有模板不可行；随包的 η=2-x²-y² 倒数证书已通过另一套精确检查。', '']
            if root == ADAPTED and row['name'].startswith('S4_'):
                lines += ['',
                    'S4 倒数成功：37 个有效候选已通过公开 verify，15 次反馈后达到时间限制，反馈未改善初始候选。'
                    '在所有列出的 n 上，正整数幂界均优于倒数界；目录标为 reciprocal 不代表正幂路线不能求解。', '']
            check_path = case / 'reference_check.json'
            if check_path.exists():
                check = read(check_path)
                lines += ['', f"独立有限时域检查：`{check['status']}`，检查范围 {check.get('horizons_checked')}，"
                          f"候选数 {check.get('candidates_checked')}，停止原因 `{check.get('stop_reason')}`。"
                          f"[原始结果]({link(check_path)})。"]
            lines.append('')
    lines += ['## 随样例提供的证书对照（不计入自动合成）', '',
              '这些模板只用于核对随包材料；自动求解命令没有将它们作为输入。', '',
              '| 样例 | 提供的模板 | A | q | n=100 上界 |',
              '|---|---|---|---|---:|']
    index = read(ROOT / 'provided_certificate_audit/certificate_index.json')
    for c in index['new_examples'] + [index['reference_not_counted_as_new']]:
        example = {'prefactor_upper': c['prefactor'], 'decay_upper': c['q_certified']}
        lines.append(f"| {c['id']} | `{c['eta_expression']}` | {c['prefactor']} | "
                     f"{c['q_certified']} | {bound(example, 100)} |")
    audit = read(ROOT / 'provided_certificate_audit/verification_report.json')
    lines += ['', f"隔离副本的 verify_all.py 结果：`{audit['status']}`。", '',
              '## 结论与限制', '']
    for row in adapted:
        c = next((c for c in row['comparisons'] if c['n'] == 100), None)
        if c:
            lines += [f"{row['name']} 适配副本：n=100 时正整数幂为 {bound(c.get('integer'), 100)}，"
                      f"非整数幂为 {bound(c.get('noninteger'), 100)}，倒数为 {bound(c.get('reciprocal'), 100)}。"
                      f"最终验证状态 `{row.get('verification', {}).get('status')}`。", '']
    lines += [
        'S1–S3 与 reference 的原文件都通过完整自动分析及公开 verify 重放；倒数失败不会阻止正幂结果输出。'
        '本轮基线倒数的 7 个初始化参数点全部在分母阶段返回数值 infeasible，没有进入有效矩证书和反馈阶段，'
        '因此实际反馈次数为 0，120 秒预算不是必须用满的运行时长。该结果仅针对当前模板和证书搜索配置，不能推出不存在其他倒数模板。', '',
        'Cauchy 分支的限制包括精确有理恢复失败/超时、数值问题、状态模型预算、矩阵 SOS 规模上限，'
        '以及已有中间证书但 rho_upper>=1（不能形成衰减尾界）。S1、S2 的联合 Cauchy 单阶段实耗约 223、163 秒，'
        '导致正幂阶段超过 180 秒软预算。实际分析耗时已在表中记录，不应视作严格的 180+120 秒硬截止性能实验。', '',
        '独立有限时域枚举只检查完整展开到的时域，不替代全状态、全时域的精确证书重放。'
        '零候选例子的枚举仅验证源码运行和注释，不构成自动合成上界的证明。', '',
        '随样例提供的人工证书另在隔离副本中执行 verify_all.py，结果见 '
        '[provided_certificate_audit/verification_report.json](provided_certificate_audit/verification_report.json)。'
        '这些证书的可验证性和自动模板搜索的成功率分开统计。', '',
        '本次只扩展批量实验脚本的目录、模板变量和配置选择参数，未修改分析器核心、原始样例或默认预算。'
        '原始输入哈希见 [input_hashes.json](input_hashes.json)。', '',
    ]
    (ROOT / 'REPORT.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    generate()
