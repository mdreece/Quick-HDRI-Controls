# Quick HDRI Controls v1.5 for Blender

![Blender Version](https://img.shields.io/badge/Blender-4.2.0+-green.svg)
![Version](https://img.shields.io/badge/Version-0.9-blue.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

![image](https://github.com/user-attachments/assets/f34ccf54-7e65-4dcb-8173-7b43ba369ea8)


Quick HDRI Controls is a Blender addon that makes working with HDRIs simple and efficient. Switch environments, adjust lighting, and control rotations directly from your 3D viewport - no more digging through node editors!

![QHDRI Full](https://github.com/user-attachments/assets/01504b2e-3130-41be-a87b-1eed2b103dca)





## Features

- 🖼️ Preview and switch HDRIs directly in the viewport
- 🔄 Quick rotation controls for environment lighting
- 💡 Easy strength adjustment for background lighting
- 📁 Built-in file browser for your HDRI collection
- 🎯 One-click loading of environments
- ⚡ Streamlined workflow with minimal UI

## Installation

1. Download the latest release zip file

![Github_Download](https://github.com/user-attachments/assets/ec266f02-a1e1-4a8a-ae84-43ded0813717)


 - Click Code
 - Click Download ZIP

2. In Blender, go to Edit > Preferences > Add-ons
3. Click the drop down and click "Install" and select the downloaded zip
![BL Install](https://github.com/user-attachments/assets/a9ff17d3-c39c-43e1-94ce-615e2468b158)

5. Enable the addon by checking the box next to "3D View: Quick HDRI Controls"
![BL Enable](https://github.com/user-attachments/assets/568ecc23-6b9f-4bf9-b187-026ff2fe358c)


## Quick Start Guide

### First Time Setup

1. Open the addon preferences (Edit > Preferences > Add-ons > Quick HDRI Controls)

![BL Preference Full](https://github.com/user-attachments/assets/851f7ab2-1c82-44fb-9e68-9e539ba4ea07)

3. Set your HDRI folder by clicking the folder icon next to "HDRI Directory"

![BL Preference HDRI directory](https://github.com/user-attachments/assets/42ecdba8-43d0-4267-a542-096ab243024f)

3. Select which file types you want to use (HDR, EXR, PNG, JPG)

![BL Preference File Settings](https://github.com/user-attachments/assets/463e9a20-765b-4d38-86b6-3dab8f0cecd2)

4. Close the preferences

### Using the Addon

1. Look for "HDRI Controls" in your 3D viewport header (top bar)

![HDRI start](https://github.com/user-attachments/assets/3b7320bd-0bb2-487b-98c8-2e59ec2e7486)


2. Click it and then 'Initialize HDRI System'
3. You'll see three main sections:

![QHDRI Full](https://github.com/user-attachments/assets/8723a08b-0207-4113-92b2-08c325bf7dd2)




#### Folder Browser

![QHDRI folder browse](https://github.com/user-attachments/assets/3b40729b-7f12-4647-b6a2-5e52056eac90)

- Navigate through your HDRI folders
- Click folder names to enter them
- Use ".." to go back up

#### HDRI Selection

![QHDRI Select](https://github.com/user-attachments/assets/592c02f9-4029-4697-88b5-2705aa1b6737)

- See thumbnails of your HDRIs
- Click one to select it
- Hit "Load Selected HDRI" to use it

#### HDRI Settings

![QHDRI Settings](https://github.com/user-attachments/assets/281bd94b-ea2e-420a-b146-d9f2e7212f04)

- Adjust X, Y, Z rotation
- Control the lighting strength
- Quick reset buttons for both
  - Addon version
  - Quick access to preferences

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

![image](https://github.com/user-attachments/assets/f7afa023-cc64-44b6-9faf-852082643e6a)


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

![image](https://github.com/user-attachments/assets/3b7e297b-7208-43ac-9986-af65fb24452d)

3. If you are up to date, a message will prompt.
4. If there is a new version, you will be prompted if you want to download/update
   (You may have to remap your HDRI directory in preferences. Working on updating so there is no need)

## Requirements

- Tested on Blender 4.2.0 (could work on previous versions)
- A collection of HDRI files
- Enough RAM to handle HDRI textures

## Support

Need help? Found a bug? Have a suggestion?
- Open an issue on GitHub or direct message on instagram
- Check existing issues for solutions
- Include steps to reproduce any bugs

## Credits

Created by Dave Nectariad Rome
- [GitHub Profile](https://github.com/mdreece)
- [Project Repository](https://github.com/mdreece/Quick-HDRI-Controls)
