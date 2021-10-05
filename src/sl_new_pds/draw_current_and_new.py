import matplotlib.pyplot as plt
from gig import ents
from utils import dt

from sl_new_pds import mapx
from sl_new_pds._utils import log

FIG_DPI = 150
WIDTH = 1600
HEIGHT = 9 * WIDTH / 16
WIDTH_INCH = WIDTH / FIG_DPI
HEIGHT_INCH = HEIGHT / FIG_DPI


def draw_current(ax_map, ax_text, ed_id):

    ed_ent = ents.get_entity(ed_id)
    ed_label = dt.to_kebab(ed_id + ' ' + ed_ent['name'])

    label_to_region_ids = {}
    label_to_pop = {}
    label_to_seats = {}

    for pd_ent in ents.get_entities('pd'):
        if pd_ent['ed_id'] != ed_id:
            continue
        label = pd_ent['name']
        pop = pd_ent['population']
        if not pop:
            continue
        region_ids = [pd_ent['id']]

        label_to_region_ids[label] = region_ids
        label_to_pop[label] = pop
        label_to_seats[label] = 1

    mapx.draw_map(
        ax_map,
        ax_text,
        'CURRENT',
        label_to_region_ids=label_to_region_ids,
        label_to_pop=label_to_pop,
        label_to_seats=label_to_seats,
    )


def draw_new(
    ax_map,
    ax_text,
    label_to_region_ids,
    label_to_seats,
    label_to_pop,
):
    mapx.draw_map(
        ax_map,
        ax_text,
        'NEW',
        label_to_region_ids,
        label_to_seats,
        label_to_pop,
    )


def draw_current_and_new(
    ed_id,
    map_name,
    label_to_region_ids,
    label_to_seats,
    label_to_pop,
):
    fig, axes = plt.subplots(ncols=3, nrows=2, figsize=(WIDTH_INCH, HEIGHT_INCH), dpi=FIG_DPI)
    axes[1, 2].set_axis_off()

    draw_current(axes[0, 0], axes[1, 0], ed_id)

    draw_new(
        axes[0, 1],
        axes[1, 1],
        label_to_region_ids,
        label_to_seats,
        label_to_pop,
    )
    mapx.draw_legend(axes[0, 2])

    image_file = f'/tmp/sl_new_pds.{map_name}.png'
    plt.savefig(image_file)
    log.info(f'Saved map to {image_file}')



    return image_file
