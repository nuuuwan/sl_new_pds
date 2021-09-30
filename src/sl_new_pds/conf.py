import json
import math
import time

from gig import ent_types, ents, ext_data
from gig.ent_types import ENTITY_TYPE
from utils import dt, jsonx

from sl_new_pds import _utils

# PARENT_TO_CHILD_TYPE = {
#     ENTITY_TYPE.DISTRICT: ENTITY_TYPE.DSD,
#     ENTITY_TYPE.DSD: ENTITY_TYPE.GND,
# }

PARENT_TO_CHILD_TYPE = {
    ENTITY_TYPE.ED: ENTITY_TYPE.PD,
    ENTITY_TYPE.PD: ENTITY_TYPE.GND,
}


START_TYPE = list(PARENT_TO_CHILD_TYPE.keys())[0]


def remove_zeros(_dict):
    return dict(
        list(
            filter(
                lambda x: x[1] > 0,
                _dict.items(),
            )
        )
    )


def sort_and_print_dict(_dict):
    for k, v in sorted(_dict.items(), key=lambda x: -x[1]):
        if v > 1_000_000:
            v_m = v / 1_000_000.0
            print(f'{v_m:,.3g}M\t{k}')
        elif v > 1_000:
            v_k = v / 1_000.0
            print(f'{v_k:,.3g}K\t{k}')
        else:
            print(f'{v}\t{k}')

    print('-' * 32)


def get_total_pop(label_to_pop):
    return sum(label_to_pop.values())


def get_label(old_label, region_ids):
    if len(region_ids) > 4:
        return old_label

    region_ents = list(
        map(
            lambda region_id: ents.get_entity(region_id),
            region_ids,
        )
    )
    label_entity_type = ent_types.get_entity_type(region_ents[0]['id'])
    return dt.to_kebab(
        label_entity_type
        + ' - '
        + ' and '.join(
            list(
                map(
                    lambda ent: ent['name'],
                    region_ents,
                )
            )
        )
    )


def allocate_seats(total_seats, label_to_pop):
    total_pop = sum(label_to_pop.values())
    label_to_seats = {}
    label_to_rem = {}
    total_seats_i = 0
    for label, pop in label_to_pop.items():
        seats_r = total_seats * pop / total_pop
        seats_i = (int)(seats_r)
        total_seats_i += seats_i
        rem = seats_r - seats_i

        label_to_seats[label] = seats_i
        label_to_rem[label] = rem

    excess_seats = total_seats - total_seats_i
    sorted_labels_and_rem = sorted(
        label_to_rem.items(),
        key=lambda x: -x[1],
    )

    for i in range(0, excess_seats):
        label = sorted_labels_and_rem[i][0]
        label_to_seats[label] += 1

    return label_to_seats


