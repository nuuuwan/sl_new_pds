import math
import os

from gig import ent_types, ents

from sl_new_pds import _utils, draw_current, region_utils
from sl_new_pds._constants import PARENT_TO_CHILD_TYPE, TOTAL_SEATS_SL
from sl_new_pds._utils import log, log_time
from sl_new_pds.conf import Conf


@log_time
def expand_region(conf, expand_label):
    expand_label_region_ids = conf.get_label_to_region_ids()[expand_label]
    all_expanded_region_ids = []
    for region_id in expand_label_region_ids:
        region_type = ent_types.get_entity_type(region_id)
        child_type = PARENT_TO_CHILD_TYPE[region_type]
        parent_id_key = region_type + '_id'

        expanded_region_ids = list(
            map(
                lambda ent: ent['id'],
                list(
                    filter(
                        lambda ent: region_id == ent[parent_id_key]
                        and ent['centroid'],
                        ents.get_entities(child_type),
                    )
                ),
            )
        )
        all_expanded_region_ids += expanded_region_ids

    new_label_to_region_ids = conf.get_label_to_region_ids()
    new_label_to_region_ids[expand_label] = all_expanded_region_ids
    return Conf(
        total_seats=conf.get_total_seats(),
        label_to_region_ids=new_label_to_region_ids,
    )


@log_time
def split_region_tentative(conf, split_label):
    label_to_pop = conf.get_label_to_pop()
    total_pop = sum(label_to_pop.values())
    total_seats = conf.get_total_seats()

    split_label_pop = label_to_pop[split_label]
    split_label_seats_r = total_seats * split_label_pop / total_pop

    if split_label_seats_r < 2:
        split_label_seats_round = split_label_seats_r * 0.5
    else:
        split_label_seats_round = round(split_label_seats_r, 0)
        split_label_seats_round = math.ceil(split_label_seats_round * 0.5) * (
            split_label_seats_r / split_label_seats_round
        )

    split_point_pop = split_label_seats_round * total_pop / total_seats

    region_ids = conf.get_label_to_region_ids()[split_label]
    n_regions = len(region_ids)

    log.info(
        'Splitting (Tentative) %s ' % (split_label)
        + '(%d child regions, %4.2f seats, %4.3fK pop) '
        % (
            n_regions,
            split_label_seats_r,
            split_label_pop / 1_000,
        )
        + 'at %d (%4.1f seats)'
        % (
            split_point_pop,
            split_label_seats_round,
        )
    )

    region_ents = list(
        map(
            lambda region_id: ents.get_entity(region_id),
            region_ids,
        )
    )
    centroids = list(map(lambda e: e['centroid'], region_ents))
    [[min_lat, min_lng], [max_lat, max_lng]] = _utils.get_bounds(centroids)
    lat_span, lng_span = max_lat - min_lat, max_lng - min_lng

    search_meta_list = []
    LAT_LNG_SKEW = 1.5
    if LAT_LNG_SKEW * lng_span > lat_span:
        low_prefix = 'W'
        high_prefix = 'E'
        ents_sorted = sorted(
            region_ents,
            key=lambda e: e['centroid'][1],
        )
        search_meta_list.append(
            dict(
                low_prefix=low_prefix,
                high_prefix=high_prefix,
                ents_sorted=ents_sorted,
            )
        )
        search_meta_list.append(
            dict(
                low_prefix=high_prefix,
                high_prefix=low_prefix,
                ents_sorted=reversed(ents_sorted),
            )
        )

    if LAT_LNG_SKEW * lat_span > lng_span:
        low_prefix = 'S'
        high_prefix = 'N'
        ents_sorted = sorted(
            region_ents,
            key=lambda e: e['centroid'][0],
        )
        search_meta_list.append(
            dict(
                low_prefix=low_prefix,
                high_prefix=high_prefix,
                ents_sorted=ents_sorted,
            )
        )
        search_meta_list.append(
            dict(
                low_prefix=high_prefix,
                high_prefix=low_prefix,
                ents_sorted=reversed(ents_sorted),
            )
        )

    def get_pop_div(pop):
        return abs(pop - split_point_pop)

    min_pop_div = None
    sel_low_region_ids = []
    sel_high_region_ids = []

    for search_meta in search_meta_list:
        split_cum_pop = 0
        cum_pop = 0
        low_region_ids = []
        high_region_ids = []

        prev_pop_div = None
        split_pop_div = None
        for e in search_meta['ents_sorted']:
            pop = e['population']
            cum_pop += pop
            pop_div = get_pop_div(cum_pop)
            if prev_pop_div is None or (pop_div < prev_pop_div):
                low_region_ids.append(e['id'])
                split_cum_pop = cum_pop
                split_pop_div = pop_div
            else:
                high_region_ids.append(e['id'])
            prev_pop_div = pop_div

        if not min_pop_div or split_pop_div < min_pop_div:
            min_pop_div = split_pop_div
            max_split_cum_pop = split_cum_pop
            sel_low_prefix = search_meta['low_prefix']
            sel_high_prefix = search_meta['high_prefix']
            sel_low_region_ids = low_region_ids
            sel_high_region_ids = high_region_ids

    split_cum_pop_seats_r = max_split_cum_pop * total_seats / total_pop
    rev_split_cum_pop_seats_r = (
        (split_label_pop - max_split_cum_pop) * total_seats / total_pop
    )

    SEAT_LIMIT = 0.76
    min_cum_pop_seats_r = min(split_cum_pop_seats_r, rev_split_cum_pop_seats_r)
    max_cum_pop_seats_r = max(split_cum_pop_seats_r, rev_split_cum_pop_seats_r)
    if min_cum_pop_seats_r > 0:
        asym = max_cum_pop_seats_r / min_cum_pop_seats_r
    else:
        asym = 0

    MAX_ASYM = 1.5
    if min_cum_pop_seats_r < SEAT_LIMIT and asym > MAX_ASYM:
        first_region_id = region_ids[0]
        first_region_id_type = ent_types.get_entity_type(first_region_id)
        if PARENT_TO_CHILD_TYPE.get(first_region_id_type):
            print('split_region_tentative: FAILED (limit/asym)')
            return None

    if not (sel_low_region_ids and sel_high_region_ids):
        print('split_region_tentative: FAILED (empty)')
        return None

    new_label_to_region_ids = conf.get_label_to_region_ids()
    del new_label_to_region_ids[split_label]
    new_label_to_region_ids[
        split_label + '-' + sel_low_prefix
    ] = sel_low_region_ids
    new_label_to_region_ids[
        split_label + '-' + sel_high_prefix
    ] = sel_high_region_ids

    return Conf(
        label_to_region_ids=new_label_to_region_ids,
        total_seats=total_seats,
    )


