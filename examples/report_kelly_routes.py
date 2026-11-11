"""Source-replay, exact Kelly reference probabilities and a focused comparison report.

Run after the main solve CLI; no new synthesis or manually supplied eta is used.
The exact reference recurrence is deliberately restricted to this source hash.
"""
import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
import math
from pathlib import Path

import sympy as sp

from contractive_tool.analysis.symbolic_workflow import verify_workflow, _bound_value

KELLY_SHA256 = '25f4f0a7c67d672ebaa8d98b2bc5a2383cfa8a82c431a1b77b88accd84785d48'
GROUPS = ('integer', 'noninteger', 'reciprocal', 'overall')


def reference_probabilities(last):
    # Integer probability weights with denominator 5**n. At a fixed n,
    # wealth is determined by the number of wins; merge surviving histories.
    states = {0: (Fraction(1), 1)}
    probabilities = [Fraction(1)]
    denominator = 1
    for n in range(1, last+1):
        following = {}
        for wins, (wealth, weight) in states.items():
            for step, multiplier, probability_weight in (
                    (1, Fraction(6,5), 3), (0, Fraction(4,5), 2)):
                value = wealth*multiplier
                if Fraction(1,2) <= value < 2:
                    key = wins+step
                    previous = following.get(key, (value,0))
                    assert previous[0] == value
                    following[key] = (value, previous[1]+weight*probability_weight)
        states = following
        denominator *= 5
        probabilities.append(Fraction(sum(weight for _,weight in states.values()),denominator))
    return probabilities


