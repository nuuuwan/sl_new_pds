import colorsys

import geopandas as gpd
import matplotlib.patches as mpatches
import pandas as pd
from geo import geodata
from gig import ent_types
from shapely.geometry import JOIN_STYLE

from sl_new_pds._constants import IDEAL_POP_PER_SEAT
from sl_new_pds._utils import get_fore_color_for_back, log_time, to_unkebab

EDGE_COLOR = 'gray'
EDGE_WIDTH = 1
ALPHA = 0.75


def format_value(x):
    if x is None:
        return ''
    return f'{x:+.1f} seats'


def get_legend_item_list():
    p_lower_bounds = [1, 0.5, 0.2, -0.2, -0.5, -1, None]
    legend_item_list = []
    p_upper_bound = None
    i_middle = (int)(len(p_lower_bounds) / 2)
    for i in range(0, len(p_lower_bounds)):
        p_lower_bound = p_lower_bounds[i]

        if p_lower_bound and p_lower_bound > 0:
            h = 0
            lightness = [0.55, 0.75, 0.95][i]
        else:
            h = 2.0 / 3
            lightness = [0.75, 0.95, 0.75, 0.55][i - i_middle]

        if i == i_middle:
            s = 0
        else:
            s = 1

        label = (
            format_value(p_lower_bound) + ' < ' + format_value(p_upper_bound)
        )

        legend_item_list.append(
            {
                'p_lower_bound': p_lower_bound,
                'p_upper_bound': p_upper_bound,
                'label': label,
                'color': colorsys.hls_to_rgb(h, lightness, s),
            }
        )
        p_upper_bound = p_lower_bound
    return legend_item_list


LEGEND_ITEM_LIST = get_legend_item_list()


def get_seats_color(seats_by_pop, seats_actual):
    diff = seats_by_pop - seats_actual

    for legend_item in LEGEND_ITEM_LIST:
        p_lower_bound = legend_item['p_lower_bound']
        if p_lower_bound is None or diff > p_lower_bound:
            return legend_item['color']
    return 'green'


def get_short_name(name):
    name = name.replace('-', ' ').upper()
    name = name.replace('ED ', '')
    words = name.split(' ')
    n_words = len(words)

    new_words = []
    if n_words == 1:
        new_words += [words[0][:5]]
    elif n_words == 2:
        new_words += [
            words[0][:3],
            words[1][:1],
        ]
    else:
        new_words += [
            words[0][:1],
            words[-2][:1],
            words[-1][:1],
        ]
    return '-'.join(new_words)


@log_time
def draw_map(
    ax_map,
    ax_text,
    title,
    label_to_region_ids,
    label_to_seats=None,
    label_to_pop=None,
    HEIGHT=900,
):
    all_gpd_df_list = []

    label_and_region_ids = sorted(
        label_to_region_ids.items(),
        key=lambda x: get_short_name(x[0]),
    )

    for i_label, [label, region_ids] in enumerate(label_and_region_ids):
        region0_id = region_ids[0]
        region0_type = ent_types.get_entity_type(region0_id)
        gpd_df = geodata.get_all_geodata(region0_type)
        gpd_df = gpd_df[gpd_df['id'].str.contains('|'.join(region_ids))]
        gpd_ds = gpd_df.explode()['geometry']
        gpd_ds = gpd.GeoSeries(gpd_ds.unary_union)
        eps = 0.0001
        gpd_ds = gpd_ds.buffer(eps, 1, join_style=JOIN_STYLE.mitre).buffer(
            -eps, 1, join_style=JOIN_STYLE.mitre
        )

        gpd_df = gpd.GeoDataFrame()
        gpd_df['geometry'] = gpd_ds
        gpd_df['name'] = label
        gpd_df['i_label'] = i_label

        seats = label_to_seats.get(label)
        gpd_df['seats'] = seats

        pop = label_to_pop.get(label)
        gpd_df['population'] = pop

        gpd_df['population_per_seat'] = gpd_df['population'] / gpd_df['seats']
        gpd_df['seats_r'] = gpd_df['population'] / gpd_df['seats']

        gpd_df['color'] = gpd_df['population'].map(
            lambda population: get_seats_color(
                population / IDEAL_POP_PER_SEAT, seats
            )
        )

        all_gpd_df_list.append(gpd_df)

    all_gpd_df = pd.concat(all_gpd_df_list)
    back_color = all_gpd_df['color']
    all_gpd_df.plot(
        ax=ax_map,
        color=back_color,
        edgecolor=EDGE_COLOR,
        linewidth=EDGE_WIDTH,
        alpha=ALPHA,
    )

    x0, y0 = 0.05, 1 - 0.2
    ax_text.annotate(
        text=title.title(),
        xy=(x0, y0),
        xycoords='axes fraction',
        fontsize=12,
    )

    for idx, row in all_gpd_df.iterrows():
        [x, y] = [
            row['geometry'].centroid.x,
            row['geometry'].centroid.y,
        ]

        i_label = row['i_label']

        population = row['population']
        if population > 1_000_000:
            population_m = population / 1_000_000
            population_str = f'{population_m:.3g}M'
        elif population > 1_000:
            population_k = population / 1_000
            population_str = f'{population_k:.3g}K'
        else:
            population_str = f'{population}'

        seats = row['seats']
        seats_str = ''
        if seats > 1:
            seats_str = f' ({seats} seats)'

        name = row['name']
        short_name = get_short_name(name)

        label = '[%s] %s %s %s' % (
            short_name,
            population_str,
            to_unkebab(name),
            seats_str,
        )

        seats_r = population / IDEAL_POP_PER_SEAT
        ax_map.annotate(
            text=short_name,
            xy=(x, y),
            fontsize=5,
            ha='center',
            color=get_fore_color_for_back(get_seats_color(seats_r, seats)),
        )

        ax_text.annotate(
            text=label,
            xy=(x0, y0 - (i_label + 1.25 + 0.5 * (int)(i_label / 5)) * 0.02),
            xycoords='axes fraction',
            fontsize=6,
        )

    ax_map.set_axis_off()
    ax_text.set_axis_off()


def draw_legend(ax):
    ax.legend(
        handles=list(
            map(
                lambda legend_item: mpatches.Patch(
                    color=legend_item['color'],
                    label=legend_item['label'],
                    alpha=ALPHA,
                ),
                LEGEND_ITEM_LIST,
            )
        ),
        loc='center right',
        fontsize=8,
    )
    ax.set_axis_off()
