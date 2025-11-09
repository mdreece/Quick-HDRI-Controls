# QUICK HDRI CONTROLS CHANGELOG

## 23-9-2025:  CYCLES: v2.9.4 | OCTANE: V2.9.4 | V-RAY: V2.9.4
### Information ⚠️:
• Restart Blender Twice to fully update (Changelog will show twice. THIS (2.9.4) is the last like this)

### Fixes 🛠️:
• OCTANE: Reset button now resets more than once to match V-Ray and Cycles builds
• All: Preferences proxy options were not being respected.
• All: Render engine selection on main panel will reflect set engine in preferences (default is cycles if no other is set).
##


## 23-9-2025:  CYCLES: v2.9.3 | OCTANE: V2.9.3 | V-RAY: V2.9.3
### Information ⚠️:
• Restart Blender Twice to fully update (Changelog will show twice. 2.9.4 is the last like this)
• 5.0 changes may cause there to be many updates

### Fixes 🛠️:
• Preview Generation - found the GPU option was no longer working. This has been resolved (CPU is still faster in my case)
##


## 22-9-2025:  CYCLES: v2.9.2 | OCTANE: V2.9.2 | V-RAY: V2.9.2
### Information ⚠️:
• Restart Blender Twice to fully update (Engine dropdown on main panel is newest update. Changelog will show twice.)
• 5.0 changes may cause there to be many updates

### Fixes 🛠️:
• CYCLES: corrected AttributeError: 'World' object has no attribute 'use_nodes' for proxy switching during renders. I more than likely have missed others that will show up as time progresses. I'm attempting as many tests as possible.
##


## 19-9-2025:  CYCLES: v2.9.1 | OCTANE: V2.9.1 | V-RAY: V2.9.1
### Information ⚠️:
• Restart Blender Twice to fully update (Engine dropdown on main panel is newest update. Changelog will show twice.)

### Fixes 🛠️:
• CYCLES: updated to support Blender v5.0.0 node changes
• OCTANE: updated for v30.7.0 and Blender v4.5.2
• V-RAY: updated for v7.10.00 and Blender v4.5.2
##


## 5-9-2025:  CYCLES: v2.9.0 | OCTANE: V2.9.0 | V-Ray: V2.9.0
### Information ⚠️:
• Restart Blender Twice to fully update (Engine dropdown on main panel is newest update. Changelog will show twice.)

### Fixes 🛠️:
• VRAY - if one does not exist, a camera will be created to allow viewport rendering (corrects "Invalid camera object")
• C/O/V - combined some processes to assist with faster UI navigation
##


## 14-7-2025:  CYCLES: v2.8.9 | OCTANE: V2.8.9 | V-Ray: V2.8.9
### Information ⚠️:
• Restart Blender Twice to fully update (Engine dropdown on main panel is newest update. Changelog will show twice.)

### Fixes 🛠️:
• Now Supports V-Ray 7 for Blender: V-Ray is now out of BETA for Blender! Woohoo! However they had adjust their API so this addon may not have worked until now. Oddly I don't recall this being an issue, but with their changes I guess you need to have a camera present in order for V-Ray to render correctly. 
##


## 26-6-2025:  CYCLES: v2.8.8 | OCTANE: V2.8.8 | V-Ray: V2.8.8
### Information ⚠️:
• Restart Blender Twice to fully update (Engine dropdown on main panel is newest update. Changelog will show twice.)

### Fixes 🛠️:
• SUBFOLDER HDRIs no londer show in PARENT folders.
• Fixed a property value WARNING related to HDRI settings.
• Added option to change the location of the main panel in UI (In HDRI Settings in preferences)
• vray_support/Previews.blend now in support.blend so a little space saved.

### Known Issues ⚠️:
• V-Ray 7 support is WIP
##



## 8-6-2025:  CYCLES: v2.8.7 | OCTANE: V2.8.7 | V-Ray: V2.8.7
### Information ⚠️: (All)
• Restart Blender Twice to fully update (Engine dropdown on main panel is newest update. Changelog will show twice.)

### Fixes 🛠️:
• 'Previews' box does not show when set to favorites if no favorites have been saved.
• 'Folder Browser' now shows 'home' button to access the main directory from anywhere as well as the previous subfolder in the chain.
• Panel Header/Engine dropdown has been changed around to allow for more clickable area to move the panel when using a shortcut.
##



## 20-5-2025:  CYCLES: v2.8.6 | OCTANE: V2.8.6 | V-Ray: V2.8.6
### Information ⚠️: (All)
• Restart Blender Twice to fully update (Engine dropdown on main panel is newest update. Changelog will show twice.)

### New Features 🔔:
• Supports proxy switching if submitting job for use with Flamenco
• Favorites can now be saved and accessed from the 'HEART' icon. HDRIs can be added/removed by clicking the red 'HEART' icon in the navigation buttons bar

