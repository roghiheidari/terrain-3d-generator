"""
Create 3D terrain with REAL UTM coordinates and correct orientation
Preserves actual distances and geographic orientation
"""

import numpy as np
from osgeo import gdal
from scipy.ndimage import zoom
import struct

# Color gradient: Red (dark/low) to Green (bright/high)
# This will be applied based on grayscale values [0, 255]

def read_tif_with_geo(filename):
    """Read GeoTIFF with geospatial information"""
    ds = gdal.Open(filename)
    if ds is None:
        raise ValueError(f"Cannot open {filename}")
    
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    nodata = band.GetNoDataValue()
    
    # Get geotransform
    gt = ds.GetGeoTransform()
    
    width = ds.RasterXSize
    height = ds.RasterYSize
    
    print(f"\n{filename}:")
    print(f"  Size: {width} x {height} pixels")
    print(f"  Origin: ({gt[0]:.2f}, {gt[3]:.2f})")
    print(f"  Pixel size: ({gt[1]:.2f}, {gt[5]:.2f}) m")
    print(f"  Data range: {np.min(data):.2f} to {np.max(data):.2f}")
    print(f"  NoData: {nodata}")
    
    # Create valid mask
    if nodata is not None:
        valid = data != nodata
        print(f"  Valid: {np.sum(valid):,} pixels")
    else:
        valid = np.ones_like(data, dtype=bool)
    
    return data, valid, gt, ds

def get_utm_coordinates(gt, width, height):
    """Calculate UTM coordinates for each pixel"""
    # gt = [origin_x, pixel_width, rotation_x, origin_y, rotation_y, pixel_height]
    
    # Create coordinate arrays
    x_coords = gt[0] + np.arange(width) * gt[1]
    y_coords = gt[3] + np.arange(height) * gt[5]
    
    # Calculate extent
    min_x, max_x = x_coords[0], x_coords[-1]
    max_y, min_y = y_coords[0], y_coords[-1]
    
    print(f"\nUTM Extent:")
    print(f"  X: {min_x:.2f} to {max_x:.2f} ({max_x - min_x:.2f} m)")
    print(f"  Y: {min_y:.2f} to {max_y:.2f} ({max_y - min_y:.2f} m)")
    
    return x_coords, y_coords

def get_colors_gradient(zonemap, dem_shape):
    """
    Convert grayscale zonemap to Red-Green gradient
    Dark pixels (0) -> Red
    Bright pixels (255) -> Green
    """
    if zonemap.shape != dem_shape:
        zy = dem_shape[0] / zonemap.shape[0]
        zx = dem_shape[1] / zonemap.shape[1]
        zonemap = zoom(zonemap, (zy, zx), order=1)  # Linear interpolation for smooth gradient
        print(f"\nZonemap resized to {zonemap.shape}")
    
    # Normalize zonemap to 0-1 range
    zmin, zmax = np.min(zonemap), np.max(zonemap)
    print(f"Zonemap value range: {zmin:.2f} to {zmax:.2f}")
    
    if zmax > zmin:
        normalized = (zonemap - zmin) / (zmax - zmin)
    else:
        normalized = np.zeros_like(zonemap, dtype=np.float32)
    
    h, w = dem_shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Create Red to Green gradient
    # normalized = 0 (dark) -> Red (255, 0, 0)
    # normalized = 1 (bright) -> Green (0, 255, 0)
    
    rgb[:, :, 0] = ((1 - normalized) * 255).astype(np.uint8)  # Red channel: high when dark
    rgb[:, :, 1] = (normalized * 255).astype(np.uint8)        # Green channel: high when bright
    rgb[:, :, 2] = 0                                           # Blue channel: always 0
    
    print(f"Color gradient applied: Dark->Red, Bright->Green")
    return rgb

