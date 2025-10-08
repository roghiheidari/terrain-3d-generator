"""
Create high-resolution 3D terrain model with proper zonemap coloring
Generates OBJ file compatible with Photoshop and STL for 3D printing
"""

import numpy as np
from osgeo import gdal
import struct
from scipy.ndimage import zoom

# Define color palette for zones (matching your zonemap image)
ZONE_COLORS = {
    0: (255, 140, 0),   # Orange
    1: (255, 255, 0),   # Yellow
    2: (0, 200, 0),     # Green
    3: (255, 165, 0),   # Light orange
    4: (200, 200, 0),   # Yellow-green
}

def read_geotiff(filename):
    """Read GeoTIFF and return data with proper nodata handling"""
    dataset = gdal.Open(filename)
    if dataset is None:
        raise ValueError(f"Could not open {filename}")
    
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()
    nodata = band.GetNoDataValue()
    
    print(f"\n{filename}:")
    print(f"  Dimensions: {data.shape}")
    print(f"  Data type: {data.dtype}")
    print(f"  Min value: {np.min(data)}")
    print(f"  Max value: {np.max(data)}")
    print(f"  NoData value: {nodata}")
    
    # Create mask for valid data
    if nodata is not None:
        valid_mask = data != nodata
        print(f"  Valid pixels: {np.sum(valid_mask):,} / {data.size:,}")
    else:
        valid_mask = np.ones_like(data, dtype=bool)
    
    return data, valid_mask, dataset

def get_rgb_from_zonemap(zonemap_data, dem_shape):
    """Convert zonemap to RGB colors matching DEM resolution"""
    
    # Resize zonemap to match DEM
    if zonemap_data.shape != dem_shape:
        zoom_factors = (dem_shape[0] / zonemap_data.shape[0], 
                       dem_shape[1] / zonemap_data.shape[1])
        zonemap_resized = zoom(zonemap_data, zoom_factors, order=0)  # Nearest neighbor
        print(f"\nResized zonemap from {zonemap_data.shape} to {zonemap_resized.shape}")
    else:
        zonemap_resized = zonemap_data
    
    # Create RGB array
    rgb_array = np.zeros((dem_shape[0], dem_shape[1], 3), dtype=np.uint8)
    
    # Map each zone to its color
    unique_zones = np.unique(zonemap_resized)
    print(f"Unique zones found: {unique_zones}")
    
    for zone in unique_zones:
        mask = zonemap_resized == zone
        if zone in ZONE_COLORS:
            rgb_array[mask] = ZONE_COLORS[zone]
        else:
            # Default color for unmapped zones
            rgb_array[mask] = (128, 128, 128)
    
    return rgb_array

