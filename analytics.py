"""Deterministic descriptive statistics, never diagnostic thresholds."""
from datetime import date, timedelta
from statistics import mean
import math


def summarize(observations, end_date, recent_days=7, baseline_days=28):
    end = date.fromisoformat(end_date)
    if not 1 <= recent_days <= 28 or not 7 <= baseline_days <= 90:
        raise ValueError('Invalid window size')
    recent_start = end - timedelta(days=recent_days - 1)
    baseline_start = recent_start - timedelta(days=baseline_days)
    seen = set()
    recent, baseline = [], []
    for row in observations:
        day = date.fromisoformat(row['date'])
        if day in seen:
            raise ValueError('Duplicate date: provide one observation per local calendar day')
        seen.add(day)
        value = row.get('value')
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('Values must be finite numbers or null')
        if recent_start <= day <= end:
            recent.append(value)
        elif baseline_start <= day < recent_start:
            baseline.append(value)
    r = mean(recent) if recent else None
    b = mean(baseline) if baseline else None
    adequate = len(recent) >= math.ceil(recent_days * .7) and len(baseline) >= math.ceil(baseline_days * .7)
    return {
        'recent': {'start': str(recent_start), 'end': str(end), 'observed_days': len(recent), 'expected_days': recent_days, 'mean': r},
        'baseline': {'start': str(baseline_start), 'end': str(recent_start-timedelta(days=1)), 'observed_days': len(baseline), 'expected_days': baseline_days, 'mean': b},
        'difference': r-b if adequate and r is not None and b is not None else None,
        'difference_percent': (r-b)/b*100 if adequate and r is not None and b not in (None, 0) else None,
        'coverage_sufficient': adequate,
        'method': 'Arithmetic means of non-overlapping windows; missing values excluded, never replaced by zero. Comparison requires 70% coverage in both windows. This is an engineering coverage rule, not clinical validation.',
    }
