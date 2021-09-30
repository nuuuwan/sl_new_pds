"""Utils."""

import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('sl_new_pds')


def dumb_copy(x):
    return json.loads(json.dumps(x))


def print_json(x):
    print(json.dumps(x, indent=2))


def get_mean_centroid(centroids):
    return list(
        map(
            lambda i: sum(list(map(lambda x: x[i], centroids)))
            / len(centroids),
            [0, 1],
        )
    )


def get_bounds(lat_lng_list):
    lat_lng_list = list(filter(
        lambda x: str(x),
        lat_lng_list,
    ))
    lats, lngs = list(
        map(
            lambda i: list(map(lambda x: x[i], lat_lng_list)),
            [0, 1],
        )
    )
    return list(map(lambda f: [f(lats), f(lngs)], [min, max]))
