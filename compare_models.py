"""
Compare different OBJ models to understand coordinate differences
"""

def analyze_obj(filename, max_lines=100000):
    """Analyze OBJ file coordinates"""
    print(f"\n{'='*70}")
    print(f"Analyzing: {filename}")
    print('='*70)
    
    try:
        vertices = []
        
        with open(filename, 'r') as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                
                line = line.strip()
                if line.startswith('v '):
                    parts = line.split()
                    if len(parts) >= 4:
                        x = float(parts[1])
                        y = float(parts[2])
                        z = float(parts[3])
                        vertices.append((x, y, z))
        
        if not vertices:
            print("No vertices found")
            return
        
        # Calculate statistics
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        zs = [v[2] for v in vertices]
        
        print(f"\nVertices analyzed: {len(vertices):,}")
        
        print(f"\nX-axis (East-West):")
        print(f"  Min: {min(xs):.3f}")
        print(f"  Max: {max(xs):.3f}")
        print(f"  Range: {max(xs) - min(xs):.3f}")
        print(f"  Center: {(min(xs) + max(xs))/2:.3f}")
        
        print(f"\nY-axis (North-South):")
        print(f"  Min: {min(ys):.3f}")
        print(f"  Max: {max(ys):.3f}")
        print(f"  Range: {max(ys) - min(ys):.3f}")
        print(f"  Center: {(min(ys) + max(ys))/2:.3f}")
        
        print(f"\nZ-axis (Elevation):")
        print(f"  Min: {min(zs):.3f}")
        print(f"  Max: {max(zs):.3f}")
        print(f"  Range: {max(zs) - min(zs):.3f}")
        print(f"  Center: {(min(zs) + max(zs))/2:.3f}")
        
        # Aspect ratio
        x_range = max(xs) - min(xs)
        y_range = max(ys) - min(ys)
        z_range = max(zs) - min(zs)
        
        print(f"\nAspect Ratio:")
        print(f"  X:Y = 1:{y_range/x_range:.2f}")
        print(f"  X:Z = 1:{z_range/x_range:.2f}")
        print(f"  Y:Z = 1:{z_range/y_range:.2f}")
        
        # Interpretation
        print(f"\nInterpretation:")
        if abs(min(xs)) < 10 and abs(max(xs)) < 10:
            print("  ✓ Normalized coordinates (range ~-1 to 1)")
        elif abs(min(xs)) > 100000:
            print("  ✓ UTM coordinates (large values)")
        elif abs(min(xs)) > 100:
            print("  ✓ UTM coordinates (centered at origin)")
        
        if z_range < 10:
            print(f"  ⚠ Very flat terrain (Z range only {z_range:.2f})")
            print(f"    Consider Z-scale of {100/z_range:.1f}x for better visualization")
        
    except FileNotFoundError:
        print("❌ File not found")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("="*70)
    print("3D MODEL COORDINATE COMPARISON")
    print("="*70)
    
    print("\n📊 Comparing coordinate systems...")
    
    # Analyze different versions
    analyze_obj("terrain_simple.obj", max_lines=50000)
    analyze_obj("terrain_utm.obj", max_lines=50000)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    print("\n📦 terrain_simple.obj:")
    print("   - Normalized coordinates (-1 to 1)")
    print("   - Compact and easy to view")
    print("   - Loses real-world scale")
    print("   - Generic orientation")
    
    print("\n🌍 terrain_utm.obj:")
    print("   - Real UTM coordinates (meters)")
    print("   - Preserves actual distances")
    print("   - Correct North/East orientation")
    print("   - Matches original DEM")
    
    print("\n💡 Recommendation:")
    print("   Use terrain_utm.obj for accurate work")
    print("   Use terrain_simple.obj for quick viewing")
    
    print("\n⚠️  Note:")
    print("   Your terrain is very flat (6.7m over 1653m)")
    print("   Consider increasing Z_SCALE to 5-10x")
    print("   Edit create_terrain_utm.py line 254")

if __name__ == "__main__":
    main()