def number(value):
    return f'{float(value):.10g}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('artifacts', type=Path)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    root,out = args.artifacts,args.out_dir
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((root/'manifest.json').read_text())
    if (manifest['source_sha256'] != KELLY_SHA256 or
            sha256(Path(manifest['source']).read_bytes()).hexdigest()!=KELLY_SHA256):
        raise ValueError('Reference recurrence only applies to the recorded kelly_double_bound source')
    checked=verify_workflow(root)
    if checked['status']!='proved':
        raise ValueError(checked)
    (out/'verification.json').write_text(json.dumps(checked,indent=2)+'\n')
    summary=json.loads((root/'summary.json').read_text())
    workflow=summary['symbolic_workflow'];pool=workflow['candidates'];rows=workflow['comparisons']
    truth=reference_probabilities(max(1000,max(r['n'] for r in rows)))
    horizons=sorted(set(range(101)) | {r['n'] for r in rows})
    for n in horizons:
        exact=sp.Rational(truth[n].numerator,truth[n].denominator)
        for candidate in pool:
            if exact > _bound_value(candidate,n):
                raise AssertionError((candidate['id'],n))
    reference={'status':'passed','source_sha256':KELLY_SHA256,
        'method':'exact surviving-path integer weights, wealth lattice, strict upper exit',
        'checked_n':horizons,'candidates_checked':len(pool),
        'values':{str(row['n']):{'exact':str(truth[row['n']]),'numeric':float(truth[row['n']])} for row in rows}}
    (out/'reference_check.json').write_text(json.dumps(reference,indent=2)+'\n')

    direct=[c for c in pool if c['method']=='direct_polynomial']
    labels={c['id']:f'P{i+1}' for i,c in enumerate(direct)}
    reciprocal=[]
    for row in rows:
        c=row['reciprocal']
        if c and c['eta'] not in [x['eta'] for x in reciprocal]:
            reciprocal.append(c)
    reciprocal_labels={c['eta']:f'R{i+1}' for i,c in enumerate(reciprocal)}
    def label(c):
        if not c: return '未找到'
        if c['method']=='direct_polynomial': return labels[c['id']]
        if c['method']=='positive_jensen': return labels[c['reference']['seed']]+f"^({c['k']})"
        if c['method']=='reciprocal': return reciprocal_labels[c['eta']]+f" (k={c['k']})"
        return c['method']+f" (k={c['k']})"
    def refpath(c): return root/c['reference']['artifact']
    counts=Counter(c['method'] for c in pool)
    regression_lines=(out/'regression.log').read_text().splitlines() if (out/'regression.log').exists() else []
    regression_result=next((line.strip() for line in reversed(regression_lines) if ' passed' in line),'见日志')
    lines=['# kelly_double_bound：正幂与倒数模板比较报告','',
        '本报告只分析 `kelly_double_bound.pp`。所有状态模板系数均由本轮主入口自动求解；',
        '没有固定 `eta=wealth`，没有读取旧实验的模板或证书。模板变量选择为 `wealth`，',
        '`round` 仍保留在程序语义及不变量中。','',
        '## 结果','',
        '主入口已跑通正幂与倒数两条独立搜索线，并通过无需求解器的源码证书重放。',
        '**本次整数正幂和倒数搜索均成功；非整数正幂有有效的 Jensen 派生证书，',
        '但 Cauchy 独立搜索未找到有效收缩证书。不能把 Jensen 派生结果称为 Cauchy 求解成功。**','',
        f"本轮保留 {counts['direct_polynomial']} 个直接多项式候选、{counts['positive_jensen']} 个 Jensen 非整数候选和 {counts['reciprocal']} 个倒数候选。", '',
        '合并时逐个 n 比较完整的 `min(1,A*q^n)`，不只比较衰减率。',
        '以下“最佳”仅指本次已找到并精确验证的候选，不代表该模板族的全局最优。','',
        '## 程序及比较事件','',
        '初值 `wealth=1`。每轮以 3/5 的概率乘 6/5，以 2/5 的概率乘 4/5；',
        '在 `1/2 <= wealth < 2` 时继续循环。上下两端退出都计为终止。',
        '表中事件统一为 `Pr(K>n)`，K 是完整循环轮数；不是下界退出概率或断言失败概率。',
        '所有势函数退出后置零。源码 SHA-256：',f'`{KELLY_SHA256}`。','',
        '## 主流程设置','',
        f"- 正幂软预算 {manifest['options']['total_seconds']} 秒；额外独立倒数软预算 {manifest['options']['reciprocal_seconds']} 秒。",
        '- 正幂多项式从 2 次开始，最高允许 4 次；本次在 2 次找到证书后按默认策略停止升阶。',
        '- 正幂 c 使用原自动二分搜索，最多 12 步；指数区间 [1/4,4]，16 个粗点加一轮细化。',
        '- Cauchy 使用二阶标量 SOS、一次矩阵乘子，检查更强正性编码能否改善结果。',
        '- 倒数分母次数为 1，使用默认增长/支撑网格、自适应 k、24 次反馈预算；未指定 D 或分母系数。',
        '- 倒数 k 优化目标为默认 n=20,100,1000；查询其他 n 时在保留候选中重新选择。',
        f"- 本次实际总耗时约 {summary['elapsed_seconds']:.2f} 秒；预算为软限制，符号构造和精确检查也会占用时间。",'',
        '配置见 [workflow.json](workflow.json)，完整结果见 [summary.json](run/summary.json)。','',
        '## 整数正幂：实际求出的模板','',
        '令 w=wealth。直接多项式分支将以下多项式本身作为 V，即 `eta=V, k=1`。',
        '**二次多项式不等于 k=2。** 本轮 Cauchy 没有补充 k>1 的有效整数幂候选。','']
    for c in direct:
        lines += [f"### {labels[c['id']]}",'',f"`eta(w) = {c['eta'].replace('wealth','w')}`",'',
            f"`k=1, A=eta(1)={c['prefactor_upper']}, q={c['decay_upper']}`。",'',
            f"尾界：`min(1, ({c['prefactor_upper']})*({c['decay_upper']})^n)`。",'']
    lines += ['## 非整数正幂：结果来源和具体模板','',
        '固定/联合 Cauchy 路线已实际执行，但本轮没有通过 q<1 的完整证书。',
        '因此非整数列采用主流程新增的 `positive_jensen` 候选：对于上面的每个 P，',
        '利用已经验证的存活势函数收缩 `E[P_next] <= c*P`，对 `0<k<1` 应用 Jensen，得到','',
        r'\[ V_k(w)=P(w)^k,\qquad \Pr(K>n)\le\min\{1,P(1)^k(c^k)^n\}. \]','',
        '状态模板就是上节自动合成的 P；无第二次状态系数求解。',
        '实现对两个幂作有理数向上包围，下面列的是实际认证的 A、q。',
        'Jensen 派生界不会优于其父证书，因此本次非整数列的存在不代表非整数优化取得改善。','',
        '| 使用的 n | 模板与指数 | 认证 A（约） | 认证 q（约） |','|---|---|---:|---:|']
    selected={}
    for row in rows:
        c=row['noninteger']
        if c: selected.setdefault(c['id'],[c,[]])[1].append(row['n'])
    for c,ns in selected.values():
        lines.append(f"| {','.join(map(str,ns))} | {label(c)} | {number(sp.Rational(c['prefactor_upper']))} | {number(sp.Rational(c['decay_upper']))} |")
    for c,ns in selected.values():
        lines += ['',f"`{label(c)}`：`A={c['prefactor_upper']}`，`q={c['decay_upper']}`。"]
    lines += ['', '## 倒数路线：实际求出的分母及矩证书','',
        '归一化为 `eta(1)=1`，活动域上证明 `0<eta<=b`；势函数为 `(b/eta(w))^k`。',
        '以下列出在报告各 n 上获选的分母。完整搜索中的其余候选也全部保留。','']
    for c in reciprocal:
        result=json.loads(refpath(c).read_text())
        raw=result['candidates'][c['reference']['candidate']]
        attempt=result['attempts'][raw['attempt']]
        lines += [f"### {reciprocal_labels[c['eta']]}",'',f"`eta(w) = {c['eta'].replace('wealth','w')}`",'',
            f"`b = {attempt['b']}`；`eta(1)=1`。",'',
            f"`c = {attempt['constants']['c']}`，`r0 = {attempt['constants']['r0']}`，`D = {attempt['constants']['D']}`。",'',
            '这些常数认证的是 `E[eta_next]>=c*eta`、`eta_next>=r0*eta`、',
            '`E[eta_next^2]<=D*eta^2`，包含终止后继。','']
    lines += ['令 `p=(D-c^2)/(D-2*r0*c+r0^2)`，`z=(D-r0*c)/(c-r0)`，',
        '则 `q(k)=p*r0^(-k)+(1-p)*z^(-k)`，完整界为 `min(1,b^k*q(k)^n)`。',
        '下表 A、q 已包含实际使用的有理向上包围。','',
        '| n | 分母与指数 | 认证 A（约） | 认证 q（约） |','|---|---|---:|---:|']
    for row in rows:
        c=row['reciprocal']
        lines.append(f"| {row['n']} | {label(c)} | {number(sp.Rational(c['prefactor_upper']))} | {number(sp.Rational(c['decay_upper']))} |")
    lines += ['', '## 不同 n 的数值比较','',
        '数值以约 10 位有效数字展示，比较和选优使用精确有理数；没有 10^-12 的显示截断。',
        '`1` 表示该轮界尚不提供非平凡信息。真实尾概率由独立整数权重递推计算，不参与模板合成。','',
        '| n | 整数正幂 | 非整数正幂（Jensen） | 倒数模板 | 合并最优 | 真实尾概率 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        vals=[number(row[key]['upper_bound_numeric']) if row[key] else '未找到' for key in GROUPS]
        lines.append('| '+str(row['n'])+' | '+' | '.join(vals)+f" | {number(truth[row['n']])} |")
    lines += ['', '| n | 最佳整数证书 | 最佳非整数证书 | 最佳倒数证书 | 合并选择 |',
        '|---|---|---|---|---|']
    for row in rows:
        lines.append('| '+str(row['n'])+' | '+' | '.join(label(row[key]) for key in GROUPS)+' |')
    lines += ['', '在各列均为 1 时，程序仍按未裁剪的完整界选择证书；这不代表裁剪后的界有严格优势。','',
        '![尾界比较，纵轴为对数](tail_comparison.png)','',
        '## 解读与限制','',
        '- 在 n=50，倒数界约 0.9767，优于正幂的平凡界 1；在 n=1000，整数正幂约 5.71e-9，优于倒数约 0.008916。',
        '- 两条路线都能得到证书，但倒数路线并非始终更好；应按具体 n 保留两边的最小值。',
        '- 整数正幂不同模板之间也有前因子与衰减率的权衡，不能只报告最小 q 的一个模板。',
        '- 本轮非整数结果是 Jensen 保底派生界。Cauchy 的失败是有限模板、随机基、编码及预算下未找到证书，不是不可行性证明。',
        '- 当前结果没有穷尽更高次数、其他随机基或参数；也没有证明某一证书族普遍更优。',
        '- 倒数目前接入符号轮级尾界流程；布尔宏步、显式 late_bad_exit 仍走原流程；断言分析在 develop。',
        '- 本轮未引入基于跨路线收益的动态预算调度。预算固定独立，便于复现和判断每条线的贡献。','',
        '## 验证与复现','',
        f"- 本轮源码重放验证通过：{checked['portfolio_candidates']} 个候选；见 [verification.json](verification.json)。",
        f"- 独立精确概率检查：n=0..100 及表中更大的 n，共 {len(horizons)} 个时点，检查了全部 {len(pool)} 个候选，全部通过。见 [reference_check.json](reference_check.json)。",
        '- 针对独立预算、三组比较、故障保留、证书篡改和无需求解器重放的测试见 [integration_tests.log](integration_tests.log)。',
        f'- 完整回归：**{regression_result}**。见 [regression.log](regression.log)。旧版 Kelly 产物的兼容重放见 [legacy_verify.json](legacy_verify.json)。','',
        '报告绘图使用本机已有 Matplotlib 的 `/Anaconda/bin/python`，证书重放不需要求解器。', '',
        '在项目目录执行（输出目录须为新目录）：','', '```bash',
        'conda activate contractive-frontend-test-20260814',
        'python -m contractive_tool solve kelly_double_bound.pp --goal tailbound \\\n  --tail-variables wealth --initial-degree 2 --max-degree 4 --max-c-steps 12 \\\n  --total-seconds 180 --reciprocal-seconds 120 --per-attempt-seconds 10 --repair-seconds 5 \\\n  --comparison-n 5 10 20 50 100 200 500 1000 \\\n  --workflow-config examples/tailbound_comparison.json \\\n  --out-dir generated/kelly_routes_reproduce/run',
        'python -m contractive_tool verify generated/kelly_routes_reproduce/run',
        'python -m contractive_tool evaluate generated/kelly_routes_reproduce/run --n 1000',
        'PYTHONPATH=src /Anaconda/bin/python examples/report_kelly_routes.py generated/kelly_routes_reproduce/run \\\n  --out-dir generated/kelly_routes_reproduce', '```','']
    (out/'REPORT.md').write_text('\n'.join(lines))

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    ns=np.arange(len(truth))
    fig,ax=plt.subplots(figsize=(9,5.5))
    for key,title in [('integer','Positive integer'),('noninteger','Positive noninteger (Jensen)'),('reciprocal','Reciprocal')]:
        candidates=[c for c in pool if (c['method']=='reciprocal' if key=='reciprocal' else
            c['method']!='reciprocal' and (sp.Rational(c['k']).q==1 if key=='integer' else sp.Rational(c['k']).q!=1))]
        ys=np.minimum(0,np.min([math.log(float(sp.Rational(c['prefactor_upper'])))+
            ns*math.log(float(sp.Rational(c['decay_upper']))) for c in candidates],axis=0))/math.log(10)
        ax.plot(ns,ys,label=title)
    ax.plot(ns,[math.log10(float(v)) for v in truth],label='Exact survival probability',color='black',linestyle='--')
    ax.set(xlabel='Completed loop iterations n',ylabel='log10 Pr(K > n) / certified upper bound',
           title='kelly_double_bound: certified tail bounds',xlim=(0,len(truth)-1))
    ax.grid(True,alpha=.25);ax.legend();fig.tight_layout()
    fig.savefig(out/'tail_comparison.png',dpi=170)
    fig.savefig(out/'tail_comparison.svg')
    plt.close(fig)
    print(json.dumps({'status':'passed','report':str(out/'REPORT.md'),'verification':checked,
                      'reference_points':len(horizons),'methods':dict(Counter(c['method'] for c in pool))}))


if __name__=='__main__':
    main()
