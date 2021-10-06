import os

import matplotlib.pyplot as plt
from gig import ents

from sl_new_pds import draw_current_and_new, mapx
from sl_new_pds._constants import FIG_DPI, FOOTER_TEXT, HEIGHT_INCH, WIDTH_INCH
from sl_new_pds._utils import log


def draw_current_lk():
    fig, axes = plt.subplots(
        ncols=2,
        figsize=(WIDTH_INCH / 2, HEIGHT_INCH),
        dpi=FIG_DPI,
        gridspec_kw={
            'width_ratios': [4, 1],
        },
    )

    ed_ids = list(
        map(
            lambda e: e['id'],
            ents.get_entities('ed'),
        )
    )

    draw_current_and_new.draw_current(axes[0], None, ed_ids)
    mapx.draw_legend(axes[1])
    fig.text(
        0.5,
        0.97,
        'Sri Lanka',
        fontsize=12,
        ha='center',
    )
    fig.text(
        0.5,
        0.92,
        'Current (160 Electorates)',
        fontsize=24,
        ha='center',
    )
    fig.text(
        0.5,
        0.88,
        'By Surplus/Deficit Seats per Electorate*',
        fontsize=12,
        ha='center',
    )
    fig.text(
        0.5,
        0.07,
        '* Assuming 160 seats in total',
        fontsize=12,
        ha='center',
    )
    fig.text(
        0.5,
        0.03,
        FOOTER_TEXT,
        fontsize=12,
        ha='center',
    )

    image_file = '/tmp/sl_new_pds.current_lk.png'
    plt.savefig(image_file)
    log.info(f'Saved map to {image_file}')
    return image_file


if __name__ == '__main__':
    image_file = draw_current_lk()
    os.system(f'open -a firefox {image_file}')
