from gig import ents, ext_data
from utils import timex
from utils.cache import cache

from sl_new_pds import seat_utils
from sl_new_pds._constants import CACHE_NAME


@cache(CACHE_NAME, timex.SECONDS_IN.YEAR)
def get_label_to_pop(label_to_region_ids):
    label_to_pop = {}
    for label, region_ids in label_to_region_ids.items():
        label_pop = 0
        for region_id in region_ids:
            region_ent = ents.get_entity(region_id)
            pop = (int)(region_ent['population'])
            label_pop += pop
        label_to_pop[label] = label_pop
    return label_to_pop


@cache(CACHE_NAME, timex.SECONDS_IN.YEAR)
def get_g2l2d2s(label_to_seats, label_to_demo):
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


@cache(CACHE_NAME, timex.SECONDS_IN.YEAR)
def get_label_to_demo(
    label_to_region_ids,
):
    label_to_demo = {}
    for label, region_ids in label_to_region_ids.items():
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
                ethnic_demo['sri_lankan_tamil'] + ethnic_demo['indian_tamil']
            )
            demo['muslim_malay'] += ethnic_demo['moor'] + ethnic_demo['malay']

            demo['buddhist'] += religion_demo['buddhist']
            demo['hindu'] += religion_demo['hindu']
            demo['islam'] += religion_demo['islam']
            demo['roman_catholic'] += religion_demo['roman_catholic']
            demo['other_christian'] += religion_demo['other_christian']

            demo['all_christian'] = (
                demo['roman_catholic'] + religion_demo['other_christian']
            )

            demo['sinhala_buddhist'] = demo['buddhist']
            demo['non_sinhala_buddhist'] = demo['_total'] - demo['buddhist']

        label_to_demo[label] = demo
    return label_to_demo
