"""Example."""
import os
import matplotlib.pyplot as plt
from geo import geodata

gpd_df = geodata.get_region_geodata('EC-01', 'pd')

gpd_df.plot(
    column='population',

    scheme='UserDefined',
    classification_kwds={
        'bins': [60_000, 95_000, 150_000, 240_000],
    },
    legend=True,
    legend_kwds={
        'labels': [
            '< 60K',
            '60K - 95K',
            '95K - 150K',
            '150K - 240K',
            '240K <',
        ],
    },
    cmap='coolwarm',
    figsize=(7, 9),
    edgecolor="black",
    linewidth=1,
)

for idx, row in gpd_df.iterrows():
    xy = [
        row['geometry'].centroid.x,
        row['geometry'].centroid.y,
    ]
    plt.annotate(
        s=row['name'],
        xy=xy,
        horizontalalignment='center',
        fontsize=8,
    )

plt.title('Colombo Electoral District - Polling Divisions')

image_file = __file__ + '.png'

fig = plt.gcf()
fig.set_size_inches(16, 9)
plt.savefig(image_file)
plt.show()
