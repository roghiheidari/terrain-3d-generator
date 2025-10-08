# Understanding Coordinate Systems in Your 3D Models

## 📊 Your Data

**DEM (cliped_DEMUTM_FIX.tif)**
- **UTM Coordinates**: 370513 to 371346 East, 5535801 to 5537454 North
- **Real dimensions**: 833 × 1653 meters
- **Pixel resolution**: 1 meter per pixel
- **Elevation**: 458.41 to 465.11 meters (6.7m range)

## 🗂️ Available Files - Comparison

### 1️⃣ terrain_simple.obj (Normalized Coordinates)
**What it does:**
- Normalizes X,Y to range -1 to 1
- Makes model compact and easy to view
- Loses real-world scale

**Coordinates:**
- X: -1.0 to 1.0 (represents 833m)
- Y: -1.0 to 1.0 (represents 1653m)
- Z: 0 to 0.3 (scaled elevation)

**Use when:**
- ✅ You want easy viewing in 3D software
- ✅ You don't need real measurements
- ✅ You want a compact model

### 2️⃣ terrain_utm.obj (Real UTM Coordinates) ⭐ NEW
**What it does:**
- Preserves actual UTM coordinates
- Real distances in meters
- Centered at origin for easier viewing

**Coordinates:**
- X: -416.5 to 416.5 meters (centered, real scale)
- Y: -826.5 to 826.5 meters (centered, real scale)
- Z: -3.35 to 3.35 meters (real elevation, centered)

**Use when:**
- ✅ You need accurate measurements
- ✅ You want real-world scale
- ✅ You need to match other UTM data
- ✅ You're doing GIS analysis

## 🔄 Orientation Differences

### Why They Look Different

**terrain_simple.obj:**
- Array indices directly mapped to coordinates
- Y-axis might appear inverted depending on viewer
- Generic orientation

**terrain_utm.obj:**
- Follows UTM convention
- X = East direction →
- Y = North direction ↑
- Z = Elevation ↑
- Matches your original DEM orientation

### Image Coordinate Systems

**Raster/Image coordinates** (how data is stored):
```
(0,0) ────────► X (columns)
  │
  │
  ▼
  Y (rows)
```

**UTM/Geographic coordinates** (real world):
```
      ▲ North (Y)
      │
      │
      └────────► East (X)
```

**OBJ 3D coordinates**:
```
      ▲ Y (up in 3D space)
      │
      │
      └────────► X
     ╱
    ╱
   Z
```

## 📏 Scale Comparison

| Aspect | terrain_simple.obj | terrain_utm.obj |
|--------|-------------------|-----------------|
| **X range** | 2 units (-1 to 1) | 833 meters |
| **Y range** | 2 units (-1 to 1) | 1653 meters |
| **Z range** | 0.3 units | 6.7 meters |
| **1 unit =** | ~416 meters | 1 meter |
| **Aspect ratio** | Distorted | Correct (1:2) |

## 🎯 Which File to Use?

### Use terrain_utm.obj when:
- ✅ You need **real measurements**
- ✅ You're doing **GIS work**
- ✅ You need to **match other datasets**
- ✅ You want **correct aspect ratio**
- ✅ You need **proper orientation** (North/East)

### Use terrain_simple.obj when:
- ✅ Just for **visualization**
- ✅ Want **compact file** size (same size but easier to work with)
- ✅ Don't care about **real-world scale**
- ✅ Want **easier viewing** in simple 3D viewers

## ⚙️ Adjusting Vertical Exaggeration

Your terrain is very flat (6.7m elevation change over 1653m distance = 0.4% slope).

### For terrain_utm.obj:

Edit `create_terrain_utm.py` line 254:
```python
Z_SCALE = 5.0  # Change this
```

Recommendations:
- `Z_SCALE = 1.0` - Real scale (very flat, hard to see detail)
- `Z_SCALE = 5.0` - 5x exaggeration (good for visualization)
- `Z_SCALE = 10.0` - 10x exaggeration (dramatic)

### For terrain_simple.obj:

Edit `create_simple_terrain.py` line 236:
```python
Z_SCALE = 0.3  # Currently 0.3
```

Since this is normalized:
- `Z_SCALE = 0.3` - Current (subtle)
- `Z_SCALE = 0.5` - More visible
- `Z_SCALE = 1.0` - Match X/Y range

## 🔍 Technical Details

### Coordinate Transformation

**terrain_simple.obj:**
```python
x_normalized = (pixel_x / width) * 2 - 1
y_normalized = (pixel_y / height) * 2 - 1
z_normalized = (elevation - min) / (max - min) * z_scale
```

**terrain_utm.obj:**
```python
x_utm = origin_x + pixel_x * pixel_width - center_x
y_utm = origin_y + pixel_y * pixel_height - center_y
z_utm = (elevation - center_z) * z_scale
```

### Why Center?

Both files center the model at (0, 0, 0) because:
- ✅ Easier to rotate/view in 3D software
- ✅ Avoids large coordinate values
- ✅ Better for rendering

The centering doesn't affect:
- ❌ Relative distances
- ❌ Aspect ratio
- ❌ Orientation

## 📝 Summary

**For Photoshop 3D visualization**: Either file works, but `terrain_utm.obj` has correct aspect ratio

**For 3D printing**: Use `terrain_utm.stl` with appropriate Z-scale (5-10x recommended)

**For GIS/measurement**: Use `terrain_utm.obj` with Z_SCALE = 1.0

**Current issue**: Your terrain is very flat (0.4% slope), so you'll want to increase Z_SCALE for better visualization!
