"""Example."""
import matplotlib.pyplot as plt
from geo import geodata

gpd_df = geodata.get_region_geodata('EC-01', 'pd')

gpd_df.plot(
    column='population',
    legend=True,
    cmap='coolwarm',
    figsize=(16, 9),
    edgecolor="black",
    linewidth=1,
)

for idx, row in gpd_df.iterrows():
    [x, y] = [
        row['geometry'].centroid.x,
        row['geometry'].centroid.y,
    ]
    plt.text(
        s=row['name'],
        xy=[x, y],
        horizontalalignment='center',
        fontsize=7,
    )
    population_k = row['population'] / 1_000
    plt.text(
        s=f'{population_k:.3g}K',
        xy=[x, y + 0.004],
        horizontalalignment='center',
        fontsize=9,
    )

plt.title('Colombo Electoral District - Polling Divisions')

image_file = __file__ + '.png'

fig = plt.gcf()
fig.set_size_inches(16, 9)
plt.savefig(image_file)
plt.show()
