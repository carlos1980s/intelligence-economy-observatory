"""Eligibility inventory and documented real-history import. No inferred rows."""
from dataclasses import asdict
from collections import Counter,defaultdict
import hashlib
import json
import math
from .models import validate_panel, increments


def quote_id(q):
    canonical=asdict(q)
    canonical.update(price=float(q.price),gpu_count=int(q.gpu_count),commitment_months=int(q.commitment_months))
    return hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:24]


def reasons(q,rights):
    why=[]
    if q.evidence!='OBSERVED':why.append('not observed')
    if q.freshness!='verified_capture':why.append('freshness not verified')
    if not q.launch_date:why.append('launch date/source qualification missing')
    if 'unknown' in q.interconnect.lower():why.append('GPU interconnect unknown')
    if 'unknown' in q.gpu_memory.lower():why.append('GPU memory unknown')
    r=rights.get(q.provider,{})
    if not r.get('local_research_allowed') or not r.get('terms_source_url') or not r.get('checked_date'):
        why.append('local source-rights qualification missing')
    if q.provider_category not in {'hyperscaler','neocloud'}:why.append('unsupported provider category')
    return why


def report(quotes,rights=None):
    rights=rights or {};rows=[]
    for q in quotes:
        why=reasons(q,rights)
        rows.append(dict(quote_id=quote_id(q),provider=q.provider,instance=q.instance,gpu=q.gpu,period=q.period,
                         evidence=q.evidence,freshness=q.freshness,eligible_for_monthly_model=not why,
                         exclusion_reasons='; '.join(why),source_url=q.source_url,licensing=q.licensing))
    groups=defaultdict(list)
    for q in quotes:groups[q.cell].append(q.period)
    pairs=sum(sum((int(b[:4])*12+int(b[5:]))-(int(a[:4])*12+int(a[5:]))==1 for a,b in zip(sorted(ms),sorted(ms)[1:])) for ms in groups.values())
    return dict(rows=rows,summary=dict(total_quotes=len(quotes),eligible_quotes=sum(r['eligible_for_monthly_model'] for r in rows),
        providers=sorted({q.provider for q in quotes}),periods=sorted({q.period for q in quotes}),consecutive_monthly_pairs=pairs,
        broad_market_fit_eligible=False,reason='Eligibility is necessary, not sufficient; require qualified multi-provider overlap and real time/provider validation'))


def import_history(quotes,bindings,rights):
    inventory={quote_id(q):q for q in quotes}
    if len(inventory)!=len(quotes):raise ValueError('Duplicate normalized quote')
    panel=[];lineage=[]
    for b in bindings:
        if set(b)!={'quote_id','anchor_quote_id'}:raise ValueError('Bindings require exactly quote_id,anchor_quote_id')
        if b['quote_id'] not in inventory or b['anchor_quote_id'] not in inventory:raise ValueError('Unresolved quote binding')
        q,a=inventory[b['quote_id']],inventory[b['anchor_quote_id']]
        for item in (q,a):
            why=reasons(item,rights)
            if why:raise ValueError(f'Ineligible quote {quote_id(item)}: '+ '; '.join(why))
        if a.provider!='AWS' or a.period!=q.period:raise ValueError('Comparable AWS anchor in the same month required')
        compare=('gpu','gpu_memory','gpu_count','interconnect','os','commitment','commitment_months','currency','unit')
        if any(getattr(a,k)!=getattr(q,k) for k in compare):raise ValueError('Anchor hardware/unit/terms mismatch; qualify comparable services explicitly')
        cell=hashlib.sha256(repr(q.cell).encode()).hexdigest()[:24]
        published=max(q.publication_date,a.publication_date)
        panel.append(dict(provider=q.provider,segment=q.provider_category,gpu=q.gpu,configuration_id=cell,month=q.period,
            log_price=math.log(q.price),anchor=math.log(a.price),launch_month=q.launch_date[:7],evidence='OBSERVED',
            publication_date=published,quote_id=quote_id(q),anchor_quote_id=quote_id(a)))
        lineage.append(dict(quote_id=quote_id(q),anchor_quote_id=quote_id(a),configuration_id=cell,period=q.period,
            quote_source=q.source_url,anchor_source=a.source_url,quote_hash=q.source_hash,anchor_hash=a.source_hash,
            publication_date=published,licensing=q.licensing))
    validate_panel(panel)
    terms={(inventory[b['quote_id']].commitment,inventory[b['quote_id']].commitment_months) for b in bindings}
    if len(terms)>1:raise ValueError('Import on-demand, spot and each term duration into separate histories')
    if not increments(panel):raise ValueError('No consecutive qualified monthly observations; endpoints are not a monthly history')
    return panel,lineage