@log_time
def mutate_split_max_region(conf):
    split_label = conf.get_max_region_label()
    return split_region(conf, split_label)


def rename_labels(conf):
    old_label_to_region_ids = conf.get_label_to_region_ids()
    new_label_to_region_ids = {}
    for label, region_ids in old_label_to_region_ids.items():
        new_label = region_utils.get_label(label, region_ids)
        new_label_to_region_ids[new_label] = region_ids
    return Conf(
        label_to_region_ids=new_label_to_region_ids,
        total_seats=conf.get_total_seats(),
    )


@log_time
def split_region(conf, split_label):

    while True:
        log.info('split_region: %s', split_label)
        split_label_region_ids = conf.get_label_to_region_ids()[split_label]
        n_region_ids = len(split_label_region_ids)

        if n_region_ids == 1:
            conf = expand_region(conf, split_label)
            continue

        conf_tentative = split_region_tentative(conf, split_label)
        if conf_tentative is None:
            conf = expand_region(conf, split_label)
            continue

        return rename_labels(conf_tentative)


@log_time
def mutate_until_only_simple_member(conf, ed_id):
    draw_current.draw(ed_id)

    MAX_ITERS = 30
    is_complete = False
    for i in range(0, MAX_ITERS):

        @log_time
        def inner(conf=conf, is_complete=is_complete):
            single_member_count = conf.get_single_member_count()
            single_member_count / conf.__total_seats__

            if single_member_count == conf.__total_seats__:
                map_name = f'{ed_id}-FINAL'
                is_complete = True
            else:
                map_name = f'{ed_id}-{i}'

            conf_file = f'/tmp/sl_new_pds.{map_name}.json'
            Conf.write(conf_file, conf)
            image_file = conf.draw_map(map_name)
            os.system(f'open -a firefox {image_file}')
            if is_complete:
                return is_complete, conf
            return is_complete, mutate_split_max_region(conf)

        is_complete, conf = inner(conf)
        if is_complete:
            break

    map_name = f'{ed_id}-FINAL'
    conf_file = f'/tmp/sl_new_pds.{map_name}.json'
    Conf.write(conf_file, conf)


if __name__ == '__main__':
    district_to_confs = Conf.get_district_to_confs(TOTAL_SEATS_SL)
    i = 6
    for ed_id, conf in list(district_to_confs.items())[i: i + 1]:
        mutate_until_only_simple_member(conf, ed_id)
