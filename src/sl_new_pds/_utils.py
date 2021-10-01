"""Utils."""

import json
import logging
import time

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
    lat_lng_list = list(
        filter(
            lambda x: str(x),
            lat_lng_list,
        )
    )
    lats, lngs = list(
        map(
            lambda i: list(map(lambda x: x[i], lat_lng_list)),
            [0, 1],
        )
    )
    return list(map(lambda f: [f(lats), f(lngs)], [min, max]))


def remove_nullish_values(_dict):
    return dict(
        list(
            filter(
                lambda x: x[1] > 0,
                _dict.items(),
            )
        )
    )


def print_kv_dict(_dict, n_tabs=0):
    total = _dict.get('_total', None)

    for k, v in sorted(_dict.items(), key=lambda x: -x[1]):
        v_str = ''
        if v > 1_000_000:
            v_m = v / 1_000_000.0
            v_str = f'{v_m:,.3g}M'
        elif v > 1_000:
            v_k = v / 1_000.0
            v_str = f'{v_k:,.3g}K'
        else:
            v_str = f'{v:,.3g}'

        p_str = ''
        if total is not None:
            p = v / total
            p_str = f'{p:.1%}\t'

        tab_str = '  ' * n_tabs
        print(f'{tab_str}{p_str}{v_str}\t{k}')

    print('-' * 32)


def print_obj(x, n_tabs=0):
    if isinstance(x, dict):
        first_value = list(x.values())[0]
        if type(first_value) in [int, float]:
            return print_kv_dict(x, n_tabs)
        else:
            for k, x1 in x.items():
                tab_str = '  ' * n_tabs
                print(f'{tab_str}{k}')
                print_obj(x1, n_tabs + 1)
    else:
        return json.dumps(x)


def log_time(method):
    def timed(*args, **kw):
        t_start = time.time()
        result = method(*args, **kw)
        t_end = time.time()
        dt = (t_end - t_start) * 1000
        log.info(method.__name__ + ':\t' + str(dt) + 'ms')
        return result

    return timed
