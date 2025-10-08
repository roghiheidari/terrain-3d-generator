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

The tool supports flexible color mapping:

### Red-Green Gradient
- Maps grayscale values to a continuous color gradient
- Dark pixels (low values) → Red
- Bright pixels (high values) → Green
- Smooth transitions for continuous data

### Custom Zone Colors
Modify the `get_colors_gradient()` function to implement:
- Discrete zone-based coloring
- Custom color palettes
- Multi-band color schemes

## Vertical Exaggeration

Adjust the `Z_SCALE` parameter to control terrain relief:
- `Z_SCALE = 1.0` - Real-world scale
- `Z_SCALE = 10.0` - 10x exaggeration
- `Z_SCALE = 20.0` - 20x exaggeration
- Higher values recommended for flat terrain visualization

## Technical Specifications

### Input Requirements
- DEM: GeoTIFF format with elevation data
- Zonemap: GeoTIFF format with classification or continuous values
- Coordinate system: UTM or any projected coordinate system

### Output Formats
- **OBJ**: Wavefront format with vertex colors
- **STL**: Binary STL for 3D printing
- Preserves real-world coordinates and scale

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
- Ensure your DEM and zonemap files are valid GeoTIFF format
- Verify GDAL installation and dependencies

## Author

Roghayeh Heidari
- PhD Candidate, Computer Science
- University of Calgary
- GitHub: [@roghiheidari](https://github.com/roghiheidari)

## Acknowledgments

Developed for GIS researchers and 3D visualization workflows.

Made with ❤️ for the research community
