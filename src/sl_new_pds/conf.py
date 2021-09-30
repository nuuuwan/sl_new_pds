import json
import math

from gig import ent_types, ents
from gig.ent_types import ENTITY_TYPE
from utils import dt

from sl_new_pds import _utils

# TOTAL_SEATS = 160
TOTAL_SEATS = 19

PARENT_TO_CHILD_TYPE = {
    ENTITY_TYPE.DISTRICT: ENTITY_TYPE.DSD,
    ENTITY_TYPE.DSD: ENTITY_TYPE.GND,
}


def get_total_pop(label_to_pop):
    return sum(label_to_pop.values())


def allocate_seats_r(label_to_pop):
    total_pop = sum(label_to_pop.values())
    label_to_seats = {}
    for label, pop in label_to_pop.items():
        seats_r = TOTAL_SEATS * pop / total_pop
        label_to_seats[label] = seats_r
    return label_to_seats


def get_label(old_label, region_ids):
    if len(region_ids) > 3:
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


def allocate_seats(label_to_pop):
    total_pop = sum(label_to_pop.values())
    label_to_seats = {}
    label_to_rem = {}
    total_seats_i = 0
    for label, pop in label_to_pop.items():
        seats_r = TOTAL_SEATS * pop / total_pop
        seats_i = (int)(seats_r)
        total_seats_i += seats_i
        rem = seats_r - seats_i

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
        # district_ents = ents.get_entities(ENTITY_TYPE.DISTRICT)
        # label_to_region_ids = dict(
        #     list(
        #         map(
        #             lambda ent: (
        #                 'district-' + dt.to_kebab(ent['name']),
        #                 [ent['id']],
        #             ),
        #             district_ents,
        #         )
        #     )
        # )
        label_to_region_ids = {'district-colombo': ['LK-11']}
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

    def get_unfairness(self):
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

        unfairness = math.sqrt(sum_sq_dev_seats_per_seat_r / total_pop)
        return unfairness

    def copy(self):
        return Conf(_utils.dumb_copy(self.__label_to_region_ids__))

    def mutate_split_max_region(self):
        max_label = sorted(
            self.get_label_to_pop().items(),
            key=lambda x: -x[1],
        )[0][0]
        print(f'max_label: {max_label}')

        new_label_to_region_ids = _utils.dumb_copy(
            self.__label_to_region_ids__
        )

        # If label points to single region then expand region
        max_label_region_ids = new_label_to_region_ids[max_label]
        if len(max_label_region_ids) == 1:
            max_label_region_id = max_label_region_ids[0]
            max_label_type = ent_types.get_entity_type(max_label_region_id)
            child_type = PARENT_TO_CHILD_TYPE[max_label_type]
            max_label_region_ids = list(
                map(
                    lambda ent: ent['id'],
                    list(
                        filter(
                            lambda ent: max_label_region_id in ent['id'],
                            ents.get_entities(child_type),
                        )
                    ),
                )
            )
            new_label_to_region_ids[max_label] = max_label_region_ids

        # split label into north and south
        centroids = list(
            map(
                lambda region_id: ents.get_entity(region_id)['centroid'],
                max_label_region_ids,
            )
        )
        pops = list(
            map(
                lambda region_id: (int)(
                    ents.get_entity(region_id)['population']
                ),
                max_label_region_ids,
            )
        )
        min_lat, max_lat = _utils.get_min_max_lat(centroids)

        max_min_pop = None
        max_north_region_ids = None
        max_south_region_ids = None
        for p in [i / 10 for i in range(0, 11)]:
            north_region_ids = []
            south_region_ids = []
            north_pop = 0
            south_pop = 0
            for region_id, centroid, pop in zip(
                max_label_region_ids, centroids, pops
            ):
                if centroid[0] > (min_lat + (max_lat - min_lat) * p):
                    north_region_ids.append(region_id)
                    north_pop += pop
                else:
                    south_region_ids.append(region_id)
                    south_pop += pop
            min_pop = min(north_pop, south_pop)
            if not max_min_pop or max_min_pop < min_pop:
                max_min_pop = min_pop
                max_north_region_ids = north_region_ids
                max_south_region_ids = south_region_ids

        del new_label_to_region_ids[max_label]
        new_label_to_region_ids[max_label + '-N'] = max_north_region_ids
        new_label_to_region_ids[max_label + '-S'] = max_south_region_ids

        new_label_to_region_ids2 = {}
        for label, region_ids in new_label_to_region_ids.items():
            new_label = get_label(label, region_ids)
            new_label_to_region_ids2[new_label] = region_ids

        return Conf(new_label_to_region_ids2)

    def print_stats(self):
        _utils.print_json(self.__label_to_region_ids__)
        _utils.print_json(self.get_label_to_pop())
        _utils.print_json(self.get_label_to_seats())
        print('unfairness:\t', self.get_unfairness())


if __name__ == '__main__':
    conf = Conf.get_init()

    for i in range(0, 20):
        print('-' * 64)
        print('%d)' % (i + 1))
        print('-' * 64)
        conf1 = conf.mutate_split_max_region()
        conf1.print_stats()
        conf = conf1
