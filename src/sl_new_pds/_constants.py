"""Constants."""

from gig.ent_types import ENTITY_TYPE

CACHE_NAME = 'sl_new_pds'
CACHE_TIMEOUT = 3600

# PARENT_TO_CHILD_TYPE = {
#     ENTITY_TYPE.DISTRICT: ENTITY_TYPE.DSD,
#     ENTITY_TYPE.DSD: ENTITY_TYPE.GND,
# }

PARENT_TO_CHILD_TYPE = {
    ENTITY_TYPE.ED: ENTITY_TYPE.PD,
    ENTITY_TYPE.PD: ENTITY_TYPE.GND,
}

# PARENT_TO_CHILD_TYPE = {
#     ENTITY_TYPE.ED: ENTITY_TYPE.GND,
# }


START_TYPE = list(PARENT_TO_CHILD_TYPE.keys())[0]


TOTAL_SEATS_SL = 160
TOTAL_POP_SL = 20_359_439
IDEAL_POP_PER_SEAT = TOTAL_POP_SL / TOTAL_SEATS_SL


WIDTH = 2400
HEIGHT = 9 * WIDTH / 16
FIG_DPI = 150
WIDTH_INCH = WIDTH / FIG_DPI
HEIGHT_INCH = HEIGHT / FIG_DPI

FOOTER_TEXT = (
    'Data from elections.gov.lk • Visualizations & Analysis by @nuuuwan'
)


DIR_REACT = '/Users/nuwan.senaratna/Not.Dropbox/_CODING/js_react/lk_regions/public/data/custom_maps'
