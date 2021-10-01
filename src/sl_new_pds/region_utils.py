from gig import ent_types, ents
from utils import dt


def get_label(old_label, region_ids):
    if len(region_ids) > 5:
        return old_label

    region_ents = list(
        map(
            lambda region_id: ents.get_entity(region_id),
            region_ids,
        )
    )
    label_entity_type = ent_types.get_entity_type(region_ents[0]['id'])
    return dt.to_kebab(
        label_entity_type
        + ' - '
        + ' '.join(
            list(
                map(
                    lambda ent: ent['name'],
                    region_ents,
                )
            )
        )
    )
