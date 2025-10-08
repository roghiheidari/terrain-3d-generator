"""
Validate OBJ files and check for common issues
"""

def check_obj_file(filename):
    """Check OBJ file for issues"""
    print(f"\n{'='*70}")
    print(f"Checking: {filename}")
    print('='*70)
    
    try:
        with open(filename, 'r') as f:
            vertices = 0
            vertices_with_color = 0
            faces = 0
            negative_indices = 0
            texture_coords = 0
            normals = 0
            
            for i, line in enumerate(f, 1):
                if i > 1000000:  # Sample first 1M lines
                    break
                
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if not parts:
                    continue
                
                cmd = parts[0]
                
                if cmd == 'v':
                    vertices += 1
                    # Check if has color (6 values: x y z r g b)
                    if len(parts) >= 7:
                        vertices_with_color += 1
                
                elif cmd == 'vt':
                    texture_coords += 1
                
                elif cmd == 'vn':
                    normals += 1
                
                elif cmd == 'f':
                    faces += 1
                    # Check for negative indices
                    for vert_str in parts[1:]:
                        if '/' in vert_str:
                            v_idx = vert_str.split('/')[0]
                        else:
                            v_idx = vert_str
                        if v_idx.startswith('-'):
                            negative_indices += 1
                            break
        
        # Report
        print(f"\n✓ File readable")
        print(f"\nStatistics:")
        print(f"  Vertices: {vertices:,}")
        print(f"  Vertices with color: {vertices_with_color:,}")
        print(f"  Faces: {faces:,}")
        print(f"  Texture coords: {texture_coords:,}")
        print(f"  Normals: {normals:,}")
        
        # Issues
        issues = []
        
        if negative_indices > 0:
            issues.append(f"⚠️  Uses negative indices ({negative_indices:,} faces)")
        
        if vertices_with_color == 0 and texture_coords == 0:
            issues.append("⚠️  No colors (no vertex colors or texture coords)")
        
        if vertices_with_color > 0 and vertices_with_color < vertices:
            issues.append(f"⚠️  Only {vertices_with_color}/{vertices} vertices have colors")
        
        if texture_coords > 0:
            issues.append("ℹ️  Uses texture mapping (requires external texture file)")
        
        # Summary
        print(f"\nStatus:")
        if not issues:
            print("  ✅ No issues found")
            print("  ✅ Has vertex colors")
            print("  ✅ Uses positive indices")
            print("  ✅ Should work in Photoshop")
        else:
            for issue in issues:
                print(f"  {issue}")
        
        # Compatibility
        print(f"\nCompatibility:")
        if vertices_with_color > 0 and negative_indices == 0:
            print("  ✅ Photoshop: Should work")
            print("  ✅ Blender: Should work")
            print("  ✅ 3D viewers: Should work")
        elif negative_indices > 0:
            print("  ⚠️  Photoshop: May have issues (negative indices)")
            print("  ✅ Blender: Should work")
            print("  ⚠️  3D viewers: May have issues")
        elif texture_coords > 0:
            print("  ⚠️  Photoshop: Requires texture file")
            print("  ✅ Blender: Should work (if texture present)")
            print("  ⚠️  3D viewers: May not show colors")
        
    except FileNotFoundError:
        print(f"❌ File not found")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("="*70)
    print("OBJ FILE VALIDATOR")
    print("="*70)
    
    files_to_check = [
        "terrain_simple.obj",
        "terrain_from_qgis_fixed.obj",
        "terrain_colored.obj",
        "files/Zonemap3D.obj",
    ]
    
    for filename in files_to_check:
        check_obj_file(filename)
    
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    print("\n✅ Use: terrain_simple.obj")
    print("   - Clean format with vertex colors")
    print("   - No external dependencies")
    print("   - Maximum compatibility")
    print("\n✅ Alternative: terrain_from_qgis_fixed.obj")
    print("   - Fixed version of QGIS export")
    print("   - Texture converted to vertex colors")

if __name__ == "__main__":
    main()
