import io
import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def generate_verification_chart(monthly_counts):
    """Generate a cumulative verification step chart and return it as a PNG bytes buffer.

    Args:
        monthly_counts: list of (year, month, count) tuples from BotDB.monthly_verification_counts()

    Returns:
        io.BytesIO with PNG data, or None if no data.
    """
    if not monthly_counts:
        return None

    dates = []
    counts = []
    cumulative = 0
    for year, month, count in monthly_counts:
        dates.append(datetime.date(year, month, 1))
        cumulative += count
        counts.append(cumulative)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.step(dates, counts, where='post', linewidth=1.5, color='#5865F2')
    ax.fill_between(dates, counts, step='post', alpha=0.15, color='#5865F2')

    # Major ticks: years. Minor ticks: months.
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())

    ax.tick_params(axis='x', which='major', labelsize=10)
    ax.tick_params(axis='x', which='minor', length=3, labelsize=0)
    ax.set_ylabel('Total verified users')
    ax.set_title('Cumulative Verifications Over Time')
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf
