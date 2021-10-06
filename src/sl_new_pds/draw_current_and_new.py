import matplotlib.pyplot as plt
from gig import ents
from matplotlib.font_manager import FontProperties
from utils import dt

from sl_new_pds import mapx
from sl_new_pds._constants import IDEAL_POP_PER_SEAT
from sl_new_pds._utils import get_fore_color_for_back, log

WIDTH = 2400
HEIGHT = 9 * WIDTH / 16

FIG_DPI = 150
WIDTH_INCH = WIDTH / FIG_DPI
HEIGHT_INCH = HEIGHT / FIG_DPI


def draw_tables(ax, g2l2d2s):

    groups = list(g2l2d2s.keys())
    n_groups = len(groups)
    table_height = 1 / n_groups
    table_width = 1
    labels = list(list(g2l2d2s.values())[0].keys())
    labels + ['_total']

    for i_group, [group, l2d2s] in enumerate(g2l2d2s.items()):
        d2s_total = l2d2s['_total']
        demos = list(d2s_total.keys())

        cell_text = []
        cell_color = []
        for label in labels:
            row_cell_text = []
            row_cell_color = []
            for demo in demos:
                stats = l2d2s.get(label, {}).get(demo, {})
                seats = stats.get('seats', '')
                pop = stats.get('pop', '')
                seats_r = pop / IDEAL_POP_PER_SEAT

                text = mapx.to_unkebab(f'{seats} ({seats_r:.2f})')
                color = mapx.get_seats_color(seats_r, seats)

                row_cell_text.append(text)
                row_cell_color.append(color)
            cell_text.append(row_cell_text)
            cell_color.append(row_cell_color)

        PADDING_P = 0.05
        PADDING_P_REV = 1 - PADDING_P * 2

        x0 = table_width * PADDING_P
        y0 = (i_group + PADDING_P) * table_height
        actual_table_width = PADDING_P_REV * table_width
        actual_table_height = PADDING_P_REV * table_height

        row_labels = []
        for label in labels:
            if label == '_total':
                row_labels.append('TOTAL')
            elif label == '_total_prop':
                row_labels.append('Prop.    ')
            else:
                row_labels.append(mapx.get_short_name(label))

        table = ax.table(
            colLabels=list(map(mapx.to_unkebab, demos)),
            rowLabels=row_labels,
            cellText=cell_text,
            cellColours=cell_color,
            bbox=(
                x0,
                y0,
                actual_table_width,
                actual_table_height,
            ),
        )
        for (row, col), cell in table.get_celld().items():
            if row > len(labels) - 2:
                cell.set_text_props(
                    fontproperties=FontProperties(weight='bold')
                )
            font_color = get_fore_color_for_back(cell.get_facecolor())
            cell.get_text().set_color(font_color)

        table_title = '/'.join(
            list(
                map(
                    lambda x: mapx.to_unkebab(x),
                    demos,
                )
            )
        )
        ax.text(x0, y0 + table_height * 0.92, table_title)

        table.set_fontsize(7)

    ax.set_axis_off()


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
    g2l2d2s,
):
    ed_ent = ents.get_entity(ed_id)
    ed_name = ed_ent['name']

    fig, axes = plt.subplots(
        ncols=6,
        figsize=(WIDTH_INCH, HEIGHT_INCH),
        dpi=FIG_DPI,
        gridspec_kw={
            'width_ratios': [1, 6, 1, 6, 1, 6],
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
    draw_tables(axes[5], g2l2d2s)

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
