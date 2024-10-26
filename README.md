# Quick HDRI Controls for Blender

![Blender Version](https://img.shields.io/badge/Blender-4.2.0+-green.svg)
![Version](https://img.shields.io/badge/Version-0.9-blue.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

Quick HDRI Controls is a Blender addon that makes working with HDRIs simple and efficient. Switch environments, adjust lighting, and control rotations directly from your 3D viewport - no more digging through node editors!

![image](https://github.com/user-attachments/assets/b5c29a71-963d-45da-a733-df24ce4e4a8a)



## Features

- 🖼️ Preview and switch HDRIs directly in the viewport
- 🔄 Quick rotation controls for environment lighting
- 💡 Easy strength adjustment for background lighting
- 📁 Built-in file browser for your HDRI collection
- 🎯 One-click loading of environments
- ⚡ Streamlined workflow with minimal UI

## Installation

1. Download the latest release zip file
2. In Blender, go to Edit > Preferences > Add-ons
3. Click "Install" and select the downloaded zip
4. Enable the addon by checking the box next to "3D View: Quick HDRI Controls"

## Quick Start Guide

### First Time Setup

1. Open the addon preferences (Edit > Preferences > Add-ons > Quick HDRI Controls)
2. Set your HDRI folder by clicking the folder icon next to "HDRI Directory"
![image](https://github.com/user-attachments/assets/f6899f91-a0aa-462c-b26f-8720187b4791)

3. Select which file types you want to use (HDR, EXR, PNG, JPG)
4. Close the preferences

### Using the Addon

1. Look for "HDRI Controls" in your 3D viewport header (top bar)
 ![image](https://github.com/user-attachments/assets/001ed482-c246-430a-b5d3-c7c652e41953)

3. Click it to open the controls panel
4. You'll see three main sections:

#### Folder Browser
- Navigate through your HDRI folders
- Click folder names to enter them
- Use ".." to go back up

#### HDRI Selection
- See thumbnails of your HDRIs
- Click one to select it
- Hit "Load Selected HDRI" to use it

#### HDRI Settings
- Adjust X, Y, Z rotation
- Control the lighting strength
- Quick reset buttons for both

## Tips & Tricks

### For Best Results
- Organize HDRIs into folders (Indoor, Outdoor, Studio, etc.)
- Use consistent naming for easier browsing
- Keep your most-used HDRIs in a favorites folder

### Quick Workflow
1. Open the HDRI Controls panel
2. Browse to your desired HDRI
3. Click to select and load
4. Adjust rotation and strength as needed
5. Use reset buttons if you need to start over

### Pro Tips
- Use the strength slider to fine-tune lighting intensity
- Rotate on the Z-axis to change light direction
- X and Y rotation help with reflection angles
- Reset buttons quickly restore default values

## Customization

### Panel Settings
You can customize:
- Panel width
- Preview size
- Button scale
- UI spacing
- Interface layout

To access these options:
1. Go to Edit > Preferences > Add-ons
2. Find Quick HDRI Controls
3. Expand the preferences section

## Troubleshooting

### Common Issues

**"HDRI Directory Not Set" Message**
- Open addon preferences
- Set your HDRI folder path

**No HDRIs Showing**
- Check that your files are supported types
- Verify the folder path is correct
- Make sure file types are enabled in preferences

**System Not Initialized**
- Click "Initialize HDRI System" button
- If issues persist, click "Repair HDRI System"

## Updates

Stay up to date:
1. Open addon preferences
2. Click "Check for Updates"
3. Restart Blender

## Requirements

- Blender 4.2.0 or newer
- A collection of HDRI files
- Enough RAM to handle HDRI textures

## Support

Need help? Found a bug? Have a suggestion?
- Open an issue on GitHub
- Check existing issues for solutions
- Include steps to reproduce any bugs

## Credits

Created by Dave Nectariad Rome
- [GitHub Profile](https://github.com/mdreece)
- [Project Repository](https://github.com/mdreece/Quick-HDRI-Controls)
