import json
import math

from gig import ents
from gig.ent_types import ENTITY_TYPE
from utils import dt

TOTAL_SEATS = 160
IDEAL_DISTRICT_FAIRNESS = 0.01865685509976343


def get_total_pop(label_to_pop):
    return sum(label_to_pop.values())


def allocate_seats_r(label_to_pop):
    total_pop = sum(label_to_pop.values())
    label_to_seats = {}
    for label, pop in label_to_pop.items():
        seats_r = TOTAL_SEATS * pop / total_pop
        label_to_seats[label] = seats_r
    return label_to_seats


def allocate_seats(label_to_pop):
    total_pop = sum(label_to_pop.values())
    label_to_seats = {}
    label_to_rem = {}
    total_seats_i = 0
    for label, pop in label_to_pop.items():
        seats_r = TOTAL_SEATS * pop / total_pop
        seats_i = (int)(seats_r)
        total_seats_i += seats_i

        rem = seats_r - seats_r

        label_to_seats[label] = seats_i
        label_to_rem[label] = rem

    excess_seats = TOTAL_SEATS - total_seats_i
    sorted_labels_and_rem = sorted(
        label_to_rem.items(),
        key=lambda x: -x[1],
    )

    for i in range(0, excess_seats):
        label = sorted_labels_and_rem[i][0]
        label_to_seats[label] += 1

    return label_to_seats


class Conf:
    def __init__(self, label_to_region_ids):
        self.__label_to_region_ids__ = label_to_region_ids

    @staticmethod
    def get_init():
        district_ents = ents.get_entities(ENTITY_TYPE.DISTRICT)
        label_to_region_ids = dict(
            list(
                map(
                    lambda ent: (
                        dt.to_kebab(ent['name']),
                        [ent['id']],
                    ),
                    district_ents,
                )
            )
        )
        return Conf(label_to_region_ids)

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
        return allocate_seats(label_to_pop)

    def get_fairness(self):
        label_to_pop = self.get_label_to_pop()
        total_pop = get_total_pop(label_to_pop)
        label_to_seats = self.get_label_to_seats(label_to_pop)

        sum_sq_dev_seats_per_seat_r = 0
        for label in self.__label_to_region_ids__:
            pop = label_to_pop[label]
            seats = label_to_seats[label]
            seats_r = TOTAL_SEATS * pop / total_pop
            seats_per_seat_r = seats / seats_r
            sq_dev_seats_per_seat_r = (seats_per_seat_r - 1) ** 2
            sum_sq_dev_seats_per_seat_r = sq_dev_seats_per_seat_r * pop

        fairness = math.sqrt(sum_sq_dev_seats_per_seat_r / total_pop)
        return (int)(100 * IDEAL_DISTRICT_FAIRNESS / fairness)


if __name__ == '__main__':
    conf = Conf.get_init()
    print(conf.get_fairness())
