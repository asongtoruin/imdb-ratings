from datetime import datetime
from pathlib import Path

import imdb
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import pandas as pd
import plot_styles
import seaborn as sns
from yaml import load, Loader


def get_episode_frame(client, show_id):
    show = client.get_movie(show_id)

    # Updated episodes
    client.update(show, 'episodes')

    episodes = []
    for _, series in show['episodes'].items():
        for _, episode in series.items():
            e_dict = dict(episode)
            e_dict.pop('episode of', None)
            episodes.append(e_dict)

    episode_frame = pd.DataFrame.from_records(episodes)
    episode_frame['Episode_ID'] = episode_frame['season'] * 100 + episode_frame['episode']
    episode_frame['episode'] = pd.Categorical(episode_frame['episode'])

    return episode_frame.sort_values(by='Episode_ID')


def draw_episode_charts(episode_frame, show_title, palette='rocket'):
    # Get matrix for use in heatmap
    matrix = episode_frame.pivot_table(
        index='episode', columns='season', values='rating'
    )

    # Scale according to number of series and max number of episodes
    height = 1 + len(matrix) / 2
    width = 1 + len(matrix.columns) / 3

    fig, axes = plt.subplots(
        figsize=(width, height + 4), nrows=2, 
        gridspec_kw=dict(height_ratios=(2, height)), sharex=True,
    )

    # Scatter needs to be offset to align properly
    offset = matrix.mean().index - 0.5
    values = matrix.mean()

    # Draw the points, and then the lines between them
    sns.scatterplot(
        x=offset, y=values, ax=axes[0], 
        hue=values, hue_norm=(0,10), palette=palette, 
        zorder=2, legend=False
    )

    # Make the line the same colour as text
    sns.lineplot(
        x=offset, y=values, ax=axes[0], color=plt.rcParams['text.color'], 
        alpha=0.1, zorder=1
    )

    # Label all of the series averages
    for x, y in zip(offset, values):
        axes[0].annotate(
            f'{y:.01f}', xy=(x, y), 
            xytext=(0, 15), textcoords='offset pixels', ha='center'
        )

    # Tweak the scatter
    axes[0].axis('off')
    axes[0].annotate(
        'Average Rating', xy=(0,0.5), xycoords='axes fraction', 
        ha='right', va='center', rotation=90
    )

    # Draw the heatmap
    sns.heatmap(
        matrix, square=False, 
        vmin=0, vmax=10, annot=True, cmap=palette,
        linewidths=1, linecolor=plt.rcParams['axes.facecolor'],
        cbar_kws=dict(
            use_gridspec=True, orientation='horizontal', label='IMDb Rating', 
            pad=0.01, shrink=3/width
        ),
        ax=axes[1],
    )

    # Heatmap configuration
    axes[1].tick_params(axis='y', rotation=0)
    axes[1].xaxis.tick_top()
    axes[1].xaxis.set_label_position('top') 
    axes[1].set_xlabel(axes[1].get_xlabel().title())
    axes[1].set_ylabel(axes[1].get_ylabel().title())
    axes[1].tick_params(length=0)

    plt.subplots_adjust(hspace=0.08)

    # Work out the highest and lowest rated episodes
    best = episode_frame.iloc[episode_frame['rating'].idxmax()]
    worst = episode_frame.iloc[episode_frame['rating'].idxmin()]

    # Some shows have an "episode 0", so we need to be careful where we highlight
    episode_offset = (
        episode_frame['episode'].astype(int).min() - axes[1].get_ylim()[1]
    )

    # Try and stop text from overlapping
    if best['episode'] == worst['episode']:
        best_va = 'bottom'
        worst_va = 'top'
    else:
        best_va = worst_va = 'center'

    # Draw boxes for bext and worst episodes
    best_box = Rectangle(
        xy=(best['season'] - 1, best['episode'] - episode_offset), 
        width=1, height=1, 
        facecolor='none', edgecolor=plt.rcParams['text.color'], linewidth=2
    )
    worst_box = Rectangle(
        xy=(worst['season'] - 1, worst['episode'] - episode_offset), 
        width=1, height=1, 
        facecolor='none', edgecolor=plt.rcParams['text.color'], linewidth=2
    )

    # Draw on the best and worst boxes
    axes[1].add_patch(best_box)
    axes[1].add_patch(worst_box)

    # Add in text for highest and lowest rated
    axes[1].annotate(
        f'Highest rated: {best["title"]}', 
        xy=(1, best['episode'] + 0.5 - episode_offset), 
        xycoords=('axes fraction', 'data'), 
        xytext=(8, 0), textcoords='offset pixels',
        ha='left', va=best_va
    )

    axes[1].annotate(
        f'Lowest rated: {worst["title"]}', 
        xy=(1, worst['episode'] + 0.5 - episode_offset), 
        xycoords=('axes fraction', 'data'), 
        xytext=(8, 0), textcoords='offset pixels',
        ha='left', va=worst_va
    )

    # Dummy text for spacing
    axes[1].annotate(
        f'Highest rated: {best["title"]}', 
        xy=(0, 0.5), alpha=0, 
        xycoords='axes fraction', 
        xytext=(-8, 0), textcoords='offset pixels',
        ha='right', va=best_va
    )
    axes[1].annotate(
        f'Lowest rated: {worst["title"]}', 
        xy=(0, 0.5), alpha=0, 
        xycoords='axes fraction', 
        xytext=(-8, 0), textcoords='offset pixels',
        ha='right', va=best_va
    )

    # Add in the overall title
    axes[0].annotate(
        f'{title} IMDb Ratings', xy=(0.5, 1), 
        xycoords='axes fraction',
        xytext=(0, 40), textcoords='offset points', 
        weight='bold', ha='center', va='bottom', size='xx-large'
    )

    # today = datetime.now().strftime('%Y-%m-%d')
    today = datetime.now().strftime('%d %B %Y').lstrip('0')
    
    axes[0].annotate(
        f'Data obtained {today}\n'
        'For more information visit ruszkow.ski/graphs/2021-06-27-imdb-series-rating-summaries', 
        xy=(0.5, 1), 
        xycoords='axes fraction',
        xytext=(0, 35), textcoords='offset points', 
        weight='regular', ha='center', va='top', size='x-small'
    )

    return fig, axes


if __name__ == '__main__':
    plt.style.use('blog')
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['savefig.dpi'] = 150
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = 'Lato'
    plt.rcParams['font.weight'] = 'regular'

    output_folder = Path(r'Graphs/Series Summaries')
    output_folder.mkdir(exist_ok=True)

    with open('tracked_series.yml', 'r') as yml_file:
        tracked_series = load(yml_file, Loader=Loader)
    
    client = imdb.IMDb()

    for series in tracked_series:
        try:
            title = series['series_name']
            print(title)
            episode_frame = get_episode_frame(client, series['series_id'])

            fig, axes = draw_episode_charts(episode_frame, title)

            fig.savefig(output_folder / title, bbox_inches='tight')

        except:
            # make sure everything is closed if we hit an error
            plt.close('all')
