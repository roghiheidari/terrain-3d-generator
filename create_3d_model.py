"""
Create high-resolution 3D model (OBJ/STL) from DEM and zonemap
DEM provides elevation data, zonemap provides color information
Output is compatible with Photoshop for 3D printing
"""

import numpy as np
from osgeo import gdal
import struct

def read_geotiff(filename):
    """Read GeoTIFF file and return data array"""
    dataset = gdal.Open(filename)
    if dataset is None:
        raise ValueError(f"Could not open {filename}")
    
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()
    
    print(f"\n{filename}:")
    print(f"  Dimensions: {data.shape}")
    print(f"  Data type: {data.dtype}")
    print(f"  Min value: {np.min(data)}")
    print(f"  Max value: {np.max(data)}")
    print(f"  No data value: {band.GetNoDataValue()}")
    
    return data, dataset

def normalize_elevation(dem_data, z_scale=1.0):
    """Normalize elevation data and apply vertical scaling"""
    # Handle no-data values
    valid_mask = np.isfinite(dem_data)
    
    if not np.any(valid_mask):
        raise ValueError("No valid elevation data found")
    
    min_elev = np.min(dem_data[valid_mask])
    max_elev = np.max(dem_data[valid_mask])
    
    print(f"\nElevation range: {min_elev:.2f} to {max_elev:.2f}")
    
    # Normalize to 0-1 range, then scale
    normalized = np.zeros_like(dem_data, dtype=np.float32)
    normalized[valid_mask] = (dem_data[valid_mask] - min_elev) / (max_elev - min_elev)
    normalized *= z_scale
    
    return normalized, valid_mask

def map_colors_from_zonemap(zonemap_data, dem_shape):
    """Map zonemap colors to DEM resolution"""
    from scipy.ndimage import zoom
    
    # If zonemap is smaller, resize it to match DEM
    if zonemap_data.shape != dem_shape:
        zoom_factors = (dem_shape[0] / zonemap_data.shape[0], 
                       dem_shape[1] / zonemap_data.shape[1])
        zonemap_resized = zoom(zonemap_data, zoom_factors, order=1)
        print(f"\nResized zonemap from {zonemap_data.shape} to {zonemap_resized.shape}")
    else:
        zonemap_resized = zonemap_data
    
    # Normalize to 0-255 range for colors
    zmin, zmax = np.min(zonemap_resized), np.max(zonemap_resized)
    if zmax > zmin:
        colors_normalized = ((zonemap_resized - zmin) / (zmax - zmin) * 255).astype(np.uint8)
    else:
        colors_normalized = np.zeros_like(zonemap_resized, dtype=np.uint8)
    
    return colors_normalized

