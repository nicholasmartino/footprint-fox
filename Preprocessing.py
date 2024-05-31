import gc
import io
import io
import os
import zipfile

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import requests
from Fabric import Buildings, Parcels
from shapely import affinity
from store import *
from tqdm import tqdm

mpl.use("Agg")


if UPDATE_FOOTPRINTS:
    # Download BC footprints from StatCan
    zipfile.ZipFile(
        io.BytesIO(requests.get(
            'https://www150.statcan.gc.ca/n1/fr/pub/34-26-0001/2018001/ODB_v2_BritishColumbia.zip?st=qdcH3z04').content)
    ).extractall('tmp/')
    print("Footprint data downloaded")

if UPDATE_PARCELS:
    # Download parcels from BC government open data
    zipfile.ZipFile(
        io.BytesIO(requests.get(
            'https://pub.data.gov.bc.ca/datasets/4cf233c2-f020-4f7a-9b87-1923252fbc24/pmbc_parcel_fabric_poly_svw.zip').content)
    ).extractall('tmp/')
    print("Parcel data downloaded")


def load_buildings():
    # Load buildings and join height from BC Assessment
    buildings_gdf = gpd.read_file('data/BritishColumbia.geojson').to_crs(26910)
    bca = gpd.read_file('G:\My Drive\Databases\BCAssessment\Metro Vancouver_parcels.geojson')
    buildings_gdf['bid'] = buildings_gdf.reset_index(drop=True).index
    buildings_centroids = buildings_gdf.copy()
    buildings_centroids['geometry'] = buildings_centroids.centroid.buffer(1)
    join = buildings_centroids.sjoin(bca.loc[:, ['NUMBER_OF_STOREYS', 'geometry']])
    grouped = join.groupby('bid', as_index=False).max()
    buildings_gdf.loc[grouped['bid'], 'NUMBER_OF_STOREYS'] = list(grouped['NUMBER_OF_STOREYS'])
    buildings_gdf = buildings_gdf[~buildings_gdf['NUMBER_OF_STOREYS'].isna()]
    buildings_gdf['height'] = buildings_gdf['NUMBER_OF_STOREYS'] * CEILING_HEIGHT
    buildings_gdf['area'] = buildings_gdf.area
    buildings_gdf['volume'] = buildings_gdf['area'] * buildings_gdf['height']
    buildings_gdf.to_feather('data/feather/buildings.feather')
    return buildings_gdf


def calculate_fsr():
    # Parcels
    parcel_gdf = gpd.read_file(filename='tmp/pmbc_parcel_fabric_poly_svw.gdb', layer='pmbc_parcel_fabric_poly_svw')
    parcel_gdf.crs = 3005
    parcel_gdf = parcel_gdf.to_crs(26910)
    pcl = Parcels(gdf=parcel_gdf)
    buildings = Buildings(gdf=gpd.read_feather('data/feather/buildings.feather'))
    buildings_centroids = buildings.gdf.copy()
    buildings_centroids['geometry'] = buildings_centroids.centroid.buffer(1)
    parcels_buildings_join = pcl.gdf.sjoin(
        buildings_centroids.loc[:, ['id', 'volume', 'geometry']],
        rsuffix="Buildings"
    )
    sum_by_parcel = parcels_buildings_join.groupby('pid', as_index=False).sum()
    pcl.gdf.loc[sum_by_parcel['pid'], 'built_volume'] = list(sum_by_parcel['volume'])
    pcl.gdf['fsr'] = (pcl.gdf['built_volume'] / CEILING_HEIGHT) / pcl.gdf.area
    pcl.gdf = pcl.gdf.drop_duplicates(subset=['geometry'])
    pcl.gdf.to_feather('data/feather/parcels_fsr.feather')
    return pcl


