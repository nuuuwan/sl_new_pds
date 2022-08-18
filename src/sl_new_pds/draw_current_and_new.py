import matplotlib.pyplot as plt
from gig import ents
from matplotlib.font_manager import FontProperties

from sl_new_pds import mapx
from sl_new_pds._constants import (
    FIG_DPI,
    FOOTER_TEXT,
    HEIGHT,
    HEIGHT_INCH,
    IDEAL_POP_PER_SEAT,
    WIDTH_INCH,
)
from sl_new_pds._utils import get_fore_color_for_back, log


def draw_tables(axes, g2l2d2s):

    groups = list(g2l2d2s.keys())
    len(groups)
    labels = list(list(g2l2d2s.values())[0].keys())
    n_labels = len(labels)
    labels + ['_total']

    for i_group, [group, l2d2s] in enumerate(g2l2d2s.items()):
        ax = axes[i_group]
        d2s_total = l2d2s['_total']
        demos = list(d2s_total.keys())
        len(demos)

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

                text = mapx.to_unkebab(f'{seats} ({seats_r:.1f})')
                color = mapx.get_seats_color(seats_r, seats)

                row_cell_text.append(text)
                row_cell_color.append(color)
            cell_text.append(row_cell_text)
            cell_color.append(row_cell_color)

        PADDING_P = 0.05
        1 - PADDING_P * 2

        row_labels = []
        for label in labels:
            if label == '_total':
                row_labels.append('TOTAL')
            elif label == '_total_prop':
                row_labels.append('PROP.  ')
            else:
                row_labels.append(mapx.get_short_name(label))

        table = ax.table(
            colLabels=list(map(mapx.to_unkebab, demos)),
            rowLabels=row_labels,
            cellText=cell_text,
            cellColours=cell_color,
            bbox=(0.0, 0.0, 1, 1),
        )
        table.auto_set_font_size(False)

        for (row, col), cell in table.get_celld().items():
            if row > len(labels) - 2:
                cell.set_text_props(
                    fontproperties=FontProperties(weight='bold')
                )
            font_color = get_fore_color_for_back(cell.get_facecolor())
            cell.get_text().set_color(font_color)
            if row != 0 and col != -1:
                cell.get_text().set_fontsize(18)
            else:
                cell.get_text().set_fontsize(15)

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
        f'Current ({seats} Polling Divisions)',
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
        f'Current ({seats} Polling Divisions)',
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
        f'New ({seats} Polling Divisions)',
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
    do_draw_tables=False,
):
    n_labels = len(label_to_region_ids.keys())
    ed_index = ents.multiget_entities(ed_ids)

    plt.rcParams.update(
        {
            'font.family': 'Futura',
        }
    )

    width_ratios = [1, 10, 1, 10, 1]
    ncols = 5
    if do_draw_tables:
        width_ratios.append(10)
        ncols += 1

    fig, axes = plt.subplots(
        ncols=ncols,
        figsize=(WIDTH_INCH, HEIGHT_INCH),
        dpi=FIG_DPI,
        gridspec_kw={
            'width_ratios': width_ratios,
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
    if do_draw_tables:
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
        'Current and New (Proposed) Polling Divisions',
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


def draw_current_and_new_split(
    ed_ids,
    map_name,
    label_to_region_ids,
    label_to_seats,
    label_to_pop,
    g2l2d2s,
):
    n_labels = len(label_to_region_ids.keys())
    ed_index = ents.multiget_entities(ed_ids)
    plt.tight_layout()
    # plt.rcParams.update(
    #     {
    #         'font.family': 'Futura',
    #     }
    # )

    if n_labels <= 20:
        title = '•'.join(
            list(
                map(
                    lambda e: '%s Electoral District (%s)'
                    % (e['name'], e['id']),
                    ed_index.values(),
                )
            )
        )
    else:
        title = 'Sri Lanka'

    # 1) draw current
    fig, axes = plt.subplots(
        ncols=3,
        figsize=(WIDTH_INCH, HEIGHT_INCH),
        dpi=FIG_DPI,
        gridspec_kw={
            'width_ratios': [1, 10, 1],
        },
    )
    draw_current(axes[1], axes[0], ed_ids)
    mapx.draw_legend(axes[2])

    fig.text(
        0.5,
        0.97,
        title,
        fontsize=12,
        ha='center',
    )
    fig.text(
        0.5,
        0.92,
        'Current Polling Divisions',
        zorder=1000,
        fontsize=24,
        ha='center',
    )
    fig.text(
        0.5,
        0.05,
        FOOTER_TEXT,
        fontsize=8,
        ha='center',
        zorder=1000,
    )

    for ax in axes:
        ax.set_axis_off()

    image_file_current = f'/tmp/sl_new_pds.{map_name}.current.png'
    plt.savefig(image_file_current)
    log.info(f'Saved map - current to {image_file_current}')

    # 2) draw new
    fig, axes = plt.subplots(
        ncols=3,
        figsize=(WIDTH_INCH, HEIGHT_INCH),
        dpi=FIG_DPI,
        gridspec_kw={
            'width_ratios': [1, 10, 1],
        },
    )
    draw_new(
        axes[1],
        axes[0],
        label_to_region_ids,
        label_to_seats,
        label_to_pop,
    )
    mapx.draw_legend(axes[2])

    fig.text(
        0.5,
        0.97,
        title,
        fontsize=12,
        ha='center',
    )
    fig.text(
        0.5,
        0.92,
        'New Polling Divisions',
        zorder=1000,
        fontsize=24,
        ha='center',
    )
    fig.text(
        0.5,
        0.05,
        FOOTER_TEXT,
        fontsize=8,
        ha='center',
        zorder=1000,
    )

    for ax in axes:
        ax.set_axis_off()

    image_file_new = f'/tmp/sl_new_pds.{map_name}.new.png'
    plt.savefig(image_file_new)
    log.info(f'Saved map - new to {image_file_new}')

    # 3) draw table
    n_labels = len(label_to_region_ids.values())
    n_groups = len(list(g2l2d2s.keys()))

    fig, axes = plt.subplots(
        ncols=n_groups,
        figsize=(
            n_groups * WIDTH_INCH * 0.5,
            HEIGHT_INCH * (10 + n_labels) / 20,
        ),
        dpi=FIG_DPI,
        gridspec_kw={
            'width_ratios': [1 for i in range(0, n_groups)],
        },
    )
    draw_tables(axes, g2l2d2s)

    fig.text(
        0.5,
        0.92,
        title + ' - Seats by Group (Hypothetical)',
        zorder=1000,
        fontsize=24,
        ha='center',
    )
    fig.text(
        0.5,
        0.05,
        FOOTER_TEXT,
        fontsize=8,
        ha='center',
        zorder=1000,
    )

    for ax in axes:
        ax.set_axis_off()

    image_file_new_table = f'/tmp/sl_new_pds.{map_name}.new_tables.png'
    plt.savefig(image_file_new_table)
    log.info(f'Saved map - new_tables to {image_file_new_table}')

    return [image_file_current, image_file_new, image_file_new_table]
