"""Example."""
import os

from gig import ents
from utils import dt

from sl_new_pds import mapx

if __name__ == '__main__':

    ED_ID = 'EC-07'
    ed_ent = ents.get_entity(ED_ID)
    ed_label = dt.to_kebab(ED_ID + ' ' + ed_ent['name'])

    label_to_region_ids = {}
    label_to_pop = {}
    label_to_seats = {}

    for pd_ent in ents.get_entities('pd'):
        if pd_ent['ed_id'] != ED_ID:
            continue
        label = pd_ent['name']
        pop = pd_ent['population']
        if not pop:
            continue
        region_ids = [pd_ent['id']]

        label_to_region_ids[label] = region_ids
        label_to_pop[label] = pop
        label_to_seats[label] = 1

    tmp_image_file = mapx.draw_map(
        map_name=ed_label,
        label_to_region_ids=label_to_region_ids,
        label_to_pop=label_to_pop,
        label_to_seats=label_to_seats,
    )
    ed_str = dt.to_kebab(ed_label)
    img_file = f'src/sl_new_pds/examples/example-1-ed-current.{ed_str}.png'
    os.system(f'cp "{tmp_image_file}" "{img_file}"')
