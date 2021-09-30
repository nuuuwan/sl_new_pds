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


def get_min_max_lat(lat_lng_list):
    lats = list(map(lambda x: x[0], lat_lng_list))
    return min(lats), max(lats)
