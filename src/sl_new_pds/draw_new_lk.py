import os

from gig import ents

from sl_new_pds.conf import Conf
from sl_new_pds._constants import DIR_REACT


def get_lk_conf():
    ed_ents = ents.get_entities('ed')
    confs = []
    ed_ids = []
    for ed_ent in ed_ents:
        ed_id = ed_ent['id']
        ed_ids.append(ed_id)
        map_name = f'{ed_id}-FINAL'
        conf = Conf.read(f'/tmp/sl_new_pds.{map_name}.json')
        confs.append(conf)

    label_to_region_ids = {}
    total_seats = 0
    for conf in confs:
        for label, region_ids in conf.get_label_to_region_ids().items():
            label_to_region_ids[label] = region_ids
        total_seats += conf.get_total_seats()

    lk_conf = Conf(
        total_seats=total_seats, label_to_region_ids=label_to_region_ids
    )
    Conf.write(f'{DIR_REACT}/sl_new_pds.lk-FINAL.json', lk_conf)
    return lk_conf, ed_ids


def draw_new_lk():
    lk_conf, ed_ids = get_lk_conf()
    image_file = lk_conf.draw_map(
        ed_ids,
        'new_lk',
    )
    os.system(f'open -a firefox {image_file}')
    return image_file


if __name__ == '__main__':
    get_lk_conf()
