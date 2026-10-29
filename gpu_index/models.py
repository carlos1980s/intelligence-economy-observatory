"""Small monthly regularized log-change models and synthetic validation.

No model is fitted to the two AWS endpoint observations. Priors and policy
transmission are declared choices. Normal predictive intervals are diagnostic,
not calibrated market uncertainty or a posterior over composition.
"""
from collections import defaultdict
from datetime import date
import math
import random
import statistics

MODELS=('own_price_random_walk','constant_aws_spread','pooled_spread','policy_jump_adjusted')

def series_key(row):
    return (row['provider'],row.get('configuration_id',row['gpu']))

def known_before(row,target):
    # Imported observations include both own and anchor publication dates.
    return row.get('publication_date','0001-01-01') < target+'-01'


def month_number(s):
    d=date.fromisoformat(s+'-01')
    return d.year*12+d.month


def validate_panel(rows):
    seen=set()
    for r in rows:
        key=(*series_key(r),r['month'])
        if key in seen: raise ValueError('Duplicate monthly series observation')
        seen.add(key)
        month_number(r['month'])
        if not math.isfinite(r['log_price']) or not math.isfinite(r['anchor']): raise ValueError('Nonfinite log price')
        if r['segment'] not in {'hyperscaler','neocloud'}: raise ValueError('Unknown segment')
        if r['month'] < r['launch_month']: raise ValueError('Pre-launch observation')
    return rows


def increments(rows):
    validate_panel(rows)
    grouped=defaultdict(list)
    for r in rows: grouped[series_key(r)].append(r)
    out=[]
    for rs in grouped.values():
        rs.sort(key=lambda r:r['month'])
        for a,b in zip(rs,rs[1:]):
            if month_number(b['month'])-month_number(a['month'])!=1: continue
            out.append(dict(b,delta=b['log_price']-a['log_price'],da=b['anchor']-a['anchor']))
    return out


class MonthlyModel:
    def __init__(self, kind, shrinkage=12.0):
        if kind not in MODELS or shrinkage <= 0: raise ValueError('Invalid model or shrinkage')
        self.kind,self.shrinkage=kind,shrinkage

    def loading(self, row):
        if self.kind=='own_price_random_walk': return 0.
        if self.kind=='policy_jump_adjusted':
            # Fixed identification restriction; NOT an estimated transmission effect.
            return 1. if row['provider']=='AWS' else 0.
        return 1.

    def fit(self, rows):
        self.training=increments(rows)
        if not self.training: raise ValueError('At least one consecutive monthly pair required')
        self.segment=defaultdict(list); self.provider=defaultdict(list); self.gpu=defaultdict(list)
        for r in self.training:
            residual=r['delta']-self.loading(r)*r['da']
            self.segment[r['segment']].append(residual)
        self.sm={s:sum(v)/(len(v)+self.shrinkage) for s,v in self.segment.items()}
        for r in self.training:
            residual=r['delta']-self.loading(r)*r['da']-self.sm[r['segment']]
            self.provider[(r['segment'],r['provider'])].append(residual)
            self.gpu[(r['segment'],r['gpu'])].append(residual)
        self.pm={k:sum(v)/(len(v)+self.shrinkage) for k,v in self.provider.items()}
        self.gm={k:sum(v)/(len(v)+self.shrinkage) for k,v in self.gpu.items()}
        # Half weight each deviation to avoid adding the same residual twice.
        errors=[r['delta']-self.predict_change(r,r['da']) for r in self.training]
        self.sigma=max(.01,math.sqrt(sum(e*e for e in errors)/len(errors)))
        return self

    def predict_change(self, row, anchor_change):
        d=self.loading(row)*anchor_change
        if self.kind in {'pooled_spread','policy_jump_adjusted'}:
            d+=self.sm.get(row['segment'],0)+.5*self.pm.get((row['segment'],row['provider']),0)+.5*self.gm.get((row['segment'],row['gpu']),0)
        return d

    def predict(self, last, next_month, next_anchor):
        if month_number(next_month)-month_number(last['month'])!=1: raise ValueError('One-month forecast only; no gap filling')
        delta=self.predict_change(last,next_anchor-last['anchor'])
        center=last['log_price']+delta
        z=1.6448536269514722
        return dict(month=next_month,log_price=center,price=math.exp(center),
                    lower=math.exp(center-z*self.sigma),upper=math.exp(center+z*self.sigma),
                    evidence='MODELLED',model=self.kind)