def write_obj_utm(dem, rgb, valid, x_coords, y_coords, filename, 
                  z_scale=1.0, center=True):
    """
    Write OBJ with real UTM coordinates
    
    Parameters:
    - center: If True, center the model at origin (easier to view)
    - z_scale: Vertical exaggeration
    """
    h, w = dem.shape
    
    # Get elevation stats
    valid_elev = dem[valid]
    emin, emax = valid_elev.min(), valid_elev.max()
    print(f"\nElevation: {emin:.2f} to {emax:.2f} m (range: {emax-emin:.2f} m)")
    
    # Calculate center for centering
    if center:
        center_x = (x_coords[0] + x_coords[-1]) / 2
        center_y = (y_coords[0] + y_coords[-1]) / 2
        center_z = (emin + emax) / 2
        print(f"Centering at: ({center_x:.2f}, {center_y:.2f}, {center_z:.2f})")
    else:
        center_x = center_y = center_z = 0
    
    print(f"\nWriting OBJ: {filename}")
    print(f"Resolution: {w} x {h}")
    print(f"Z-scale: {z_scale}")
    
    # Build vertex map
    vmap = np.full((h, w), -1, dtype=np.int32)
    vidx = 0
    
    with open(filename, 'w') as f:
        f.write("# Terrain Model with UTM Coordinates\n")
        f.write(f"# Size: {w} x {h} pixels\n")
        f.write(f"# Real dimensions: {x_coords[-1] - x_coords[0]:.2f} x {y_coords[-1] - y_coords[0]:.2f} meters\n")
        f.write(f"# Z-scale: {z_scale}\n")
        if center:
            f.write(f"# Centered at origin\n")
        f.write("\n")
        
        # Write vertices
        print("Writing vertices...")
        for y in range(h):
            if y % 200 == 0:
                print(f"  {y}/{h}")
            for x in range(w):
                if valid[y, x]:
                    # Real UTM coordinates
                    px = x_coords[x] - center_x
                    py = y_coords[y] - center_y
                    pz = (dem[y, x] - center_z) * z_scale
                    
                    # Color
                    r, g, b = rgb[y, x] / 255.0
                    
                    f.write(f"v {px:.3f} {py:.3f} {pz:.3f} {r:.3f} {g:.3f} {b:.3f}\n")
                    
                    vmap[y, x] = vidx
                    vidx += 1
        
        print(f"Vertices: {vidx:,}")
        
        # Write faces
        print("Writing faces...")
        fcount = 0
        for y in range(h-1):
            if y % 200 == 0:
                print(f"  {y}/{h-1}")
            for x in range(w-1):
                v1 = vmap[y, x]
                v2 = vmap[y, x+1]
                v3 = vmap[y+1, x+1]
                v4 = vmap[y+1, x]
                
                if v1 >= 0 and v2 >= 0 and v3 >= 0 and v4 >= 0:
                    f.write(f"f {v1+1} {v2+1} {v3+1}\n")
                    f.write(f"f {v1+1} {v3+1} {v4+1}\n")
                    fcount += 2
        
        print(f"Faces: {fcount:,}")
    
    print(f"✓ Created: {filename}")
    return vidx, fcount