def create_obj_with_colors(dem_data, rgb_colors, valid_mask, output_file, 
                          downsample=1, z_scale=1.0, base_thickness=0.05):
    """
    Create OBJ file with proper RGB vertex colors and solid base
    """
    
    height, width = dem_data.shape
    
    # Downsample if needed
    if downsample > 1:
        dem_data = dem_data[::downsample, ::downsample]
        rgb_colors = rgb_colors[::downsample, ::downsample]
        valid_mask = valid_mask[::downsample, ::downsample]
        height, width = dem_data.shape
        print(f"\nDownsampled to: {height} x {width}")
    
    # Normalize elevation
    valid_elevations = dem_data[valid_mask]
    min_elev = np.min(valid_elevations)
    max_elev = np.max(valid_elevations)
    elev_range = max_elev - min_elev
    
    print(f"\nElevation range: {min_elev:.2f} to {max_elev:.2f}")
    print(f"Range: {elev_range:.2f}")
    
    # Normalize elevations to 0-1
    dem_normalized = np.zeros_like(dem_data, dtype=np.float32)
    dem_normalized[valid_mask] = (dem_data[valid_mask] - min_elev) / elev_range
    
    print(f"\nGenerating OBJ file...")
    
    # Create vertex index map
    vertex_map = np.full((height, width), -1, dtype=np.int32)
    vertices = []
    colors = []
    
    # Generate top surface vertices
    print("Creating top surface vertices...")
    for y in range(height):
        if y % 100 == 0:
            print(f"  Row {y}/{height}")
        for x in range(width):
            if valid_mask[y, x]:
                # Normalize x,y to -1 to 1
                vx = (x / (width - 1)) * 2 - 1
                vy = (y / (height - 1)) * 2 - 1
                vz = dem_normalized[y, x] * z_scale
                
                vertices.append((vx, vy, vz))
                colors.append(rgb_colors[y, x] / 255.0)  # Normalize to 0-1
                vertex_map[y, x] = len(vertices) - 1
    
    num_top_vertices = len(vertices)
    print(f"Created {num_top_vertices:,} top vertices")
    
    # Create bottom surface vertices (for solid model)
    print("Creating bottom surface vertices...")
    bottom_vertex_map = np.full((height, width), -1, dtype=np.int32)
    for y in range(height):
        for x in range(width):
            if valid_mask[y, x]:
                vx = (x / (width - 1)) * 2 - 1
                vy = (y / (height - 1)) * 2 - 1
                vz = -base_thickness
                
                vertices.append((vx, vy, vz))
                colors.append(rgb_colors[y, x] / 255.0)
                bottom_vertex_map[y, x] = len(vertices) - 1
    
    print(f"Total vertices: {len(vertices):,}")
    
    # Write OBJ file
    print("Writing OBJ file...")
    with open(output_file, 'w') as f:
        f.write("# 3D Terrain Model with Zonemap Colors\n")
        f.write(f"# Vertices: {len(vertices)}\n")
        f.write(f"# Resolution: {width} x {height}\n\n")
        
        # Write vertices with RGB colors
        print("  Writing vertices...")
        for i, (v, c) in enumerate(zip(vertices, colors)):
            if i % 100000 == 0 and i > 0:
                print(f"    {i:,} / {len(vertices):,}")
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f} {c[0]:.3f} {c[1]:.3f} {c[2]:.3f}\n")
        
        # Write top surface faces
        print("  Writing top surface faces...")
        face_count = 0
        for y in range(height - 1):
            if y % 100 == 0:
                print(f"    Row {y}/{height-1}")
            for x in range(width - 1):
                v1 = vertex_map[y, x]
                v2 = vertex_map[y, x + 1]
                v3 = vertex_map[y + 1, x + 1]
                v4 = vertex_map[y + 1, x]
                
                if v1 >= 0 and v2 >= 0 and v3 >= 0 and v4 >= 0:
                    # Two triangles (1-indexed)
                    f.write(f"f {v1+1} {v2+1} {v3+1}\n")
                    f.write(f"f {v1+1} {v3+1} {v4+1}\n")
                    face_count += 2
        
        # Write bottom surface faces (reversed winding)
        print("  Writing bottom surface faces...")
        for y in range(height - 1):
            for x in range(width - 1):
                v1 = bottom_vertex_map[y, x]
                v2 = bottom_vertex_map[y, x + 1]
                v3 = bottom_vertex_map[y + 1, x + 1]
                v4 = bottom_vertex_map[y + 1, x]
                
                if v1 >= 0 and v2 >= 0 and v3 >= 0 and v4 >= 0:
                    # Reversed winding for bottom
                    f.write(f"f {v1+1} {v3+1} {v2+1}\n")
                    f.write(f"f {v1+1} {v4+1} {v3+1}\n")
                    face_count += 2
        
        # Write side walls
        print("  Writing side walls...")
        # Left and right edges
        for y in range(height - 1):
            # Left edge
            for x in [0, width-1]:
                if valid_mask[y, x] and valid_mask[y+1, x]:
                    t1 = vertex_map[y, x]
                    t2 = vertex_map[y+1, x]
                    b1 = bottom_vertex_map[y, x]
                    b2 = bottom_vertex_map[y+1, x]
                    
                    if t1 >= 0 and t2 >= 0 and b1 >= 0 and b2 >= 0:
                        f.write(f"f {t1+1} {b1+1} {b2+1}\n")
                        f.write(f"f {t1+1} {b2+1} {t2+1}\n")
                        face_count += 2
        
        # Top and bottom edges
        for x in range(width - 1):
            # Top and bottom edges
            for y in [0, height-1]:
                if valid_mask[y, x] and valid_mask[y, x+1]:
                    t1 = vertex_map[y, x]
                    t2 = vertex_map[y, x+1]
                    b1 = bottom_vertex_map[y, x]
                    b2 = bottom_vertex_map[y, x+1]
                    
                    if t1 >= 0 and t2 >= 0 and b1 >= 0 and b2 >= 0:
                        f.write(f"f {t1+1} {t2+1} {b2+1}\n")
                        f.write(f"f {t1+1} {b2+1} {b1+1}\n")
                        face_count += 2
        
        print(f"Total faces: {face_count:,}")
    
    print(f"\nOBJ file created: {output_file}")
    return len(vertices), face_count

