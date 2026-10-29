"""Optional ridge corrections to rental-only changes. Never promoted by default."""
from collections import Counter
import math
import statistics
from .models import MonthlyModel, increments, validate_panel, series_key, known_before
from .finance import feature_map


def solve(matrix, rhs):
    n=len(rhs);a=[list(r)+[v] for r,v in zip(matrix,rhs)]
    for i in range(n):
        pivot=max(range(i,n),key=lambda j:abs(a[j][i]));a[i],a[pivot]=a[pivot],a[i]
        if abs(a[i][i])<1e-12:raise ValueError('Singular regularized system')
        v=a[i][i];a[i]=[x/v for x in a[i]]
        for j in range(n):
            if j==i:continue
            v=a[j][i];a[j]=[x-v*y for x,y in zip(a[j],a[i])]
    return [r[-1] for r in a]


class FinancialChallenger:
    def __init__(self,features,*,ridge=24.,base_kind='policy_jump_adjusted'):
        if ridge<=0 or not math.isfinite(ridge):raise ValueError('Positive finite ridge required')
        self.features=list(features);self.ridge=ridge;self.base_kind=base_kind

    def fit(self,rows,records):
        self.base=MonthlyModel(self.base_kind).fit(rows);self.fm=feature_map(records)
        train=increments(rows);months=sorted({r['month'] for r in train})
        self.means={};self.scales={};self.active=[]
        for feature in self.features:
            values=[self.fm.get(m,{}).get(feature,{}).get('value') for m in months]
            values=[x for x in values if x is not None]
            mean=statistics.mean(values) if values else 0
            scale=statistics.pstdev(values) if len(values)>1 else 0
            self.means[feature]=mean;self.scales[feature]=scale
            if len(values)>=3 and scale>1e-8:self.active.append(feature)
        self.coef={};self.sigma={};self.effective_months={}
        for segment in sorted({r['segment'] for r in train}):
            sr=[r for r in train if r['segment']==segment];counts=Counter(r['month'] for r in sr)
            n=len(self.active);matrix=[[0. for _ in range(n)] for _ in range(n)];rhs=[0.]*n
            for i in range(n):matrix[i][i]=self.ridge
            for r in sr:
                x=self.vector(r['month']);y=r['delta']-self.base.predict_change(r,r['da']);w=1/counts[r['month']]
                for i in range(n):
                    rhs[i]+=w*x[i]*y
                    for j in range(n):matrix[i][j]+=w*x[i]*x[j]
            beta=solve(matrix,rhs) if n else []
            self.coef[segment]=beta;self.effective_months[segment]=len(counts)
            errors=[r['delta']-self.predict_change(r,r['da'],r['month']) for r in sr]
            self.sigma[segment]=max(.01,math.sqrt(sum(e*e for e in errors)/len(errors)))
        return self

    def vector(self,month):
        # Missing values are imputed to training mean => standardized zero.
        # No future scaling, backward interpolation or inference from missingness.
        return [(self.fm.get(month,{}).get(f,{}).get('value')-self.means[f])/self.scales[f]
                if self.fm.get(month,{}).get(f,{}).get('value') is not None else 0. for f in self.active]

    def predict_change(self,row,anchor_change,target_month):
        return self.base.predict_change(row,anchor_change)+sum(b*x for b,x in zip(self.coef.get(row['segment'],[]),self.vector(target_month)))

    def parameters(self):
        return dict(ridge=self.ridge,features_requested=self.features,active_features=self.active,means=self.means,scales=self.scales,
            coefficients={s:dict(zip(self.active,b)) for s,b in self.coef.items()},effective_months=self.effective_months,
            warning='Optional issuer-proxy correction to rental log changes; not a compute-price identity or promoted model')


def compare(rows,records,config,*,holdout=None,ridge=24.):
    validate_panel(rows);months=sorted({r['month'] for r in rows});by={(*series_key(r),r['month']):r for r in rows}
    specs=[s for s in config['features'] if s['enabled']];blocks=sorted({s['block'] for s in specs})
    full=[s['name'] for s in specs]
    variants={'no_finance':[],'all_finance':full}
    for block in blocks:
        variants['only_'+block]=[s['name'] for s in specs if s['block']==block]
        variants['drop_'+block]=[s['name'] for s in specs if s['block']!=block]
    out=[]
    for i in range(12,len(months)):
        target=months[i];train=[r for r in rows if r['month']<target and r['provider']!=holdout and known_before(r,target)]
        for name,features in variants.items():
            m=FinancialChallenger(features,ridge=ridge).fit(train,records)
            for actual in (r for r in rows if r['month']==target and (not holdout or r['provider']==holdout)):
                last=by.get((*series_key(actual),months[i-1]))
                if last is None or not known_before(last,target):continue
                delta=m.predict_change(last,actual['anchor']-last['anchor'],target)
                error=delta-(actual['log_price']-last['log_price']);sigma=m.sigma[actual['segment']];width=1.6448536269514722*sigma
                out.append(dict(variant=name,validation='held_out_provider_dynamics' if holdout else 'rolling_time',heldout=holdout or '',
                    month=target,block='first' if i<21 else 'second',provider=actual['provider'],gpu=actual['gpu'],
                    absolute_log_relative_error=abs(error),interval_covered=int(abs(error)<=width),
                    interval_score_90=2*width+20*max(abs(error)-width,0),active_features=len(m.active),ridge=ridge,
                    rental_evidence=actual['evidence'],financial_evidence='DERIVED_FROM_OBSERVED_FILINGS',
                    evidence=('Observed rental validation; actual financial vintages; no promotion' if actual['evidence']=='OBSERVED' else 'SYNTHETIC RENTAL validation; actual financial vintages; no market fit')))
    return out


def summary(scores):
    groups={}
    for r in scores:groups.setdefault((r['validation'],r['heldout'],r['variant'],r['block'],r['ridge']),[]).append(r)
    return [dict(validation=k[0],heldout=k[1],variant=k[2],block=k[3],ridge=k[4],n=len(v),
        median_absolute_log_relative_error=statistics.median(r['absolute_log_relative_error'] for r in v),
        coverage_90=statistics.mean(r['interval_covered'] for r in v),mean_interval_score_90=statistics.mean(r['interval_score_90'] for r in v),
        active_features_max=max(r['active_features'] for r in v),evidence=('Observed rental validation; no automatic promotion' if all(r['rental_evidence']=='OBSERVED' for r in v) else 'Synthetic rentals + actual filing features; not real-data promotion')) for k,v in groups.items()]
