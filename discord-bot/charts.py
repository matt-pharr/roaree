import io
import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def generate_verification_chart(monthly_counts):
    """Generate a two-panel verification chart and return it as a PNG bytes buffer.

    Top panel: cumulative verified users (step).
    Bottom panel: new verifications per month (bar).

    Args:
        monthly_counts: list of (year, month, count) tuples from BotDB.monthly_verification_counts()

    Returns:
        io.BytesIO with PNG data, or None if no data.
    """
    if not monthly_counts:
        return None

    dates = []
    per_month = []
    cumulative_counts = []
    cumulative = 0
    for year, month, count in monthly_counts:
        dates.append(datetime.date(year, month, 1))
        per_month.append(count)
        cumulative += count
        cumulative_counts.append(cumulative)

    fig, (ax_cum, ax_month) = plt.subplots(2, 1, figsize=(7, 5), sharex=True)

    # Top: cumulative step chart
    ax_cum.step(dates, cumulative_counts, where='post', linewidth=1.5, color='#5865F2')
    ax_cum.fill_between(dates, cumulative_counts, step='post', alpha=0.15, color='#5865F2')
    ax_cum.set_ylabel('Total verified')
    ax_cum.set_title('Verification Stats')
    ax_cum.grid(axis='y', alpha=0.3)

    # Bottom: per-month bar chart
    bar_width = 25  # days, slightly less than a month
    ax_month.bar(dates, per_month, width=bar_width, color='#5865F2', alpha=0.7)
    ax_month.set_ylabel('New per month')
    ax_month.grid(axis='y', alpha=0.3)

    # Shared x-axis: major = years, minor = months
    ax_month.xaxis.set_major_locator(mdates.YearLocator())
    ax_month.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax_month.xaxis.set_minor_locator(mdates.MonthLocator())
    ax_month.tick_params(axis='x', which='minor', length=3, labelsize=0)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf
