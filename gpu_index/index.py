"""Version 1 fixed-cohort indices; no interpolation or missing-cell reweighting."""
import math


def matched_index(quotes, base, target, instances, *, evidence='OBSERVED', as_of=None):
    if len(set(instances)) != len(instances) or not instances:
        raise ValueError('Unique nonempty cohort required')
    selected = [q for q in quotes if q.instance in instances]
    if len({(q.provider_category,q.provider,q.commitment,q.commitment_months) for q in selected}) > 1:
        raise ValueError('Separate providers/categories and commitment segments before aggregation')
    def cells(period, eligible_only=True):
        out={}
        for q in selected:
            q.validate()
            if q.period != period:
                continue
            if eligible_only and (q.evidence != evidence or q.freshness != 'verified_capture'):
                continue
            if as_of and q.publication_date > as_of:
                continue
            if q.cell in out:
                raise ValueError('Duplicate exact matched cell')
            out[q.cell]=q
        return out
    b,t=cells(base),cells(target)
    inventory=cells(target,eligible_only=False)
    if len(b) != len(instances) or {q.instance for q in b.values()} != set(instances):
        raise ValueError('Baseline cohort is incomplete or ambiguous; no pre-launch filling')
    matches=[(v,t[k]) for k,v in b.items() if k in t]
    rows=[]
    for qb,qt in matches:
        ratio=qt.price/qb.price
        rows.append(dict(instance=qb.instance,gpu=qb.gpu,baseline_price=qb.price,target_price=qt.price,
                         ratio=ratio,baseline_expenditure_weight=1/len(b),evidence=evidence,
                         source_url_base=qb.source_url,source_url_target=qt.source_url))
    n=len(matches)
    complete=n==len(b)
    status={'observed':0.,'modelled':0.,'stale':0.,'unavailable':0.}
    for key in b:
        q=inventory.get(key)
        category='unavailable'
        if q is not None:
            if q.freshness=='stale': category='stale'
            elif q.freshness=='verified_capture' and q.evidence=='OBSERVED': category='observed'
            elif q.evidence=='MODELLED': category='modelled'
        status[category]+=1/len(b)
    # Quantity q_i is proportional to 1/p_i0: each cell has equal base expenditure.
    return dict(base=base,target=target,cohort_size=len(b),matched_cells=n,
                coverage=n/len(b),observed_weight=status['observed'],
                modelled_weight=status['modelled'],stale_weight=status['stale'],
                unavailable_weight=status['unavailable'],
                laspeyres=100*sum(r['ratio'] for r in rows)/len(b) if complete else None,
                geometric=100*math.exp(sum(math.log(r['ratio']) for r in rows)/len(b)) if complete else None,
                members=rows,formula_version='matched-equal-base-expenditure-v1',
                interpretation='Retrospective AWS bundled on-demand list tariffs; not transactions or verified available capacity')


def replacement_cost(result, budget=1e12):
    if result['coverage'] != 1 or budget<=0 or not math.isfinite(budget):
        raise ValueError('Complete fixed cohort and positive budget required')
    spend=budget/result['cohort_size']
    rows=[dict(instance=r['instance'],baseline_spend=spend,
               instance_hours=spend/r['baseline_price'],baseline_price=r['baseline_price'],
               target_price=r['target_price'],target_cost=spend/r['baseline_price']*r['target_price'])
          for r in result['members']]
    cost=sum(r['target_cost'] for r in rows)
    return dict(baseline_budget=budget,replacement_cost=cost,difference=budget-cost,quantities=rows,
                label='ASSUMED fixed quantities at observed tariffs; no capacity, discounting, execution or resale assumption; not OpenAI contract valuation or realizable profit')