def create_stl_file(dem_data, valid_mask, output_file, downsample=1, 
                   z_scale=1.0, base_thickness=0.05):
    """Create binary STL file for 3D printing"""
    
    height, width = dem_data.shape
    
    if downsample > 1:
        dem_data = dem_data[::downsample, ::downsample]
        valid_mask = valid_mask[::downsample, ::downsample]
        height, width = dem_data.shape
    
    # Normalize elevation
    valid_elevations = dem_data[valid_mask]
    min_elev = np.min(valid_elevations)
    max_elev = np.max(valid_elevations)
    elev_range = max_elev - min_elev
    
    dem_normalized = np.zeros_like(dem_data, dtype=np.float32)
    dem_normalized[valid_mask] = (dem_data[valid_mask] - min_elev) / elev_range
    
    print(f"\nGenerating STL file...")
    triangles = []
    
    # Top surface
    print("Creating top surface...")
    for y in range(height - 1):
        if y % 100 == 0:
            print(f"  Row {y}/{height-1}")
        for x in range(width - 1):
            if (valid_mask[y, x] and valid_mask[y, x+1] and 
                valid_mask[y+1, x+1] and valid_mask[y+1, x]):
                
                # Vertex coordinates
                x0 = (x / (width - 1)) * 2 - 1
                x1 = ((x + 1) / (width - 1)) * 2 - 1
                y0 = (y / (height - 1)) * 2 - 1
                y1 = ((y + 1) / (height - 1)) * 2 - 1
                
                z00 = dem_normalized[y, x] * z_scale
                z10 = dem_normalized[y, x + 1] * z_scale
                z11 = dem_normalized[y + 1, x + 1] * z_scale
                z01 = dem_normalized[y + 1, x] * z_scale
                
                # Triangle 1
                v1 = np.array([x0, y0, z00])
                v2 = np.array([x1, y0, z10])
                v3 = np.array([x1, y1, z11])
                normal = np.cross(v2 - v1, v3 - v1)
                norm = np.linalg.norm(normal)
                if norm > 0:
                    normal /= norm
                    triangles.append((normal, v1, v2, v3))
                
                # Triangle 2
                v1 = np.array([x0, y0, z00])
                v2 = np.array([x1, y1, z11])
                v3 = np.array([x0, y1, z01])
                normal = np.cross(v2 - v1, v3 - v1)
                norm = np.linalg.norm(normal)
                if norm > 0:
                    normal /= norm
                    triangles.append((normal, v1, v2, v3))
    
    # Bottom surface
    print("Creating bottom surface...")
    for y in range(height - 1):
        for x in range(width - 1):
            if (valid_mask[y, x] and valid_mask[y, x+1] and 
                valid_mask[y+1, x+1] and valid_mask[y+1, x]):
                
                x0 = (x / (width - 1)) * 2 - 1
                x1 = ((x + 1) / (width - 1)) * 2 - 1
                y0 = (y / (height - 1)) * 2 - 1
                y1 = ((y + 1) / (height - 1)) * 2 - 1
                z = -base_thickness
                
                # Reversed winding for bottom
                v1 = np.array([x0, y0, z])
                v2 = np.array([x1, y1, z])
                v3 = np.array([x1, y0, z])
                normal = np.array([0, 0, -1])
                triangles.append((normal, v1, v2, v3))
                
                v1 = np.array([x0, y0, z])
                v2 = np.array([x0, y1, z])
                v3 = np.array([x1, y1, z])
                triangles.append((normal, v1, v2, v3))
    
    # Write binary STL
    print("Writing STL file...")
    with open(output_file, 'wb') as f:
        header = b'Binary STL - Terrain Model' + b' ' * (80 - 27)
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))
        
        for i, (normal, v1, v2, v3) in enumerate(triangles):
            if i % 100000 == 0 and i > 0:
                print(f"  {i:,} / {len(triangles):,}")
            f.write(struct.pack('<fff', *normal))
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            f.write(struct.pack('<fff', *v3))
            f.write(struct.pack('<H', 0))
    
    print(f"\nSTL file created: {output_file}")
    print(f"Triangles: {len(triangles):,}")
    return len(triangles)