def write_stl_utm(dem, valid, x_coords, y_coords, filename, 
                  z_scale=1.0, center=True):
    """Write STL with real UTM coordinates"""
    h, w = dem.shape
    
    valid_elev = dem[valid]
    emin, emax = valid_elev.min(), valid_elev.max()
    
    if center:
        center_x = (x_coords[0] + x_coords[-1]) / 2
        center_y = (y_coords[0] + y_coords[-1]) / 2
        center_z = (emin + emax) / 2
    else:
        center_x = center_y = center_z = 0
    
    print(f"\nWriting STL: {filename}")
    
    triangles = []
    
    print("Creating triangles...")
    for y in range(h-1):
        if y % 200 == 0:
            print(f"  {y}/{h-1}")
        for x in range(w-1):
            if (valid[y,x] and valid[y,x+1] and 
                valid[y+1,x+1] and valid[y+1,x]):
                
                # Real coordinates
                x0 = x_coords[x] - center_x
                x1 = x_coords[x+1] - center_x
                y0 = y_coords[y] - center_y
                y1 = y_coords[y+1] - center_y
                
                z00 = (dem[y, x] - center_z) * z_scale
                z10 = (dem[y, x+1] - center_z) * z_scale
                z11 = (dem[y+1, x+1] - center_z) * z_scale
                z01 = (dem[y+1, x] - center_z) * z_scale
                
                # Triangle 1
                v1 = np.array([x0, y0, z00])
                v2 = np.array([x1, y0, z10])
                v3 = np.array([x1, y1, z11])
                n = np.cross(v2-v1, v3-v1)
                norm = np.linalg.norm(n)
                if norm > 0:
                    n /= norm
                    triangles.append((n, v1, v2, v3))
                
                # Triangle 2
                v1 = np.array([x0, y0, z00])
                v2 = np.array([x1, y1, z11])
                v3 = np.array([x0, y1, z01])
                n = np.cross(v2-v1, v3-v1)
                norm = np.linalg.norm(n)
                if norm > 0:
                    n /= norm
                    triangles.append((n, v1, v2, v3))
    
    # Write binary STL
    print("Writing binary STL...")
    with open(filename, 'wb') as f:
        header = b'Binary STL - UTM Terrain' + b' ' * (80 - 24)
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))
        
        for i, (n, v1, v2, v3) in enumerate(triangles):
            if i % 100000 == 0 and i > 0:
                print(f"  {i:,}/{len(triangles):,}")
            f.write(struct.pack('<fff', *n))
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            f.write(struct.pack('<fff', *v3))
            f.write(struct.pack('<H', 0))
    
    print(f"Triangles: {len(triangles):,}")
    print(f"✓ Created: {filename}")
    return len(triangles)

def main():
    print("="*70)
    print("3D TERRAIN WITH REAL UTM COORDINATES")
    print("="*70)
    
    # Files
    DEM_FILE = "cliped_DEMUTM_FIX.tif"
    ZONE_FILE = "zonemap.tif"
    
    # Output
    OUT_OBJ = "terrain_utm.obj"
    OUT_STL = "terrain_utm.stl"
    
    # Settings
    Z_SCALE = 20.0     # 20.0 = 20x exaggeration for balanced terrain relief
    CENTER = True      # Center model at origin for easier viewing
    
    # Read DEM with geospatial info
    print("\n[1/5] Reading DEM...")
    dem, dem_valid, gt, dem_ds = read_tif_with_geo(DEM_FILE)
    # Get UTM coordinates
    print("\n[2/5] Calculating UTM coordinates...")
    x_coords, y_coords = get_utm_coordinates(gt, dem_ds.RasterXSize, dem_ds.RasterYSize)
    
    # Read zonemap
    print("\n[3/5] Reading zonemap...")
    zonemap, _, _, _ = read_tif_with_geo(ZONE_FILE)
    
    # Get colors
    print("\n[4/5] Processing colors...")
    rgb = get_colors_gradient(zonemap, dem.shape)
    
    # Create models
    print("\n[5/5] Creating 3D models...")
    verts, faces = write_obj_utm(dem, rgb, dem_valid, x_coords, y_coords, 
                                  OUT_OBJ, Z_SCALE, CENTER)
    
    tris = write_stl_utm(dem, dem_valid, x_coords, y_coords, 
                         OUT_STL, Z_SCALE, CENTER)
    
    # Summary
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)
    print(f"\n✓ {OUT_OBJ}")
    print(f"  {verts:,} vertices, {faces:,} faces")
    print(f"  Real UTM coordinates preserved")
    print(f"\n✓ {OUT_STL}")
    print(f"  {tris:,} triangles")
    print(f"\nSettings:")
    print(f"  Z-scale: {Z_SCALE} (1.0 = real scale)")
    print(f"  Centered: {CENTER}")
    print(f"  Real dimensions: {x_coords[-1] - x_coords[0]:.1f} x {y_coords[-1] - y_coords[0]:.1f} meters")
    print(f"\nOrientation:")
    print(f"  X-axis: East (→)")
    print(f"  Y-axis: North (↑)")
    print(f"  Z-axis: Elevation (↑)")
    print(f"\nTo adjust vertical exaggeration:")
    print(f"  Edit Z_SCALE in script (currently {Z_SCALE})")
    print(f"  Z_SCALE = 2.0 for 2x exaggeration")
    print(f"  Z_SCALE = 5.0 for 5x exaggeration")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
