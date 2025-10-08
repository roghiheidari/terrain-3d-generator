"""
Fix QGIS-generated OBJ file and convert texture to vertex colors
This will convert the texture-mapped model to vertex colors for Photoshop
"""

import numpy as np
from PIL import Image
import re

def parse_obj_file(filename):
    """Parse OBJ file and extract vertices, texture coords, and faces"""
    vertices = []
    texcoords = []
    faces = []
    
    print(f"Reading {filename}...")
    with open(filename, 'r') as f:
        for i, line in enumerate(f):
            if i % 100000 == 0 and i > 0:
                print(f"  Line {i:,}")
            
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if not parts:
                continue
            
            cmd = parts[0]
            
            if cmd == 'v':
                # Vertex: v x y z
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                vertices.append((x, y, z))
            
            elif cmd == 'vt':
                # Texture coordinate: vt u v
                u, v = float(parts[1]), float(parts[2])
                texcoords.append((u, v))
            
            elif cmd == 'f':
                # Face: f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3
                face_verts = []
                face_texcoords = []
                
                for vert_str in parts[1:]:
                    # Parse v/vt/vn format
                    indices = vert_str.split('/')
                    v_idx = int(indices[0])
                    vt_idx = int(indices[1]) if len(indices) > 1 and indices[1] else None
                    
                    face_verts.append(v_idx)
                    face_texcoords.append(vt_idx)
                
                faces.append((face_verts, face_texcoords))
    
    print(f"  Vertices: {len(vertices):,}")
    print(f"  Texture coords: {len(texcoords):,}")
    print(f"  Faces: {len(faces):,}")
    
    return vertices, texcoords, faces

def sample_texture(texture_img, u, v):
    """Sample color from texture at UV coordinates"""
    width, height = texture_img.size
    
    # Clamp UV to 0-1
    u = max(0, min(1, u))
    v = max(0, min(1, v))
    
    # Convert to pixel coordinates
    x = int(u * (width - 1))
    y = int((1 - v) * (height - 1))  # Flip V
    
    # Get pixel color
    pixel = texture_img.getpixel((x, y))
    
    if isinstance(pixel, int):
        # Grayscale
        return (pixel, pixel, pixel)
    else:
        # RGB or RGBA
        return pixel[:3]

def convert_to_vertex_colors(vertices, texcoords, faces, texture_file, output_file):
    """Convert texture-mapped OBJ to vertex colors"""
    
    print(f"\nLoading texture: {texture_file}")
    texture = Image.open(texture_file)
    print(f"  Texture size: {texture.size}")
    print(f"  Texture mode: {texture.mode}")
    
    # Convert to RGB if needed
    if texture.mode != 'RGB':
        texture = texture.convert('RGB')
    
    print(f"\nConverting to vertex colors...")
    
    # Create vertex color map
    vertex_colors = {}
    
    # Process each face to assign colors to vertices
    for i, (face_verts, face_texcoords) in enumerate(faces):
        if i % 50000 == 0 and i > 0:
            print(f"  Face {i:,}/{len(faces):,}")
        
        for v_idx, vt_idx in zip(face_verts, face_texcoords):
            if vt_idx is None:
                continue
            
            # Handle negative indices
            if v_idx < 0:
                v_idx = len(vertices) + v_idx + 1
            if vt_idx < 0:
                vt_idx = len(texcoords) + vt_idx + 1
            
            # Get texture coordinate
            if 1 <= vt_idx <= len(texcoords):
                u, v = texcoords[vt_idx - 1]
                
                # Sample texture
                color = sample_texture(texture, u, v)
                
                # Store color for this vertex (average if multiple)
                if v_idx not in vertex_colors:
                    vertex_colors[v_idx] = []
                vertex_colors[v_idx].append(color)
    
    print(f"  Colored vertices: {len(vertex_colors):,}")
    
    # Average colors for vertices with multiple samples
    print("  Averaging colors...")
    for v_idx in vertex_colors:
        colors = vertex_colors[v_idx]
        avg_color = tuple(int(sum(c[i] for c in colors) / len(colors)) for i in range(3))
        vertex_colors[v_idx] = avg_color
    
    # Write new OBJ file
    print(f"\nWriting {output_file}...")
    with open(output_file, 'w') as f:
        f.write("# Converted from texture-mapped to vertex colors\n")
        f.write(f"# Original: {texture_file}\n\n")
        
        # Write vertices with colors
        print("  Writing vertices...")
        for i, (x, y, z) in enumerate(vertices, 1):
            if i % 100000 == 0:
                print(f"    {i:,}/{len(vertices):,}")
            
            if i in vertex_colors:
                r, g, b = vertex_colors[i]
                r, g, b = r/255.0, g/255.0, b/255.0
                f.write(f"v {x:.6f} {y:.6f} {z:.6f} {r:.3f} {g:.3f} {b:.3f}\n")
            else:
                # Default gray color
                f.write(f"v {x:.6f} {y:.6f} {z:.6f} 0.5 0.5 0.5\n")
        
        # Write faces (simple vertex indices only)
        print("  Writing faces...")
        for i, (face_verts, _) in enumerate(faces):
            if i % 100000 == 0 and i > 0:
                print(f"    {i:,}/{len(faces):,}")
            
            # Convert negative indices to positive
            positive_verts = []
            for v_idx in face_verts:
                if v_idx < 0:
                    v_idx = len(vertices) + v_idx + 1
                positive_verts.append(v_idx)
            
            # Write face
            f.write("f " + " ".join(str(v) for v in positive_verts) + "\n")
    
    print(f"✓ Created: {output_file}")

def main():
    print("="*70)
    print("FIX QGIS OBJ FILE - CONVERT TEXTURE TO VERTEX COLORS")
    print("="*70)
    
    # Input files
    OBJ_FILE = "files/Zonemap3D.obj"
    TEXTURE_FILE = "files/Terrain_DEM_tile_material.jpg"
    
    # Output
    OUTPUT_FILE = "terrain_from_qgis_fixed.obj"
    
    # Parse OBJ
    vertices, texcoords, faces = parse_obj_file(OBJ_FILE)
    
    # Convert
    convert_to_vertex_colors(vertices, texcoords, faces, TEXTURE_FILE, OUTPUT_FILE)
    
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)
    print(f"\n✓ {OUTPUT_FILE}")
    print(f"\nThis file has vertex colors baked in from the texture.")
    print(f"Open in Photoshop: File → Open → {OUTPUT_FILE}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
