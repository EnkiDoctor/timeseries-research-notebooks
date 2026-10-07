"""Optional public-data exercise. Downloads only from the official French Data Library.

The default notebooks are synthetic and offline; this script is not called by them.
Third-party data are not covered by this repository's MIT license.
"""
import argparse
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

URL = 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/30_Industry_Portfolios_daily_CSV.zip'
DETAILS = 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_30_ind_port.html'
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', default='2010-01-01')
    parser.add_argument('--end', default='2025-12-31')
    args = parser.parse_args()
    start, end = pd.Timestamp(args.start), pd.Timestamp(args.end)
    if start > end:
        raise ValueError('--start must be <= --end')
    request = Request(URL, headers={'User-Agent': 'timeseries-research-notebooks/1.0'})
    with urlopen(request, timeout=60) as response:
        payload = response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [n for n in archive.namelist() if n.lower().endswith('.csv')]
        if len(members) != 1:
            raise ValueError('Unexpected source archive structure; inspect provider format.')
        source = archive.read(members[0]).decode('utf-8-sig')
    lines = source.splitlines()
    marker = next(i for i, line in enumerate(lines) if 'Average Value Weighted Returns -- Daily' in line)
    header_i = next(i for i in range(marker + 1, len(lines)) if lines[i].strip().startswith(','))
    selected = [lines[header_i]]
    for line in lines[header_i + 1:]:
        if re.match(r'^\s*\d{8}\s*,', line):
            selected.append(line)
        elif len(selected) > 1:
            break
    wide = pd.read_csv(io.StringIO('\n'.join(selected)), index_col=0)
    wide.columns = wide.columns.str.strip()
    wide.index = pd.to_datetime(wide.index.astype(str), format='%Y%m%d')
    wide.index.name = 'date'
    wide = wide.loc[start:end].replace([-99.99, -999.0], np.nan)
    if wide.empty or wide.shape[1] != 30:
        raise ValueError('Unexpected sample dimensions; inspect source and date range.')
    long = wide.reset_index().melt(id_vars='date', var_name='asset', value_name='return_pct')
    long['ret'] = long['return_pct'] / 100.0
    long = long.sort_values(['date', 'asset']).reset_index(drop=True)
    assert not long.duplicated(['date', 'asset']).any()
    out = ROOT / 'data' / 'downloads'
    out.mkdir(parents=True, exist_ok=True)
    target = out / 'french_30_industry_returns.csv'
    long.to_csv(target, index=False)
    metadata = {'source_url': URL, 'definition_url': DETAILS,
        'downloaded_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_archive_sha256': hashlib.sha256(payload).hexdigest(),
        'source_header': lines[:12], 'date_start': str(wide.index.min().date()),
        'date_end': str(wide.index.max().date()), 'dates': len(wide), 'assets': len(wide.columns),
        'missing_returns': int(long['ret'].isna().sum()),
        'note': 'Value-weighted research portfolio simple returns. Revised historical snapshot; not tradable ETF prices. No imputation.'}
    (out / 'french_source_metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Saved data/downloads/french_30_industry_returns.csv:', long.shape)
    print('return_pct is percent; ret is decimal. Missing returns remain missing.')


if __name__ == '__main__':
    main()
