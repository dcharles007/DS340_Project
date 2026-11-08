"""DS340W Group 46: controlled comparisons of assistant index-return forecasts.

Run from the project directory. Core evaluation uses the Python standard library.
Graphs require matplotlib. Nothing in this program calls a live assistant.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

ASSISTANTS = ('ChatGPT', 'Claude', 'Gemini', 'Copilot')
BASELINES = ('Zero baseline', 'Momentum baseline')


def write_csv(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0])
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path, required):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not set(required) <= set(reader.fieldnames or []):
            raise ValueError('CSV must contain columns: ' + ','.join(required))
        return list(reader)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_prices(path):
    series = defaultdict(list)
    for r in read_csv(path, ('date', 'index', 'close')):
        d = date.fromisoformat(r['date']).isoformat()
        index = r['index'].strip()
        close = float(r['close'])
        if not index or not math.isfinite(close) or close <= 0:
            raise ValueError(f'Invalid index/closing price: {r}')
        series[index].append((d, close))
    if not series:
        raise ValueError('No prices supplied')
    for index, rows in series.items():
        rows.sort()
        if len(set(d for d, _ in rows)) != len(rows):
            raise ValueError(f'Duplicate price dates: {index}')
    calendars = [tuple(d for d, _ in rows) for rows in series.values()]
    if any(c != calendars[0] for c in calendars):
        raise ValueError('Indexes must have identical trading dates. Investigate missing data; do not forward-fill.')
    return dict(series)


def partitions(dates):
    n = len(dates)
    a, b = int(n * .7), int(n * .9)
    if a < 1 or b <= a or b >= n:
        raise ValueError('Too few dates for a 70/20/10 split')
    return {'train': (0, a), 'test': (a, b), 'validation': (b, n)}


def prompt_text(index, history, horizon):
    table = '\n'.join(f'{d},{p:.6f}' for d, p in history)
    return (f'Use ONLY this supplied historical closing-price table for {index}. '
            'Do not browse, search, use news, or use other market information. '
            f'From the last supplied closing price, predict the percentage return '
            f'to the close {horizon} trading observations later. '
            'Return exactly one signed number without a percent sign or explanation. '
            'Example: -0.75 means a decline of 0.75%.\n'
            f'date,close\n{table}')


def make_cases(prices, split='test', horizons=(3,5,10), lookback=20, step=10,
               unlock_validation=False):
    if split == 'validation' and not unlock_validation:
        raise ValueError('Validation is held out. Use --unlock-validation only after the protocol is fixed.')
    if split not in ('train', 'test', 'validation'):
        raise ValueError('Unknown split')
    if not horizons or min(horizons) < 1 or lookback < max(horizons)+1 or step < 1:
        raise ValueError('Horizons/step must be positive; lookback must exceed every horizon.')
    if len(set(horizons)) != len(horizons):
        raise ValueError('Duplicate horizons')
    series = read_prices(prices)
    dates = [d for d, _ in next(iter(series.values()))]
    start, end = partitions(dates)[split]
    cases = []
    # The origin AND target must lie within the selected split. This purges
    # boundary-spanning labels. Past-only histories can cross earlier boundaries.
    origins = range(max(start, lookback-1), end-max(horizons), step)
    for index, rows in sorted(series.items()):
        for i in origins:
            history = rows[i-lookback+1:i+1]
            for h in sorted(horizons):
                as_of, close = rows[i]
                target_date, target_close = rows[i+h]
                cases.append({'prompt_id': f'{index}_{as_of}_h{h}', 'index': index,
                    'split': split, 'as_of_date': as_of, 'target_date': target_date,
                    'horizon_trading_days': h,
                    'prompt': prompt_text(index, history, h),
                    'momentum_baseline_pct': 100*(close/rows[i-h][1]-1),
                    '_actual_pct': 100*(target_close/close-1)})
    if not cases:
        raise ValueError('No eligible cases. Supply more dates, reduce step, or reduce horizons/lookback.')
    return cases


def save_experiment(prices, out, split, horizons, lookback, step,
                    unlock_validation=False, demo=False):
    out = Path(out)
    if (out/'experiment.json').exists():
        raise ValueError('Experiment already exists; use a new output directory to preserve the protocol.')
    cases = make_cases(prices, split, horizons, lookback, step, unlock_validation)
    fields = ['prompt_id','index','split','as_of_date','target_date','horizon_trading_days','prompt']
    # No actual outcomes or baseline values are exported to the prompt file.
    write_csv(out/'prompts.csv', [{k:c[k] for k in fields} for c in cases], fields)
    fields = ['prompt_id','model','predicted_return_pct','model_version','collected_at_utc','notes']
    template = [{'prompt_id':c['prompt_id'], 'model':m, 'predicted_return_pct':'',
                 'model_version':'','collected_at_utc':'','notes':''}
                for c in cases for m in ASSISTANTS]
    write_csv(out/'prediction_template.csv', template, fields)
    # Also provide separate prompt files so copying multiline CSV cells is unnecessary.
    prompt_dir = out/'prompt_text'
    prompt_dir.mkdir(parents=True, exist_ok=True)
    for n, c in enumerate(cases, 1):
        (prompt_dir/f'{n:04d}.txt').write_text(c['prompt_id']+'\n\n'+c['prompt']+'\n', encoding='utf-8')
    manifest = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'prices_path':str(Path(prices).resolve()), 'prices_sha256':digest(prices),
                'prompts_sha256':digest(out/'prompts.csv'), 'split':split,
                'horizons':list(horizons),'lookback':lookback,'step':step,
                'case_count':len(cases),'required_models':list(ASSISTANTS),
                'synthetic_demo':demo,'split_rule':'chronological 70/20/10 of trading dates; origin and target inside split',
                'source_metadata_file':'data/DATA_SOURCE.md'}
    (out/'experiment.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return cases


def sign(x):
    return (x > 0) - (x < 0)


def aggregate(details, grouping):
    groups = defaultdict(list)
    for r in details:
        groups[tuple(r[k] for k in grouping)].append(r)
    result = []
    for key, rows in sorted(groups.items()):
        errors = [r['predicted_return_pct']-r['actual_return_pct'] for r in rows]
        result.append(dict(zip(grouping,key), n=len(rows),
            mae_percentage_points=statistics.mean(abs(e) for e in errors),
            rmse_percentage_points=math.sqrt(statistics.mean(e*e for e in errors)),
            mean_error_percentage_points=statistics.mean(errors),
            direction_accuracy=statistics.mean(r['direction_correct'] for r in rows)))
    return result


def evaluate(cases, predictions, required_models, require_metadata=True):
    by_id = {c['prompt_id']:c for c in cases}
    expected = {(p,m) for p in by_id for m in required_models}
    seen = set()
    rows = []
    for r in read_csv(predictions, ('prompt_id','model','predicted_return_pct')):
        key = (r['prompt_id'],r['model'])
        if key not in expected or key in seen:
            raise ValueError(f'Unknown or duplicate prediction: {key}')
        try:
            value = float(r['predicted_return_pct'].strip().removesuffix('%'))
        except ValueError:
            raise ValueError(f'Missing or invalid numeric prediction: {key}') from None
        if not math.isfinite(value) or value < -100:
            raise ValueError(f'Invalid percentage return: {key}')
        if require_metadata:
            if not r.get('model_version','').strip() or not r.get('collected_at_utc','').strip():
                raise ValueError(f'Record model_version and collected_at_utc: {key}')
            timestamp = datetime.fromisoformat(r['collected_at_utc'].replace('Z','+00:00'))
            if timestamp.utcoffset() != timedelta(0):
                raise ValueError(f'Collection timestamp must explicitly use UTC: {key}')
        seen.add(key)
        rows.append((by_id[key[0]],key[1],value))
    if seen != expected:
        raise ValueError(f'Incomplete comparison: missing {len(expected-seen)} forecasts. Complete every model/case.')
    for c in cases:
        rows.extend([(c,BASELINES[0],0.),(c,BASELINES[1],c['momentum_baseline_pct'])])
    details = []
    for c,m,p in rows:
        actual = c['_actual_pct']
        details.append({k:c[k] for k in ('prompt_id','index','split','as_of_date','target_date','horizon_trading_days')}
            | {'model':m,'predicted_return_pct':p,'actual_return_pct':actual,
               'absolute_error_pp':abs(p-actual),'direction_correct':int(sign(p)==sign(actual))})
    return details


def score_experiment(prices, experiment, predictions, unlock_validation=False):
    out = Path(experiment)
    manifest = json.loads((out/'experiment.json').read_text(encoding='utf-8'))
    if digest(prices) != manifest['prices_sha256']:
        raise ValueError('Price file changed since prepare. Use the original data or prepare a new experiment.')
    if digest(out/'prompts.csv') != manifest['prompts_sha256']:
        raise ValueError('Prompts changed since prepare. Prepare a new experiment.')
    cases = make_cases(prices, manifest['split'], manifest['horizons'],
                       manifest['lookback'],manifest['step'],unlock_validation)
    required = ('Toy momentum','Toy contrarian') if manifest['synthetic_demo'] else manifest['required_models']
    details = evaluate(cases,predictions,required,not manifest['synthetic_demo'])
    for name,groups in [('metrics_overall.csv',['model']),
                        ('metrics_by_horizon.csv',['model','horizon_trading_days']),
                        ('metrics_by_index_horizon.csv',['model','index','horizon_trading_days'])]:
        write_csv(out/name,aggregate(details,groups))
    write_csv(out/'forecast_details.csv',details)
    summary = {'synthetic_demo':manifest['synthetic_demo'], 'split':manifest['split'],
               'case_count':len(cases),'predictions_sha256':digest(predictions),
               'prices_sha256':digest(prices),'scored_at_utc':datetime.now(timezone.utc).isoformat(),
               'note':'Synthetic data and toy rules; not assistant research results.' if manifest['synthetic_demo']
                      else 'Supplied assistant forecasts; program does not call or verify assistant identities.'}
    (out/'run_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    write_report(out,details,summary)
    return aggregate(details,['model'])


def write_report(out, details, summary):
    table = aggregate(details,['model'])
    label = 'SYNTHETIC DEMO — NOT RESEARCH FINDINGS' if summary['synthetic_demo'] else 'Supplied assistant forecasts'
    text = f'# Group 46 Index Return Comparison\n\n{label}\n\nSplit: {summary["split"]}; forecast cases: {summary["case_count"]}.\n\n'
    text += '| Model | Cases | MAE (pp) | RMSE (pp) | Direction accuracy |\n|---|---:|---:|---:|---:|\n'
    for r in table:
        text += f'| {r["model"]} | {r["n"]} | {r["mae_percentage_points"]:.4f} | {r["rmse_percentage_points"]:.4f} | {r["direction_accuracy"]:.1%} |\n'
    text += ('\nMAE and RMSE measure percentage-point error. Lower is better. Direction accuracy '
             'compares positive, negative, and exactly zero signs; higher is better. A zero forecast '
             'is neutral and is correct only when the actual return is exactly zero.\n\n'
             'These are descriptive scores. Shared dates, indexes, and overlapping horizons '
             'make observations dependent; scores alone do not establish statistical significance. '
             'The results do not establish trading profitability.\n')
    (out/'REPORT.md').write_text(text,encoding='utf-8')


def charts(experiment):
    # Separate optional dependency: prepare/score still work without matplotlib.
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        raise ValueError('Graphs need matplotlib. Run: python -m pip install -r requirements.txt') from None
    out = Path(experiment)
    summary = json.loads((out/'run_summary.json').read_text())
    rows = read_csv(out/'forecast_details.csv', ('model','actual_return_pct','predicted_return_pct'))
    for r in rows:
        for k in ('actual_return_pct','predicted_return_pct','horizon_trading_days','direction_correct'):
            r[k] = float(r[k])
    metrics = aggregate(rows,['model'])
    models = [r['model'] for r in metrics]
    palette = ['#64748b' if m in BASELINES else '#166534' for m in models]
    label = 'Synthetic demo: toy forecasts, not assistant results' if summary['synthetic_demo'] else 'Assistant index-return comparison'
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    output = out/'charts'
    output.mkdir(exist_ok=True)
    def save(fig,name):
        fig.savefig(output/(name+'.png'),dpi=180,bbox_inches='tight')
        fig.savefig(output/(name+'.svg'),bbox_inches='tight')
        plt.close(fig)
    fig, ax = plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for a,k,title in [(ax[0],'mae_percentage_points','Mean absolute error'),(ax[1],'rmse_percentage_points','Root mean squared error')]:
        vals = [r[k] for r in metrics]
        a.barh(models,vals,color=palette)
        a.set_xlabel('Percentage points (lower is better)'); a.set_title(title)
        a.invert_yaxis();a.grid(axis='x',alpha=.15)
    fig.suptitle(label);save(fig,'return_error')
    fig, a = plt.subplots(figsize=(9,5),layout='constrained')
    a.barh(models,[100*r['direction_accuracy'] for r in metrics],color=palette)
    a.set_xlim(0,100);a.set_xlabel('Correct direction (%)');a.invert_yaxis()
    a.set_title(label+'\nDirection accuracy (zero forecasts are neutral)')
    save(fig,'direction_accuracy')
    by_h = aggregate(rows,['model','horizon_trading_days'])
    fig,a = plt.subplots(figsize=(9,5),layout='constrained')
    for m in models:
        rr = sorted([r for r in by_h if r['model']==m],key=lambda r:r['horizon_trading_days'])
        a.plot([r['horizon_trading_days'] for r in rr],[r['mae_percentage_points'] for r in rr],marker='o',label=m)
    a.set_xticks(sorted({r['horizon_trading_days'] for r in by_h}))
    a.set_xlabel('Forecast horizon (trading observations)');a.set_ylabel('MAE (percentage points)')
    a.set_title(label+'\nError by forecast horizon');a.legend();a.grid(alpha=.15)
    save(fig,'error_by_horizon')
    evaluated = [m for m in models if m not in BASELINES]
    fig,axes = plt.subplots(1,len(evaluated),figsize=(max(7,len(evaluated)*3.4),4),squeeze=False,layout='constrained')
    lim = max(abs(float(r[k])) for r in rows for k in ('actual_return_pct','predicted_return_pct'))*1.08 or 1
    for a,m in zip(axes[0],evaluated):
        rr = [r for r in rows if r['model']==m]
        a.scatter([r['actual_return_pct'] for r in rr],[r['predicted_return_pct'] for r in rr],s=18,alpha=.65,color='#166534')
        a.plot([-lim,lim],[-lim,lim],linestyle='--',color='#64748b',label='Perfect prediction')
        a.set(xlim=(-lim,lim),ylim=(-lim,lim),xlabel='Actual return (%)',ylabel='Predicted return (%)',title=m)
        a.set_aspect('equal');a.grid(alpha=.15)
    fig.suptitle(label);save(fig,'predicted_vs_actual')
    return output


def demo(out):
    out = Path(out)
    prices = out/'synthetic_prices.csv'
    if (out/'experiment.json').exists():
        raise ValueError('Demo already exists; choose a new --out directory.')
    rows = []
    day = date(2025,1,2)
    t = 0
    while t < 360:
        if day.weekday() < 5:
            for j,index in enumerate(('SP500','NASDAQ100','DOW')):
                value = (100+10*j)*math.exp(.0003*t+.018*math.sin(t/7+j)+.005*math.sin(t/2.7+2*j))
                rows.append({'date':day.isoformat(),'index':index,'close':f'{value:.6f}'})
            t += 1
        day += timedelta(days=1)
    write_csv(prices,rows)
    cases = save_experiment(prices,out,'test',(3,5,10),20,10,demo=True)
    toy = [{'prompt_id':c['prompt_id'],'model':m,
            'predicted_return_pct':w*c['momentum_baseline_pct']}
           for c in cases for m,w in [('Toy momentum',.7),('Toy contrarian',-.4)]]
    preds = out/'toy_predictions.csv'
    write_csv(preds,toy)
    score_experiment(prices,out,preds)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command',required=True)
    prepare = sub.add_parser('prepare',help='Freeze an experiment and create identical assistant prompts')
    prepare.add_argument('--prices',required=True)
    prepare.add_argument('--out',required=True)
    prepare.add_argument('--split',choices=('train','test','validation'),default='test')
    prepare.add_argument('--horizons',nargs='+',type=int,default=[3,5,10])
    prepare.add_argument('--lookback',type=int,default=20)
    prepare.add_argument('--step',type=int,default=10)
    prepare.add_argument('--unlock-validation',action='store_true')
    score = sub.add_parser('score',help='Score a complete set using its frozen experiment settings')
    score.add_argument('--prices',required=True)
    score.add_argument('--experiment',required=True)
    score.add_argument('--predictions',required=True)
    score.add_argument('--unlock-validation',action='store_true')
    chart = sub.add_parser('charts',help='Create PNG and SVG graphs from scored results')
    chart.add_argument('--experiment',required=True)
    d = sub.add_parser('demo',help='Run synthetic data and toy rules, without API keys')
    d.add_argument('--out',default='results/demo')
    args = p.parse_args()
    try:
        if args.command == 'prepare':
            cases = save_experiment(args.prices,args.out,args.split,args.horizons,args.lookback,args.step,args.unlock_validation)
            print(f'Prepared {len(cases)} cases and {len(cases)*len(ASSISTANTS)} assistant rows in {args.out}')
        elif args.command == 'score':
            metrics = score_experiment(args.prices,args.experiment,args.predictions,args.unlock_validation)
            for r in metrics:
                print(f'{r["model"]:20s} MAE={r["mae_percentage_points"]:.4f} pp; direction={r["direction_accuracy"]:.1%}')
        elif args.command == 'charts':
            print('Saved graphs to',charts(args.experiment))
        else:
            print('Saved synthetic demonstration to',demo(args.out))
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:
        p.exit(2,f'Error: {e}\n')


if __name__ == '__main__':
    main()
