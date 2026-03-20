import io
import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def _monthly_dates_and_counts(monthly_counts):
    """Convert (year, month, count) tuples to (dates, per_period, cumulative) lists."""
    dates = []
    per_period = []
    cumulative = []
    total = 0
    for year, month, count in monthly_counts:
        dates.append(datetime.date(year, month, 1))
        per_period.append(count)
        total += count
        cumulative.append(total)
    return dates, per_period, cumulative


def _weekly_dates_and_counts(weekly_counts):
    """Convert (iso_date_string, count) tuples to (dates, per_period, cumulative) lists."""
    dates = []
    per_period = []
    cumulative = []
    total = 0
    for date_str, count in weekly_counts:
        dates.append(datetime.date.fromisoformat(date_str))
        per_period.append(count)
        total += count
        cumulative.append(total)
    return dates, per_period, cumulative


def generate_verification_chart(data, granularity='monthly'):
    """Generate a two-panel verification chart and return it as a PNG bytes buffer.

    Top panel: cumulative verified users (step).
    Bottom panel: new verifications per period (bar).

    Args:
        data: list of tuples from BotDB — either monthly_verification_counts()
              or weekly_verification_counts() depending on granularity.
        granularity: 'monthly' or 'weekly'

    Returns:
        io.BytesIO with PNG data, or None if no data.
    """
    if not data:
        return None

    if granularity == 'weekly':
        dates, per_period, cumulative = _weekly_dates_and_counts(data)
        bar_width = 6
        bar_label = 'New per week'
    else:
        dates, per_period, cumulative = _monthly_dates_and_counts(data)
        bar_width = 25
        bar_label = 'New per month'

    fig, (ax_cum, ax_bar) = plt.subplots(2, 1, figsize=(7, 5), sharex=True)

    # Top: cumulative step chart
    ax_cum.step(dates, cumulative, where='post', linewidth=1.5, color='#5865F2')
    ax_cum.fill_between(dates, cumulative, step='post', alpha=0.15, color='#5865F2')
    ax_cum.set_ylabel('Total verified')
    ax_cum.set_title('Verification Stats')
    ax_cum.grid(axis='y', alpha=0.3)

    # Bottom: per-period bar chart
    ax_bar.bar(dates, per_period, width=bar_width, color='#5865F2', alpha=0.7)
    ax_bar.set_ylabel(bar_label)
    ax_bar.grid(axis='y', alpha=0.3)

    # X-axis formatting based on granularity
    if granularity == 'weekly':
        ax_bar.xaxis.set_major_locator(mdates.MonthLocator())
        ax_bar.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax_bar.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
        ax_bar.tick_params(axis='x', which='minor', length=3, labelsize=0)
        plt.setp(ax_bar.xaxis.get_majorticklabels(), rotation=30, ha='right')
    else:
        ax_bar.xaxis.set_major_locator(mdates.YearLocator())
        ax_bar.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax_bar.xaxis.set_minor_locator(mdates.MonthLocator())
        ax_bar.tick_params(axis='x', which='minor', length=3, labelsize=0)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf
