import os

from gig import ents
from utils import dt

from sl_new_pds import mapx


def draw(ed_id):

    ed_ent = ents.get_entity(ed_id)
    ed_label = dt.to_kebab(ed_id + ' ' + ed_ent['name'])

    label_to_region_ids = {}
    label_to_pop = {}
    label_to_seats = {}

    for pd_ent in ents.get_entities('pd'):
        if pd_ent['ed_id'] != ed_id:
            continue
        label = pd_ent['name']
        pop = pd_ent['population']
        if not pop:
            continue
        region_ids = [pd_ent['id']]

        label_to_region_ids[label] = region_ids
        label_to_pop[label] = pop
        label_to_seats[label] = 1

    image_file = mapx.draw_map(
        map_name=ed_label,
        label_to_region_ids=label_to_region_ids,
        label_to_pop=label_to_pop,
        label_to_seats=label_to_seats,
    )
    os.system(f'open -a firefox {image_file}')


if __name__ == '__main__':
    draw('EC-01')
