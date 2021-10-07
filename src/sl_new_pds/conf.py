import json
import math
import os

from gig import ents
from utils import dt, jsonx

from sl_new_pds import _utils, conf_helpers, seat_utils
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
        return conf_helpers.get_label_to_pop(self.__label_to_region_ids__)

    def get_total_pop(self, label_to_pop=None):
        if label_to_pop is None:
            label_to_pop = self.get_label_to_pop()
        return sum(label_to_pop.values())

    def get_label_to_seats(self, label_to_pop=None):
        if label_to_pop is None:
            label_to_pop = self.get_label_to_pop()
        return seat_utils.allocate_seats(self.__total_seats__, label_to_pop)

    def get_label_to_demo(self):
        return conf_helpers.get_label_to_demo(self.__label_to_region_ids__)

    def get_g2l2d2s(self, label_to_seats=None):
        if label_to_seats is None:
            label_to_seats = self.get_label_to_seats()
        label_to_demo = self.get_label_to_demo()

        return conf_helpers.get_g2l2d2s(label_to_seats, label_to_demo)

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

    def get_biggest_member_seats(self):
        label_to_seats = self.get_label_to_seats()
        return max(
            list(
                label_to_seats.values(),
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

    def draw_map(self, ed_ids, map_name):
        log.info('Drawing Map...')

        label_to_pop = self.get_label_to_pop()
        log.info('Computed label_to_pop')

        label_to_seats = self.get_label_to_seats(label_to_pop=label_to_pop)
        log.info('Computed label_to_seats')

        g2l2d2s = self.get_g2l2d2s(label_to_seats=label_to_seats)
        log.info('Computed g2l2d2s')

        return draw_current_and_new(
            ed_ids,
            map_name,
            self.get_label_to_region_ids(),
            label_to_seats,
            label_to_pop,
            g2l2d2s,
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
    for ed_ent in ed_ents:
        ed_id = ed_ent['id']
        map_name = f'{ed_id}-FINAL'
        conf = Conf.read(f'/tmp/sl_new_pds.{map_name}.json')
        image_file = conf.draw_map(
            [ed_id],
            map_name,
        )
        os.system(f'open -a firefox {image_file}')
