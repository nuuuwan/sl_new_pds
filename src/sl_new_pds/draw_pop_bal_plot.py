import os

import matplotlib.pyplot as plt
from gig import ents

from sl_new_pds import draw_new_lk, mapx
from sl_new_pds._constants import FOOTER_TEXT, IDEAL_POP_PER_SEAT
from sl_new_pds._utils import log


def current_pop_list():
    return sorted(
        list(
            filter(
                lambda pop: pop > 0,
                list(
                    map(
                        lambda e: e['population'],
                        ents.get_entities('pd'),
                    )
                ),
            )
        )
    )


def new_pop_list():
    lk_conf, _ = draw_new_lk.get_lk_conf()
    label_to_pop = lk_conf.get_label_to_pop()
    return sorted(
        label_to_pop.values(),
    )


def draw_pop_bal_plot(pop_list, plot_label):
    fig, ax = plt.subplots()

    n = len(pop_list)
    xs = [x for x in range(0, n)]
    ys = pop_list
    color = list(
        map(
            lambda pop: mapx.get_seats_color(pop / IDEAL_POP_PER_SEAT, 1),
            pop_list,
        )
    )

    ax.bar(xs, ys, color=color, edgecolor=(0.9, 0.9, 0.9))
    ax.set_ylabel('Population', fontsize=24)
    fig.set_size_inches(32, 18)
    ax.tick_params(axis='both', which='major', labelsize=18)
    plt.ylim([0, 420_000])

    fig.text(
        0.5,
        0.97,
        'Sri Lanka',
        fontsize=24,
        ha='center',
    )
    plot_label_str = plot_label.title()
    fig.text(
        0.5,
        0.92,
        f'{plot_label_str} Polling Divisions',
        zorder=1000,
        fontsize=48,
        ha='center',
    )
    fig.text(
        0.5,
        0.05,
        FOOTER_TEXT,
        fontsize=18,
        ha='center',
        zorder=1000,
    )

    image_file = f'/tmp/sl_new_pds.pop_bal_plot.{plot_label}.png'
    plt.savefig(image_file)
    log.info(f'Saved map to {image_file}')
    return image_file


if __name__ == '__main__':
    image_file = draw_pop_bal_plot(current_pop_list(), 'current')
    os.system(f'open -a firefox {image_file}')
    image_file = draw_pop_bal_plot(new_pop_list(), 'new')
    os.system(f'open -a firefox {image_file}')
