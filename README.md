# 3D Terrain Model Generator

Generate high-quality 3D terrain models (OBJ/STL) from DEM and zonemap data with proper UTM coordinates and color mapping.

## Features

- ✅ **Real UTM coordinates** - Preserves actual distances in meters
- ✅ **Correct orientation** - North/East aligned with source DEM
- ✅ **Color mapping** - Red-to-Green gradient or custom zone colors
- ✅ **Vertical exaggeration** - Adjustable for flat terrain visualization
- ✅ **High resolution** - Full DEM resolution preserved
- ✅ **Photoshop compatible** - Vertex colors embedded in OBJ
- ✅ **3D print ready** - Binary STL format included

## Quick Start

### Requirements

```bash
conda create -n gdal_env python=3.9
conda activate gdal_env
conda install -c conda-forge gdal scipy numpy
```

Or use the provided `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Usage

1. Place your DEM and zonemap GeoTIFF files in the directory
2. Edit `create_terrain_utm.py`:
   ```python
   DEM_FILE = "your_dem.tif"
   ZONE_FILE = "your_zonemap.tif"
   Z_SCALE = 20.0  # Adjust vertical exaggeration
   ```
3. Run:
   ```bash
   conda activate gdal_env
   python create_terrain_utm.py
   ```

## Output Files

- **terrain_utm.obj** - 3D model with vertex colors (for Photoshop)
- **terrain_utm.stl** - 3D model for 3D printing (no colors)

## Color Mapping

### Red-Green Gradient (Current)
- Dark pixels (0) → Red
- Bright pixels (255) → Green
- Smooth gradient in between

### Custom Zone Colors
Edit the `get_colors_gradient()` function to use discrete zone colors instead.

## Vertical Exaggeration

For flat terrain (< 1% slope), use higher Z_SCALE values:
- `Z_SCALE = 10.0` - Subtle
- `Z_SCALE = 20.0` - Balanced (recommended)
- `Z_SCALE = 40.0` - Dramatic

## Documentation

- **QUICK_REFERENCE.md** - One-page summary
- **COORDINATE_SYSTEMS.md** - Technical details about coordinate systems
- **WHY_IT_WAS_FLAT.md** - Explanation of vertical exaggeration
- **FINAL_SUMMARY.md** - Complete guide

## Examples

### Input
- DEM: 834 × 1654 pixels, 1m resolution, UTM coordinates
- Zonemap: Grayscale values 0-255

### Output
- 1,008,581 vertices with RGB colors
- 2,006,592 triangular faces
- Real-world scale: 833m × 1653m × 6.7m (with exaggeration)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this tool for academic or commercial purposes.

## Citation

If you use this tool in your research, please cite:

```
Heidari, R. (2025). 3D Terrain Model Generator. GitHub repository: https://github.com/roghiheidari/terrain-3d-generator
```

## Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check the documentation files for detailed information
- Ensure your DEM and zonemap files are valid GeoTIFF format

## Author

Roghayeh Heidari
- PhD Candidate, Computer Science
- University of Calgary
- Email: roghi1024@gmail.com
- GitHub: [@roghiheidari](https://github.com/roghiheidari)

## Acknowledgments

Developed for GIS researchers and 3D visualization workflows.

Made with ❤️ for the research community
