import matplotlib.pyplot as plt
from gig import ents
from matplotlib.font_manager import FontProperties

from sl_new_pds import mapx
from sl_new_pds._constants import (FIG_DPI, FOOTER_TEXT, HEIGHT, HEIGHT_INCH,
                                   IDEAL_POP_PER_SEAT, WIDTH_INCH)
from sl_new_pds._utils import get_fore_color_for_back, log


def draw_tables(ax, g2l2d2s):

    groups = list(g2l2d2s.keys())
    n_groups = len(groups)
    table_height = 1 / n_groups
    table_width = 1
    labels = list(list(g2l2d2s.values())[0].keys())
    n_labels = len(labels)
    labels + ['_total']

    for i_group, [group, l2d2s] in enumerate(g2l2d2s.items()):
        d2s_total = l2d2s['_total']
        demos = list(d2s_total.keys())

        cell_text = []
        cell_color = []
        for label in labels:
            if n_labels > 20 and 'total' not in label:
                continue
            row_cell_text = []
            row_cell_color = []
            for demo in demos:
                stats = l2d2s.get(label, {}).get(demo, {})
                seats = stats.get('seats', '')
                pop = stats.get('pop', '')
                seats_r = pop / IDEAL_POP_PER_SEAT

                text = mapx.to_unkebab(f'{seats} ({seats_r:.2f})')
                if seats <= 1:
                    color = mapx.get_seats_color(seats_r, seats)
                else:
                    color = mapx.get_seats_color(seats_r / seats, 1)

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
                row_labels.append('Prop.' + ' ' * 6)
            elif n_labels <= 20:
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


def draw_current(ax_map, ax_text, ed_ids):

    label_to_region_ids = {}
    label_to_pop = {}
    label_to_seats = {}

    for pd_ent in ents.get_entities('pd'):
        if pd_ent['ed_id'] not in ed_ids:
            continue
        label = pd_ent['name']
        pop = pd_ent['population']
        if not pop:
            continue
        region_ids = [pd_ent['id']]

        label_to_region_ids[label] = region_ids
        label_to_pop[label] = pop
        label_to_seats[label] = 1

    seats = len(label_to_region_ids.keys())
    mapx.draw_map(
        ax_map,
        ax_text,
        f'Current ({seats} electorates)',
        label_to_region_ids=label_to_region_ids,
        label_to_pop=label_to_pop,
        label_to_seats=label_to_seats,
        HEIGHT=HEIGHT,
    )


def draw_current_by_ed(ax_map, ax_text):

    label_to_region_ids = {}
    label_to_pop = {}
    label_to_seats = {}

    pd_ents = ents.get_entities('pd')
    ed_to_pds = {}
    for pd_ent in pd_ents:
        ed_id = pd_ent['ed_id']
        if ed_id not in ed_to_pds:
            ed_to_pds[ed_id] = []
        pd_id = pd_ent['id']
        ed_to_pds[ed_id].append(pd_id)

    for ed_ent in ents.get_entities('ed'):
        label = ed_ent['name']
        ed_id = ed_ent['id']
        pop = ed_ent['population']

        pd_ids = ed_to_pds[ed_id]
        label_to_region_ids[label] = [ed_id]
        label_to_pop[label] = pop / len(pd_ids)
        label_to_seats[label] = 1

    seats = len(label_to_region_ids.keys())
    mapx.draw_map(
        ax_map,
        ax_text,
        f'Current ({seats} electorates)',
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
    seats = len(label_to_pop.keys())
    mapx.draw_map(
        ax_map,
        ax_text,
        f'New ({seats} electorates)',
        label_to_region_ids,
        label_to_seats,
        label_to_pop,
        HEIGHT=HEIGHT,
    )


def draw_current_and_new(
    ed_ids,
    map_name,
    label_to_region_ids,
    label_to_seats,
    label_to_pop,
    g2l2d2s,
):
    n_labels = len(label_to_region_ids.keys())
    ed_index = ents.multiget_entities(ed_ids)

    plt.rcParams.update(
        {
            'font.family': 'Futura',
        }
    )

    fig, axes = plt.subplots(
        ncols=6,
        figsize=(WIDTH_INCH, HEIGHT_INCH),
        dpi=FIG_DPI,
        gridspec_kw={
            'width_ratios': [1, 6, 1, 6, 1, 6],
        },
    )
    plt.tight_layout()

    draw_current(axes[1], axes[0], ed_ids)

    draw_new(
        axes[3],
        axes[2],
        label_to_region_ids,
        label_to_seats,
        label_to_pop,
    )
    mapx.draw_legend(axes[4])
    draw_tables(axes[5], g2l2d2s)

    if n_labels <= 20:
        title = '•'.join(
            list(
                map(
                    lambda e: e['name'],
                    ed_index.values(),
                )
            )
        )
    else:
        title = 'Sri Lanka'

    axes[2].text(
        0,
        0.97,
        title,
        fontsize=12,
        ha='center',
    )
    axes[2].text(
        0,
        0.92,
        'Current and New (Proposed) Electorates',
        zorder=1000,
        fontsize=24,
        ha='center',
    )
    axes[2].text(
        0,
        0.05,
        FOOTER_TEXT,
        fontsize=8,
        ha='center',
        zorder=1000,
    )

    for ax in axes:
        ax.set_axis_off()

    image_file = f'/tmp/sl_new_pds.{map_name}.png'
    plt.savefig(image_file)
    log.info(f'Saved map to {image_file}')

    return image_file