class Conf:
    def __init__(self, total_seats, label_to_region_ids):
        self.__total_seats__ = total_seats
        self.__label_to_region_ids__ = label_to_region_ids

    @staticmethod
    def get_district_to_confs(total_seats):
        district_ents = ents.get_entities(START_TYPE)
        label_to_region_ids = dict(
            list(
                map(
                    lambda ent: (
                        START_TYPE + '-' + dt.to_kebab(ent['name']),
                        [ent['id']],
                    ),
                    district_ents,
                )
            )
        )
        conf = Conf(total_seats, label_to_region_ids)
        label_to_seats = conf.get_label_to_seats()

        district_to_confs = {}
        for label, seats in label_to_seats.items():
            region_ids = label_to_region_ids[label]
            district_id = region_ids[0]
            district_to_confs[district_id] = Conf(
                seats,
                {label: region_ids},
            )

        return district_to_confs

    def __str__(self):
        return json.dumps(self.__label_to_region_ids__)

    def get_label_to_pop(self):
        label_to_pop = {}
        for label, region_ids in self.__label_to_region_ids__.items():
            label_pop = 0
            for region_id in region_ids:
                region_ent = ents.get_entity(region_id)
                pop = (int)(region_ent['population'])
                label_pop += pop
            label_to_pop[label] = label_pop
        return label_to_pop

    def get_label_to_seats(self, label_to_pop=None):
        if label_to_pop is None:
            label_to_pop = self.get_label_to_pop()
        return allocate_seats(self.__total_seats__, label_to_pop)

    def get_label_to_demo(self):
        label_to_demo = {}
        for label, region_ids in self.__label_to_region_ids__.items():
            ethnic_index = ext_data.get_table_data(
                'census', 'ethnicity_of_population', region_ids
            )
            religious_index = ext_data.get_table_data(
                'census', 'religious_affiliation_of_population', region_ids
            )
            demo = {
                '_total': 0,
                # ethnic
                'sinhala': 0,
                'tamil_all': 0,
                'muslim_malay': 0,
                # religion
                'buddhist': 0,
                'hindu': 0,
                'islam': 0,
                'roman_catholic': 0,
                'other_christian': 0,
                'all_christian': 0,
                # sinhala_buddhist
                'sinhala_buddhist': 0,
                'non_sinhala_buddhist': 0,
            }
            for region_id in region_ids:
                religion_demo = religious_index[region_id]
                ethnic_demo = ethnic_index[region_id]

                demo['_total'] += ethnic_demo['total_population']

                demo['sinhala'] += ethnic_demo['sinhalese']
                demo['tamil_all'] += (
                    ethnic_demo['sri_lankan_tamil']
                    + ethnic_demo['indian_tamil']
                )
                demo['muslim_malay'] += (
                    ethnic_demo['moor'] + ethnic_demo['malay']
                )

                demo['buddhist'] += religion_demo['buddhist']
                demo['hindu'] += religion_demo['hindu']
                demo['islam'] += religion_demo['islam']
                demo['roman_catholic'] += religion_demo['roman_catholic']
                demo['other_christian'] += religion_demo['other_christian']

                demo['all_christian'] = (
                    demo['roman_catholic'] + religion_demo['other_christian']
                )

                demo['sinhala_buddhist'] = demo['buddhist']
                demo['non_sinhala_buddhist'] = (
                    demo['_total'] - demo['buddhist']
                )

            label_to_demo[label] = demo
        return label_to_demo

    def get_l2g2d2s(self):
        label_to_demo = self.get_label_to_demo()
        label_to_seats = self.get_label_to_seats()

        groups_map = {
            'ethnic': ['sinhala', 'tamil_all', 'muslim_malay'],
            'religious': ['buddhist', 'hindu', 'islam', 'all_christian'],
            'sinhala_buddhist': ['sinhala_buddhist', 'non_sinhala_buddhist'],
        }
        l2g2d2s = {}
        for group, groups in groups_map.items():
            l2g2d2s[group] = {}
            total_demo_to_seats = {}
            for label, seats in label_to_seats.items():
                demo = label_to_demo[label]
                label_to_pop0 = dict(
                    list(
                        map(
                            lambda group: [group, demo[group]],
                            groups,
                        )
                    )
                )
                l2g2d2s[group][label] = remove_zeros(
                    allocate_seats(seats, label_to_pop0)
                )
                for demo, seats in l2g2d2s[group][label].items():
                    if demo not in total_demo_to_seats:
                        total_demo_to_seats[demo] = 0
                    total_demo_to_seats[demo] += seats
            l2g2d2s[group]['_total'] = total_demo_to_seats
        return l2g2d2s

    def get_unfairness(self):
        label_to_pop = self.get_label_to_pop()
        total_pop = get_total_pop(label_to_pop)
        label_to_seats = self.get_label_to_seats(label_to_pop)

        sum_sq_dev_seats_per_seat_r = 0
        for label in self.__label_to_region_ids__:
            pop = label_to_pop[label]
            seats = label_to_seats[label]
            seats_r = self.__total_seats__ * pop / total_pop
            seats_per_seat_r = seats / seats_r
            sq_dev_seats_per_seat_r = (seats_per_seat_r - 1) ** 2
            sum_sq_dev_seats_per_seat_r = sq_dev_seats_per_seat_r * pop

        unfairness = math.sqrt(sum_sq_dev_seats_per_seat_r / total_pop)
        return unfairness

    def get_multi_member_count(self):
        label_to_seats = self.get_label_to_seats()
        return len(
            list(
                filter(
                    lambda seats: seats > 1,
                    label_to_seats.values(),
                )
            )
        )

    def get_single_member_count(self):
        label_to_seats = self.get_label_to_seats()
        return len(
            list(
                filter(
                    lambda seats: seats == 1,
                    label_to_seats.values(),
                )
            )
        )

    def get_zero_member_count(self):
        label_to_seats = self.get_label_to_seats()
        return len(
            list(
                filter(
                    lambda seats: seats == 0,
                    label_to_seats.values(),
                )
            )
        )

    def get_target_pop_per_seat(self):
        total_pop = get_total_pop(self.get_label_to_pop())
        return total_pop / self.__total_seats__

    def copy(self):
        return Conf(_utils.dumb_copy(self.__label_to_region_ids__))

    def mutate_split_max_region(self):
        print('mutate_split_max_region...')
        label_to_pop = self.get_label_to_pop()
        total_pop = sum(label_to_pop.values())
        max_label = sorted(label_to_pop.items(), key=lambda x: -x[1],)[
            0
        ][0]
        max_label_pop = label_to_pop[max_label]
        max_label_seats_r = self.__total_seats__ * max_label_pop / total_pop
        if max_label_seats_r >= 3:
            target_cand_pop = (
                (int)(max_label_seats_r / 2 + 0.5)
                * max_label_pop
                / max_label_seats_r
            )
        else:
            target_cand_pop = max_label_pop / 2

        print(
            f'max_label: {max_label}, {max_label_seats_r}, {target_cand_pop}'
        )

        new_label_to_region_ids = _utils.dumb_copy(
            self.__label_to_region_ids__
        )

        # If label points to single region then expand region
        max_label_region_ids = self.__label_to_region_ids__[max_label]
        do_expand = False

        if len(max_label_region_ids) == 1:
            do_expand = True

        elif len(max_label_region_ids) == 2:
            pops = list(
                map(
                    lambda region_id: (int)(
                        ents.get_entity(region_id)['population']
                    ),
                    max_label_region_ids,
                )
            )
            cand_pop = min(pops)
            min_seats_r = self.__total_seats__ * cand_pop / total_pop
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
                                lambda ent: max_label_region_id == ent[parent_id_key] and ent['centroid'],
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
                lambda region_id: (int)(
                    ents.get_entity(region_id)['population']
                ),
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
            for p in [i / 10 for i in range(0, 10 + 1)]:
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

        del new_label_to_region_ids[max_label]
        new_label_to_region_ids[
            max_label + '-' + max_north_label
        ] = max_north_region_ids
        new_label_to_region_ids[
            max_label + '-' + max_south_label
        ] = max_south_region_ids

        new_label_to_region_ids2 = {}
        for label, region_ids in new_label_to_region_ids.items():
            new_label = get_label(label, region_ids)
            new_label_to_region_ids2[new_label] = region_ids

        return Conf(self.__total_seats__, new_label_to_region_ids2)

    def print_stats(self):
        # _utils.print_json(self.__label_to_region_ids__)
        sort_and_print_dict(self.get_label_to_pop())
        sort_and_print_dict(self.get_label_to_seats())

        print('unfairness:\t%f' % self.get_unfairness())
        # print('multi-member:\t%d' % self.get_multi_member_count())
        # print('single-member:\t%d' % self.get_single_member_count())
        # print('zero-member:\t%d' % self.get_zero_member_count())
        print('target pop-per-seat:\t %4.0f' % self.get_target_pop_per_seat())

        print('-' * 64)


if __name__ == '__main__':
    TOTAL_SEATS = 160
    district_to_confs = Conf.get_district_to_confs(TOTAL_SEATS)

    for district_id, conf in list(district_to_confs.items())[2:3]:
        _utils.print_json(conf.get_label_to_demo())
        for i in range(0, 100):
            print('-' * 64)
            print('%d)' % (i + 1))
            print('-' * 64)

            conf.print_stats()
            _utils.print_json(conf.get_l2g2d2s())
            conf_file = f'/tmp/sl_new_pds.{district_id}.json'
            jsonx.write(conf_file, conf.__label_to_region_ids__)

            if conf.get_single_member_count() == conf.__total_seats__:
                break

            t = time.time()
            conf = conf.mutate_split_max_region()
            print('t = %dms' % ((time.time() - t) * 1_000))
        _utils.print_json(conf.get_label_to_demo())