def create_obj_file(dem_data, color_data, valid_mask, output_file, 
                    downsample=1, z_scale=1.0):
    """
    Create OBJ file with vertex colors
    
    Parameters:
    - dem_data: elevation data (normalized)
    - color_data: color values (0-255)
    - valid_mask: boolean mask of valid data points
    - output_file: output filename
    - downsample: factor to reduce resolution (1=full res, 2=half, etc.)
    - z_scale: vertical exaggeration factor
    """
    
    height, width = dem_data.shape
    
    # Downsample if requested
    if downsample > 1:
        dem_data = dem_data[::downsample, ::downsample]
        color_data = color_data[::downsample, ::downsample]
        valid_mask = valid_mask[::downsample, ::downsample]
        height, width = dem_data.shape
        print(f"\nDownsampled to: {height} x {width}")
    
    print(f"\nGenerating OBJ file with {height * width} potential vertices...")
    
    # Create vertex index map
    vertex_map = np.full((height, width), -1, dtype=np.int32)
    vertex_count = 0
    
    # Write OBJ file
    with open(output_file, 'w') as f:
        # Write header
        f.write("# 3D Terrain Model\n")
        f.write(f"# Generated from DEM with zonemap coloring\n")
        f.write(f"# Dimensions: {width} x {height}\n\n")
        
        # Write material library reference
        mtl_file = output_file.replace('.obj', '.mtl')
        f.write(f"mtllib {mtl_file.split('/')[-1]}\n")
        f.write("usemtl terrain\n\n")
        
        # Write vertices with colors
        print("Writing vertices...")
        for y in range(height):
            if y % 100 == 0:
                print(f"  Progress: {y}/{height} rows")
            for x in range(width):
                if valid_mask[y, x]:
                    # Normalize x, y to -1 to 1 range for better viewing
                    vx = (x / width) * 2 - 1
                    vy = (y / height) * 2 - 1
                    vz = dem_data[y, x] * z_scale
                    
                    # Color (normalized to 0-1)
                    color_val = color_data[y, x] / 255.0
                    
                    # Write vertex with color (using vertex colors)
                    f.write(f"v {vx:.6f} {vy:.6f} {vz:.6f} {color_val:.3f} {color_val:.3f} {color_val:.3f}\n")
                    
                    vertex_map[y, x] = vertex_count
                    vertex_count += 1
        
        print(f"Wrote {vertex_count} vertices")
        
        # Write faces (triangles)
        print("Writing faces...")
        face_count = 0
        for y in range(height - 1):
            if y % 100 == 0:
                print(f"  Progress: {y}/{height-1} rows")
            for x in range(width - 1):
                # Get vertex indices for quad
                v1 = vertex_map[y, x]
                v2 = vertex_map[y, x + 1]
                v3 = vertex_map[y + 1, x + 1]
                v4 = vertex_map[y + 1, x]
                
                # Only create faces if all vertices are valid
                if v1 >= 0 and v2 >= 0 and v3 >= 0 and v4 >= 0:
                    # Two triangles per quad (OBJ uses 1-based indexing)
                    f.write(f"f {v1+1} {v2+1} {v3+1}\n")
                    f.write(f"f {v1+1} {v3+1} {v4+1}\n")
                    face_count += 2
        
        print(f"Wrote {face_count} faces")
    
    # Create simple MTL file
    with open(mtl_file, 'w') as f:
        f.write("# Material file\n")
        f.write("newmtl terrain\n")
        f.write("Ka 1.0 1.0 1.0\n")
        f.write("Kd 1.0 1.0 1.0\n")
        f.write("Ks 0.0 0.0 0.0\n")
        f.write("d 1.0\n")
        f.write("illum 1\n")
    
    print(f"\nOBJ file created: {output_file}")
    print(f"Material file created: {mtl_file}")
    return vertex_count, face_count

def create_stl_file(dem_data, valid_mask, output_file, downsample=1, z_scale=1.0):
    """
    Create binary STL file (no color support in standard STL)
    
    Parameters:
    - dem_data: elevation data (normalized)
    - valid_mask: boolean mask of valid data points
    - output_file: output filename
    - downsample: factor to reduce resolution
    - z_scale: vertical exaggeration factor
    """
    
    height, width = dem_data.shape
    
    # Downsample if requested
    if downsample > 1:
        dem_data = dem_data[::downsample, ::downsample]
        valid_mask = valid_mask[::downsample, ::downsample]
        height, width = dem_data.shape
        print(f"\nDownsampled to: {height} x {width}")
    
    print(f"\nGenerating STL file...")
    
    # Collect all triangles
    triangles = []
    
    for y in range(height - 1):
        if y % 100 == 0:
            print(f"  Progress: {y}/{height-1} rows")
        for x in range(width - 1):
            if (valid_mask[y, x] and valid_mask[y, x+1] and 
                valid_mask[y+1, x+1] and valid_mask[y+1, x]):
                
                # Normalize coordinates
                x0 = (x / width) * 2 - 1
                x1 = ((x + 1) / width) * 2 - 1
                y0 = (y / height) * 2 - 1
                y1 = ((y + 1) / height) * 2 - 1
                
                # Get elevations
                z00 = dem_data[y, x] * z_scale
                z10 = dem_data[y, x + 1] * z_scale
                z11 = dem_data[y + 1, x + 1] * z_scale
                z01 = dem_data[y + 1, x] * z_scale
                
                # Create two triangles
                # Triangle 1: (x0,y0,z00), (x1,y0,z10), (x1,y1,z11)
                v1 = np.array([x0, y0, z00])
                v2 = np.array([x1, y0, z10])
                v3 = np.array([x1, y1, z11])
                normal1 = np.cross(v2 - v1, v3 - v1)
                norm = np.linalg.norm(normal1)
                if norm > 0:
                    normal1 /= norm
                triangles.append((normal1, v1, v2, v3))
                
                # Triangle 2: (x0,y0,z00), (x1,y1,z11), (x0,y1,z01)
                v1 = np.array([x0, y0, z00])
                v2 = np.array([x1, y1, z11])
                v3 = np.array([x0, y1, z01])
                normal2 = np.cross(v2 - v1, v3 - v1)
                norm = np.linalg.norm(normal2)
                if norm > 0:
                    normal2 /= norm
                triangles.append((normal2, v1, v2, v3))
    
    # Write binary STL
    with open(output_file, 'wb') as f:
        # Header (80 bytes)
        header = b'Binary STL file - Terrain Model' + b' ' * (80 - 32)
        f.write(header)
        
        # Number of triangles (4 bytes, little endian)
        f.write(struct.pack('<I', len(triangles)))
        
        # Write each triangle
        for normal, v1, v2, v3 in triangles:
            # Normal vector (3 floats)
            f.write(struct.pack('<fff', *normal))
            # Vertex 1 (3 floats)
            f.write(struct.pack('<fff', *v1))
            # Vertex 2 (3 floats)
            f.write(struct.pack('<fff', *v2))
            # Vertex 3 (3 floats)
            f.write(struct.pack('<fff', *v3))
            # Attribute byte count (2 bytes)
            f.write(struct.pack('<H', 0))
    
    print(f"\nSTL file created: {output_file}")
    print(f"Triangle count: {len(triangles)}")
    return len(triangles)

