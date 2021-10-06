import json
import math
import os

from gig import ents, ext_data
from utils import dt, jsonx

from sl_new_pds import _utils, seat_utils
from sl_new_pds._constants import START_TYPE
from sl_new_pds._utils import log, log_time
from sl_new_pds.draw_current_and_new import draw_current_and_new


class Conf:
    def __init__(self, total_seats, label_to_region_ids):
        self.__total_seats__ = total_seats
        self.__label_to_region_ids__ = label_to_region_ids

    def get_total_seats(self):
        return self.__total_seats__

    def get_label_to_region_ids(self):
        return self.__label_to_region_ids__

    @staticmethod
    def read(conf_file):
        data = jsonx.read(conf_file)
        conf = Conf(
            total_seats=data['total_seats'],
            label_to_region_ids=data['label_to_region_ids'],
        )
        log.info(f'Read conf from {conf_file}')
        return conf

    @staticmethod
    def write(conf_file, conf):
        jsonx.write(
            conf_file,
            dict(
                total_seats=conf.__total_seats__,
                label_to_region_ids=conf.__label_to_region_ids__,
            ),
        )
        log.info(f'Wrote conf to {conf_file}')

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

    def get_g2l2d2s(self):
        label_to_demo = self.get_label_to_demo()
        label_to_seats = self.get_label_to_seats()

        groups_map = {
            'ethnic': ['sinhala', 'tamil_all', 'muslim_malay'],
            'religious': ['buddhist', 'hindu', 'islam', 'all_christian'],
            'sinhala_buddhist': ['sinhala_buddhist', 'non_sinhala_buddhist'],
        }
        g2l2d2s = {}
        for group, groups in groups_map.items():
            g2l2d2s[group] = {}
            total_demo_to_stats = {}
            for label, seats in label_to_seats.items():
                if label not in g2l2d2s[group]:
                    g2l2d2s[group][label] = {}

                demo = label_to_demo[label]
                demo_to_pop = dict(
                    list(
                        map(
                            lambda group: [group, demo[group]],
                            groups,
                        )
                    )
                )
                demo_to_seats = seat_utils.allocate_seats(seats, demo_to_pop)
                for demo, pop in demo_to_pop.items():
                    g2l2d2s[group][label][demo] = {
                        'pop': pop,
                        'seats': demo_to_seats.get(demo, 0),
                    }

                for demo, stats in g2l2d2s[group][label].items():
                    if demo not in total_demo_to_stats:
                        total_demo_to_stats[demo] = {
                            'pop': 0,
                            'seats': 0,
                        }
                    total_demo_to_stats[demo]['pop'] += stats['pop']
                    total_demo_to_stats[demo]['seats'] += stats['seats']

            g2l2d2s[group]['_total'] = total_demo_to_stats
            total_demo_to_pop = dict(
                list(
                    map(
                        lambda x: (x[0], x[1]['pop']),
                        total_demo_to_stats.items(),
                    )
                )
            )
            total_seats = sum(
                list(
                    map(
                        lambda x: x['seats'],
                        total_demo_to_stats.values(),
                    )
                )
            )
            total_demo_to_seats_pr = seat_utils.allocate_seats(
                total_seats, total_demo_to_pop
            )
            g2l2d2s[group]['_total_prop'] = dict(
                list(
                    map(
                        lambda x: (
                            x[0],
                            {
                                'pop': x[1],
                                'seats': total_demo_to_seats_pr[x[0]],
                            },
                        ),
                        total_demo_to_pop.items(),
                    )
                )
            )

        return g2l2d2s

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

    def get_max_region_label(self):
        """Get the label with the largest population."""
        label_to_pop = self.get_label_to_pop()
        sorted_label_and_pop = sorted(
            label_to_pop.items(), key=lambda x: -x[1]
        )
        return sorted_label_and_pop[0][0]

    def copy(self):
        return Conf(_utils.dumb_copy(self.__label_to_region_ids__))

    def draw_map(self, ed_id, map_name):
        return draw_current_and_new(
            ed_id,
            map_name,
            self.get_label_to_region_ids(),
            self.get_label_to_seats(),
            self.get_label_to_pop(),
            self.get_g2l2d2s(),
        )

    @log_time
    def log_stats(self):
        log.info('-' * 64)
        log.info('unfairness:\t%f', self.get_unfairness())
        log.info('multi-member:\t%d', self.get_multi_member_count())
        log.info('single-member:\t%d', self.get_single_member_count())
        log.info('zero-member:\t%d', self.get_zero_member_count())
        log.info(
            'target pop-per-seat:\t %4.0f', self.get_target_pop_per_seat()
        )
        log.info('-' * 64)


if __name__ == '__main__':
    ed_ents = ents.get_entities('ed')
    i = 13
    for ed_ent in ed_ents[i: i + 1]:
        ed_id = ed_ent['id']
        map_name = f'{ed_id}-FINAL'
        conf = Conf.read(f'/tmp/sl_new_pds.{map_name}.json')
        image_file = conf.draw_map(
            ed_id,
            map_name,
        )
        os.system(f'open -a firefox {image_file}')
