"""
Simple, robust 3D terrain generator with vertex colors
Creates clean OBJ/STL files compatible with Photoshop and 3D printing
"""

import numpy as np
from osgeo import gdal
from scipy.ndimage import zoom
import struct

# Color palette matching your zonemap
ZONE_COLORS = {
    0: (255, 140, 0),   # Orange
    1: (255, 255, 0),   # Yellow  
    2: (0, 200, 0),     # Green
    3: (255, 165, 0),   # Light orange
    4: (200, 200, 0),   # Yellow-green
}

def read_tif(filename):
    """Read GeoTIFF file"""
    ds = gdal.Open(filename)
    if ds is None:
        raise ValueError(f"Cannot open {filename}")
    
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    nodata = band.GetNoDataValue()
    
    print(f"\n{filename}:")
    print(f"  Size: {data.shape[1]} x {data.shape[0]}")
    print(f"  Range: {np.min(data):.2f} to {np.max(data):.2f}")
    print(f"  NoData: {nodata}")
    
    # Create valid mask
    if nodata is not None:
        valid = data != nodata
        print(f"  Valid: {np.sum(valid):,} pixels")
    else:
        valid = np.ones_like(data, dtype=bool)
    
    return data, valid

def get_colors(zonemap, dem_shape):
    """Get RGB colors from zonemap"""
    # Resize to match DEM
    if zonemap.shape != dem_shape:
        zy = dem_shape[0] / zonemap.shape[0]
        zx = dem_shape[1] / zonemap.shape[1]
        zonemap = zoom(zonemap, (zy, zx), order=0)
        print(f"\nZonemap resized to {zonemap.shape}")
    
    # Create RGB array
    h, w = dem_shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    
    for zone_id, color in ZONE_COLORS.items():
        mask = zonemap == zone_id
        rgb[mask] = color
    
    print(f"Zones: {np.unique(zonemap)}")
    return rgb

def write_obj_simple(dem, rgb, valid, filename, z_scale=0.3):
    """
    Write simple OBJ file with vertex colors
    Uses positive indices only for maximum compatibility
    """
    h, w = dem.shape
    
    # Normalize elevation
    valid_elev = dem[valid]
    emin, emax = valid_elev.min(), valid_elev.max()
    print(f"\nElevation: {emin:.2f} to {emax:.2f} (range: {emax-emin:.2f})")
    
    # Normalize to 0-1
    dem_norm = np.zeros_like(dem, dtype=np.float32)
    dem_norm[valid] = (dem[valid] - emin) / (emax - emin)
    
    print(f"\nWriting OBJ: {filename}")
    print(f"Resolution: {w} x {h}")
    
    # Build vertex map
    vmap = np.full((h, w), -1, dtype=np.int32)
    vidx = 0
    
    with open(filename, 'w') as f:
        f.write("# Terrain Model\n")
        f.write(f"# Size: {w} x {h}\n\n")
        
        # Write vertices
        print("Writing vertices...")
        for y in range(h):
            if y % 200 == 0:
                print(f"  {y}/{h}")
            for x in range(w):
                if valid[y, x]:
                    # Position (normalized to -1 to 1)
                    px = (x / (w-1)) * 2 - 1
                    py = (y / (h-1)) * 2 - 1
                    pz = dem_norm[y, x] * z_scale
                    
                    # Color (normalized to 0-1)
                    r, g, b = rgb[y, x] / 255.0
                    
                    # Write vertex with color
                    f.write(f"v {px:.6f} {py:.6f} {pz:.6f} {r:.3f} {g:.3f} {b:.3f}\n")
                    
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
                # Get vertex indices (1-based for OBJ)
                v1 = vmap[y, x]
                v2 = vmap[y, x+1]
                v3 = vmap[y+1, x+1]
                v4 = vmap[y+1, x]
                
                # Only write face if all vertices exist
                if v1 >= 0 and v2 >= 0 and v3 >= 0 and v4 >= 0:
                    # Two triangles per quad
                    f.write(f"f {v1+1} {v2+1} {v3+1}\n")
                    f.write(f"f {v1+1} {v3+1} {v4+1}\n")
                    fcount += 2
        
        print(f"Faces: {fcount:,}")
    
    print(f"✓ Created: {filename}")
    return vidx, fcount

def write_stl(dem, valid, filename, z_scale=0.3):
    """Write binary STL file"""
    h, w = dem.shape
    
    # Normalize elevation
    valid_elev = dem[valid]
    emin, emax = valid_elev.min(), valid_elev.max()
    
    dem_norm = np.zeros_like(dem, dtype=np.float32)
    dem_norm[valid] = (dem[valid] - emin) / (emax - emin)
    
    print(f"\nWriting STL: {filename}")
    
    # Collect triangles
    triangles = []
    
    print("Creating triangles...")
    for y in range(h-1):
        if y % 200 == 0:
            print(f"  {y}/{h-1}")
        for x in range(w-1):
            if (valid[y,x] and valid[y,x+1] and 
                valid[y+1,x+1] and valid[y+1,x]):
                
                # Positions
                x0 = (x / (w-1)) * 2 - 1
                x1 = ((x+1) / (w-1)) * 2 - 1
                y0 = (y / (h-1)) * 2 - 1
                y1 = ((y+1) / (h-1)) * 2 - 1
                
                z00 = dem_norm[y, x] * z_scale
                z10 = dem_norm[y, x+1] * z_scale
                z11 = dem_norm[y+1, x+1] * z_scale
                z01 = dem_norm[y+1, x] * z_scale
                
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
        # Header
        header = b'Binary STL Terrain' + b' ' * (80 - 18)
        f.write(header)
        
        # Triangle count
        f.write(struct.pack('<I', len(triangles)))
        
        # Triangles
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
    print("SIMPLE TERRAIN 3D MODEL GENERATOR")
    print("="*70)
    
    # Files
    DEM_FILE = "cliped_DEMUTM_FIX.tif"
    ZONE_FILE = "zonemap.tif"
    
    # Output
    OUT_OBJ = "terrain_simple.obj"
    OUT_STL = "terrain_simple.stl"
    
    # Settings
    Z_SCALE = 0.3  # Vertical exaggeration
    
    # Read data
    print("\n[1/4] Reading DEM...")
    dem, dem_valid = read_tif(DEM_FILE)
    
    print("\n[2/4] Reading zonemap...")
    zonemap, _ = read_tif(ZONE_FILE)
    
    print("\n[3/4] Processing colors...")
    rgb = get_colors(zonemap, dem.shape)
    
    # Create OBJ
    print("\n[4/4] Creating 3D models...")
    verts, faces = write_obj_simple(dem, rgb, dem_valid, OUT_OBJ, Z_SCALE)
    
    # Create STL
    tris = write_stl(dem, dem_valid, OUT_STL, Z_SCALE)
    
    # Summary
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)
    print(f"\n✓ {OUT_OBJ}")
    print(f"  {verts:,} vertices, {faces:,} faces")
    print(f"\n✓ {OUT_STL}")
    print(f"  {tris:,} triangles")
    print(f"\nSettings:")
    print(f"  Z-scale: {Z_SCALE}")
    print(f"\nTo open in Photoshop:")
    print(f"  File → Open → {OUT_OBJ}")
    print(f"\nFor 3D printing:")
    print(f"  Import {OUT_STL} into your slicer")
    print(f"\nColors:")
    for zone, color in ZONE_COLORS.items():
        print(f"  Zone {zone}: RGB{color}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
