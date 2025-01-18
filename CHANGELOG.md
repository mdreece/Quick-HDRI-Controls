# QUICK HDRI CONTROLS CHANGELOG

## 15-1-2025: V2.6.8
		- Updated both Cycles and Octane instances to respect the HDRI visibility option when changing and resetting.

## 14-1-2025: V2.6.7
		- Big fix for Octane build. issue relating to \addons\Quick-HDRI-Controls-main\init.py", line 2652, in draw
		  version_text.label(text=f"Octane Version: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}", icon_value=icon_id)

## 13-1-2025: V2.6.6
		- Fixed bug where if set to 'Octane' as 'Render Engine' and update is installed,  it would revert back to cycles. The user chosen engine is saved in a preferences file.
		- Added custom UI icons for blender/cycles and octane to panel and preferences UI.

## 11-1/2025: 2.6.5
		- Added support for OctaneRenderer

## 10-1-2025: V2.6.3
		- Thumbnails now update correctly when resetting.
		- Folder location of HDRI is respected
		- Prompt to enable Cycles as this is only written to work with Cycles.

## 4-1-2025: V2.6.2
		- Had to rework the reset options to account for using proxies (somehow I forgot to do this)
		- Added version and preferences access to not initialized panel for quick access. no longer need to initialize to access preferences.

## 3-1-2025: V2.5.9
		- Updated UI for preview generation. 'Full Batch' now doesnt automatically run when clicked. Quality settings can be chosen before generation.

## 2-1-2025: V2.5.7
		- Added batch proxy generation for directories in preferences

## 1-1-2025: V2.5.5
		- Bug fixes with preview generation/changed error handling for generation file selection

## 1-1-2025: V2.5.4
		- Proxy options added for HDRIs
		- Options to have set for 'Viewport Only' or 'Both
			 - Viewport Only: When a proxy image is used for the HDRI, when a render is begun it will reset to the full resolution HDRI and will reset back to proxy when completed.
			 - Both: When a proxy image is selected and a render is begun, the same proxy will be used for rendering.
		- 'Proxies' folders will generate in each HDRI subfolder.
		- Once a proxy is created, it will be referenced/used when a proxy is set instead of a new instance being created
		- Proxies can all be cleared from within preferences.
		- Compression method can be adjusted (there isn't a clear advantage to either. ZIP has been more consistent on both Windows and MacOS, but wanted to keep options open)

## 15-12-2024: V2.5.2
		- Preview generation tool in preferences. Use this function to create .png thumbnails of HDRIs to ease resource usage (Support creating for .hdr and .exr)
		- Single File: Use this function to create a thumbnail of a specific HDRI file (output file will be in same directory as selected HDRI)
		- Batch Process: Use this function to create thumbnails for a folder fill of .hdr and .exr files. The more files the longer the process will take (also depends on user selected render settings)
		- Quick HDRI Controls will detect these new preview files upon next use.
		- Update function to allow extraction of .zip update files. Included is the 'Preview'blend' in the addon directory that drives the main HDRI preview scene. Background processes run the rendering.

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

## 22-11-2024: V2.5
		- Key frame options added in panel for rotation as well as strength.
		- There is a bug when changing HDRIs that will prompt with an error and clear keyframes.

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
