from datetime import datetime
from pathlib import Path

from imdb import Cinemagoer
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import plot_styles
import seaborn as sns

plt.style.use('blog')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = 'Lato'
plt.rcParams['font.weight'] = 'regular'

output_dir = Path('Graphs')
output_dir.mkdir(exist_ok=True)

client = Cinemagoer()

top = client.get_top250_tv()[:100]

for show in top:
    print(show)
    try:
        client.update(show, 'episodes')
    except KeyError:
        print(f'Could not get episodes for {show}')

top_episodes = []
for show in top:
    for _, series in show.get('episodes', dict()).items():
        for _, episode in series.items():
            e_dict = dict(episode)
            e_dict.pop('episode of', None)
            top_episodes.append(e_dict)

top_frame = pd.DataFrame.from_records(top_episodes)
top_frame['original air date'] = pd.to_datetime(top_frame['original air date'])
top_frame['series_short'] = top_frame['series title'].str.split(r' \(').str[0]

top_frame.sort_values(by=['original air date', 'series_short', 'season', 'episode'], inplace=True)

top_frame = top_frame.dropna(subset=['original air date', 'rating'])\
                     .reset_index(drop=True)

top_frame['date_rejigged'] = top_frame['original air date']

cumulative_date_count = top_frame.groupby(['series_short', 'date_rejigged']).transform('cumcount')

while cumulative_date_count.max() > 0:
    top_frame['date_rejigged'] += cumulative_date_count.apply(pd.Timedelta, unit='D')
    cumulative_date_count = top_frame.groupby(['series_short', 'date_rejigged']).transform('cumcount')


fig, ax = plt.subplots(figsize=(30, 30))

sns.scatterplot(
    data=top_frame, x='date_rejigged', y='series_short', hue='rating', 
    hue_norm=(0,10), marker='|', ax=ax, palette='rocket', s=100, zorder=2,
    legend=False
)

ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.tick_params(axis='both', which='both', length=0, labelsize='xx-large')

ax.xaxis.set_minor_locator(mdates.YearLocator())
ax.grid(axis='x', zorder=1, alpha=0.3, which='major')
ax.grid(axis='x', zorder=1, alpha=0.3, ls=':', which='minor')

fig.canvas.draw()
for show in ax.get_yticklabels():
    name = show.get_text()
    first_aired = top_frame[top_frame['series_short'].eq(name)]['original air date'].min()
    ax.annotate(
        name, (first_aired, show._y), 
        xytext=(-20, 0), textcoords='offset pixels', 
        ha='right', va='center'
    )

ax.set_yticklabels([])
ax.set_ylabel(None)
ax.set_xlabel(None)


sm = plt.cm.ScalarMappable(cmap='rocket', norm=plt.Normalize(0, 10))
cbar = ax.figure.colorbar(
    sm, orientation='horizontal', shrink=0.3, pad=0.03, label='User Rating', 
    drawedges=False
)
cbar.outline.set_linewidth(0)

ax.set_title(
    'IMDb\'s 100 Highest User-Rated TV Shows', size=40, weight='bold', 
    pad=30, va='bottom'
)
ax.annotate(
    f'As of {datetime.now().strftime("%Y-%m-%d")}, sorted by original air '
    'date of first episode. For more information, visit '
    'ruszkow.ski/graphs/2021-06-23-imdbs-highest-rated-tv-series', xy=(0.5, 1), 
    xycoords='axes fraction', xytext=(0, 25), textcoords='offset points', 
    va='top', ha='center',size='xx-large'
)

ax.margins(x=0.01, y=0.01)

plt.savefig(output_dir /'Highest Rated.png', bbox_inches='tight')
