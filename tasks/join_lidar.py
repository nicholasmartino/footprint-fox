import gc
import os

from store import *

import geopandas as gpd
import laspy
import pandas as pd
from Fabric import Buildings
from ShapeTools import Analyst
from shapely.geometry import Point
from tqdm import tqdm


def join_footprint_height():
    feather_dir = '../data/feather'
    # Buildings
    building_gdf = gpd.read_file(filename='../tmp/ODB_BritishColumbia/odb_britishcolumbia.shp')
    building_gdf.crs = 3347
    building_gdf = building_gdf.to_crs(26910)
    bld = Buildings(gdf=building_gdf, to_crs=26910, group_by='Build_ID')
    building_gdf.to_feather(f'{feather_dir}/buildings_odb_british_columbia.feather')
    buildings_gdf = gpd.read_feather(f'{feather_dir}/buildings_odb_british_columbia.feather')

    # laz_bounds = gpd.GeoDataFrame()
    # for feather in tqdm(os.listdir(feather_dir)):
    #     if '_bounds' in feather:
    #         laz_bound = gpd.read_feather(f"../data/feather/{feather}").to_crs(26910)
    #         laz_bounds = pd.concat([laz_bounds, laz_bound])
    #         gc.collect()

    # Get heights from digital surface models
    output = []
    for laz_file in tqdm(os.listdir('../data/laz')):
        join_file = f'footprints_join_{laz_file}.feather'
        if (f'{laz_file}_bounds.feather' in os.listdir(feather_dir)) & (join_file not in os.listdir(feather_dir)):
            laz_bound = gpd.read_feather(f"{feather_dir}/{laz_file}_bounds.feather").to_crs(26910)
            overlay = gpd.overlay(bld.gdf, laz_bound)
            if len(overlay) > 0:
                dsm = laspy.read(f"../data/laz/{laz_file}")
                dsm_gdf = gpd.GeoDataFrame({'geometry': [Point(xy) for xy in zip(dsm.x, dsm.y)]})
                dsm_gdf['z'] = [z for z in dsm.z]
                dsm_gdf.crs = 6653
                dsm_gdf['geometry'] = dsm_gdf.buffer(1)
                dsm_gdf = dsm_gdf.to_crs(26910)
                gdf = Analyst(bld.gdf, dsm_gdf).spatial_join(operations=['min', 'mean', 'max'])
                gdf = gdf[~gdf['z_mean'].isna()]
                gdf.to_feather(f'{feather_dir}/{join_file}')
                output.append(laz_file)
                gc.collect()

    return output


if __name__ == '__main__':
    print(f"'z' data from {len(join_footprint_height())} quadrants joined to building footprints")
