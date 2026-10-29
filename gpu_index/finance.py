"""As-of financial disclosure features. No financial number is a rental quote."""
from collections import defaultdict
from datetime import datetime, date, time, timezone, timedelta
import math


def utc(s):
    t=datetime.fromisoformat(s.replace('Z','+00:00'))
    if t.tzinfo is None: raise ValueError('UTC-aware timestamp required')
    return t.astimezone(timezone.utc)


def origin_for(target_month):
    d=date.fromisoformat(target_month+'-01')
    return datetime.combine(d,time.min,tzinfo=timezone.utc)-timedelta(microseconds=1)


def release_time(row):
    if not row.get('sec_acceptance_utc') or not row.get('filed_date'): return None
    acceptance=utc(row['sec_acceptance_utc'])
    # Conservative when the filed date supplies no intraday time.
    filed=datetime.combine(date.fromisoformat(row['filed_date']),time.max,tzinfo=timezone.utc)
    return max(acceptance,filed)


def feature_snapshot(facts,config,as_of):
    cutoff=utc(as_of) if isinstance(as_of,str) else as_of
    if cutoff.tzinfo is None: raise ValueError('UTC-aware cutoff required')
    output=[]
    if len({s['name'] for s in config['features']})!=len(config['features']):raise ValueError('Duplicate feature names')
    for spec in config['features']:
        if spec['kind']!='annual_flow_yoy':raise ValueError('Unsupported feature transform; qualify and implement explicitly')
        base=dict(feature=spec['name'],block=spec['block'],company=spec['company'],as_of=cutoff.isoformat(),
                  value=None,available=False,evidence='UNAVAILABLE',business_definition=spec['business_definition'],
                  accession='',current_end='',prior_end='',release_utc='',source_url='',reason='')
        if not spec['enabled']:
            output.append(dict(base,reason='disabled: business perimeter not qualified'));continue
        candidates=[]
        for r in facts:
            if (r['company'],r['tag'],r['unit']) != (spec['company'],spec['tag'],spec['unit']):continue
            release=release_time(r)
            if release is None or release>cutoff:continue
            if (cutoff-release).days>config['max_acceptance_age_days']:continue
            if not r['start'] or not r['end']:continue
            duration=(date.fromisoformat(r['end'])-date.fromisoformat(r['start'])).days
            if not 330<=duration<=380:continue
            v=float(r['value'])
            if not math.isfinite(v) or v<=0:continue
            candidates.append((r,release,v))
        pairs=[]
        for current,release,cv in candidates:
            for prior,_,pv in candidates:
                if current['accession']!=prior['accession']:continue
                gap=(date.fromisoformat(current['end'])-date.fromisoformat(prior['end'])).days
                if 300<=gap<=430:
                    pairs.append((current['end'],release,current,prior,math.log(cv/pv)))
        if not pairs:
            output.append(dict(base,reason='no eligible same-accession annual growth pair'));continue
        _,release,current,prior,value=max(pairs,key=lambda x:(x[0],x[1],x[2]['accession']))
        output.append(dict(base,value=value,available=True,evidence='DERIVED_FROM_OBSERVED_FILINGS',
            accession=current['accession'],current_end=current['end'],prior_end=prior['end'],
            release_utc=release.isoformat(),source_url=current['filing_document_url'] or current['source_url'],
            reason='same-accession annual log growth; issuer proxy, not a rental rate'))
    return output


def monthly_features(facts,config,months):
    return [dict(target_month=m,**row) for m in sorted(set(months)) for row in feature_snapshot(facts,config,origin_for(m))]


def feature_map(records):
    by=defaultdict(dict)
    for r in records:
        key=(r['target_month'],r['feature'])
        if r['feature'] in by[r['target_month']]:raise ValueError('Duplicate feature/month')
        if r['release_utc'] and utc(r['release_utc'])>origin_for(r['target_month']):raise ValueError('Future financial feature')
        if r['value'] is not None and not r['release_utc'] and not r.get('evidence','').startswith('ASSUMED'):
            raise ValueError('Observed financial feature requires a verified release timestamp')
        if r['value'] is not None and not math.isfinite(r['value']):raise ValueError('Nonfinite financial feature')
        by[r['target_month']][r['feature']]=r
    return by
