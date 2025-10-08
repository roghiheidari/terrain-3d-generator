"""
Check DEM geospatial information
"""
from osgeo import gdal
import numpy as np

def check_dem():
    filename = "cliped_DEMUTM_FIX.tif"
    
    ds = gdal.Open(filename)
    if ds is None:
        print(f"Cannot open {filename}")
        return
    
    # Get dimensions
    width = ds.RasterXSize
    height = ds.RasterYSize
    
    print(f"DEM: {filename}")
    print(f"="*70)
    print(f"\nDimensions:")
    print(f"  Width: {width} pixels")
    print(f"  Height: {height} pixels")
    
    # Get geotransform
    gt = ds.GetGeoTransform()
    print(f"\nGeoTransform:")
    print(f"  Origin X: {gt[0]:.2f}")
    print(f"  Pixel Width: {gt[1]:.2f}")
    print(f"  Rotation X: {gt[2]:.2f}")
    print(f"  Origin Y: {gt[3]:.2f}")
    print(f"  Rotation Y: {gt[4]:.2f}")
    print(f"  Pixel Height: {gt[5]:.2f}")
    
    # Calculate extent
    min_x = gt[0]
    max_x = gt[0] + width * gt[1]
    max_y = gt[3]
    min_y = gt[3] + height * gt[5]
    
    print(f"\nUTM Extent:")
    print(f"  Min X: {min_x:.2f}")
    print(f"  Max X: {max_x:.2f}")
    print(f"  Min Y: {min_y:.2f}")
    print(f"  Max Y: {max_y:.2f}")
    print(f"  Width: {max_x - min_x:.2f} meters")
    print(f"  Height: {max_y - min_y:.2f} meters")
    
    # Get projection
    proj = ds.GetProjection()
    print(f"\nProjection:")
    if proj:
        # Extract EPSG if present
        if 'EPSG' in proj or 'AUTHORITY' in proj:
            print(f"  {proj[:200]}...")
        else:
            print(f"  {proj[:200]}...")
    else:
        print("  No projection info")
    
    # Get elevation data
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    nodata = band.GetNoDataValue()
    
    valid = data != nodata if nodata is not None else np.ones_like(data, dtype=bool)
    
    print(f"\nElevation:")
    print(f"  Min: {np.min(data[valid]):.2f} m")
    print(f"  Max: {np.max(data[valid]):.2f} m")
    print(f"  Range: {np.max(data[valid]) - np.min(data[valid]):.2f} m")
    print(f"  NoData: {nodata}")
    
    # Pixel size
    print(f"\nPixel Resolution:")
    print(f"  X: {abs(gt[1]):.2f} meters/pixel")
    print(f"  Y: {abs(gt[5]):.2f} meters/pixel")
    
    # Check orientation
    print(f"\nOrientation:")
    if gt[5] < 0:
        print(f"  Y-axis: Top to bottom (standard)")
    else:
        print(f"  Y-axis: Bottom to top (inverted)")
    
    if gt[1] > 0:
        print(f"  X-axis: Left to right (standard)")
    else:
        print(f"  X-axis: Right to left (inverted)")

if __name__ == "__main__":
    check_dem()