def main():
    # Configuration
    DEM_FILE = "cliped_DEMUTM_FIX.tif"
    ZONEMAP_FILE = "zonemap.tif"
    
    # Output settings
    OUTPUT_OBJ = "terrain_model.obj"
    OUTPUT_STL = "terrain_model.stl"
    
    # Quality settings
    DOWNSAMPLE = 1  # 1 = full resolution, 2 = half, 4 = quarter, etc.
    Z_SCALE = 0.5   # Vertical exaggeration (adjust based on your needs)
    
    print("="*60)
    print("3D Terrain Model Generator")
    print("="*60)
    
    # Read input files
    print("\nReading DEM file...")
    dem_data, dem_dataset = read_geotiff(DEM_FILE)
    
    print("\nReading zonemap file...")
    zonemap_data, zonemap_dataset = read_geotiff(ZONEMAP_FILE)
    
    # Process elevation data
    print("\nProcessing elevation data...")
    normalized_dem, valid_mask = normalize_elevation(dem_data, z_scale=1.0)
    
    # Process color data
    print("\nProcessing color data...")
    color_data = map_colors_from_zonemap(zonemap_data, dem_data.shape)
    
    # Estimate output size
    valid_points = np.sum(valid_mask)
    estimated_faces = valid_points * 2
    print(f"\nEstimated model complexity:")
    print(f"  Valid data points: {valid_points:,}")
    print(f"  Estimated faces: {estimated_faces:,}")
    
    if DOWNSAMPLE > 1:
        print(f"  Downsampling by factor of {DOWNSAMPLE}")
        print(f"  Final vertices: ~{valid_points // (DOWNSAMPLE**2):,}")
        print(f"  Final faces: ~{estimated_faces // (DOWNSAMPLE**2):,}")
    
    # Create OBJ file (with colors - best for Photoshop)
    print("\n" + "="*60)
    print("Creating OBJ file (recommended for Photoshop)...")
    print("="*60)
    vertex_count, face_count = create_obj_file(
        normalized_dem, color_data, valid_mask, 
        OUTPUT_OBJ, downsample=DOWNSAMPLE, z_scale=Z_SCALE
    )
    
    # Create STL file (standard for 3D printing, but no colors)
    print("\n" + "="*60)
    print("Creating STL file (standard for 3D printing)...")
    print("="*60)
    triangle_count = create_stl_file(
        normalized_dem, valid_mask, 
        OUTPUT_STL, downsample=DOWNSAMPLE, z_scale=Z_SCALE
    )
    
    # Summary
    print("\n" + "="*60)
    print("GENERATION COMPLETE")
    print("="*60)
    print(f"\nOutput files:")
    print(f"  OBJ: {OUTPUT_OBJ} ({vertex_count:,} vertices, {face_count:,} faces)")
    print(f"  STL: {OUTPUT_STL} ({triangle_count:,} triangles)")
    print(f"\nFor Photoshop:")
    print(f"  1. Open Photoshop")
    print(f"  2. Go to: 3D > New 3D Layer from File")
    print(f"  3. Select: {OUTPUT_OBJ}")
    print(f"  4. The model will load with vertex colors from zonemap")
    print(f"\nFor 3D Printing:")
    print(f"  - Use {OUTPUT_STL} in your slicer software")
    print(f"  - Adjust Z_SCALE in script if vertical exaggeration needed")
    print(f"  - Current Z_SCALE: {Z_SCALE}")
    print(f"\nTo adjust resolution:")
    print(f"  - Edit DOWNSAMPLE variable (currently: {DOWNSAMPLE})")
    print(f"  - Lower = higher resolution, larger file")
    print(f"  - Higher = lower resolution, smaller file")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
