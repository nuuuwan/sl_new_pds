import colorsys
import math
import os
import random

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd
from geo import geodata
from gig import ent_types
from utils import dt
from shapely.geometry import Polygon


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
    all_gpd_df_list = []
    for label, region_ids in label_to_region_ids.items():
        gpd_ds_list = []
        for region_id in region_ids:
            region_type = ent_types.get_entity_type(region_id)
            gpd_df = geodata.get_region_geodata(region_id, region_type)
            gpd_ds_list.append(gpd_df.explode()['geometry'])
        gpd_ds = gpd.GeoSeries(pd.concat(gpd_ds_list).unary_union)

        from shapely.geometry import JOIN_STYLE
        eps = 0.0001
        gpd_ds = gpd_ds.buffer(eps, 1, join_style=JOIN_STYLE.mitre).buffer(
            -eps, 1, join_style=JOIN_STYLE.mitre
        )

        gpd_df = gpd.GeoDataFrame()
        gpd_df['geometry'] = gpd_ds
        gpd_df['name'] = label

        seats = label_to_seats.get(label)
        gpd_df['seats'] = seats

        pop = label_to_pop.get(label)
        gpd_df['population'] = pop

        gpd_df['population_per_seat'] = gpd_df['population'] / gpd_df['seats']

        all_gpd_df_list.append(gpd_df)

    all_gpd_df = pd.concat(all_gpd_df_list)
    all_gpd_df.plot(
        column='population_per_seat',
        legend=True,
        cmap='coolwarm',
        figsize=(16, 9),
        edgecolor="black",
        linewidth=1,
    )

    for idx, row in all_gpd_df.iterrows():
        [x, y] = [
            row['geometry'].centroid.x,
            row['geometry'].centroid.y,
        ]
        plt.annotate(
            s=row['name'],
            xy=[x, y],
            horizontalalignment='center',
            fontsize=8,
        )
        population_k = row['population'] / 1_000
        seats = row['seats']
        seats_str = ''
        if seats > 1:
            seats_str = f' ({seats})'

        plt.annotate(
            s=f'{population_k:.3g}K {seats_str}',
            xy=[x, y + 0.004],
            horizontalalignment='center',
            fontsize=12,
        )

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
            'Colombo North': [
                'EC-01A',
            ],
            'Colombo Central': [
                'EC-01B',
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
            'Kaduwela': [
                'EC-01J',
            ],
        },
        label_to_seats={
            'Colombo North': 1,
            'Colombo Central': 1,
            'Borella': 1,
            'Colombo East': 1,
            'Colombo West': 1,
            'Kaduwela': 1,
        },
        label_to_pop={
            'Colombo North': 121603,
            'Colombo Central': 201620,
            'Borella': 89806,
            'Colombo East': 93260,
            'Colombo West': 54682,
            'Kaduwela': 252041,
        },
    )
