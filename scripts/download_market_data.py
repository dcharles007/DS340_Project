"""Fetch observed index closes from FRED and build the project's long CSV.

No API key is needed. Market observations retain their providers' copyrights.
Run from any directory; output defaults to this repository's data/local folder.
"""
import argparse
import csv
from datetime import date, datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import urllib.request

SERIES = {'SP500': 'SP500', 'NASDAQ100': 'NASDAQ100', 'DJIA': 'DOW'}
URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500,NASDAQ100,DJIA'

def clean_csv(payload, start, end):
    reader = csv.DictReader(io.StringIO(payload.decode('utf-8-sig')))
    if not {'observation_date', *SERIES}.issubset(reader.fieldnames or []):
        raise ValueError('Unexpected FRED CSV columns')
    cleaned, excluded, seen = [], [], set()
    for row in reader:
        day = row['observation_date']
        date.fromisoformat(day)
        if not start <= day <= end:
            continue
        if day in seen:
            raise ValueError('Duplicate source date: ' + day)
        seen.add(day)
        missing = [s for s in SERIES if row[s].strip() in ('', '.', 'NA')]
        if missing:
            excluded.append({'date': day, 'missing_series': missing})
            continue
        for source, label in SERIES.items():
            value = float(row[source])
            if not math.isfinite(value) or value <= 0:
                raise ValueError('Invalid closing level: ' + day)
            cleaned.append({'date': day, 'index': label, 'close': row[source].strip()})
    cleaned.sort(key=lambda r: (r['date'], r['index']))
    if not cleaned:
        raise ValueError('No complete observations in requested period')
    return cleaned, excluded

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start', default='2024-01-01')
    p.add_argument('--end', default='2026-10-23')
    p.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'data/local')
    args = p.parse_args()
    date.fromisoformat(args.start)
    if date.fromisoformat(args.end) > datetime.now(timezone.utc).date():
        raise ValueError('End date cannot be in the future')
    if args.start > args.end:
        raise ValueError('Start must precede end')
    with urllib.request.urlopen(URL, timeout=60) as response:
        payload = response.read()
    rows, excluded = clean_csv(payload, args.start, args.end)
    args.out.mkdir(parents=True, exist_ok=True)
    raw_path, clean_path = args.out / 'fred_source.csv', args.out / 'market_prices.csv'
    raw_path.write_bytes(payload)
    with clean_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'index', 'close'], lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        'source': 'FRED, Federal Reserve Bank of St. Louis',
        'download_url': URL,
        'series_urls': {s: f'https://fred.stlouisfed.org/series/{s}' for s in SERIES},
        'collected_at_utc': datetime.now(timezone.utc).isoformat(),
        'requested_start': args.start, 'requested_end': args.end,
        'first_complete_date': rows[0]['date'], 'last_complete_date': rows[-1]['date'],
        'common_observation_dates': len(rows) // len(SERIES), 'long_format_rows': len(rows),
        'series_mapping': SERIES, 'excluded_incomplete_dates': excluded,
        'price_convention': 'Daily market-close index levels, not dividend-adjusted total returns or ETFs',
        'missing_data_policy': 'Complete-case intersection of all three series; no filling or interpolation',
        'calendar_limit': 'Observed common dates; this script does not independently verify exchange holidays',
        'source_sha256': hashlib.sha256(payload).hexdigest(),
        'clean_sha256': hashlib.sha256(clean_path.read_bytes()).hexdigest(),
        'rights': 'Third-party index data. FRED series mark copyrighted/pre-approval required. Public repository includes retrieval code and links, not observed prices or price-containing prompts.'
    }
    (args.out / 'collection_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ['first_complete_date', 'last_complete_date', 'common_observation_dates', 'long_format_rows', 'clean_sha256']}, indent=2))

if __name__ == '__main__':
    main()
