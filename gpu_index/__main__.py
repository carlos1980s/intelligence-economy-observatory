from dataclasses import asdict
from pathlib import Path
import argparse
import functools
import http.server
import json
import platform
import sys
from .data import ROOT, CORE, LEGACY, aws_quotes, export_quotes, load_quotes, read_csv, write_csv, sha256, available_facts
from .index import matched_index, replacement_cost
from .models import synthetic_panel, evaluate, summarize, MonthlyModel, MODELS
from .report import render
from .adapters import fetch_archive, SOURCE_POLICY
from .finance import monthly_features, feature_snapshot, utc
from .challengers import FinancialChallenger, compare as financial_compare, summary as financial_summary
from .eligibility import report as eligibility_report, import_history


def dump(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')


def lab(out):
    rows=synthetic_panel()
    dump(out/'synthetic_monthly_panel.json',rows)
    scores=[]
    for shrink in (6.,12.,24.):
        scores.extend(evaluate(rows,shrink))
        for p in ('NeoA','NeoB','NeoC'): scores.extend(evaluate(rows,shrink,p))
    summary=summarize(scores)
    write_csv(out/'synthetic_predictions.csv',scores)
    write_csv(out/'synthetic_model_scores.csv',summary)
    return summary


def financial_lab(inputs,out,panel=None,ridge=24.,holdout=None,as_of='2026-10-28T23:59:59Z'):
    cfg=json.loads((ROOT/'schemas/financial_features.json').read_text())
    facts=read_csv(inputs/'gpu_calibration_financial_fact_vintages.csv')
    rows=panel if panel is not None else synthetic_panel(months=34)
    cutoff=utc(as_of)
    rows=[r for r in rows if r['month']<=cutoff.strftime('%Y-%m') and r.get('publication_date','0001-01-01')<=cutoff.date().isoformat()]
    if not rows:raise ValueError('No rental observations available at as-of cutoff')
    dump(out/'financial_rental_panel.json',rows)
    features=monthly_features(facts,cfg,[r['month'] for r in rows])
    dump(out/'financial_feature_vintages.json',features)
    write_csv(out/'financial_feature_vintages.csv',features)
    scores=financial_compare(rows,features,cfg,holdout=holdout,ridge=ridge)
    if holdout is None:
        for provider in sorted({r['provider'] for r in rows if r['provider']!='AWS'}):
            scores.extend(financial_compare(rows,features,cfg,holdout=provider,ridge=ridge))
        for penalty in (ridge/2,ridge*2):
            scores.extend(financial_compare(rows,features,cfg,ridge=penalty))
    if not scores:raise ValueError('No eligible evaluation observations; supply qualified monthly overlap after 12 training months')
    stats=financial_summary(scores)
    write_csv(out/'financial_challenger_predictions.csv',scores)
    write_csv(out/'financial_challenger_scores.csv',stats)
    enabled=[s['name'] for s in cfg['features'] if s['enabled']]
    fitted=FinancialChallenger(enabled,ridge=ridge).fit(rows,features)
    dump(out/'financial_challenger_parameters.json',dict(**fitted.parameters(),
        rental_evidence=sorted({r['evidence'] for r in rows}),financial_evidence='DERIVED_FROM_OBSERVED_FILINGS',as_of=as_of,promoted=False))
    return stats


def build(inputs,out):
    out.mkdir(parents=True,exist_ok=True)
    quotes=aws_quotes(inputs/'aws_gpu_2024_2026_expanded10.csv')
    export_quotes(out/'quotes.csv',quotes)
    core=matched_index(quotes,'2024-10','2026-10',CORE)
    legacy=matched_index(quotes,'2024-10','2026-10',LEGACY)
    replacement=replacement_cost(core)
    metrics=lab(out)
    manifest=dict(schema_version=1,formula_version='matched-equal-base-expenditure-v1',
        research_date='2026-10-28',runtime=platform.python_version(),
        network_used_by_build=False,inputs={p.name:dict(sha256=sha256(p),size_bytes=p.stat().st_size) for p in sorted(inputs.iterdir()) if p.is_file()},
        source_policy=SOURCE_POLICY,claim_status='AWS retrospective observed tariffs only; no broad-market fit',
        unknown_fields=['GPU interconnect','some GPU-memory descriptors','launch dates','capacity','market transaction weights'],
        original_archive_bytes_independently_verified=False,
        bounded_live_aws_scan=json.loads((inputs/'aws_live_verification.json').read_text()) if (inputs/'aws_live_verification.json').exists() else None,
        uncertainty=dict(model='Synthetic model-conditional normal intervals only',structural='No broad-market historical level identified',weights='Five-cell versus eight-cell sensitivity; assumed equal base spending'))
    dump(out/'manifest.json',manifest)
    dump(out/'summary.json',dict(core=core,legacy_sensitivity=legacy,replacement_illustration=replacement,broad_market_estimate=None))
    scalar=lambda r,name:dict(series=name,base=r['base'],target=r['target'],laspeyres=r['laspeyres'],geometric=r['geometric'],percentage_change=r['laspeyres']-100,cohort_size=r['cohort_size'],matched_cells=r['matched_cells'],coverage=r['coverage'],observed_weight=r['observed_weight'],modelled_weight=r['modelled_weight'],stale_weight=r['stale_weight'],unavailable_weight=r['unavailable_weight'])
    write_csv(out/'index_summary.csv',[scalar(core,'AWS_core5'),scalar(legacy,'AWS_legacy8_sensitivity')])
    write_csv(out/'cohort_members.csv',[dict(series=n,**row) for n,r in [('AWS_core5',core),('AWS_legacy8_sensitivity',legacy)] for row in r['members']])
    write_csv(out/'replacement_quantities.csv',replacement['quantities'])
    facts=read_csv(inputs/'gpu_calibration_financial_fact_vintages.csv')
    eligible=available_facts(facts,'2024-10-31T23:59:59Z')
    write_csv(out/'financial_facts_known_2024_10_31.csv',eligible)
    dump(out/'financial_audit.json',dict(total_vintages=len(facts),with_acceptance=sum(bool(r['sec_acceptance_utc']) for r in facts),known_by_2024_10_31=len(eligible),used_in_observed_market_fit=False,used_in_synthetic_rental_challenger=True,warning='Fact vintages are not independent observations or a cleaned quarterly panel'))
    finance=financial_lab(inputs,out)
    eligibility=eligibility_report(quotes)
    dump(out/'data_eligibility.json',eligibility['summary'])
    write_csv(out/'data_eligibility.csv',eligibility['rows'])
    from .report import financial_section
    html=render(core,legacy,replacement,metrics,manifest)
    html=html.replace('<details>',financial_section(finance,eligibility['summary'])+'<details>')
    (out/'report.html').write_text(html,encoding='utf-8')
    return dict(report=str(out/'report.html'),core5=core['laspeyres'],legacy8=legacy['laspeyres'],replacement_cost=replacement['replacement_cost'])


def main(argv=None):
    parser=argparse.ArgumentParser(description='Local GPU rental quote research. No default network access.')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('build',help='Build all exports and offline report')
    p.add_argument('--inputs',type=Path,default=ROOT/'inputs');p.add_argument('--out',type=Path,default=ROOT/'outputs')
    p=sub.add_parser('validate',help='Validate normalized quote CSV')
    p.add_argument('path',type=Path)
    p=sub.add_parser('model-lab',help='Synthetic monthly model validation only');p.add_argument('--out',type=Path,default=ROOT/'outputs')
    p=sub.add_parser('fit',help='Fit one-step estimator to explicit monthly JSON panel; no automatic market index')
    p.add_argument('panel',type=Path);p.add_argument('--model',choices=MODELS,default='policy_jump_adjusted');p.add_argument('--shrinkage',type=float,default=12);p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('facts',help='Acceptance-time financial vintage gate')
    p.add_argument('--as-of',required=True);p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('financial-features',help='Derived issuer features available at an explicit as-of time')
    p.add_argument('--as-of',required=True);p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('financial-lab',help='Optional financial challenger and block ablations; synthetic rentals by default')
    p.add_argument('--panel',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--ridge',type=float,default=24);p.add_argument('--holdout-provider');p.add_argument('--as-of',default='2026-10-28T23:59:59Z')
    p=sub.add_parser('eligibility',help='Source and monthly-data eligibility inventory')
    p.add_argument('quotes',type=Path);p.add_argument('--rights',type=Path);p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('import-history',help='Import qualified normalized quotes and explicit AWS anchor bindings')
    p.add_argument('quotes',type=Path);p.add_argument('--bindings',type=Path,required=True);p.add_argument('--rights',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('fetch-aws',help='Optional bounded archive extraction; may be incomplete')
    p.add_argument('period',choices=['2024-10','2026-10']);p.add_argument('--out',type=Path,required=True);p.add_argument('--max-mib',type=int,default=64);p.add_argument('--max-seconds',type=float,default=30)
    p=sub.add_parser('serve',help='Serve existing report on loopback only')
    p.add_argument('--directory',type=Path,default=ROOT/'outputs');p.add_argument('--port',type=int,default=8765)
    a=parser.parse_args(argv)
    if a.command=='build': print(json.dumps(build(a.inputs.resolve(),a.out.resolve()),indent=2))
    elif a.command=='validate': print(json.dumps(dict(valid_quotes=len(load_quotes(a.path)))))
    elif a.command=='model-lab': a.out.mkdir(parents=True,exist_ok=True);print(json.dumps(lab(a.out),indent=2))
    elif a.command=='fit':
        rows=json.loads(a.panel.read_text());m=MonthlyModel(a.model,a.shrinkage).fit(rows)
        dump(a.out,dict(model=m.kind,shrinkage=m.shrinkage,segment=m.sm,
            provider={str(k):v for k,v in m.pm.items()},gpu={str(k):v for k,v in m.gm.items()},sigma=m.sigma,
            training_pairs=len(m.training),evidence='MODELLED',training_evidence=sorted({r['evidence'] for r in rows}),
            warning='Estimator parameters only; no broad-market index or validated backcast'))
    elif a.command=='facts':
        rs=available_facts(read_csv(ROOT/'inputs/gpu_calibration_financial_fact_vintages.csv'),a.as_of)
        if rs: write_csv(a.out,rs)
        else: a.out.write_text('company,sec_acceptance_utc\n')
        print(json.dumps(dict(eligible_vintages=len(rs),as_of=a.as_of)))
    elif a.command=='financial-features':
        cfg=json.loads((ROOT/'schemas/financial_features.json').read_text())
        dump(a.out,feature_snapshot(read_csv(ROOT/'inputs/gpu_calibration_financial_fact_vintages.csv'),cfg,a.as_of))
    elif a.command=='financial-lab':
        a.out.mkdir(parents=True,exist_ok=True)
        stats=financial_lab(ROOT/'inputs',a.out,json.loads(a.panel.read_text()) if a.panel else None,a.ridge,a.holdout_provider,a.as_of)
        print(json.dumps(dict(comparisons=len(stats),promoted=False)))
    elif a.command=='eligibility':
        a.out.mkdir(parents=True,exist_ok=True)
        r=eligibility_report(load_quotes(a.quotes),json.loads(a.rights.read_text()) if a.rights else None)
        dump(a.out/'data_eligibility.json',r['summary']);write_csv(a.out/'data_eligibility.csv',r['rows']);print(json.dumps(r['summary']))
    elif a.command=='import-history':
        a.out.mkdir(parents=True,exist_ok=True)
        panel,lineage=import_history(load_quotes(a.quotes),read_csv(a.bindings),json.loads(a.rights.read_text()))
        dump(a.out/'monthly_panel.json',panel);write_csv(a.out/'lineage.csv',lineage)
        print(json.dumps(dict(monthly_observations=len(panel),providers=sorted({r['provider'] for r in panel}),promoted=False)))
    elif a.command=='fetch-aws':
        result=fetch_archive(a.period,a.out,CORE,max_bytes=a.max_mib*1024*1024,max_seconds=a.max_seconds)
        print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
    elif a.command=='serve':
        handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(a.directory.resolve()))
        server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),handler)
        print(f'Local report: http://127.0.0.1:{server.server_port}/report.html',flush=True)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close()

if __name__=='__main__':
    try: main()
    except (ValueError,OSError,KeyError,TypeError) as e:
        print(f'Error: {e}',file=sys.stderr);sys.exit(2)
