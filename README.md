# Quick HDRI Controls | Cycles | Octane | V-Ray | v2.8.4

### !!! RESTART BLENDER AT LEAST TWICE FOR v2.8.4 !!! ###
### !!! THIS PROCESS WILL REMAIN UNTIL v3.0.0 (AT THE LATEST) TO ENSURE THAT USERS GET THE SPLIT INSTANCE !!! ###

![Blender Version](https://img.shields.io/badge/Blender-4.2.0-green.svg)

![image](https://github.com/user-attachments/assets/f34ccf54-7e65-4dcb-8173-7b43ba369ea8)

v2.7.0 Video Demonstration: https://youtu.be/J7YdZQ2oxQA?si=_VRiLHIhQbZ1yVK4

Quick HDRI Controls is a Blender addon that makes working with HDRIs simple and efficient. Switch environments, adjust lighting, and control rotations directly from your 3D viewport - no more digging through node editors!

![AddonHeader](https://github.com/user-attachments/assets/e13b76ee-8c89-4a05-9855-03a18e1b2af8)

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
    
![image](https://github.com/user-attachments/assets/25c57a1e-c207-4560-83dc-2e625796726c)

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
   
![image](https://github.com/user-attachments/assets/42f925ac-f443-4ee2-a5fc-6da4808500c1)
![image](https://github.com/user-attachments/assets/d170aea9-90eb-4f1a-90d7-4839d185131d)
![image](https://github.com/user-attachments/assets/80ea20e2-a58e-4c4d-8f72-05a7d8a24530)

Depending on the your set render engine (both in blender and in addon preferences) you will be prompted to switch to the set Render Engine if you are not already.
 - IF set to Cycles or V-Ray, the View Transform changes to AgX (can be adjusted in panel)
 - IF set to Octane, the View Transform changes to Raw (can be adjusted in panel)

   
3. You'll be prompted with your HDRI folders/main directory in the "HDRI Browser" section
 - Click a folder to browse the HDRIs
 - Use the search option to find HDRIs (use clear button to enter new search)

![image](https://github.com/user-attachments/assets/60d3cb46-7602-4df9-bd99-4d0961582759)

4. Once a folder has been selected, 'HDRI Select' appears.

![Screenshot 2024-12-13 181705](https://github.com/user-attachments/assets/b78a08f4-1d95-4696-a8fe-e69b5cd65b22)

![Screenshot 2024-12-13 181739](https://github.com/user-attachments/assets/30e1fc8e-9206-4611-984f-106fd93752f9)

- Click the box to see thumbnails of your HDRIs
- Click on the desired HDRI to load it to use it
- The navigation buttons can be used as well to choose the next or previous HDRI in the list.

![image](https://github.com/user-attachments/assets/fce17064-9822-4444-ac0d-7c9cfaf5fe7f)

- Once more than one HDRI has been selected, a reset button will appear to reset to the previously selected HDRI

5. 'Settings' will appear once an HDRI has been loaded.

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

![image](https://github.com/user-attachments/assets/38062ade-0af4-47db-8a11-e0b9c3a24962)

 - Proxy Resolution Selection: Choose the desired resolution for your proxy of the selected HDRI
 - Proxy Mode: Choose between 'Viewport Only' or 'Both' (more info below)



##
## Full Dropdown Panel

![image](https://github.com/user-attachments/assets/d4ca9198-5077-405a-b400-f55bdc38aa51)



##
## Updates

Stay up to date:
Updates are based on Render Engine that is selected.
   
![image](https://github.com/user-attachments/assets/5e441aa5-46bd-4334-9789-b8b7aec3bfc8)

Click on 'Check Now' to see if there are any pending updates.
 - If there are updates a message will prompt to update
 - Click on 'Revert version' to do what the button says (If no backup a message will prompt. Backup happens before updates install)
   
![image](https://github.com/user-attachments/assets/a8a72360-8fe5-4050-adcf-4b694849611f)

 - If no updates are available, the following message will prompt
   
![Update to date](https://github.com/user-attachments/assets/663565f0-a41a-436b-b05a-d9fb7e9a1ed3)

3. Auto-Check Updates can be enabled

 (This feature checks for updates on startup of Blender)

 - If enabled/blender restarted, the following will prompt upon accessing HDRI Controls if there is a pending update
   
![Pending Update](https://github.com/user-attachments/assets/0405dd5c-5921-4d3e-bb13-6e052bdf23d3)

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
 - Choose you desired resolution %
 - Choose number of samples
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

- Viewport Only: The selected HDRI proxy will be used for viewport rendering. When a render begins (single frame or animation) the full resolution HDRI will be loaded in. Once completed the proxy will be reloaded for viewport rendering. (Proxy switching does not work with V-Ray Interactive Render. Use F12 render option/button for function to work).
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

Windows/Linux:

![QHDRIC_Shortcut](https://github.com/user-attachments/assets/2386ee2a-7904-42e4-92fb-05bf0d9c8e85)

MacOS:

<img width="533" alt="Screenshot 2024-10-28 at 6 14 22 PM" src="https://github.com/user-attachments/assets/32e18476-9c7e-46b5-a583-8b34027db7ef">

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

![image](https://github.com/user-attachments/assets/50a5d22b-4346-4525-a88e-241b4c7b1d24)

 - Keep Rotation options between HDRI changes
 - Maximum Strength value for lighting in scenes
 - Rotations step degree for when rotating HDRIs in increments
 - Supported File Types" explained above


##
## Render Engine Specifics
Each render engine requires specific nodes and settings changes (settings can be changed if desired but the nodes cannot) The following information will show what information changes and the overall nodes/objects that are needed for operation on a per engine basis.


### Cycles:

![image](https://github.com/user-attachments/assets/6091e730-069b-4953-a426-7f37f52a6fef)

When set to Cycles and the HDRI System is initalized:

1. The Render Engine switches to 'Cycles'

![image](https://github.com/user-attachments/assets/dd5d89b1-7843-45ee-89c5-fa016bcabd52)

2. The View Transform changes to AgX (can be adjusted in panel)

![image](https://github.com/user-attachments/assets/ede429d9-7fca-41a8-b293-a73eaf32416d)

3. The following World node tree is created.

![image](https://github.com/user-attachments/assets/91efde77-03aa-4c31-8661-de1d8868e0f9)


### Octane:

![image](https://github.com/user-attachments/assets/95684867-b4c1-48f8-ad46-b173cf146057)

When set to Octane and the HDRI System is initialized:

1. The Render Engine switches to 'Octane'

![image](https://github.com/user-attachments/assets/c6ae2704-f6cd-45f4-a810-a8fe9cc38c89)

2. The View Transform changes to RAW (can be adjusted in panel)

![image](https://github.com/user-attachments/assets/a0bfd5dd-d1ca-49e1-9f1c-4aeda0bf649e)

3. The following World node tree is created.

![image](https://github.com/user-attachments/assets/0ffb693a-75be-4328-9049-d35a1aa5fe99)


### V-Ray:

![image](https://github.com/user-attachments/assets/1747660b-31d9-4984-8c77-7ec55c914e94)

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
     - Linux Manjaro (others may work): Cycles 
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
