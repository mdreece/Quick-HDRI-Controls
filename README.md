# Quick HDRI Controls v2.5.4 for Blender

![Blender Version](https://img.shields.io/badge/Blender-4.3.0-green.svg)
![Version](https://img.shields.io/badge/Version-2.5.4-blue.svg)

![image](https://github.com/user-attachments/assets/f34ccf54-7e65-4dcb-8173-7b43ba369ea8)

v2.5.3 Video Demonstration: [https://youtu.be/YFAPNMnai0U](https://youtu.be/tIpI3xYmims)

Quick HDRI Controls is a Blender addon that makes working with HDRIs simple and efficient. Switch environments, adjust lighting, and control rotations directly from your 3D viewport - no more digging through node editors!

![image](https://github.com/user-attachments/assets/bfb0a8bc-b3ad-4bba-b622-d16943a6a3d1)


## Features

- 🖼️ Preview and switch HDRIs directly in the viewport
- 🔄 Quick rotation controls for environment lighting
- 💡 Easy strength adjustment for background lighting
- 📁 Built-in file browser for your HDRI collection
- 🎯 One-click loading of environments
- ⚡ Streamlined workflow with minimal UI and automatic updates

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

![image](https://github.com/user-attachments/assets/b977a654-6bf7-4ccb-9d6b-1ef5638119f2)

2. Set your HDRI folder by clicking the folder icon next to "HDRI Directory"

![image](https://github.com/user-attachments/assets/38793fa1-bfd0-4a9a-9d04-3a943ee34582)

 - If this is not done, when attempting to use you will be prompted to set it anyway
   
![image](https://github.com/user-attachments/assets/2af89aa1-9333-4e4b-8abd-79dccd056116)
 - Open Preferences set to HDRI Directory
 - Open/Choose HDRI Directory directly

3. In 'HDRI Settings' select which file types you want to use (HDR, EXR, PNG, JPG)
(All are enabled by default)

![image](https://github.com/user-attachments/assets/64f7d509-f9cb-4bc7-978c-693b7f0b5417)

(Preview limit is related to .png thumbnails for HDRIs that you can use to save on resources) 

4. Close the preferences

### Using the Addon

1. Look for "HDRI Controls" in your 3D viewport header (top bar)

![image](https://github.com/user-attachments/assets/8054b0e6-3a2c-4f36-9833-974d80fe42a6)

2. Click it and then 'Initialize HDRI System'
3. You'll be prompted with your HDRI folders/main directory in the "HDRI Browser" section
 - Click a folder to browse the HDRIs

![image](https://github.com/user-attachments/assets/bb644a5b-dee0-4516-941a-b9b0b1a63e4f)

4. Once a folder has been selected, 'HDRI Select' appears.

![Screenshot 2024-12-13 181705](https://github.com/user-attachments/assets/b78a08f4-1d95-4696-a8fe-e69b5cd65b22)

![Screenshot 2024-12-13 181739](https://github.com/user-attachments/assets/30e1fc8e-9206-4611-984f-106fd93752f9)

- Click the box to see thumbnails of your HDRIs
- Click on the desired HDRI to load it to use it
   - Click Reset to revert to previously selected HDRI
- Once loaded, use navigation arrows to cycle through HDRs in the present folder.

5. 'Settings' will appear once an HDRI has been loaded.

![image](https://github.com/user-attachments/assets/025a3773-b03e-45eb-95c7-64e86edd76b1)

Buttons:
- Keep Rotation lock (keeps rotation changes between HDRI switching)
- Reset HDRI Rotation (resets all rotation options to 0.0)
- Reset HDRI Strength (resets HDRI strength to 1.0 or default option set in preferneces)
- HDRI Visibiliy (adjusts ray visibility of the selected HDRI)

Options:
-  X, Y, Z rotation ( + and - relates to rotation step size in Preferences)
- Control the lighting strength
  - Quick access to preferences
  - Addon version
  - Delete World

#Proxies (more info below: close tab for better performance)

![image](https://github.com/user-attachments/assets/e154145c-75f7-4e69-ba14-7eb0e16ae32d)

Proxy Resolution Selection: Choose the desired resolution for your proxy of the selected HDRI
Proxy Mode: Choose between 'Viewport Only' or 'Both' (more info below)


 Full Dropdown Panel

![image](https://github.com/user-attachments/assets/b196d0b3-a2fc-4406-a47f-a34606697763)

## Preview Thumbnail Generation
You can setup thumbnail previews using a .png that has the same name as the hdr file but ends with _thumb.png
Add the .png thumbnails to the same directory as the hdr.
  
![image](https://github.com/user-attachments/assets/abc869b0-f8d4-4285-a3d9-6b72a336f965)

![image](https://github.com/user-attachments/assets/88460dba-c484-4bd2-b778-577924bbb4b8)

Processing Type:

 Single File: Select a single .hdr or .exr file from you file browser and create a _thumb.png for it.

 Batch PRocess: Select a folder with .hdr and/or .exr files and create _thumb.png for each.

 (For both the _thumb.png is in the same folder location as the chosen .hdr or .exr)

 User Source selection to choose you HDR or folder of HDRs
 - Choose you desired resolution %
 - Choose number of samples
 - GENERATE

Example of original and _thumb.png instance:

![image](https://github.com/user-attachments/assets/5e0789da-7f73-4ad3-aed4-f6e905646c28)

## Proxy Settings

![image](https://github.com/user-attachments/assets/d13e9918-c338-4f0e-aba3-ef2591f73897)

Default Resolution: The desired default resolution for proxies (if set to ORIGINAL, no proxies will be created and full resolution HDRI will be used - options = 1K, 2K, 4K, Original)
Default Application: Options are 'Viewport Only' (default) and 'Both'
        Viewport Only: The selected HDRI proxy will be used for viewport rendering. When a render begins (single frame or animation) the full resolution HDRI will be loaded in. Once completed the proxy will be    reloaded for viewport rendering.
        Both: The selected HDRI proxy will be used for both viewport and final rendering.
#Cache Settings
Cache Size Limit: Limits the amount of space that proxy files can take up (in MB)
Clear Proxy Cache: Will clear/delete all proxy files and folders for HDRIs
#Advanced Settings: More than likely these will not need to be adjusted. Compression using ZIP works well in both MacOS and Windows. The format option is for you to set the proxies to be HDR or EXR formats



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
 - BE SURE TO APPLY CHANGES IN PREFERENCES UI
 - When the key combination is pressed, the HDRI panel will appear where the cursor is

![image](https://github.com/user-attachments/assets/ee5479f0-7324-48c9-9127-5225903c8cd7)

Keyboard Shortcut Conflicts

![image](https://github.com/user-attachments/assets/3ec991ee-c3e6-4edf-be86-c33b9a173840)

 - Conflicts will show in dropdown menu.
 - Even if there is a conflict, from time to time it can work since we are in the 3dviewport.




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

![image](https://github.com/user-attachments/assets/50a5d22b-4346-4525-a88e-241b4c7b1d24)

 - Keep Rotation options between HDRI changes
 - Maximum Strength value for lighting in scenes
 - Rotations step degree for when rotating HDRIs in increments
 - Supported File Types" explained above




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

2. Click on 'Check Now'
 - If there are updates a message will prompt to update
   
![image](https://github.com/user-attachments/assets/a8a72360-8fe5-4050-adcf-4b694849611f)

 - If no updates are available, the following message will prompt
   
![Update to date](https://github.com/user-attachments/assets/663565f0-a41a-436b-b05a-d9fb7e9a1ed3)

3. Auto-Check Updates can be enabled

 (This feature checks for updates on startup of Blender)

 - If enabled/blender restarted, the following will prompt upon accessing HDRI Controls if there is a pending update
   
![Pending Update](https://github.com/user-attachments/assets/0405dd5c-5921-4d3e-bb13-6e052bdf23d3)
 


## Requirements

- Blender 4.3.0 (could work on previous versions)
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
