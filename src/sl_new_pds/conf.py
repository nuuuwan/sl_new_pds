import json
import math

from gig import ents, ext_data
from utils import dt

from sl_new_pds import _utils, seat_utils
from sl_new_pds._constants import START_TYPE
from sl_new_pds._utils import log_time


class Conf:
    def __init__(self, total_seats, label_to_region_ids):
        self.__total_seats__ = total_seats
        self.__label_to_region_ids__ = label_to_region_ids

    def get_total_seats(self):
        return self.__total_seats__

    def get_label_to_region_ids(self):
        return self.__label_to_region_ids__

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

    def get_total_pop(self, label_to_pop=None):
        if label_to_pop is None:
            label_to_pop = self.get_label_to_pop()
        return sum(label_to_pop.values())

    def get_label_to_seats(self, label_to_pop=None):
        if label_to_pop is None:
            label_to_pop = self.get_label_to_pop()
        return seat_utils.allocate_seats(self.__total_seats__, label_to_pop)

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

                if not religion_demo or not ethnic_demo:
                    continue

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
                l2g2d2s[group][label] = _utils.remove_nullish_values(
                    seat_utils.allocate_seats(seats, label_to_pop0)
                )
                for demo, seats in l2g2d2s[group][label].items():
                    if demo not in total_demo_to_seats:
                        total_demo_to_seats[demo] = 0
                    total_demo_to_seats[demo] += seats
            l2g2d2s[group]['_total'] = total_demo_to_seats
        return l2g2d2s

    def get_unfairness(self):
        label_to_pop = self.get_label_to_pop()
        total_pop = self.get_total_pop(label_to_pop)
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
        total_pop = self.get_total_pop(self.get_label_to_pop())
        return total_pop / self.__total_seats__

    def copy(self):
        return Conf(_utils.dumb_copy(self.__label_to_region_ids__))

    @log_time
    def print_stats(self):
        # _utils.print_json(self.__label_to_region_ids__)
        _utils.print_kv_dict(self.get_label_to_pop())
        _utils.print_kv_dict(self.get_label_to_seats())

        print('unfairness:\t%f' % self.get_unfairness())
        # print('multi-member:\t%d' % self.get_multi_member_count())
        # print('single-member:\t%d' % self.get_single_member_count())
        # print('zero-member:\t%d' % self.get_zero_member_count())
        print('target pop-per-seat:\t %4.0f' % self.get_target_pop_per_seat())

        print('-' * 64)
