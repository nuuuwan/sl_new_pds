import matplotlib.pyplot as plt
from gig import ents
from utils import dt

from sl_new_pds import mapx
from sl_new_pds._utils import log

WIDTH = 2400
HEIGHT = 9 * WIDTH / 16

FIG_DPI = 150
WIDTH_INCH = WIDTH / FIG_DPI
HEIGHT_INCH = HEIGHT / FIG_DPI


def draw_current(ax_map, ax_text, ed_id):

    ed_ent = ents.get_entity(ed_id)
    dt.to_kebab(ed_id + ' ' + ed_ent['name'])

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
        'Current',
        label_to_region_ids=label_to_region_ids,
        label_to_pop=label_to_pop,
        label_to_seats=label_to_seats,
        HEIGHT=HEIGHT,
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
        'New (Proposed)',
        label_to_region_ids,
        label_to_seats,
        label_to_pop,
        HEIGHT=HEIGHT,
    )


def draw_current_and_new(
    ed_id,
    map_name,
    label_to_region_ids,
    label_to_seats,
    label_to_pop,
):
    ed_ent = ents.get_entity(ed_id)
    ed_name = ed_ent['name']

    fig, axes = plt.subplots(
        ncols=5,
        figsize=(WIDTH_INCH, HEIGHT_INCH),
        dpi=FIG_DPI,
        gridspec_kw={
            'width_ratios': [1, 6, 1, 6, 1],
        },
    )
    plt.tight_layout()

    draw_current(axes[1], axes[0], ed_id)

    draw_new(
        axes[3],
        axes[2],
        label_to_region_ids,
        label_to_seats,
        label_to_pop,
    )
    mapx.draw_legend(axes[4])
    axes[2].text(
        0,
        0.97,
        f'{ed_name} Electoral District ({ed_id})',
        fontsize=12,
        ha='center',
    )
    axes[2].text(
        0,
        0.92,
        'Current and New (Proposed) Electorates',
        fontsize=24,
        ha='center',
    )
    axes[2].text(
        0,
        0.05,
        'Data from elections.gov.lk • Visualizations & Analysis by @nuuuwan',
        fontsize=8,
        ha='center',
    )

    image_file = f'/tmp/sl_new_pds.{map_name}.png'
    plt.savefig(image_file)
    log.info(f'Saved map to {image_file}')

    return image_file