### Bug Fixes 🛠️:
• Proxy resolution set in preferences is the default in the panel (not sure when this had stopped working).
##



## 19-5-2025:  CYCLES: v2.8.5 | OCTANE: V2.8.5 | V-Ray: V2.8.5
### Information ⚠️: (All)
• Restart Blender Twice to fully update (Engine dropdown on main panel is newest update. Changelog will show twice.)

### New Features 🔔:
• Supports proxy switching if submitting job for use with Flamenco
• Favorites can now be saved and accessed from the 'HEART' icon. HDRIs can be added/removed by clicking the red 'HEART' icon in the navigation buttons bar
##



## 10-5-2025:  CYCLES: v2.8.4 | OCTANE: V2.8.4 | V-Ray: V2.8.4
### Information 🔔: (All)
• Restart Blender Twice to fully update (Engine dropdown on main panel is newest update. Changelog will show twice
• UI Changes in Preferences
• Extended HDRI Settings

### Bug Fixes ⚠️:
• Preview Generation is working now. Changed up how the addon checks files and had missed the preview generations.
##



## 9-5-2025:  CYCLES: v2.8.3 | OCTANE: V2.8.3 | V-Ray: V2.8.3
### Information 🔔: (All)
• Restart Blender Twice to fully update (Engine dropdown on main panel is newest update. Changelog will show twice
• UI Changes in Preferences
• Extended HDRI Settings

### INFORM OF ANY ERRORS/ISSUES ⚠️:
• Though not much has changed, the addon was completely rewritten to be broken up into parts. Issues are entirely possible...
##



## 16-4-2025: CYCLES: v2.8.2 | OCTANE: V2.8.2 | V-Ray: V1.0.8
### New Features 🔔: (All)
• Now supporting ACES color space/transform.

### Fixes 🛠️:
• None

### Known Issues ⚠️:
• None
##



## 16-4-2025: CYCLES: v2.8.1 | OCTANE: V2.8.1 | V-Ray: V1.0.7
### New Features 🔔: (All)
• Hide/Show Search.
• Update prompt on panel shows on bottom.

### Fixes 🛠️:
• None

### INFORMATION ⚠️:
• None
##


## 12-4-2025: CYCLES: v2.8.0 | OCTANE: V2.8.0 | V-Ray: V1.0.6
### New Features 🔔:
• Pages option for HDRI Browser. You can now set a folder limit of displayed folders to assist with UI bloat if you have several folders with HDRIs. Access the settings in preferences-HDRI Settings. 

### Fixes 🛠️:
• None

### Known Issues ⚠️:
• None
##



## 11-4-2025: CYCLES: v2.7.9 | OCTANE: V2.7.9 | V-Ray: V1.0.5
### New Features 🔔:
• Testing a new update process on a per Render Engine basis. Cycles instance now how its own custom icon instead of using Blender icon.

### Fixes 🛠️:
• None

### Known Issues ⚠️:
• None
##



## 5-4-2025: CYCLES: v2.7.8 | OCTANE: V2.7.8 | V-Ray: V1.0.4
### New Features 🔔:
• None

### Fixes 🛠️:• V-Ray: Preview loading should be much quicker (Had a repeating check that was causing locks)

### Known Issues ⚠️:
• None
##



## 28-2-2025: CYCLES: v2.7.7 | OCTANE: V2.7.7 | V-Ray: V1.0.3
### New Features 🔔:
• None

### Fixes 🛠️:
• 'clear search' button only shows when there is an active search.

### Known Issues ⚠️:
• V-RAY: Proxy switching works if done by pressing F12/Start Production Render. Does not work in Interactive Render (WIP)
##



## 25-2-2025: CYCLES: v2.7.6 | OCTANE: V2.7.6 | V-Ray: V1.0.2
### New Features 🔔:
• Keyboard shortcut keys now have cursor button support (if additional buttons are needed, let me know)

### Fixes 🛠️:
• CYCLES & OCTANE: Updated to show the navigation options once a folder that has HDRIs present is accessed to match V-RAY functions (this was missed initially)

### Known Issues ⚠️:
• V-RAY: Proxy switching works if done by pressing F12/Start Production Render. Does not work in Interactive Render (WIP)
##



## 21-2-2025: CYCLES: v2.7.5 | OCTANE: V2.7.5 | V-Ray: V1.0.1
### New Features 🔔:
• None

### Fixes 🛠️:
• Had cleared import bpy.utils.previews wihtout realizing it causing MacOS users to experience issues (Linux and Windows appear to be uneffected.) It has been re-added resulting in no further issues. Manual update may be required.

### Known Issues ⚠️:
• V-Ray: Proxy switching only works if done by pressing F12 OR by clicking 'Start Production Render'. Does not work when using Interactive Render (WIP on solution)
##



## 18-2-2025: CYCLES: v2.7.4 | OCTANE: V2.7.4 | V-Ray: V1.0.0
### New Features 🔔:
• V-Ray now supported (v1.0.0)

• UI adjustments for preview generation area. Now within 'preview thumbnails' section.

### Fixes 🛠️:
• None

### Known Issues ⚠️:
• MacOS is hit or miss with this update. Working on that.
##



## 7-2-2025: V2.7.3
### New Features 🔔:
• UI updates to Preferences

• Render Engine option now on same line as HDRI Directory

• Updates & Information has 'Backup Settings' and 'Documentation' dropdown sections.

• Preview Generation are updated to be more coherant. Dropdown menu options and layed out for a top down process.

• V-Ray is WIP for those who would use it. Release is TBD.

### Fixes 🛠️:
• None

### Known Issues ⚠️:
• None
##



## 3-2-2025: V2.7.2
### New Features 🔔:
• Search feature now in 'HDRI Browser' for both Cycles and Octane.

### Fixes 🛠️:
• v2.7.1 search option was not locking. Text must be cleared for new search.

• If set to Octane, but Octane is not installed, will prompt to change render engine in preferences.

### Known Issues ⚠️:
• None
##



## 2-2-2025: V2.7.1
### New Features:
• Search feature now in 'HDRI Browser' for both Cycles and Octane.

### Fixes 🛠️:
• None

### Known Issues ⚠️:
• None
##



## 21-1-2025: V2.7.0
### New Features:
• Changed Preview 'Scene Type' options. Removed 'Monk' and 'Cube' options. Adjusted 'Orbs' to 'Orbs-4'. Added 'Orbs-3' and 'Teapot'.

### Fixes 🛠️:
• Fixed registration formatting (would error when enabling and disabling more than once)

### Known Issues ⚠️:
• None
##



## 19-1-2025: V2.6.9
### New Features:
• Upon opening blender post update, the changelog entry for the update will display.

### Fixes 🛠️:
• None

### Known Issues ⚠️:
• None
##



## 15-1-2025: V2.6.8
### New Features:
• None

### Fixes 🛠️:
• Updated both Cycles and Octane instances to respect the HDRI visibility option when changing and resetting.

### Known Issues ⚠️:
• None
##



## 14-1-2025: V2.6.7
### New Features:
• None

### Fixes 🛠️:
• Bug fix for Octane build. issue relating to \addons\Quick-HDRI-Controls-main\init.py", line 2652, in draw version_text.label(text=f"Octane Version: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}", icon_value=icon_id)

### Known Issues ⚠️:
• None
##



## 13-1-2025: V2.6.6
### New Features:
• Added custom UI icons for blender/cycles and octane to panel and preferences UI.

### Fixes 🛠️:
• Fixed bug where if set to 'Octane' as 'Render Engine' and update is installed,  it would revert back to cycles. The user chosen engine is saved in a preferences file.

### Known Issues ⚠️:
• None
##



## 11-1/2025: 2.6.5
### New Features:
• Added support for OctaneRenderer

### Fixes 🛠️:
• None

### Known Issues ⚠️:
• None
##



## 10-1-2025: V2.6.3
### New Features:
• Prompt to enable Cycles as this is only written to work with Cycles.

### Fixes 🛠️:
• Thumbnails now update correctly when resetting.
• Folder location of HDRI is respected

### Known Issues ⚠️:
• None
##



## 4-1-2025: V2.6.2
	Had to rework the reset options to account for using proxies (somehow I forgot to do this)
	Added version and preferences access to not initialized panel for quick access. no longer need to initialize to access preferences.

## 3-1-2025: V2.5.9
	Updated UI for preview generation. 'Full Batch' now doesnt automatically run when clicked. Quality settings can be chosen before generation.

## 2-1-2025: V2.5.7
	Added batch proxy generation for directories in preferences

## 1-1-2025: V2.5.5
	Bug fixes with preview generation/changed error handling for generation file selection

## 1-1-2025: V2.5.4
	Proxy options added for HDRIs
	Options to have set for 'Viewport Only' or 'Both
		 - Viewport Only: When a proxy image is used for the HDRI, when a render is begun it will reset to the full resolution HDRI and will reset back to proxy when completed.
		 - Both: When a proxy image is selected and a render is begun, the same proxy will be used for rendering.
	'Proxies' folders will generate in each HDRI subfolder.
	Once a proxy is created, it will be referenced/used when a proxy is set instead of a new instance being created
	Proxies can all be cleared from within preferences.
	Compression method can be adjusted (there isn't a clear advantage to either. ZIP has been more consistent on both Windows and MacOS, but wanted to keep options open)

## 15-12-2024: V2.5.2
	Preview generation tool in preferences. Use this function to create .png thumbnails of HDRIs to ease resource usage (Support creating for .hdr and .exr)
	Single File: Use this function to create a thumbnail of a specific HDRI file (output file will be in same directory as selected HDRI)
	Batch Process: Use this function to create thumbnails for a folder fill of .hdr and .exr files. The more files the longer the process will take (also depends on user selected render settings)
	Quick HDRI Controls will detect these new preview files upon next use.
	Update function to allow extraction of .zip update files. Included is the 'Preview'blend' in the addon directory that drives the main HDRI preview scene. Background processes run the rendering.

## 14-12-2024: V2.5.1
	- Added the obvious function that once the HDRI is selected in the preview popup, it is loaded

## 14-12-2024: 2.5.0
	- Added metadata menu to show information related to selected HDRI
	---> HDRI name
	--->HDRI resolution
	--->Colorspace
	---># channels
	--->File size
	--->File format

## 14-12-2024: V2.4.9
	-bug fix at times when repairing hdri system

## 13-12-2024: V2.4.8
	- Once an HDRI folder is accessed and at least one HDR loaded, navigation buttons can be used to cycle through HDRs.
	- Slight UI adjustments
	- General UI updates

## 12-12-2024: V2.4.7
	- Moved Preferences button to the right side of the panel
	- Added a button to 'delete world' (full reset)

## 12-12-2024: V2.4.6
	- If you have .png preview images of your HDRI files, name them the same as the core HDRI with '_thumb.png' at the end of the name. These will be used for generating HDR previews to save resources. If you don't have png previews, the normal functions will continue. I reworked them slightly to try to be as efficient as possible.
	- Fixed a bug where accessing a subfolders subfolder, and attempting to navigate to the initial subfolder, the panel would lose options and would require 'going home'.
	- When clicking 'Reset HDRI' the panel will revert the preview to the previous HDR as well as set navigation to its directory.
	- Added function in preferences for setting a preview limit. This is to additionally assist with resources so not all previews will show, but files should still be select able if you know the names. 
          !!! 0 = Unlimited Preview Loading

## 8-12-2024: V2.4.5
	- When updates installed, messages appears to save-restart blender that is more apparent.

## 8-12-2024: V2.4.4
	- UI updates in panel and preferences

## 25-11-2024: V2.4.3
	- improved folder browsing icons for navigating back a folder or returning the the main HDRI directory
	- Preferences sections are now their own menus

## 24-11-2024: V2.4.2
	- updated preview generation
	- updated folder navigation to allow quick access to main HDRI directory as well as navigate to previous folder.

## 24-11-2024: V2.4.1
	- Reverting back to v2.4.1 to rework animation options.

## 1-11-2024: V2.4.1
	- Fixed bug (really I accidentally cleared it) where 'keep rotation' option was not applying when selected.
		
## 1-11-2024: V2.4
	- Fixed bug where HDRI visibility toggle would clear the HDRI instead of only adjusting ray visibility

## 1-11-2024: V2.3
	- Updated HDRI Settings panel to have a visibility option for the currently selected HDRI

## 1-11-2024: V2.2
	- Removed preview-keep-cancel options
	- Replaced with a reset HDRI option that will reset to last selected HDRI
	- General UI adjustments in preferences

## 31-10-2024: V2.1
	- Fixes rotation increments (idk how I had missed that for so long)
	- Adjusted Load-Preview buttons

## 29-10-2024: V2.0
	- Added feature to preview HDRI and either keep or cancel the preview
		
## 29-10-2024: V1.9
	- 'Keep Rotation' option added on panel and preferences. This will keep any rotation options when a new HDRI is selected.
	- Updated strength default-max to 100
		
## 29-10-2024: V1.8
	- HDRI Selection does not appear until an HDRI folder location is selected (if main HDRI directory has any supported files, they will show)
	- HDRI Settings does not appear until an HDRI has been selected for the scene.
		
## 28-10-2024: V1.6
	- Adjusted memory usage to clear HDRI previews when changing folders.
	- Added functions for shortcut key combinations to bring up panel quicker if needed.		
		
## 27-10-2024: V1.5
	- UI reordering in preferences
		
## 27-10-2024: V1.4
	- Added option to enable 'Auto Check Updates' at startup. Will prompt to download update when attempting to add HDRI when enabled.

## 27-10-2024: v1.3
	- Update function now 'Checks for Update' and prompts user as needed in lower message.
		
## 27-10-2024: V1.2
	- Version number displays in panel
	- Preferences can be accessed from button in panel
	- Documentation link to Github in preferences
		
## 27-10-2024: V1.1
	- Fixed bug where sub folders would only show primary directory HDRI files. 
	- When sub folders are selected, they will now display the HDRI files within the selected folder.










