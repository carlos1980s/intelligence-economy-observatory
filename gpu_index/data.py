"""Strict quote semantics and lossless research-input conversion."""
from dataclasses import dataclass, asdict, fields
from datetime import date, datetime, timezone
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ('p5.48xlarge', 'p4d.24xlarge', 'g5.xlarge', 'g4dn.xlarge', 'g6.xlarge')
LEGACY = CORE + ('p3.2xlarge', 'g3.4xlarge', 'p2.xlarge')
TERMS = {'on_demand', 'interruptible_spot', 'term'}

@dataclass(frozen=True)
class Quote:
    provider: str
    provider_category: str
    region: str
    gpu: str
    gpu_memory: str
    host_bundle: str
    gpu_count: int
    interconnect: str
    os: str
    tenancy: str
    commitment: str
    commitment_months: int
    currency: str
    unit: str
    price: float
    availability_evidence: str
    source_url: str
    source_hash: str
    source_hash_scope: str
    observation_date: str
    publication_date: str
    effective_date: str
    period: str
    launch_date: str
    licensing: str
    evidence: str
    freshness: str
    instance: str
    sku: str
    rate_code: str

    def validate(self):
        if self.commitment not in TERMS or self.evidence not in {'OBSERVED', 'MODELLED', 'ASSUMED'}:
            raise ValueError('Unknown commitment or evidence label')
        if self.price <= 0 or not math.isfinite(self.price) or self.gpu_count < 1:
            raise ValueError('Price and GPU count must be positive and finite')
        if self.currency != 'USD' or self.unit != 'instance_hour':
            raise ValueError('Normalize currencies and units explicitly before ingestion')
        if self.commitment == 'term' and self.commitment_months < 1:
            raise ValueError('Term quotes require a duration')
        if self.commitment != 'term' and self.commitment_months != 0:
            raise ValueError('Unexpected duration for non-term quote')
        for d in (self.observation_date, self.publication_date, self.effective_date):
            date.fromisoformat(d)
        date.fromisoformat(self.period + '-01')
        if self.launch_date and self.effective_date < self.launch_date:
            raise ValueError('Pre-launch quote rejected')
        if self.freshness not in {'verified_capture', 'unverified', 'stale'}:
            raise ValueError('Unknown freshness')
        if not self.source_url.startswith('https://') or len(self.source_hash) != 64:
            raise ValueError('Source URL and SHA256 required')
        int(self.source_hash, 16)
        if any(not getattr(self, f) for f in ('provider', 'provider_category', 'region', 'gpu', 'gpu_memory', 'host_bundle', 'interconnect', 'os', 'tenancy', 'availability_evidence', 'licensing', 'instance', 'sku', 'rate_code', 'source_hash_scope')):
            raise ValueError('Required descriptors cannot be empty; use explicit unknown where necessary')
        return self

    @property
    def cell(self):
        # Publication/effective dates and prices vary; all economic terms must match.
        return tuple(getattr(self, f) for f in (
            'provider', 'provider_category', 'region', 'gpu', 'gpu_memory', 'host_bundle',
            'gpu_count', 'interconnect', 'os', 'tenancy', 'commitment', 'commitment_months',
            'currency', 'unit', 'instance', 'sku', 'rate_code'))


def read_csv(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    rows = list(rows)
    if not rows:
        raise ValueError('Cannot export an empty table')
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def aws_quotes(path):
    """Research CSV contains ten matched configurations and two tariff vintages.

    Source hashes cover the supplied extraction, not the undownloaded AWS archive.
    Publication occurs after the labelled effective month: retrospective, not real-time.
    """
    rows = read_csv(path)
    digest = sha256(path)
    out = []
    for r in rows:
        if (r['purchase_option'],r['currency'],r['unit_original'],r['operating_system'],r['tenancy']) != ('OnDemand','USD','Hrs','Linux','Shared'):
            raise ValueError('AWS research adapter only admits declared Linux shared on-demand USD instance-hour rows')
        if r['same_sku'] != 'True' or r['same_rate_code'] != 'True':
            raise ValueError('Research extraction must preserve matched SKU and rate code')
        for prefix, pricecol in [('baseline', 'baseline_instance_usd_per_hour'), ('terminal', 'terminal_instance_usd_per_hour')]:
            host = json.dumps({k: r[k] for k in ('vcpu','memory_catalog','physical_processor_catalog','storage_catalog','network_performance_catalog')}, sort_keys=True)
            bundle_memory=r['gpu_memory_catalog']
            if int(r['gpu_count']) > 1 and bundle_memory:
                amount,unit,*kind=bundle_memory.split()
                device_memory=f'{float(amount)/int(r["gpu_count"]):g} {unit} {" ".join(kind)} per GPU; bundle catalog: {bundle_memory}'
            else:
                device_memory=(bundle_memory+' per GPU') if bundle_memory else '12 GiB per GPU device per source price-basis note; catalog blank'
            q = Quote(
                provider='AWS', provider_category='hyperscaler', region=r['region'],
                gpu=r['gpu_model'], gpu_memory=device_memory,
                host_bundle=host, gpu_count=int(r['gpu_count']), interconnect='unknown; network specification retained in host bundle',
                os=r['operating_system'], tenancy=r['tenancy'], commitment='on_demand', commitment_months=0,
                currency=r['currency'], unit='instance_hour', price=float(r[pricecol]),
                availability_evidence='Catalog listing only; launchability not verified; capacity_status=' + r['capacity_status_catalog'],
                source_url=r[prefix+'_source_url'], source_hash=digest, source_hash_scope='supplied matched extraction CSV, not original archive bytes',
                observation_date=r[prefix+'_archive_publication_utc'][:10],
                publication_date=r[prefix+'_archive_publication_utc'][:10], effective_date=r[prefix+'_price_row_effective_date'],
                period=r[prefix+'_period'] if prefix+'_period' in r else r['terminal_period'],
                launch_date='', licensing='AWS public pricing; reuse terms not independently reviewed; local research only',
                evidence='OBSERVED', freshness='verified_capture', instance=r['instance_type'], sku=r['sku'], rate_code=r['rate_code'])
            out.append(q.validate())
    return out


def export_quotes(path, quotes):
    write_csv(path, [asdict(q) for q in quotes])


def load_quotes(path):
    rows = read_csv(path)
    expected = {f.name for f in fields(Quote)}
    out=[]
    for r in rows:
        if set(r) != expected:
            raise ValueError('Quote schema fields do not match version 1')
        r.update(price=float(r['price']), gpu_count=int(r['gpu_count']), commitment_months=int(r['commitment_months']))
        out.append(Quote(**r).validate())
    return out


def available_facts(rows, as_of):
    """Strict acceptance-time filter. Missing acceptance stays unavailable.

    Retain restatements as vintages; this is not a cleaned quarterly factor panel.
    """
    cutoff = datetime.fromisoformat(as_of.replace('Z','+00:00'))
    if cutoff.tzinfo is None:
        raise ValueError('as_of must include an explicit timezone')
    return [r for r in rows if r['sec_acceptance_utc'] and datetime.fromisoformat(r['sec_acceptance_utc'].replace('Z','+00:00')) <= cutoff]
