"""Summarize actual automated synthesis artifacts; never import supplied eta witnesses."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shlex
import sympy as sp

PROJECT=Path(__file__).resolve().parents[1]
GROUPS=('integer','noninteger','reciprocal','overall')
LABELS={'integer':'整数正幂','noninteger':'非整数正幂','reciprocal':'倒数','overall':'合并最优'}


def read(path,default=None):
    return json.loads(path.read_text()) if path.exists() else default


def num(value):
    return str(sp.N(value,9))


def bound(c,n):
    return '—' if c is None else num(min(sp.Integer(1),sp.Rational(c['prefactor_upper'])*sp.Rational(c['decay_upper'])**n))


def diagnostic(result):
    counts=Counter()
    for attempt in result.get('attempts',[]):
        if attempt.get('stages'):
            for stage in attempt['stages']:
                if stage.get('status')!='proved':
                    counts[(stage.get('kind','?'),stage.get('status','?'),stage.get('reason',''))]+=1
        elif attempt.get('status')!='proved':
            counts[('state_model',attempt.get('status','?'),attempt.get('reason',''))]+=1
    return [{'stage':k[0],'status':k[1],'reason':k[2],'count':v} for k,v in counts.items()]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    args=parser.parse_args();root=args.root.resolve()
    rows=read(root/'results.json');reference=read(root/'reference_checks.json',[])
    refs={r['name']:r for r in reference}
    statuses=Counter(r['status'] for r in rows)
    method_counts=Counter()
    for row in rows:
        method_counts.update(row['candidate_counts'])
    lines=['# contractive_examples：自动尾界分析实测（2026-11-09）','',
        f'本报告覆盖本轮选择的 {len(rows)} 个 `.pp`，来源于 `contractive_examples`。',
        f'状态统计：`{dict(statuses)}`；有效候选按方法统计：`{dict(method_counts)}`。',
        '**这里只把本次自动合成并独立重放通过的证书计为有效结果。** 样例目录附带的手工证书未用于合成，',
        '不能将“目录里已有证书”当成“本工具已经找到”。','',
        '## 测试规则','',
        '- 沿用此前 Kelly 报告：正幂总软预算 180 秒，倒数额外 120 秒；倒数反馈时间 90 秒、最多 24 次。',
        '- 单次求解器 10 秒，修复 5 秒；正幂从二次模板开始、最高四次，c 最多 12 步，首个成功次数后停止升阶。',
        '- 正幂指数区间 [1/4,4]，16 个粗点加一轮细化；Cauchy 二阶标量 SOS、一次矩阵乘子。',
        '- 倒数保持一次分母、默认增长与支撑网格、自适应 k，指数优化目标 n=20,100,1000。',
        '- 倒数初始 c 网格为 3/2、5/4、9/8、17/16、33/32、65/64、129/128，r_seed=1/2；反馈可调整参数。',
        '- 比较 n=5,10,20,50,100,200,500,1000；逐个 n 比较完整 `min(1,A*q^n)`，保留所有有效候选。',
        '- 各例使用全部程序状态变量。这些输入没有 Kelly 原例的额外 round 计数器，因此不需要排除它。',
        '- 串行运行，避免不同实验之间的求解资源竞争。外层单例求解保护上限 600 秒、独立重放 180 秒；这不是额外搜索预算。',
        '- 不修改输入、不固定 eta、不针对个别样例更改规则。配置见 [workflow.json](workflow.json)，全部命令见 [results.json](results.json)。',
        '- `integer` 中直接多项式按 k=1 解释，多项式次数不等于 k；`noninteger` 区分 Cauchy 与 Jensen 派生。',
        '- 退出时势函数为零，尾界事件统一为完整循环轮数 `K>n`；不混入其他时钟或断言失败概率。','',
        '## 总览','',
        '| 样例 | 主流程状态 | 整数正幂 | 非整数正幂来源 | 倒数 | 求解进程墙钟秒 | 独立重放 |',
        '|---|---|---|---|---|---:|---|']
    for row in rows:
        counts=row['candidate_counts'];stages=row['stages']
        reciprocal=next((s for s in stages if s['stage']=='reciprocal'),{})
        methods=set(c['method'] for r in row['comparisons'] for c in [r.get('noninteger')] if c)
        integer=any(r.get('integer') for r in row['comparisons'])
        lines.append(f"| [{row['name']}](#{row['name'].lower()}) | {row['status']} | {'有' if integer else '未找到/未进入'} | {','.join(sorted(methods)) or '—'} | {reciprocal.get('status','未进入')} | {row['wall_seconds']:.2f} | {row.get('verification',{}).get('status','—')} |")
    statuses=Counter(r['status'] for r in rows)
    lines += ['',f'主流程状态统计：`{dict(statuses)}`。',
        f"独立重放通过：{sum(r.get('verification',{}).get('status')=='proved' for r in rows)} 个样例。",'',
        '主流程 `proved` 表示至少一条路线成功，不代表所有路线都找到证书。',
        '数值 infeasible/unknown 不是数学不可行性证明；unsupported 表示未能完成所需编译/语义证明。',
        f"{len(rows)} 个求解进程累计墙钟 {sum(r['wall_seconds'] for r in rows):.2f} 秒（不含后续独立验证与诊断）。",'',
        '## 有效尾界摘要','', '| 样例 | n=20 | n=100 | n=1000 |', '|---|---:|---:|---:|']
    for row in rows:
        if not row['comparisons']:continue
        by_n={r['n']:r for r in row['comparisons']}
        lines.append('| '+row['name']+' | '+' | '.join(bound(by_n[n].get('overall'),n) for n in (20,100,1000))+' |')
    lines += ['', '## 分支时间与反馈预算', '',
        '| 样例 | 直接多项式秒 | Cauchy 已记录秒 | 倒数搜索秒 | 反馈迭代数 | 倒数停止原因 |',
        '|---|---:|---:|---:|---:|---|']
    for row in rows:
        direct_times=[s['elapsed_seconds'] for s in row['stages'] if s['stage']=='direct_polynomial' and 'elapsed_seconds' in s]
        cauchy_times=[s['elapsed_seconds'] for s in row['stages'] if s['stage'].startswith('cauchy') and 'elapsed_seconds' in s]
        direct=f'{sum(direct_times):.3f}' if direct_times else '—'
        cauchy=f'{sum(cauchy_times):.3f}' if cauchy_times else '—'
        rec=row.get('reciprocal_search',{})
        reciprocal_time=f"{rec['elapsed_seconds']:.3f}" if rec.get('elapsed_seconds') is not None else '—'
        lines.append(f"| {row['name']} | {direct} | {cauchy} | {reciprocal_time} | {rec.get('feedback_iterations','—')} | {rec.get('feedback_stop_reason','未进入搜索')} |")
    lines += ['', '阶段未记录的时间不能解释为零成本：异常阶段、共享编译和独立重放需结合日志与进程墙钟读取。',
        '倒数搜索耗时不含外层独立验证；24 次反馈是上限，无初始矩候选时会提前停止。',
        '未进入工作流的样例在此表中不会贡献有效的预算利用率数据。','',
        '以下各例给出完整的三路线比较、获选模板和诊断。小数仅展示，排序与证书验证使用精确有理数。',
        '极小数用科学计数法显示，不把浮点下溢的 0 当作精确概率。','']
    conclusions=root/'CONCLUSIONS.md'
    if conclusions.exists():
        lines += [conclusions.read_text()]
    diagnoses=[]
    for row in rows:
        name=row['name'];case=root/name;summary=read(case/'run/summary.json',{})
        workflow=summary.get('symbolic_workflow',{})
        lines += [f'## {name}', '',f"源码：`{row['source']}`。SHA-256：`{row['source_sha256']}`。",'',
            f"状态 **{row['status']}**；求解进程墙钟 {row['wall_seconds']:.3f} 秒；工具记录耗时 {row.get('elapsed_seconds')} 秒。",'',
            f"有效候选数量（按方法）：`{row['candidate_counts']}`。",'',
            f"已尝试的多项式次数：`{row.get('degrees_attempted')}`；主阶段停止原因：`{row.get('stop_reason')}`。",'',
            f"[原始日志]({name}/solve.log) / [测量数据]({name}/measurement.json) / [产物目录]({name}/run/)。",'']
        if row.get('diagnostic'):
            lines += [f"前置诊断：`{row['diagnostic']}`。",'']
        lines += ['| 阶段 | 状态 | 阶段耗时秒 | 原因/停止信息 |','|---|---|---:|---|']
        details=[]
        for stage in row['stages']:
            elapsed=stage.get('elapsed_seconds')
            reason=stage.get('reason',stage.get('stop_reason',''))
            lines.append(f"| {stage['stage']} | {stage['status']} | {f'{elapsed:.3f}' if elapsed is not None else '—'} | {reason} |")
            if stage.get('artifact') and stage['stage']!='direct_polynomial':
                result=read(case/'run'/stage['artifact'],{})
                reasons=diagnostic(result)
                details.append({'stage':stage['stage'],'artifact':stage['artifact'],'reasons':reasons})
        for detail in details:
            if detail['reasons']:
                lines += ['',f"`{detail['stage']}` 内层诊断：`{detail['reasons']}`。",'']
        if row.get('reciprocal_search'):
            lines += ['',f"倒数搜索统计：`{row['reciprocal_search']}`。",'']
        history=read(case/'run/analyses/tailbound/search_history.json',[])
        if history:
            raw_counts=Counter((h.get('status','?'),h.get('raw_status','?')) for h in history)
            lines += ['',f'直接多项式编码/求解记录统计（状态、求解器原始状态）：`{dict(raw_counts)}`。','']
        verification_failures=[]
        for proof in sorted((case/'run/analyses/tailbound/degrees').glob('*/c-*/attempts/*/verification.json')):
            checked=read(proof,{})
            if checked.get('status') in ('proved',None):continue
            repair=read(proof.with_name('repair.json'),{})
            blocks=sorted({b for a in checked.get('gram_reconstruction',{}).get('attempts',[]) for b in a.get('nonpsd_blocks',[])})
            verification_failures.append({'path':str(proof.relative_to(case)),
                'status':checked.get('status'),'reason':checked.get('reason'),'nonpsd_blocks':blocks,
                'repair_status':repair.get('status'),'repair_seconds':repair.get('elapsed_seconds'),
                'repair_solver_calls':repair.get('solver_calls')})
        if verification_failures:
            lines += ['', '精确证书恢复未通过的记录（未计为有效尾界）：','',
                '```json',json.dumps(verification_failures,indent=2,ensure_ascii=False),'```','']
        diagnose=read(case/'diagnostic.json',{})
        if diagnose:
            lines += ['', '补充前端诊断：','', '```json',json.dumps(diagnose,indent=2,ensure_ascii=False),'```','']
        diagnoses.append({'name':name,'stages':details,'frontend':diagnose,'verification_failures':verification_failures})
        comparisons=workflow.get('comparisons',[])
        if not comparisons:
            lines += ['', '本次没有可用于三路线比较的完整工作流结果；不填入手工证书的数值。','']
        else:
            pool=workflow['candidates'];by_id={c['id']:c for c in pool}
            winners=[]
            for r in comparisons:
                for group in GROUPS:
                    c=r.get(group)
                    if c and c['id'] not in [v['id'] for v in winners]:winners.append(c)
            labels={c['id']:f'C{i+1}' for i,c in enumerate(winners)}
            lines += ['', '| n | 整数正幂 | 非整数正幂 | 倒数 | 合并最优 | 合并证书 |',
                '|---|---:|---:|---:|---:|---|']
            for r in comparisons:
                lines.append('| '+str(r['n'])+' | '+' | '.join(bound(r.get(g),r['n']) for g in GROUPS)+' | '+(labels[r['overall']['id']] if r.get('overall') else '—')+' |')
            lines += ['', '| n | 整数证书 | 非整数证书 | 倒数证书 |', '|---|---|---|---|']
            for r in comparisons:
                lines.append('| '+str(r['n'])+' | '+' | '.join(labels[r[g]['id']] if r.get(g) else '—' for g in GROUPS[:3])+' |')
            lines += ['', '### 在比较表中获选的具体模板','',
                '全部候选见本例 summary.json；以下去重列出表中实际获选者。每个候选的界为 `min(1,A*q^n)`。','']
            for c in winners:
                lines += [f"**{labels[c['id']]}：{c['method']}，k={c['k']}**",'',
                    f"`eta = {c['eta']}`",'',f"`A = {c['prefactor_upper']}`",'',f"`q = {c['decay_upper']}`",'']
                if c['method']=='positive_jensen':
                    parent=by_id[c['reference']['seed']]
                    lines += [f"由直接多项式父证书 `{parent['id']}` 派生 `V=eta^k`；不是 Cauchy 求解成功，且不会优于父证书。",'']
                elif c['method']=='reciprocal':
                    result=read(case/'run'/c['reference']['artifact'])
                    original=result['candidates'][c['reference']['candidate']]
                    attempt=result['attempts'][original['attempt']]
                    lines += [f"`b={attempt['b']}`，`eta(initial)=1`，`V=(b/eta)^k`。",'',
                        f"矩参数：`{attempt['constants']}`；合成来源 `{attempt.get('origin','grid')}`。",'']
                else:
                    lines += ['正幂势函数为 `V=eta^k`；活动域 eta 归一化下界为 1。','']
                lines += [f"来源：`{c['reference']}`。",'']
        if name in refs:
            ref=refs[name]
            lines += ['### 独立有限轮概率核对','',
                f"状态 `{ref['status']}`；完整核对轮数 `{ref.get('horizons_checked')}`；候选数 `{ref.get('candidates_checked')}`；停止原因 `{ref.get('stop_reason')}`。",'',
                f"[详细概率记录]({name}/reference_check.json)。该检查独立读取源码，用精确分数传播全部存活路径；超过状态/算术/时间上限时只报告已完整算出的轮数。",'']
            if ref.get('candidates_checked')==0:
                lines += ['本例没有自动合成候选，因此这里仅为源码有限前缀检查，不能算自动尾界验证通过。','']
    (root/'diagnoses.json').write_text(json.dumps(diagnoses,indent=2,ensure_ascii=False)+'\n')
    lines += ['## 复现','', '在项目目录激活原求解环境，输出目录应为新目录：','', '```bash',
        'conda activate contractive-frontend-test-20260814',
        'python examples/run_contractive_examples.py --out-dir generated/contractive_examples_reproduce --cases '+
        ' '.join(shlex.quote(row['name']) for row in rows),
        'python examples/check_contractive_examples.py generated/contractive_examples_reproduce',
        'python examples/diagnose_contractive_examples.py generated/contractive_examples_reproduce',
        'python examples/report_contractive_examples.py generated/contractive_examples_reproduce','```','',
        '样例输入哈希见逐例记录。全域有效性依赖精确证书重放，有限轮概率传播仅是额外回归核对。','']
    (root/'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps({'report':str(root/'REPORT.md'),'cases':len(rows),'statuses':dict(statuses)},ensure_ascii=False))


if __name__=='__main__':main()
