# Quick HDRI Controls

![Blender Version](https://img.shields.io/badge/Blender-4.2.0+-blue.svg)
![Version](https://img.shields.io/badge/Version-0.8-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A Blender addon for quickly managing and adjusting HDRI environments. Streamline your HDRI workflow with an intuitive interface for browsing, loading, and adjusting environment lighting.

## Features

- 🖼️ Visual HDRI browser with thumbnails
- 📂 Directory navigation system
- 🔄 Quick rotation controls
- 💡 Lighting strength adjustment
- 🎯 One-click HDRI loading
- ⚡ Popup browser for quick access

## Installation

1. Download the latest release from the [releases page](https://github.com/mdreece/Quick-HDRI-Controls/releases)
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click `Install...` and select the downloaded `.py` file
4. Enable the addon by checking the box next to `3D View: Quick HDRI Controls`

## Quick Start

1. Set your HDRI directory in the addon preferences
2. Access controls via `3D Viewport header > HDRI Controls`
3. Click `Browse HDRIs` to open the HDRI browser
4. Select and load your desired HDRI

## Usage Guide

### Initial Setup

1. **Configure HDRI Directory**
   - Open addon preferences
   - Set the directory containing your HDRI files
   - Select which file types to include (.hdr, .exr, .png, .jpg)

2. **Access Controls**
   ```
   3D Viewport Header > HDRI Controls
   ```

### Basic Operations

#### Loading HDRIs
1. Click `Browse HDRIs` in the panel
2. Navigate to desired folder
3. Select HDRI from thumbnails
4. Click `Load Selected HDRI`

#### Adjusting Rotation
- **X°**: Horizontal rotation
- **Y°**: Vertical tilt
- **Z°**: Roll/twist
- Use reset button (↺) to zero all rotations

#### Managing Strength
- Adjust slider for HDRI intensity
- Values < 1.0: Decrease intensity
- Values > 1.0: Increase intensity
- Reset button returns to 1.0

## Configuration

### File Settings
```
✓ HDR  Files (.hdr)
✓ EXR  Files (.exr)
✓ PNG  Files (.png)
✓ JPEG Files (.jpg, .jpeg)
```

### Layout Settings
| Setting | Description | Default |
|---------|-------------|---------|
| Panel Width | Overall panel size | 10 |
| Preview Size | Thumbnail dimensions | 8 |
| Button Scale | UI button sizing | 1.0 |
| Grid Columns | Thumbnail grid layout | 3 |

### Interface Settings
| Setting | Description | Range |
|---------|-------------|-------|
| Strength Max | Maximum intensity | 1.0 - 10.0 |
| Rotation Increment | Rotation precision | 0.1° - 45° |

## Troubleshooting

### Common Issues

#### HDRI Directory Not Set
```
Solution: Open preferences and set valid HDRI directory
```

#### HDRIs Not Displaying
- Verify file types are enabled in preferences
- Check file permissions
- Confirm directory path is correct

#### System Initialization
If "Initialize HDRI System" appears:
1. Click to setup nodes
2. Use "Repair HDRI System" if issues persist

## Updates

1. Click `Check for Updates` in preferences
2. Restart Blender after update completion

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the Blender community for feedback and testing
- HDRI haven for sample HDRIs used in testing

## Support

- 📫 Report issues via [GitHub Issues](https://github.com/mdreece/Quick-HDRI-Controls/issues)
- 💬 Join discussions in [Discussions](https://github.com/mdreece/Quick-HDRI-Controls/discussions)

---
Made with ❤️ for the Blender Community
