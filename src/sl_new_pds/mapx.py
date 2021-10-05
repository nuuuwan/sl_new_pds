import colorsys
import os

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from geo import geodata
from gig import ent_types
from shapely.geometry import JOIN_STYLE
from utils import dt

from sl_new_pds._constants import IDEAL_POP_PER_SEAT
from sl_new_pds._utils import log, log_time


def format_value(x):
    if x is None:
        return ''
    if x > 1_000_000:
        x_m = x / 1_000_000
        return f'{x_m:.0f}M'
    if x > 1_000:
        x_k = x / 1_000
        return f'{x_k:.0f}K'
    return f'{x}'


def get_legend_item_list():
    p_lower_bounds = [2, 3 / 2, 5 / 4, 4 / 5, 2 / 3, 1 / 2, None]
    legend_item_list = []
    upper_bound = None
    i_middle = (int)(len(p_lower_bounds) / 2)
    for i in range(0, len(p_lower_bounds)):
        p_lower_bound = p_lower_bounds[i]

        if p_lower_bound and p_lower_bound > 1:
            h = 0
            lightness = [0.55, 0.75, 0.95][i]
        else:
            h = 2.0 / 3
            lightness = [0.95, 0.95, 0.75, 0.55][i - i_middle]

        if i == i_middle:
            s = 0
        else:
            s = 1

        if p_lower_bound is not None:
            lower_bound = IDEAL_POP_PER_SEAT * p_lower_bound
        else:
            lower_bound = None

        label = format_value(lower_bound) + ' < ' + format_value(upper_bound)

        legend_item_list.append(
            {
                'lower_bound': lower_bound,
                'label': label,
                'color': colorsys.hls_to_rgb(h, lightness, s),
            }
        )
        upper_bound = lower_bound
    return legend_item_list


LEGEND_ITEM_LIST = get_legend_item_list()


def get_pop_color(pop):
    for legend_item in LEGEND_ITEM_LIST:
        lower_bound = legend_item['lower_bound']
        if lower_bound is None or pop > lower_bound:
            return legend_item['color']
    return 'black'


@log_time
def draw_map(
    map_name, label_to_region_ids, label_to_seats=None, label_to_pop=None
):
    all_gpd_df_list = []

    label_and_region_ids = sorted(
        label_to_region_ids.items(),
        key=lambda x: -label_to_pop[x[0]],
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

        gpd_df['color'] = gpd_df['population_per_seat'].map(
            lambda population_per_seat: get_pop_color(population_per_seat)
        )

        all_gpd_df_list.append(gpd_df)

    all_gpd_df = pd.concat(all_gpd_df_list)
    all_gpd_df.plot(
        color=all_gpd_df['color'],
        figsize=(16, 9),
        edgecolor="white",
        linewidth=2,
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
            seats_str = f' ({seats})'

        name = row['name']
        label = '(%d) %s %s %s' % (
            i_label + 1,
            population_str,
            name,
            seats_str,
        )
        label_min = '(%d)' % (i_label + 1)

        name_str = name
        if len(name_str) > 15:
            name_str = name_str[:6] + '...' + name_str[-6:]

        plt.annotate(
            text=label_min,
            xy=(x, y + 0.008),
            fontsize=12,
            ha='center',
        )

        plt.annotate(
            text=name_str,
            xy=(x, y - 0.008),
            fontsize=9,
            ha='center',
        )

        plt.annotate(
            text=label,
            xy=(24, 500 - i_label * 24),
            xycoords='figure points',
            fontsize=9,
        )

    map_name_str = dt.to_kebab(map_name)
    image_file = f'/tmp/sl_new_pds.map.{map_name_str}.png'


    plt.legend(
        handles=list(
            map(
                lambda legend_item: mpatches.Patch(
                    color=legend_item['color'], label=legend_item['label']
                ),
                LEGEND_ITEM_LIST,
            )
        )
    )

    plt.axis('off')
    plt.savefig(image_file)
    log.info(f'Wrote map to {image_file}')
    return image_file


if __name__ == '__main__':
    draw_map(
        map_name='New Electoral Districts',
        label_to_region_ids={
            'Colombo Central': [
                'EC-01B',
            ],
            'Colombo North': [
                'EC-01A',
            ],
            'Borella': [
                'EC-01C',
            ],
            'Colombo East': [
                'EC-01D',
            ],
            'Colombo West': [
                'EC-01E',
            ],
            'Maharagama & Homagama': [
                'EC-01L',
                'EC-01M',
            ],
        },
        label_to_seats={
            'Colombo Central': 1,
            'Colombo North': 1,
            'Borella': 1,
            'Colombo East': 1,
            'Colombo West': 1,
            'Maharagama & Homagama': 1 + 1,
        },
        label_to_pop={
            'Colombo Central': 201620,
            'Colombo North': 121603,
            'Borella': 89806,
            'Colombo East': 93260,
            'Colombo West': 54682,
            'Maharagama & Homagama': 237905 + 196423,
        },
    )
