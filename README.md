# Quick HDRI Controls | Cycles | Octane | V-Ray | v2.8.8
![Blender Version](https://img.shields.io/badge/Blender-4.0.0-green.svg)
![QHDRIC Version](https://img.shields.io/badge/QHDRIC-2.8.8-blue.svg)

### !!! RESTART BLENDER AT LEAST TWICE FOR v2.8.8 !!! ###
### !!! THIS PROCESS WILL REMAIN UNTIL v3.0.0 (AT THE LATEST) TO ENSURE THAT USERS GET THE SPLIT INSTANCE DUE TO RECENT FULL REWRITE OF ADDON !!! ###
### !!! V-Ray only tested up to 4.2.0 BETA | Octane only tested up to 4.3.0 !!! ###

![image](https://github.com/user-attachments/assets/f34ccf54-7e65-4dcb-8173-7b43ba369ea8)

v2.7.0 Video Demonstration: https://youtu.be/J7YdZQ2oxQA?si=_VRiLHIhQbZ1yVK4

![Banner3](https://github.com/user-attachments/assets/ae37d669-eaca-4836-bf9b-cef0103f51fe)

# Table of Contents

- [Installation](#installation)
- [Quick Start Guide](#quick-start-guide)
  - [First Time Setup](#first-time-setup)
- [Using the Addon](#using-the-addon)
  - [Proxies](#proxies-more-info-below-close-tab-for-better-performance)
- [Full Dropdown Panel](#full-dropdown-panel)
- [Updates](#updates)
  - [Backup Settings](#backup-settings)
  - [Documentation & Resources](#documentation--resources)
- [Preview Thumbnail Generation](#preview-thumbnail-generation)
  - [Processing Type](#processing-type)
  - [Scene Type Examples](#scene-type-examples-orbs-3-orbs-4-teapot)
- [Proxy Settings](#proxy-settings)
  - [Cache Settings](#cache-settings)
  - [Batch Proxy Generation](#batch-proxy-generation)
- [Keyboard Shortcut](#keyboard-shortcut)
- [HDRI Settings](#hdri-settings)
- [Render Engine Specifics](#render-engine-specifics)
  - [Cycles](#cycles)
  - [Octane](#octane)
  - [V-Ray](#v-ray)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
- [Requirements](#requirements)
- [Support](#support)
- [Credits](#credits)


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

![image](https://github.com/user-attachments/assets/41958f5e-cdc0-4476-829c-9a1c27f09100)

2. Perform the following:
   
![image](https://github.com/user-attachments/assets/c88d2dd1-8b12-4376-a383-2b3a4651a8f9)

    - Set your HDRI folder by clicking the folder icon next to "HDRI Directory".
    - Select your desired Render Engine and Apply '+'. (Cycles by default, but supports Cycles, V-Ray and Octane. Blender will need to be restarted after changing and applying.)
    
![image](https://github.com/user-attachments/assets/1bcb5854-b0e9-4b2d-9bfd-c5cd8b7c63a7)

- If this is not done, when attempting to use you will be prompted to set it anyway

![Screenshot_20250510_134935](https://github.com/user-attachments/assets/1c04d8fa-292e-4f9a-88f9-8ace40584f16)

 - Open Preferences set to HDRI Directory
 - Open/Choose HDRI Directory directly

3. In 'HDRI Settings' select which file types you want to use (HDR, EXR, PNG, JPG)
(All are enabled by default)

![Screenshot_20250510_135103](https://github.com/user-attachments/assets/1cc32d62-0fa4-41b2-b978-652c6313ec3d)

4. Close the preferences


##
## Using the Addon

1. Look for "HDRI Controls" in your 3D viewport header (top bar)
   
![Screenshot_20250510_142404](https://github.com/user-attachments/assets/88377152-0d50-40dc-a10e-e62d203bd4f8)

Click it and then 'Initialize HDRI System'
 - IF set to Cycles, the View Transform changes to AgX (can be adjusted in panel)
 - IF set to Octane, the View Transform changes to Raw (can be adjusted in panel)
 - IF set to V-Ray, the View Transform changes to Standard (can be adjusted in panel)

   
2. You'll be prompted with your HDRI folders/main directory in the "HDRI Browser" section
   
![image](https://github.com/user-attachments/assets/c2b6f039-16ca-4cc5-9263-794ca19c0dbe)

 - Click a folder to browse the HDRIs
 - Use the search option to find HDRIs (use clear button to enter new search)
 - 'HEART' shows only saved 'favorite' HDRIs. (more below)
 - Choose a proxy resolution if desired for faster viewport rendering (a proxy will generate if one does not exist)

3. Once a folder has been selected, 'HDRI Select' appears.

![Screenshot 2024-12-13 181705](https://github.com/user-attachments/assets/b78a08f4-1d95-4696-a8fe-e69b5cd65b22)

![Screenshot 2024-12-13 181739](https://github.com/user-attachments/assets/30e1fc8e-9206-4611-984f-106fd93752f9)

- Click the box to see thumbnails of your HDRIs
- Click on the desired HDRI to load it to use it
- The navigation buttons can be used as well to choose the next or previous HDRI in the list.
- The 'HEART' button is to save an HDRI to favorites. Click to save or remove from favorites (will show as RED if saved)

![image](https://github.com/user-attachments/assets/257f5120-cd10-400d-94af-da1d730128ed)

- Once more than one HDRI has been selected, a reset button will appear to reset to the previously selected HDRI

4. 'Settings' will appear once an HDRI has been loaded.

![image](https://github.com/user-attachments/assets/ab401ff6-d8d2-4e49-8e04-1e2b1ea852a7)

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

### Proxies (more info below: [Proxy Settings](#proxy-settings))

![image](https://github.com/user-attachments/assets/90f66b7f-b779-47f1-9c50-0c6268e2ca41)

 - Proxy Resolution Selection: Choose the desired resolution for your proxy of the selected HDRI
 - Proxy Mode: Choose between 'Viewport Only' or 'Both' (more info below)



##
## Full Dropdown Panel

![image](https://github.com/user-attachments/assets/3a43bfb3-8a9d-4527-8a35-7a06d329fda0)



##
## Updates

Stay up to date:
   
![Screenshot_20250510_140046](https://github.com/user-attachments/assets/25d6f81f-1c57-4b41-ad22-6c639cbaee88)

Click on 'Check Now' to see if there are any pending updates.
 - If there are updates a message will prompt to update
 - Click on 'Revert version' to do what the button says (If no backup a message will prompt. Backup happens before updates install)
   
![image](https://github.com/user-attachments/assets/a8a72360-8fe5-4050-adcf-4b694849611f)

 - If no updates are available, the following message will prompt
   
![Update to date](https://github.com/user-attachments/assets/663565f0-a41a-436b-b05a-d9fb7e9a1ed3)

3. Auto-Check Updates can be enabled

 (This feature checks for updates on startup of Blender)

 - If enabled/blender restarted, the following will prompt upon accessing HDRI Controls if there is a pending update
   
![image](https://github.com/user-attachments/assets/981665e2-7689-424c-899a-e91718c50070)

 - Upon Blender restart, the changelog entry will show NewFeatures, Fixes and Known Issues

![image](https://github.com/user-attachments/assets/fa34b209-fb68-4cb2-9e35-34e397102ba6)

### Backup Settings:

![image](https://github.com/user-attachments/assets/e91e404c-6b3a-4620-b739-791d9437cefa)

Enable backups for when updating to new versions
 - Max Backup Files: Maximum number of saved previous addon versions

### Documentation & Resources:

![image](https://github.com/user-attachments/assets/ecc827b8-1b24-45bf-a87b-68491e273ca3)





##
## Preview Thumbnail Generation
You can setup thumbnail previews using a .png that has the same name as the hdr file but ends with _thumb.png
Add the .png thumbnails to the same directory as the hdr.

![image](https://github.com/user-attachments/assets/d3d6e99d-8a0e-456d-aa91-f679561cf843)

### Processing Type:

 - Single File: Select a single .hdr or .exr file from you file browser and create a _thumb.png for it.
 - Batch Process: Select a folder with .hdr and/or .exr files and create _thumb.png for each.
 - Full Batch: Creates _thumb.png for all .hdr and .exr files in the main HDRI directory.
   (For both the _thumb.png is in the same folder location as the chosen .hdr or .exr)

 User Source selection to choose you HDRI, folder of HDRIs, or batch process all.
 - Choose you desired resolution % (Lower will be faster)
 - Choose number of samples (Lower will be faster)
 - Choose Render Device
 - Select scene type: Orbs-3, Orbs-4 or Teapot
 - GENERATE

### Scene Type Examples: Orbs-3, Orbs-4, Teapot

![image](https://github.com/user-attachments/assets/3670e94d-598a-47d7-990b-1004c41cd3a9)


Example of original and _thumb.png instance:

![image](https://github.com/user-attachments/assets/5e0789da-7f73-4ad3-aed4-f6e905646c28)



##
## Proxy Settings

![image](https://github.com/user-attachments/assets/19e12083-1e15-44af-acca-99831b5acdc6)

Default Resolution: The desired default resolution for proxies (if set to ORIGINAL, no proxies will be created and full resolution HDRI will be used - options = 1K, 2K, 4K, Original)

Default Application: Options are 'Viewport Only' (default) and 'Both'

- Viewport Only: The selected HDRI proxy will be used for viewport rendering. When a render begins (single frame or animation) the full resolution HDRI will be loaded in. Once completed the proxy will be reloaded for viewport rendering. (Supports switching when submitting jobs to Flamenco)
- Both: The selected HDRI proxy will be used for both viewport and final rendering.
   
### Cache Settings

 - Cache Size Limit: Limits the amount of space that proxy files can take up (in MB)
 - Clear Proxy Cache: Will clear/delete all proxy files and folders for HDRIs

### Batch Proxy Generation

![ScreenRecording_01-03-2025 15-02-29_1 2](https://github.com/user-attachments/assets/c262cce4-6b77-48f4-8ec7-08a037f4579b)

 - Generate Proxies: This process will create proxies for the chosen folder directory
 - Full Batch Process: This will create proxies for all folders and subfolders within the set main HDRI directory



##
## Keyboard Shortcut
Keyboard shortcut can be set for quickly pulling up the panel in the 3D viewport

![image](https://github.com/user-attachments/assets/30ff5841-84e3-40b4-878e-2187c7a7416c)

 - Set you current shortcut combination
 - Consists of:
   
   Windows\Linux: Shift, Alt, Ctrl
   
   MacOS: Shift, Command, Option
   
 - A-Z key options
 - BE SURE TO APPLY CHANGES IN PREFERENCES UI
 - When the key combination is pressed, the HDRI panel will appear where the cursor is

![shortcut](https://github.com/user-attachments/assets/9c0e019a-b41b-485e-bb99-7f7598805a4a)

Keyboard Shortcut Conflicts

![image](https://github.com/user-attachments/assets/3ec991ee-c3e6-4edf-be86-c33b9a173840)

 - Conflicts will show in dropdown menu.
 - Even if there is a conflict, from time to time it can work since we are in the 3dviewport.


##
## HDRI Settings

![Screenshot_20250510_140144](https://github.com/user-attachments/assets/a0199536-07e3-4d6e-a966-5aa1fc7cf420)

- Supported File Types: EXR, HDR, JPG (JPEG), PNG
- Rotation Settings: Keep Rotation - Rotation Steps
- Maximum Strength
- UI Adjust options (they're wonky so youve been warned)
- Preview limits and Folder Browser Page options


##
## Render Engine Specifics
Each render engine requires specific nodes and settings changes (settings can be changed if desired but the nodes cannot) The following information will show what information changes and the overall nodes/objects that are needed for operation on a per engine basis.


### Cycles:

![cycles_icon](https://github.com/user-attachments/assets/7e3bd0f9-0298-4f10-be7f-173be39beb77)

When set to Cycles and the HDRI System is initalized:

1. The Render Engine switches to 'Cycles'

![image](https://github.com/user-attachments/assets/dd5d89b1-7843-45ee-89c5-fa016bcabd52)

2. The View Transform changes to AgX (can be adjusted in panel)

![image](https://github.com/user-attachments/assets/ede429d9-7fca-41a8-b293-a73eaf32416d)

3. The following World node tree is created.

![image](https://github.com/user-attachments/assets/91efde77-03aa-4c31-8661-de1d8868e0f9)


### Octane:

![octane_icon](https://github.com/user-attachments/assets/b5de57d4-2336-4dd3-ab88-d57202398216)

When set to Octane and the HDRI System is initialized:

1. The Render Engine switches to 'Octane'

![image](https://github.com/user-attachments/assets/c6ae2704-f6cd-45f4-a810-a8fe9cc38c89)

2. The View Transform changes to RAW (can be adjusted in panel)

![image](https://github.com/user-attachments/assets/a0bfd5dd-d1ca-49e1-9f1c-4aeda0bf649e)

3. The following World node tree is created.

![image](https://github.com/user-attachments/assets/0ffb693a-75be-4328-9049-d35a1aa5fe99)


### V-Ray:

![vray_icon](https://github.com/user-attachments/assets/c4cca536-d385-4410-9ef3-e387bd5f1084)

When set to V-Ray and the HDRI System is initialized:

1. The Render Engine switches to 'V-Ray'

![image](https://github.com/user-attachments/assets/c87f76bf-d201-4f0e-acb1-269655942a75)

2. The View Transform changes to AgX (can be adjusted in panel)

![image](https://github.com/user-attachments/assets/ede429d9-7fca-41a8-b293-a73eaf32416d)

3. A collection called 'vRay HDRI Controls' appears with a 'VRayDomeLight'

![image](https://github.com/user-attachments/assets/6590417a-ed09-48d6-adf4-ab55576c60c1)

4. The following node is imported from misc\vray\vray_support.blend and applied to the VRayDomeLight through the V-Ray Node Editor/Shader

![image](https://github.com/user-attachments/assets/8a998e08-c61e-4b95-ab89-8a4b14541b15)



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

**Errors Post Update**
 - Use the 'Revert to Previous' option in the updates section of preferences to reload the previous version of the addon.
 - Visit the archive: https://github.com/mdreece/QHDRIC-ARCHIVE/tree/main

##
## Requirements

- Blender 4.2.0+ (older instances may work)
- Supported Operation Systems & Render Engine
     - Windows 10/11 (older may work): Cycles, V-Ray, Octane
     - Linux: Cycles (Theoretically Octane as well if installed)
     - MacOS 14.0+ (older may work): Cycles

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
