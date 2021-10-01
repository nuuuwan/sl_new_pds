from gig import ent_types, ents
from utils import jsonx

from sl_new_pds import _utils, region_utils
from sl_new_pds._constants import PARENT_TO_CHILD_TYPE
from sl_new_pds._utils import log_time
from sl_new_pds.conf import Conf


@log_time
def mutate_split_max_region(conf):
    print('mutate_split_max_region...')
    label_to_pop = conf.get_label_to_pop()
    total_pop = sum(label_to_pop.values())
    max_label = sorted(label_to_pop.items(), key=lambda x: -x[1],)[
        0
    ][0]
    max_label_pop = label_to_pop[max_label]
    max_label_seats_r = conf.get_total_seats() * max_label_pop / total_pop
    if max_label_seats_r >= 2.5:
        target_cand_pop = (
            (int)(max_label_seats_r / 2 + 0.5)
            * max_label_pop
            / max_label_seats_r
        )
    else:
        target_cand_pop = max_label_pop / 2

    _utils.print_json(
        dict(
            max_label=max_label,
            max_label_seats_r=max_label_seats_r,
            target_cand_pop=target_cand_pop,
        )
    )

    new_label_to_region_ids = _utils.dumb_copy(conf.get_label_to_region_ids())

    # If label points to single region then expand region
    max_label_region_ids = conf.get_label_to_region_ids()[max_label]
    do_expand = False

    if len(max_label_region_ids) == 1:
        do_expand = True

    elif len(max_label_region_ids) <= 2:
        pops = list(
            map(
                lambda region_id: (int)(
                    ents.get_entity(region_id)['population']
                ),
                max_label_region_ids,
            )
        )
        cand_pop = min(pops)
        min_seats_r = conf.get_total_seats() * cand_pop / total_pop
        print(max_label_region_ids, cand_pop, min_seats_r)
        if min_seats_r < 0.9:
            do_expand = True

    if do_expand:
        new_max_label_region_ids = []
        for max_label_region_id in max_label_region_ids:
            max_label_type = ent_types.get_entity_type(max_label_region_id)
            child_type = PARENT_TO_CHILD_TYPE[max_label_type]
            parent_id_key = max_label_type + '_id'
            new_max_label_region_ids0 = list(
                map(
                    lambda ent: ent['id'],
                    list(
                        filter(
                            lambda ent: max_label_region_id
                            == ent[parent_id_key]
                            and ent['centroid'],
                            ents.get_entities(child_type),
                        )
                    ),
                )
            )
            new_max_label_region_ids += new_max_label_region_ids0
    else:
        new_max_label_region_ids = max_label_region_ids

    # split label into north and south
    centroids = list(
        map(
            lambda region_id: ents.get_entity(region_id)['centroid'],
            new_max_label_region_ids,
        )
    )
    pops = list(
        map(
            lambda region_id: (int)(ents.get_entity(region_id)['population']),
            new_max_label_region_ids,
        )
    )
    bounds = _utils.get_bounds(centroids)

    min_cand_pop_div = None
    max_north_region_ids = None
    max_south_region_ids = None
    max_north_label = None
    max_south_label = None
    for i in [0, 1]:
        N_P = 40
        prev_cand_pop_div = None
        for p in [i / N_P for i in range(0, N_P + 1)]:
            north_label = ['NORTH', 'EAST'][i]
            south_label = ['SOUTH', 'WEST'][i]

            north_region_ids = []
            south_region_ids = []
            north_pop = 0
            south_pop = 0
            min_bound, max_bound = bounds[0][i], bounds[1][i]
            for region_id, centroid, pop in zip(
                new_max_label_region_ids, centroids, pops
            ):
                if centroid[i] > (min_bound + (max_bound - min_bound) * p):
                    north_region_ids.append(region_id)
                    north_pop += pop
                else:
                    south_region_ids.append(region_id)
                    south_pop += pop
            cand_pop = north_pop
            cand_pop_div = abs(cand_pop - target_cand_pop)
            if not min_cand_pop_div or min_cand_pop_div > cand_pop_div:
                min_cand_pop_div = cand_pop_div
                max_north_region_ids = north_region_ids
                max_south_region_ids = south_region_ids
                max_north_label = north_label
                max_south_label = south_label
            if prev_cand_pop_div and prev_cand_pop_div < cand_pop_div:
                break

            prev_cand_pop_div = cand_pop_div

    del new_label_to_region_ids[max_label]
    new_label_to_region_ids[
        max_label + '-' + max_north_label
    ] = max_north_region_ids
    new_label_to_region_ids[
        max_label + '-' + max_south_label
    ] = max_south_region_ids

    new_label_to_region_ids2 = {}
    for label, region_ids in new_label_to_region_ids.items():
        new_label = region_utils.get_label(label, region_ids)
        new_label_to_region_ids2[new_label] = region_ids

    return Conf(conf.get_total_seats(), new_label_to_region_ids2)


def mutate_until_only_simple_member(conf, district_id):
    _utils.print_json(conf.get_label_to_demo())
    MAX_INTERATIONS = 100
    for i in range(0, MAX_INTERATIONS):

        @log_time
        def inner(conf=conf):
            single_member_count = conf.get_single_member_count()
            p_single_member_count = single_member_count / conf.__total_seats__
            print('-' * 64)
            print(f'{i}) {p_single_member_count:.0%} complete...')
            print('-' * 64)
            if single_member_count == conf.__total_seats__:
                True, conf
            return False, mutate_split_max_region(conf)

        is_complete, conf = inner(conf)
        if is_complete:
            break

    _utils.print_obj(conf.get_label_to_demo())
    conf.print_stats()
    _utils.print_obj(conf.get_l2g2d2s())
    conf_file = f'/tmp/sl_new_pds.{district_id}.json'
    Conf.write(conf_file, conf)


if __name__ == '__main__':
    TOTAL_SEATS = 160
    district_to_confs = Conf.get_district_to_confs(TOTAL_SEATS)

    for district_id, conf in list(district_to_confs.items())[0:1]:
        mutate_until_only_simple_member(conf, district_id)
