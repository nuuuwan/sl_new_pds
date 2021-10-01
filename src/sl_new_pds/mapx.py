import colorsys
import math
import os
import random

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from geo import geodata
from gig import ent_types
from utils import dt

from sl_new_pds._constants import IDEAL_POP_PER_SEAT
from sl_new_pds._utils import log

LABEL_TO_COLOR = {}


def get_random_color():
    return [random.random() * 0.5 + 0.5 for _ in range(0, 3)]


# @cache('sl_new_pds', timex.SECONDS_IN.YEAR)
def get_label_color(label):
    if label not in LABEL_TO_COLOR:
        LABEL_TO_COLOR[label] = get_random_color()
    return LABEL_TO_COLOR[label]


def get_pop_color(pop):
    p_pop = pop / IDEAL_POP_PER_SEAT
    LIMIT_P = 3
    p_pop = max(min(p_pop, LIMIT_P), 1.0 / LIMIT_P)
    log_p_pop = math.log(p_pop) / math.log(LIMIT_P)

    h = 0 if (log_p_pop > 0) else 120
    lightness = 1 - 0.5 * abs(log_p_pop)
    s = 1.0
    r, g, b = colorsys.hls_to_rgb(h, lightness, s)
    return r, g, b


def draw_map(
    map_name, label_to_region_ids, label_to_seats=None, label_to_pop=None
):
    fig, ax = plt.subplots(figsize=(32, 18))

    for label, region_ids in label_to_region_ids.items():
        gpd_df_list = []
        for region_id in region_ids:
            region_type = ent_types.get_entity_type(region_id)
            gpd_df = geodata.get_region_geodata(region_id, region_type)
            gpd_df_list.append(gpd_df.explode()['geometry'])

        gpd_df = gpd.GeoSeries(pd.concat(gpd_df_list).unary_union)

        from shapely.geometry import JOIN_STYLE

        eps = 0.0001
        gpd_df = gpd_df.buffer(eps, 1, join_style=JOIN_STYLE.mitre).buffer(
            -eps, 1, join_style=JOIN_STYLE.mitre
        )

        xy = [
            gpd_df.centroid.x.tolist()[0],
            gpd_df.centroid.y.tolist()[0],
        ]

        label_final = label
        color = get_label_color(label)
        if label_to_seats:
            seats = label_to_seats.get(label)
            label_final += f' ({seats})'

            if label_to_pop:
                pop = label_to_pop.get(label)
                color = get_pop_color(pop / seats)
                if pop > 1_000_000:
                    pop_m = pop / 1_000_000
                    label_final += f' - {pop_m:.3g}M'
                elif pop > 1_000:
                    pop_k = pop / 1_000
                    label_final += f' - {pop_k:.3g}K'
                else:
                    label_final += f' - {pop:.3g}'

        gpd_df.plot(ax=ax, color=color, edgecolor="black", linewidth=1)
        ax.annotate(
            label_final, xy=(xy), horizontalalignment='center', size=12
        )

    ax.legend(loc='lower right', fontsize=15, frameon=True)

    map_name_str = dt.to_kebab(map_name)
    image_file = f'/tmp/sl_new_pds.map.{map_name_str}.png'
    plt.savefig(image_file)
    log.info(f'Wrote map to {image_file}')
    os.system(f'open -a firefox {image_file}')
    return image_file


if __name__ == '__main__':
    draw_map(
        map_name='New Electoral Districts',
        label_to_region_ids={
            'Colombo': [
                'LK-1127',
                'LK-1103',
            ],
            'Gampaha': [
                'LK-12',
            ],
            {},
        },
        label_to_seats={
            'Colombo': 4,
            'Gampaha': 19,
        },
        label_to_pop={
            'Colombo': 500_000,
            'Gampaha': 2_000_000,
        },
    )
