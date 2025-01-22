# Quick HDRI Controls v2.7.0 for Blender (Cycles & Octane)

![Blender Version](https://img.shields.io/badge/Blender-4.3.0-green.svg)
![Version](https://img.shields.io/badge/Version-2.7.0-blue.svg)

![image](https://github.com/user-attachments/assets/f34ccf54-7e65-4dcb-8173-7b43ba369ea8)

v2.5.3 Video Demonstration: [https://youtu.be/YFAPNMnai0U](https://youtu.be/tIpI3xYmims)

Quick HDRI Controls is a Blender addon that makes working with HDRIs simple and efficient. Switch environments, adjust lighting, and control rotations directly from your 3D viewport - no more digging through node editors!

![image](https://github.com/user-attachments/assets/2d3e23a9-5032-4835-9cf6-0ffefba74393)

# Table of Contents

1. [Installation](#installation)
2. [Quick Start Guide](#quick-start-guide)
   - [First Time Setup](#first-time-setup)
3. [Using the Addon](#using-the-addon)
   - [Proxies](#proxies-more-info-below-close-tab-for-better-performance)
   - [HDRI Metadata](#hdri-metadata)
4. [Full Dropdown Panel](#full-dropdown-panel)
5. [Updates](#updates)
   - [Backup Settings](#backup-settings)
6. [Preview Thumbnail Generation](#preview-thumbnail-generation)
   - [Processing Type](#processing-type)
   - [Scene Type Examples](#scene-type-examples-cube-monk-orbs)
7. [Proxy Settings](#proxy-settings)
   - [Cache Settings](#cache-settings)
   - [Advanced Settings](#advanced-settings)
   - [Batch Proxy Generation](#batch-proxy-generation)
8. [Render Engine](#render-engine)
9. [Keyboard Shortcut](#keyboard-shortcut)
10. [HDRI Settings](#hdri-settings)
11. [Tips & Tricks](#tips--tricks)
    - [For Best Results](#for-best-results)
    - [Quick Workflow](#quick-workflow)
    - [Pro Tips](#pro-tips)
12. [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
13. [Requirements](#requirements)
14. [Support](#support)
15. [Credits](#credits)


##
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



##
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

4. Close the preferences


##
## Using the Addon

1. Look for "HDRI Controls" in your 3D viewport header (top bar)

![image](https://github.com/user-attachments/assets/a1cd44f1-f46c-44ee-89bd-7ea8c9537b84)

2. Click it and then 'Initialize HDRI System'
 - Quick access to addon preferences
 - Version number display
   
![image](https://github.com/user-attachments/assets/768e9735-d1b1-4cb1-bdd7-f80091e87228)
![image](https://github.com/user-attachments/assets/06c27270-693f-4053-94ea-0775220d1522)

Depending on the your set render engine (both in blender and in addon preferences) you will be prompted to switch to the set Render Engine if you are not already.
 - IF set to Cycles, the View Transform changes to AgX (can be adjusted in panel)
 - IF set to Octane, the View Transform changes to  Raw (can be adjusted in panel)


     
3. You'll be prompted with your HDRI folders/main directory in the "HDRI Browser" section
 - Click a folder to browse the HDRIs

![image](https://github.com/user-attachments/assets/bf89338f-39f9-44d8-9028-3e256c37c8ba)

4. Once a folder has been selected, 'HDRI Select' appears.

![Screenshot 2024-12-13 181705](https://github.com/user-attachments/assets/b78a08f4-1d95-4696-a8fe-e69b5cd65b22)

![Screenshot 2024-12-13 181739](https://github.com/user-attachments/assets/30e1fc8e-9206-4611-984f-106fd93752f9)

- Click the box to see thumbnails of your HDRIs
- Click on the desired HDRI to load it to use it
- Once loaded, use navigation arrows to cycle through HDRs in the present folder.

![image](https://github.com/user-attachments/assets/f10988b1-7721-446e-a1e2-e079e0e2fb8a)
  
- Once more than one HDRI has been selected, a reset button will appear to reset to the previously selected HDRI

5. 'Settings' will appear once an HDRI has been loaded.

![image](https://github.com/user-attachments/assets/254e00b4-30d6-4faa-adf0-a535bb13745a)

Buttons:
- Keep Rotation lock (keeps rotation changes between HDRI switching)
- HDRI Visibiliy (adjusts ray visibility of the selected HDRI)

Options:
-  X, Y, Z rotation ( + and - relates to rotation step size in Preferences)
-  X, Y, Z rotation reset (resets rotation options to 0)
- Control the lighting strength
  - Quick access to preferences
  - Addon version
  - Delete World

### Proxies (more info below: close tab for better performance)

![image](https://github.com/user-attachments/assets/38062ade-0af4-47db-8a11-e0b9c3a24962)

 - Proxy Resolution Selection: Choose the desired resolution for your proxy of the selected HDRI
 - Proxy Mode: Choose between 'Viewport Only' or 'Both' (more info below)

### HDRI Metadata

![image](https://github.com/user-attachments/assets/f5c2c1f1-abd4-49d8-994e-ad951a6b3f6f)

 - Shows metadata related to the currently selected HDRI file (proxies included)


##
## Full Dropdown Panel

![image](https://github.com/user-attachments/assets/662023f7-51d8-41f2-a574-f625706f7f3d)



##
## Updates

Stay up to date:
   
![image](https://github.com/user-attachments/assets/f97eae56-54d3-43d9-bb2b-d8f2df973485)

Click on 'Check Now' to see if there are any pending updates.
 - If there are updates a message will prompt to update
 - Click on 'Revert to Previous version' to do what the button says (If no backup a message will prompt. Backup happens before updates install)
   
![image](https://github.com/user-attachments/assets/a8a72360-8fe5-4050-adcf-4b694849611f)

 - If no updates are available, the following message will prompt
   
![Update to date](https://github.com/user-attachments/assets/663565f0-a41a-436b-b05a-d9fb7e9a1ed3)

3. Auto-Check Updates can be enabled

 (This feature checks for updates on startup of Blender)

 - If enabled/blender restarted, the following will prompt upon accessing HDRI Controls if there is a pending update
   
![Pending Update](https://github.com/user-attachments/assets/0405dd5c-5921-4d3e-bb13-6e052bdf23d3)

 - Upon Blender restart, the changelog entry will show NewFeatures, Fixes and Known Issues

![image](https://github.com/user-attachments/assets/35f4b808-c425-4089-a7e1-6219da4a852b)


### Backup Settings:

![image](https://github.com/user-attachments/assets/6663eed7-8654-44dc-900d-6d0074ed3694)

Enable backups for when updating to new versions
 - Max Backup Files: Maximum number of saved previous addon versions



##
## Preview Thumbnail Generation
You can setup thumbnail previews using a .png that has the same name as the hdr file but ends with _thumb.png
Add the .png thumbnails to the same directory as the hdr.

![ScreenRecording_01-03-2025 15-02-29_1](https://github.com/user-attachments/assets/86ecacc2-b239-4169-8d9a-32d2cb359b58)

### Processing Type:

 - Single File: Select a single .hdr or .exr file from you file browser and create a _thumb.png for it.
 - Batch Process: Select a folder with .hdr and/or .exr files and create _thumb.png for each.
 - Full Batch: Creates _thumb.png for all .hdr and .exr files in the main HDRI directory.
   (For both the _thumb.png is in the same folder location as the chosen .hdr or .exr)

 User Source selection to choose you HDRI, folder of HDRIs, or batch process all.
 - Choose you desired resolution %
 - Choose number of samples
 - Choose Render Device
 - Select scene type: Orbs (orbs preview), Monk (suzanne), Cube (the default twins)
 - GENERATE

### Scene Type Examples: Orbs-3, Orbs-4, Teapot

![image](https://github.com/user-attachments/assets/3670e94d-598a-47d7-990b-1004c41cd3a9)


Example of original and _thumb.png instance:

![image](https://github.com/user-attachments/assets/5e0789da-7f73-4ad3-aed4-f6e905646c28)



##
## Proxy Settings

![image](https://github.com/user-attachments/assets/04767c24-dc3b-401b-be5d-ac6f5178c2f6)

Default Resolution: The desired default resolution for proxies (if set to ORIGINAL, no proxies will be created and full resolution HDRI will be used - options = 1K, 2K, 4K, Original)

Default Application: Options are 'Viewport Only' (default) and 'Both'

- Viewport Only: The selected HDRI proxy will be used for viewport rendering. When a render begins (single frame or animation) the full resolution HDRI will be loaded in. Once completed the proxy will be    reloaded for viewport rendering.
- Both: The selected HDRI proxy will be used for both viewport and final rendering.
   
### Cache Settings

 - Cache Size Limit: Limits the amount of space that proxy files can take up (in MB)
 - Clear Proxy Cache: Will clear/delete all proxy files and folders for HDRIs

### Advanced Settings

 - More than likely these will not need to be adjusted. Compression using ZIP works well in both MacOS and Windows. The format option is for you to set the proxies to be HDR or EXR formats

### Batch Proxy Generation

![ScreenRecording_01-03-2025 15-02-29_1 2](https://github.com/user-attachments/assets/c262cce4-6b77-48f4-8ec7-08a037f4579b)

 - Generate Proxies: This process will create proxies for the chosen folder directory
 - Full Batch Process: This will create proxies for all folders and subfolders within the set main HDRI directory



##
## Render Engine

Select your render engine for compatibility (cycles is set by default)

![image](https://github.com/user-attachments/assets/3d7ca2dd-61b2-4817-bf66-08b591968962)

 - Select desired engine
    - Cycles: ![image](https://github.com/user-attachments/assets/924e7ef0-121f-48c6-a8d0-946b64a3ed24)

    - Octane: ![image](https://github.com/user-attachments/assets/adf19051-eb2a-4d48-bd31-99ec0dd6afc4)

 - Click 'Apply Render Engine'
 - Restart Blender



##
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

![image](https://github.com/user-attachments/assets/da92f557-1df0-4666-934e-17af4907438c)

Keyboard Shortcut Conflicts

![image](https://github.com/user-attachments/assets/3ec991ee-c3e6-4edf-be86-c33b9a173840)

 - Conflicts will show in dropdown menu.
 - Even if there is a conflict, from time to time it can work since we are in the 3dviewport.


##
## HDRI Settings

![image](https://github.com/user-attachments/assets/50a5d22b-4346-4525-a88e-241b4c7b1d24)

 - Keep Rotation options between HDRI changes
 - Maximum Strength value for lighting in scenes
 - Rotations step degree for when rotating HDRIs in increments
 - Supported File Types" explained above


##
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


##
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

##
## Requirements

- Blender 4.3.0 (could work on previous versions)
- Works with Cycles and Octane Render Engines only
- Windows 10, Windows 11, MacOS Sequoia(ignore error on installation), Linux
- A collection of HDRI files
- Enough RAM to handle HDRI textures

##
## Support

Need help? Found a bug? Have a suggestion?
- Open an issue on GitHub or direct message on instagram @montanadreece (https://www.instagram.com/montanadreece/)
- Check existing issues for solutions
- Include steps to reproduce any bugs

##
## Credits

Created by Dave Nectariad Rome
- [GitHub Profile](https://github.com/mdreece)
- [Project Repository](https://github.com/mdreece/Quick-HDRI-Controls)
