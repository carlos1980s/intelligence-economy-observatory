"""Bounded AWS archive selector. Never accepts restricted bulk data sources."""
import csv
import hashlib
import io
import json
import time
import urllib.request
from pathlib import Path

AWS_ARCHIVES={
 '2024-10':'https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/20241104205721/us-east-1/index.csv',
 '2026-10':'https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/20261027193004/us-east-1/index.csv'}


def extract_aws(stream, instances, *, max_bytes=64*1024*1024, max_seconds=30):
    """Stream extraction; completion status describes scan, not market coverage.

    Returns all matching on-demand rows scanned (including different OS/tenancies),
    without pretending that a truncated scan is exhaustive. Output hash is of the
    scanned prefix only. Raw rows remain available for exact downstream selection.
    """
    if max_bytes < 1 or max_seconds <= 0: raise ValueError('Positive bounds required')
    start=time.monotonic(); size=0; digest=hashlib.sha256(); names=None; selected=[]; complete=False
    while time.monotonic()-start<max_seconds:
        line=stream.readline(min(1024*1024,max_bytes-size+1))
        if not line:
            complete=True;break
        if size+len(line)>max_bytes: break
        size+=len(line);digest.update(line)
        values=next(csv.reader([line.decode('utf-8-sig')]))
        if values and values[0]=='SKU': names=values;continue
        if names is None: continue
        if len(values)!=len(names): raise ValueError('Malformed AWS row')
        row=dict(zip(names,values))
        if row.get('Instance Type') in instances and row.get('TermType')=='OnDemand': selected.append(row)
    return dict(rows=selected,scan_complete=complete,bytes_scanned=size,sha256_scanned_prefix=digest.hexdigest(),
                hash_scope='scanned prefix; full archive only if scan_complete=true',licensing='AWS pricing terms unreviewed; local research only')


def fetch_archive(period, destination, instances, max_bytes=64*1024*1024, max_seconds=30):
    if period not in AWS_ARCHIVES: raise ValueError('Only the two pinned AWS archives are supported')
    with urllib.request.urlopen(AWS_ARCHIVES[period],timeout=min(max_seconds,15)) as response:
        result=extract_aws(response,instances,max_bytes=max_bytes,max_seconds=max_seconds)
    result['source_url']=AWS_ARCHIVES[period]
    Path(destination).write_text(json.dumps(result,indent=2)+'\n')
    return result

SOURCE_POLICY={
    'AWS': 'Pinned archived tariff extraction; not verified capacity; no network fetch by default',
    'SkyPilot': 'Not ingested; qualify immutable snapshots, refresh evidence and catalog reuse rights first',
    'GetDeploying': 'Not ingested; weekly aggregate CC BY 4.0 per research; composition-sensitive, not provider panel',
    'SiliconData': 'No systematic extraction or republication adapter',
    'Ornn': 'No systematic extraction or republication adapter',
    'SEC': 'Supplied financial fact vintages; strict acceptance-time filter; optional challenger only'}