def join_parcel_id():
    parcels_gdf = gpd.read_feather('data/feather/parcels_fsr.feather').drop_duplicates(subset=['geometry'])
    buildings_gdf = gpd.read_feather('data/feather/buildings.feather').drop_duplicates(subset=['geometry'])

    parcels_gdf = parcels_gdf.reset_index(drop=True)
    buildings_gdf = buildings_gdf.reset_index(drop=True)

    parcels_gdf['pid'] = parcels_gdf.index
    buildings_gdf['bid'] = buildings_gdf.index

    bld_gdf_ctr = buildings_gdf.copy()
    bld_gdf_ctr['geometry'] = bld_gdf_ctr.centroid.buffer(0.0001)
    
    # bld_gdf_join = bld_gdf_ctr.sjoin(parcels_gdf.loc[:, ['pid', 'geometry']])
    # grouped_join = bld_gdf_join.groupby('bid', as_index=False).first()

    bld_gdf_overlay = gpd.overlay(bld_gdf_ctr.loc[:, ['bid', 'geometry']], parcels_gdf.loc[:, ['pid', 'geometry']])
    bld_gdf_overlay['area'] = bld_gdf_overlay.area
    grouped_overlay = bld_gdf_overlay.sort_values('area', ascending=False).groupby('bid', as_index=False).first()
    buildings_gdf.loc[grouped_overlay['bid'], 'pid'] = list(grouped_overlay['pid'])
    
    parcels_gdf.to_feather('data/feather/parcels_pid.feather')
    buildings_gdf.to_feather('data/feather/buildings_pid.feather')
    return


def plot_parcels():
    flt_parcels = gpd.read_feather('data/feather/parcels_pid.feather')
    buildings = Buildings(gdf=gpd.read_feather('data/feather/buildings_pid.feather'))

    # Filter parcels by area and fsr
    flt_parcels = flt_parcels.loc[:, ['pid', 'area', 'built_volume', 'fsr', 'geometry']].dropna().copy()
    flt_parcels = flt_parcels[(flt_parcels.area > 300) & (flt_parcels.fsr < 30) & (flt_parcels.area < 3000)]

    # Plot parcel boundaries and building footprints
    parcel_boundary = flt_parcels.copy()
    parcel_boundary['geometry'] = [geom for geom in parcel_boundary.boundary]
    parcel_boundary = parcel_boundary.set_geometry('geometry')

    # Make convex hull around largest parcel that will be plotted along with all other parcels to standardize the scale
    largest = flt_parcels.sort_values('area', ignore_index=True, ascending=False).iloc[0]['geometry'].convex_hull
    largest_centroid = largest.centroid

    print("Plotting parcels and footprint skeletons")
    parcel_ids = flt_parcels.pid

    # Get parcels not yet plotted
    all_dir = 'data/footprints/all'
    plotted = os.listdir(all_dir)
    plotted_int = [int(i.split('.png')[0]) for i in plotted]
    not_plotted = set.difference(set(parcel_ids), set(plotted_int))

    for k, (j, t) in enumerate(zip(not_plotted, tqdm(range(len(not_plotted))))):
        j = int(j)

        # Move convex hull to parcel to standardize the plot scale
        p_centroid = flt_parcels[flt_parcels['pid'] == j].centroid
        largest_overlap = affinity.translate(
            largest,
            (p_centroid.x - largest_centroid.x).values,
            (p_centroid.y - largest_centroid.y).values
        )
        moved = gpd.GeoDataFrame({'geometry': [largest_overlap]}, geometry='geometry')

        # # Filter buildings with this parcel id
        # footprints = gpd.overlay(buildings.gdf, flt_parcels[flt_parcels['pid'] == j].loc[:, ['geometry']])

        footprints = buildings.gdf[buildings.gdf['pid'] == j].copy()

        if len(footprints) > 0:
            if len(gpd.overlay(footprints, flt_parcels[flt_parcels['pid'] == j])) > 0:
                parcel_boundary_color = 'black'
                building_footprint_color = 'gray'
    
                # Plot footprint, boundary and parcel
                fig, ax = plt.subplots(ncols=2, figsize=(8, 4))
    
                moved.plot(ax=ax[0], color='white')
                moved.plot(ax=ax[1], color='white')
    
                flt_parcels[flt_parcels['pid'] == j]\
                    .plot('fsr', ax=ax[0], cmap='viridis', vmin=0, vmax=5, k=len(flt_parcels))
                flt_parcels[flt_parcels['pid'] == j]\
                    .plot('fsr', ax=ax[1], cmap='viridis', vmin=0, vmax=5, k=len(flt_parcels))
    
                parcel_boundary[parcel_boundary['pid'] == j].plot(ax=ax[0], color=parcel_boundary_color)
                parcel_boundary[parcel_boundary['pid'] == j].plot(ax=ax[1], color=parcel_boundary_color)
    
                footprints.plot(ax=ax[0], color=building_footprint_color)
    
                ax[0].set_axis_off()
                ax[1].set_axis_off()
    
                fig.savefig(fname=f'{all_dir}/{j}.png', dpi=64)
                plt.close()

        gc.collect()
    return


if __name__ == '__main__':
    # load_buildings()
    # calculate_fsr()
    # join_parcel_id()
    plot_parcels()
