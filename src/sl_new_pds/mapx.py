import os
import random

import matplotlib.pyplot as plt
from geo import geodata
from gig import ent_types
from utils import dt, timex
from utils.cache import cache

from sl_new_pds._utils import log

LABEL_TO_COLOR = {}


def get_random_color():
    return [random.random() * 0.5 + 0.5 for _ in range(0, 3)]


@cache('sl_new_pds', timex.SECONDS_IN.YEAR)
def get_color(label):
    if label not in LABEL_TO_COLOR:
        LABEL_TO_COLOR[label] = get_random_color()
    return LABEL_TO_COLOR[label]


def draw_map(
    map_name, label_to_region_ids, label_to_seats=None, label_to_pop=None
):
    fig, ax = plt.subplots(figsize=(32, 18))

    for label, region_ids in label_to_region_ids.items():
        gpd_df = None
        for region_id in region_ids:
            region_type = ent_types.get_entity_type(region_id)
            new_gpd_df = geodata.get_region_geodata(region_id, region_type)
            if gpd_df is None:
                gpd_df = new_gpd_df
            else:
                gpd_df = gpd_df.append(new_gpd_df)

        gpd_df.plot(ax=ax, color=get_color(label))
        xy = [
            sum(gpd_df.centroid.x.tolist()) / len(region_ids),
            sum(gpd_df.centroid.y.tolist()) / len(region_ids),
        ]
        label_final = label
        if label_to_seats:
            seats = label_to_seats.get(label)
            label_final += f' ({seats})'
        if label_to_pop:
            pop = label_to_pop.get(label)
            pop_k = pop / 1_000
            label_final += f' - {pop_k:.3g}K'

        ax.annotate(
            label_final, xy=(xy), horizontalalignment='center', size=12
        )

    map_name_str = dt.to_kebab(map_name)
    image_file = f'/tmp/sl_new_pds.map.{map_name_str}.png'
    plt.savefig(image_file)
    log.info(f'Wrote map to {image_file}')
    os.system(f'open -a firefox {image_file}')
    return image_file


if __name__ == '__main__':
    label_to_region_ids = {
        'Colombo': [
            'LK-1103',
            'LK-1127',
        ],
        # 'Gampaha': [
        #     'LK-12',
        # ],
    }
    draw_map('New Electoral Districts', label_to_region_ids)
