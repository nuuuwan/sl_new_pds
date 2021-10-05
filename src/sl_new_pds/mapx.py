import colorsys
import math
import os
import random

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from geo import geodata
from gig import ent_types
from shapely.geometry import JOIN_STYLE
from utils import dt

from sl_new_pds._constants import IDEAL_POP_PER_SEAT
from sl_new_pds._utils import log, log_time

LABEL_TO_COLOR = {}


def get_random_color():
    return [random.random() * 0.5 + 0.5 for _ in range(0, 3)]


# @cache('sl_new_pds', timex.SECONDS_IN.YEAR)
def get_label_color(label):
    if label not in LABEL_TO_COLOR:
        LABEL_TO_COLOR[label] = get_random_color()
    return LABEL_TO_COLOR[label]


def get_pop_color(pop):
    pop_r = pop / IDEAL_POP_PER_SEAT
    log_pop_r = math.log(pop_r) / math.log(2)
    abs_log_pop_r = abs(log_pop_r)

    h = 0 if (log_pop_r > 0) else 2 / 3

    if abs_log_pop_r < 0.25:
        s = 0
        lightness = 0.9
    else:
        s = 1
        if abs_log_pop_r > 1:
            lightness = 0.5

        elif abs_log_pop_r > 0.5:
            lightness = 0.9
            
        else:
            lightness = 0.95

    return colorsys.hls_to_rgb(h, lightness, s)


def get_pop_color2(pop):
    pop_r = pop / IDEAL_POP_PER_SEAT
    log_pop_r = math.log(pop_r) / math.log(2)

    abs_log_pop_r = min(abs(log_pop_r), 1)
    P_POP_PER_SEAT_LIMIT = 0.25
    log_limit = math.log(P_POP_PER_SEAT_LIMIT + 1) / math.log(2)

    if abs_log_pop_r < log_limit:
        return (0.8, 0.8, 0.8)

    h = 0 if (log_pop_r > 0) else 2 / 3
    lightness = 1 - 0.8 * (abs_log_pop_r - P_POP_PER_SEAT_LIMIT) / (
        1 - P_POP_PER_SEAT_LIMIT
    )
    s = 1

    return colorsys.hls_to_rgb(h, lightness, s)


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
        edgecolor="black",
        linewidth=1,
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

        plt.annotate(
            text=label_min,
            xy=(x, y),
            fontsize=12,
        )

        plt.annotate(
            text=label,
            xy=(24, 500 - i_label * 24),
            xycoords='figure points',
            fontsize=9,
        )

    map_name_str = dt.to_kebab(map_name)
    image_file = f'/tmp/sl_new_pds.map.{map_name_str}.png'
    plt.axis('off')
    plt.savefig(image_file)
    log.info(f'Wrote map to {image_file}')
    os.system(f'open -a firefox {image_file}')
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