def main():
    print("="*70)
    print("3D TERRAIN MODEL GENERATOR WITH ZONEMAP COLORS")
    print("="*70)
    
    # Configuration
    DEM_FILE = "cliped_DEMUTM_FIX.tif"
    ZONEMAP_FILE = "zonemap.tif"
    OUTPUT_OBJ = "terrain_colored.obj"
    OUTPUT_STL = "terrain_colored.stl"
    
    # Quality settings
    DOWNSAMPLE = 1      # 1=full res, 2=half, 4=quarter
    Z_SCALE = 0.3       # Vertical exaggeration
    BASE_THICKNESS = 0.05  # Thickness of base for 3D printing
    
    # Read DEM
    print("\nReading DEM...")
    dem_data, dem_valid, dem_ds = read_geotiff(DEM_FILE)
    
    # Read zonemap
    print("\nReading zonemap...")
    zonemap_data, zonemap_valid, zonemap_ds = read_geotiff(ZONEMAP_FILE)
    
    # Get RGB colors from zonemap
    print("\nMapping zonemap colors to RGB...")
    rgb_colors = get_rgb_from_zonemap(zonemap_data, dem_data.shape)
    
    # Estimate complexity
    valid_count = np.sum(dem_valid)
    print(f"\nModel complexity:")
    print(f"  Valid DEM points: {valid_count:,}")
    print(f"  Estimated faces: ~{valid_count * 2:,}")
    if DOWNSAMPLE > 1:
        print(f"  Downsampling: {DOWNSAMPLE}x")
        print(f"  Final faces: ~{(valid_count // (DOWNSAMPLE**2)) * 2:,}")
    
    # Create OBJ file
    print("\n" + "="*70)
    print("CREATING OBJ FILE (for Photoshop)")
    print("="*70)
    vertices, faces = create_obj_with_colors(
        dem_data, rgb_colors, dem_valid, OUTPUT_OBJ,
        downsample=DOWNSAMPLE, z_scale=Z_SCALE, base_thickness=BASE_THICKNESS
    )
    
    # Create STL file
    print("\n" + "="*70)
    print("CREATING STL FILE (for 3D printing)")
    print("="*70)
    triangles = create_stl_file(
        dem_data, dem_valid, OUTPUT_STL,
        downsample=DOWNSAMPLE, z_scale=Z_SCALE, base_thickness=BASE_THICKNESS
    )
    
    # Summary
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  {OUTPUT_OBJ} - {vertices:,} vertices, {faces:,} faces")
    print(f"  {OUTPUT_STL} - {triangles:,} triangles")
    print(f"\nSettings used:")
    print(f"  Resolution: {DOWNSAMPLE}x downsample")
    print(f"  Z-scale: {Z_SCALE}")
    print(f"  Base thickness: {BASE_THICKNESS}")
    print(f"\nTo open in Photoshop:")
    print(f"  1. File > Open")
    print(f"  2. Select {OUTPUT_OBJ}")
    print(f"  3. Or: 3D > New 3D Layer from File")
    print(f"\nColors from zonemap:")
    for zone, color in ZONE_COLORS.items():
        print(f"  Zone {zone}: RGB{color}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
