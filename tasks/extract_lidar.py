import gc
import os

import geopandas as gpd
import laspy
from shapely.geometry import box
from tqdm import tqdm


def generate_lidar_boundaries():
    output = []
    for laz_file in tqdm(os.listdir('../data/laz')):
        if f'{laz_file}_bounds.feather' not in os.listdir(f'../data/feather'):
            dsm = laspy.read(f"../data/laz/{laz_file}")
            dsm_gdf = gpd.GeoDataFrame({'geometry': [box(min(dsm.x), min(dsm.y), max(dsm.x), max(dsm.y))]})
            dsm_gdf['file'] = laz_file
            dsm_gdf.crs = 6653
            dsm_gdf.to_feather(f'../data/feather/{laz_file}_bounds.feather')
            output.append(laz_file)
            gc.collect()
    return output


if __name__ == '__main__':
    print(f"{len(generate_lidar_boundaries())} boundaries extracted from data/laz")
