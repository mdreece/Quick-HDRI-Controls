# Quick HDRI Controls v2.4.6 for Blender

![Blender Version](https://img.shields.io/badge/Blender-4.3.0+-green.svg)
![Version](https://img.shields.io/badge/Version-2.4.6-blue.svg)

![image](https://github.com/user-attachments/assets/f34ccf54-7e65-4dcb-8173-7b43ba369ea8)

v2.0 Video Demonstration: https://youtu.be/YFAPNMnai0U

Quick HDRI Controls is a Blender addon that makes working with HDRIs simple and efficient. Switch environments, adjust lighting, and control rotations directly from your 3D viewport - no more digging through node editors!

![image](https://github.com/user-attachments/assets/def21442-bf51-4ba2-bbd9-59e1832e4237)






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

4. Enable the addon by checking the box next to "3D View: Quick HDRI Controls"
   
![BL Enable](https://github.com/user-attachments/assets/568ecc23-6b9f-4bf9-b187-026ff2fe358c)


## Quick Start Guide

### First Time Setup

1. Open the addon preferences (Edit > Preferences > Add-ons > Quick HDRI Controls)

![image](https://github.com/user-attachments/assets/5d0a283c-9381-4d63-960d-b79636a60c37)

2. Set your HDRI folder by clicking the folder icon next to "HDRI Directory"

![image](https://github.com/user-attachments/assets/38793fa1-bfd0-4a9a-9d04-3a943ee34582)

 - If this is not done, when attempting to use you will be prompted to set it anyway
   
![image](https://github.com/user-attachments/assets/2af89aa1-9333-4e4b-8abd-79dccd056116)
 - Open Preferences set to HDRI Directory
 - Open/Choose HDRI Directory directly

3. In 'Supported File Tyypes' select which file types you want to use (HDR, EXR, PNG, JPG)
(All are enabled by default)

![image](https://github.com/user-attachments/assets/2ce6fd31-adf5-40e8-abfe-3168cce47869)
(Preview limit is related to .png thumbnails for HDRIs that you can use to save on resources) 

4. Close the preferences

### Using the Addon

1. Look for "HDRI Controls" in your 3D viewport header (top bar)

![image](https://github.com/user-attachments/assets/8054b0e6-3a2c-4f36-9833-974d80fe42a6)

2. Click it and then 'Initialize HDRI System'
3. You'll be prompted with your HDRI folders/main directory in the "HDRI Browser" section
 - Click a folder to browse the HDRIs

![image](https://github.com/user-attachments/assets/9e08da51-b2d9-4bb8-a538-124ad9da2d1d)

4. Once a folder has been selected, 'HDRI Select' appears.

![image](https://github.com/user-attachments/assets/99006cff-9db7-48a2-8320-4863d483c171)

- Click the box to see thumbnails of your HDRIs
   (You can setup thumbnail previews using a .png that has the same name as the hdr file but ends with _thumb.png
      Add the .png thumbnails to the same directory as the hdr.)
  
![image](https://github.com/user-attachments/assets/abc869b0-f8d4-4285-a3d9-6b72a336f965)


- Click the preview window to show the HDRIs in the selected location, select your HDRI.
- Click "Load Selected HDRI" to use it
   - Click Reset to revert to previously selected HDRI

5. 'Settings' will appear once an HDRI has been loaded.

![image](https://github.com/user-attachments/assets/5eb1fdca-2103-4198-bd32-c5a0a72f10d5)

Buttons:
- Keep Rotation lock (keeps rotation changes between HDRI switching)
- Reset HDRI Rotation (resets all rotation options to 0.0)
- Reset HDRI Strength (resets HDRI strength to 1.0 or default option set in preferneces)
- HDRI Visibiliy (adjusts ray visibility of the selected HDRI)

Options:
-  X, Y, Z rotation ( + and - relates to rotation step size in Preferences)
- Control the lighting strength
  - Addon version
  - Quick access to preferences

 Full Dropdown Panel

![image](https://github.com/user-attachments/assets/5cd6a2c7-31ed-4875-b2e3-e9880f09b2ee)


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

## Keyboard Shortcut
Keyboard shortcut can be set for quickly pulling up the panel in the 3D viewport

Windows/Linux:

![QHDRIC_Shortcut](https://github.com/user-attachments/assets/2386ee2a-7904-42e4-92fb-05bf0d9c8e85)

MacOS (Intel, Apple Silicon has not been tested)

<img width="533" alt="Screenshot 2024-10-28 at 6 14 22 PM" src="https://github.com/user-attachments/assets/32e18476-9c7e-46b5-a583-8b34027db7ef">

 - Set you current shortcut combination
 - Consists of:
   
   Windows\Linux: Shift, Alt, Ctrl
   
   MacOS: Shift, Command, Option
   
 - A-Z key options
 - Confirm with OS or blender shortcuts to ensure no issues
   
 - BE SURE TO APPLY CHANGES IN PREFERENCES UI
 - When the key combination is pressed, the HDRI panel will appear where the cursor is

![image](https://github.com/user-attachments/assets/03b5816c-236f-4c94-b823-9daae277c078)



### Interface Settings
You can customize:
- Preview size
- Button scale
- Spacing scale
- Show Strength Slider
- Show Rotation Values

To access these options:
1. Go to Edit > Preferences > Add-ons
2. Find Quick HDRI Controls
3. Expand the preferences section

![image](https://github.com/user-attachments/assets/d0e42dc4-97bc-4b84-97ec-f8f39b3c4687)

### HDRI Settings

![image](https://github.com/user-attachments/assets/7a907fc4-d83e-4468-9924-5bf1aff142ef)

 - Keep Rotation options between HDRI changes
 - Maximum Strength value for lighting in scenes
 - Rotations step degree for when rotating HDRIs in increments




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
   
![image](https://github.com/user-attachments/assets/582a0099-5be8-4f99-bc92-d6df699a9751)

2. Click on 'Check for Updates'
 - If there are updates a message will prompt to update
   
![image](https://github.com/user-attachments/assets/a8a72360-8fe5-4050-adcf-4b694849611f)

 - If no updates are available, the following message will prompt
   
![Update to date](https://github.com/user-attachments/assets/663565f0-a41a-436b-b05a-d9fb7e9a1ed3)

3. Auto-Check Updates can be enabled

 (This feature checks for updates on startup of Blender)

 - If enabled/blender restarted, the following will prompt upon accessing HDRI Controls if there is a pending update
   
![Pending Update](https://github.com/user-attachments/assets/0405dd5c-5921-4d3e-bb13-6e052bdf23d3)
 


## Requirements

- Blender 4.2.0 (could work on previous versions)
- Windows 10, Windows 11, MacOS Sequoia, Linux
- A collection of HDRI files
- Enough RAM to handle HDRI textures

## Support

Need help? Found a bug? Have a suggestion?
- Open an issue on GitHub or direct message on instagram @montanadreece (https://www.instagram.com/montanadreece/)
- Check existing issues for solutions
- Include steps to reproduce any bugs

## Credits

Created by Dave Nectariad Rome
- [GitHub Profile](https://github.com/mdreece)
- [Project Repository](https://github.com/mdreece/Quick-HDRI-Controls)
