# 3D Terrain Model - Complete Guide

## 📁 Available Files

### ✅ RECOMMENDED: terrain_simple.obj (97 MB)
**Best for Photoshop and 3D printing**
- **1,008,581 vertices** with RGB vertex colors
- **2,006,592 faces**
- Clean, simple format with positive indices only
- Zonemap colors baked into vertices
- No external texture files needed
- Maximum compatibility

**How to use:**
1. Open Photoshop
2. **File → Open** → select `terrain_simple.obj`
3. Colors will display automatically

### ✅ ALTERNATIVE: terrain_from_qgis_fixed.obj (52 MB)
**Fixed version of your QGIS export**
- Converted texture to vertex colors
- Uses the texture from QGIS
- Positive indices for compatibility
- Ready for Photoshop

### ⚠️ terrain_colored.obj (201 MB)
**Has issues - includes bottom surface**
- Double the vertices (top + bottom surfaces)
- May cause errors in some viewers
- Use terrain_simple.obj instead

### ⚠️ files/Zonemap3D.obj (62 MB)
**Original QGIS export - has problems**
- Uses negative indices (causes errors)
- Requires external texture file
- Texture not properly applied in viewers
- **Problem shown in your screenshot**: White terrain with separate colored plane

## 🎨 Color Zones

Your zonemap defines 5 terrain zones:

| Zone | Color | RGB | Description |
|------|-------|-----|-------------|
| 0 | 🟠 Orange | (255, 140, 0) | Terrain type 1 |
| 1 | 🟡 Yellow | (255, 255, 0) | Terrain type 2 |
| 2 | 🟢 Green | (0, 200, 0) | Vegetation/type 3 |
| 3 | 🟠 Light Orange | (255, 165, 0) | Intermediate zone |
| 4 | 🟡 Yellow-Green | (200, 200, 0) | Mixed zone |

## 🔧 What Was Wrong with QGIS Export

The QGIS file had several issues:

1. **Negative indices**: Used negative vertex references (e.g., `f -297391/-297391/-297391`)
   - Valid in OBJ spec but causes errors in many viewers
   - Your screenshot shows this problem

2. **External texture dependency**: Required `Terrain_DEM_tile_material.jpg`
   - Texture wasn't being applied to the terrain mesh
   - Resulted in white/gray terrain with separate colored plane

3. **Complex structure**: Included normals and texture coordinates
   - More complex than needed
   - Harder for viewers to parse

## ✅ How I Fixed It

### Solution 1: terrain_simple.obj
- Read DEM and zonemap directly from source TIF files
- Sample zonemap colors for each vertex position
- Write vertices with RGB colors directly embedded
- Use only positive indices
- Simple, clean format

### Solution 2: terrain_from_qgis_fixed.obj
- Parsed your QGIS OBJ file
- Sampled the texture image at each vertex's UV coordinate
- Converted texture colors to vertex colors
- Converted negative indices to positive
- Removed texture dependency

## 📊 Technical Details

### Your Data
- **DEM**: cliped_DEMUTM_FIX.tif
  - Size: 834 × 1654 pixels
  - Elevation: 458.41 to 465.11 meters (6.7m range)
  - Valid pixels: 1,008,581 (73% of total)
  - NoData value: -32767 (properly filtered)

- **Zonemap**: zonemap.tif
  - Size: 80 × 164 pixels
  - Upscaled to match DEM resolution
  - 5 distinct zones (0-4)

### Model Settings
- **Vertical scale**: 0.3x (adjustable)
- **Coordinate range**: -1 to 1 (normalized)
- **Color format**: RGB vertex colors (0-1 range)

## 🖨️ For 3D Printing

Use `terrain_simple.stl` (100 MB)
- 2,006,592 triangles
- Binary STL format
- Import into any slicer (Cura, PrusaSlicer, etc.)

**Note**: STL files don't support colors, but the geometry is identical

## 🔄 Regenerating with Different Settings

Edit `create_simple_terrain.py`:

```python
# Line ~236
Z_SCALE = 0.3  # Change this for more/less vertical exaggeration
```

Then run:
```powershell
conda activate gdal_env
python create_simple_terrain.py
```

### Vertical Scale Examples
- `Z_SCALE = 0.1` - Very flat (subtle elevation)
- `Z_SCALE = 0.3` - Current setting (moderate)
- `Z_SCALE = 0.5` - More dramatic
- `Z_SCALE = 1.0` - Full elevation range

## ❓ Troubleshooting

### "Error opening file in Photoshop"
- Try `terrain_simple.obj` first
- Make sure you're using Photoshop CC or later
- Try: **3D → New 3D Layer from File** instead of File → Open

### "Colors not showing"
- Vertex colors require Photoshop CC 2014 or later
- Check that 3D features are enabled in Preferences
- Try opening in Blender to verify colors are present

### "File too large"
- Current files are full resolution (1M+ vertices)
- Edit script and change `DOWNSAMPLE = 2` for half resolution
- Or `DOWNSAMPLE = 4` for quarter resolution

### "Need different colors"
- Edit `ZONE_COLORS` dictionary in `create_simple_terrain.py`
- Change RGB values for each zone
- Regenerate the model

## 📝 Summary

**Use this file**: `terrain_simple.obj`

**Why**: 
- ✅ Proper vertex colors from zonemap
- ✅ Clean, compatible format
- ✅ No external dependencies
- ✅ Works in Photoshop
- ✅ Ready for 3D printing (use .stl version)

The QGIS export had structural issues (negative indices, external texture) that prevented proper display. The new files have colors baked directly into the vertices.
