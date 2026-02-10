from mpl_toolkits.basemap import Basemap, maskoceans
import matplotlib.pyplot as plt

m = Basemap(projection='cyl', llcrnrlat=5, urcrnrlat=80, llcrnrlon=125, urcrnrlon=312.5,
            resolution='c')
# draw coastlines.
m.drawcoastlines()
# m.drawlsmask()
# draw a boundary around the map, fill the background.
# this background will end up being the ocean color, since
# the continents will be drawn on top.
# m.drawmapboundary(fill_color='aqua')
# fill continents, set lake color same as ocean color.
# m.fillcontinents(color='coral',lake_color='aqua')
plt.show()