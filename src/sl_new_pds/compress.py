from gig import ents
from sl_new_pds._constants import DIR_REACT
from sl_new_pds._utils import log
from sl_new_pds.conf import Conf

LEN_GND_ID = 10
LEN_DSD_ID = 7


def get_dsd_to_n_gnd_total():
    gnds = ents.get_entities('gnd')
    dsd_to_n_gnds = {}
    for gnd in gnds:
        gnd_id = gnd['id']
        dsd_id = gnd_id[:LEN_DSD_ID]
        if dsd_id not in dsd_to_n_gnds:
            dsd_to_n_gnds[dsd_id] = 0
        dsd_to_n_gnds[dsd_id] += 1
    return dsd_to_n_gnds


def compress_item(label, region_ids, dsd_to_n_gnd_total):
    n_regions_before = len(region_ids)

    gnd_ids = list(
        filter(
            lambda region_id: len(region_id) == LEN_GND_ID,
            region_ids,
        )
    )
    dsd_to_n_gnds = {}
    for gnd_id in gnd_ids:
        dsd_id = gnd_id[:LEN_DSD_ID]
        if dsd_id not in dsd_to_n_gnds:
            dsd_to_n_gnds[dsd_id] = 0
        dsd_to_n_gnds[dsd_id] += 1

    complete_dsd_ids = []
    for dsd_id, n_gnds in dsd_to_n_gnds.items():
        n_gnds_total = dsd_to_n_gnd_total[dsd_id]

        complete_str = ''
        if n_gnds == n_gnds_total:
            complete_dsd_ids.append(dsd_id)
            complete_str = '✓'

        log.info(f'({n_gnds}/{n_gnds_total})\t{dsd_id}\t{complete_str}')

    new_region_ids = complete_dsd_ids + list(
        filter(
            lambda region_id: region_id[:LEN_DSD_ID] not in complete_dsd_ids,
            region_ids,
        )
    )
    n_regions_after = len(new_region_ids)
    log.info(
        f'Compressed {label} from {n_regions_before} to {n_regions_after}'
    )
    return new_region_ids


def compress(conf):
    label_to_region_ids = conf.get_label_to_region_ids()
    dsd_to_n_gnd_total = get_dsd_to_n_gnd_total()
    new_label_to_region_ids = {}
    for label, region_ids in label_to_region_ids.items():
        new_label_to_region_ids[label] = compress_item(
            label, region_ids, dsd_to_n_gnd_total
        )
    return Conf(
        total_seats=conf.get_total_seats(),
        label_to_region_ids=new_label_to_region_ids,
    )


def compress_file(conf_file):
    lk_conf = Conf.read(conf_file)
    compressed_conf = compress(lk_conf)
    compressed_conf_file = conf_file[:-5] + '.compressed.json'
    Conf.write(compressed_conf_file, compressed_conf)
    log.info(f'Compressed {conf_file} to {compressed_conf_file}')
    return compressed_conf_file


if __name__ == '__main__':
    conf_file = f'{DIR_REACT}/sl_new_pds.lk-FINAL.json'
    compress_file(conf_file)