def synthetic_panel(seed=20261028, months=30):
    """ASSUMED scenario. AWS policy jump, independent neocloud trend, no market data."""
    rng=random.Random(seed); out=[]
    for provider,segment,offset in [('AWS','hyperscaler',0),('NeoA','neocloud',-.6),('NeoB','neocloud',-.8),('NeoC','neocloud',-.5)]:
        for gpu,level in [('H100',2.5),('A100',1.5),('L4',0.)]:
            own=level+offset
            for t in range(months):
                month=f'{2024+t//12:04}-{1+t%12:02}'
                anchor=level+(-.4 if t>=17 else 0.)
                if t:
                    own+=(-.4 if provider=='AWS' and t==17 else 0.)+(-.008 if segment=='neocloud' else 0.)+rng.gauss(0,.018)
                out.append(dict(provider=provider,segment=segment,gpu=gpu,month=month,
                                log_price=own,anchor=anchor,launch_month='2024-01',evidence='ASSUMED'))
    return out


def evaluate(rows, shrinkage=12., holdout_provider=None):
    """Expanding-origin one-step errors on log changes; never random row splits.

    Provider holdout excludes all that provider's changes from fitting. Its last
    observed price is a conditioning input; this tests dynamics, not cold-start levels.
    AWS t+1 tariff is known scenario input, so this is conditional prediction, not
    a forecast of future AWS administrative prices.
    """
    validate_panel(rows)
    months=sorted({r['month'] for r in rows}); output=[]
    by={(*series_key(r),r['month']):r for r in rows}
    for i in range(12,len(months)):
        target=months[i]
        train=[r for r in rows if r['month']<target and r['provider']!=holdout_provider and known_before(r,target)]
        for name in MODELS:
            m=MonthlyModel(name,shrinkage).fit(train)
            for actual in (r for r in rows if r['month']==target and (holdout_provider is None or r['provider']==holdout_provider)):
                last=by.get((*series_key(actual),months[i-1]))
                if last is None or not known_before(last,target): continue
                p=m.predict(last,target,actual['anchor']); error=p['log_price']-actual['log_price']
                lo,hi=math.log(p['lower']),math.log(p['upper']); y=actual['log_price']
                score=hi-lo+20*max(lo-y,0)+20*max(y-hi,0)
                output.append(dict(validation='held_out_provider_dynamics' if holdout_provider else 'rolling_time',
                    heldout=holdout_provider or '',model=name,month=target,block='first' if i<21 else 'second',
                    provider=actual['provider'],gpu=actual['gpu'],absolute_log_relative_error=abs(error),
                    actual_log_price=actual['log_price'],predicted_log_price=p['log_price'],
                    actual_log_change=actual['log_price']-last['log_price'],predicted_log_change=p['log_price']-last['log_price'],
                    predicted_price=p['price'],lower_90=p['lower'],upper_90=p['upper'],
                    interval_covered=int(lo<=y<=hi),interval_score_90=score,evidence='ASSUMED synthetic validation',shrinkage=shrinkage))
    return output


def summarize(scores):
    groups=defaultdict(list)
    for r in scores: groups[(r['validation'],r['heldout'],r['model'],r['block'],r['shrinkage'])].append(r)
    return [dict(validation=k[0],heldout=k[1],model=k[2],block=k[3],shrinkage=k[4],n=len(v),
        median_absolute_log_relative_error=statistics.median(r['absolute_log_relative_error'] for r in v),
        p90_absolute_log_relative_error=sorted(r['absolute_log_relative_error'] for r in v)[int(.9*(len(v)-1))],
        coverage_90=statistics.mean(r['interval_covered'] for r in v),
        mean_interval_score_90=statistics.mean(r['interval_score_90'] for r in v),
        evidence='ASSUMED synthetic; not broad-market validation') for k,v in groups.items()]
