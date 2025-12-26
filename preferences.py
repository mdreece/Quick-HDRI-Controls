"""
Quick HDRI Controls - Addon preferences
"""
import os
import sys
import re
import bpy
import shutil
from bpy.types import AddonPreferences
from bpy.props import (FloatProperty, StringProperty, EnumProperty,
                     CollectionProperty, PointerProperty, IntProperty,
                     BoolProperty, FloatVectorProperty)

class QuickHDRIPreferences(AddonPreferences):
    # We need to manually set this for proper detection
    bl_idname = "Quick-HDRI-Controls-main"

    # Properties for auto-update and update alert
    enable_auto_update_check: BoolProperty(
        name="Enable Auto-Update Check on Startup",
        description="Automatically check for updates when Blender starts",
        default=False
    )

    update_available: BoolProperty(
        name="Update Available",
        default=False
    )

    # Show Conflicts
    show_conflicts: BoolProperty(
        name="Show Conflicts",
        description="Show keyboard shortcut conflicts",
        default=False
    )

    # Keyboard shortcut properties
    popup_key: EnumProperty(
        name="Key",
        description="Key or mouse button for the popup menu shortcut",
        items=[
            # Keyboard keys (existing)
            ('A', 'A', ''), ('B', 'B', ''), ('C', 'C', ''),
            ('D', 'D', ''), ('E', 'E', ''), ('F', 'F', ''),
            ('G', 'G', ''), ('H', 'H', ''), ('I', 'I', ''),
            ('J', 'J', ''), ('K', 'K', ''), ('L', 'L', ''),
            ('M', 'M', ''), ('N', 'N', ''), ('O', 'O', ''),
            ('P', 'P', ''), ('Q', 'Q', ''), ('R', 'R', ''),
            ('S', 'S', ''), ('T', 'T', ''), ('U', 'U', ''),
            ('V', 'V', ''), ('W', 'W', ''), ('X', 'X', ''),
            ('Y', 'Y', ''), ('Z', 'Z', ''),
            ('SPACE', 'Space', ''),
            ('LEFT_SHIFT', 'Left Shift', ''),
            ('RIGHT_SHIFT', 'Right Shift', ''),
            ('LEFT_CTRL', 'Left Control', ''),
            ('RIGHT_CTRL', 'Right Control', ''),
            ('LEFT_ALT', 'Left Alt', ''),
            ('RIGHT_ALT', 'Right Alt', ''),
            ('LEFT_COMMAND', 'Left Command', ''),
            ('RIGHT_COMMAND', 'Right Command', ''),
            ('OSKEY', 'OS Key', ''),

            # Mouse buttons (new)
            ('LEFTMOUSE', 'Left Mouse', ''),
            ('MIDDLEMOUSE', 'Middle Mouse', ''),
            ('RIGHTMOUSE', 'Right Mouse', ''),
            ('BUTTON4MOUSE', 'Mouse Button 4', ''),
            ('BUTTON5MOUSE', 'Mouse Button 5', ''),
            ('BUTTON6MOUSE', 'Mouse Button 6', ''),
            ('BUTTON7MOUSE', 'Mouse Button 7', ''),

            # Mouse wheel options
            ('WHEELUPMOUSE', 'Mouse Wheel Up', ''),
            ('WHEELDOWNMOUSE', 'Mouse Wheel Down', ''),
            ('WHEELINMOUSE', 'Mouse Wheel In', ''),
            ('WHEELOUTMOUSE', 'Mouse Wheel Out', ''),
        ],
        default='A'
    )

    popup_ctrl: BoolProperty(
        name="Control/Command",
        description="Use Command (MacOS) or Control (Windows/Linux) modifier",
        default=True
    )

    popup_shift: BoolProperty(
        name="Shift",
        description="Use Shift modifier",
        default=True
    )

    popup_alt: BoolProperty(
        name="Option/Alt",
        description="Use Option (MacOS) or Alt (Windows/Linux) modifier",
        default=False
    )

    # Directory
    hdri_directory: StringProperty(
        name="HDRI Directory",
        subtype='DIR_PATH',
        description="Directory containing HDRI files",
        default="",
        update=lambda self, context: refresh_previews(context)
    )

    use_hdr: BoolProperty(
        name="HDR",
        description="Include .hdr files",
        default=True
    )

    use_exr: BoolProperty(
        name="EXR",
        description="Include .exr files",
        default=True
    )

    use_png: BoolProperty(
        name="PNG",
        description="Include .png files",
        default=True
    )

    use_jpg: BoolProperty(
        name="JPG",
        description="Include .jpg and .jpeg files",
        default=True
    )

    # UI Layout Settings
    ui_scale: IntProperty(
        name="Panel Width",
        description="Width of the HDRI control panel",
        default=10,
        min=1,
        max=30,
        subtype='PIXEL'
    )

    preview_scale: IntProperty(
        name="Preview Size",
        description="Size of HDRI preview thumbnails",
        default=8,
        min=1,
        max=20
    )

    button_scale: FloatProperty(
        name="Button Scale",
        description="Scale of UI buttons",
        default=1.0,
        min=0.5,
        max=100.0,
        step=0.05
    )

    spacing_scale: FloatProperty(
        name="Spacing Scale",
        description="Scale of UI element spacing",
        default=1.0,
        min=0.5,
        max=100.0,
        step=0.1
    )

    # Visual Settings
    use_compact_ui: BoolProperty(
        name="Compact UI",
        description="Use compact UI layout",
        default=True
    )

    # Interface Settings
    show_strength_slider: BoolProperty(
        name="Show Strength Slider",
        description="Show the strength slider in the main UI",
        default=True
    )

    show_rotation_values: BoolProperty(
        name="Show Rotation Values",
        description="Show numerical values for rotation",
        default=True
    )

    keep_rotation: BoolProperty(
        name="Keep Rotation When Switching HDRIs",
        description="Maintain rotation settings when switching between HDRIs",
        default=False
    )

    strength_max: FloatProperty(
        name="Max Strength",
        description="Maximum value for strength slider",
        default=100.0,
        min=1.0,
        max=100.0,
        step=0.001
    )

    rotation_increment: FloatProperty(
        name="Rotation Increment",
        description="Increment for rotation controls",
        default=45.0,
        min=0.1,
        max=360.0,
        step=0.1
    )

    preview_limit: IntProperty(
        name="Preview Limit",
        description="Maximum number of HDRI previews to load at once (0 = no limit)",
        default=0,
        min=0,
        max=9000
    )

    preview_sort: EnumProperty(
        name="Preview Sort",
        description="How to sort HDRIs when preview limit is active",
        items=[
            ('NAME', 'Name', 'Sort alphabetically by name'),
            ('DATE', 'Date', 'Sort by most recently modified'),
            ('SIZE', 'Size', 'Sort by file size')
        ],
        default='NAME'
    )

    # Preview Generation Settings
    preview_resolution: IntProperty(
        name="Resolution Percentage",
        description="Percentage of base resolution (1024x768)",
        default=100,
        min=10,
        max=200,
        subtype='PERCENTAGE'
    )

    preview_generation_type: EnumProperty(
        name="Preview Generation Type",
        description="Method for generating HDRI previews",
        items=[
            ('SINGLE', 'Single HDRI', 'Generate preview for a single HDRI'),
            ('MULTIPLE', 'Multiple HDRIs', 'Generate previews for all HDRIs in a folder'),
            ('FULL_BATCH', 'Full Batch', 'Process all HDRIs in directory structure')
        ],
        default='SINGLE'
    )

    preview_single_file: StringProperty(
        name="HDRI File",
        description="Single HDRI file to generate preview for",
        subtype='FILE_PATH'
    )

    preview_multiple_folder: StringProperty(
        name="HDRI Folder",
        description="Folder containing HDRIs to generate previews for",
        subtype='DIR_PATH'
    )

    preview_samples: IntProperty(
        name="Render Samples",
        description="Number of samples for preview renders",
        default=32,
        min=1,
        max=999999
    )

    preview_image: StringProperty(
        name="Preview Image",
        description="Name of the currently displayed preview image",
        default=""
    )

    preview_render_device: EnumProperty(
        name="Render Device",
        description="Device to use for preview rendering",
        items=[
            ('CPU', 'CPU', 'Use CPU for rendering'),
            ('GPU', 'GPU', 'Use GPU for rendering')
        ],
        default='GPU'
    )

    preview_scene_type: EnumProperty(
        name="Scene Type",
        description="Objects to include in the preview scene",
        items=[
            ('ORBS_4', 'Orbs - 4', 'Use the four orbs collection'),
            ('ORBS_3', 'Orbs - 3', 'Use the three orbs collection'),
            ('TEAPOT', 'Teapot', 'Use the teapot collection')
        ],
        default='ORBS_4'
    )

    # Proxy Settings
    default_proxy_resolution: EnumProperty(
        name="Default Proxy Resolution",
        description="Default resolution for HDRI proxies",
        items=[
            ('ORIGINAL', 'Original', 'Use original resolution'),
            ('1K', '1K', 'Use 1K resolution'),
            ('2K', '2K', 'Use 2K resolution'),
            ('4K', '4K', 'Use 4K resolution'),
        ],
        default='ORIGINAL'
    )

    proxy_cache_limit: IntProperty(
        name="Proxy Cache Limit",
        description="Maximum size for proxy cache in megabytes",
        default=500,
        min=1,
        max=999999999
    )

    default_proxy_mode: EnumProperty(
        name="Default Proxy Mode",
        description="Default proxy application mode",
        items=[
            ('VIEWPORT', 'Viewport Only', 'Apply proxy resolution only in viewport'),
            ('BOTH', 'Both', 'Apply proxy resolution to both viewport and render'),
        ],
        default='VIEWPORT'
    )

    # Proxy Generation Settings
    proxy_generation_resolution: EnumProperty(
        name="Proxy Resolution",
        description="Resolution to use for proxy generation",
        items=[
            ('1K', '1K', 'Generate 1K proxies'),
            ('2K', '2K', 'Generate 2K proxies'),
            ('4K', '4K', 'Generate 4K proxies'),
        ],
        default='1K'
    )

    proxy_generation_directory: StringProperty(
        name="Proxy Generation Directory",
        subtype='DIR_PATH',
        description="Directory containing HDRI files for proxy generation",
        default=""
    )

    proxy_format: EnumProperty(
        name="Proxy Format",
        description="File format for proxy files",
        items=[
            ('HDR', 'HDR', 'OpenEXR HDR format'),
            ('EXR', 'EXR', 'OpenEXR format'),
        ],
        default='EXR'
    )

    proxy_generation_device: EnumProperty(
        name="Render Device",
        description="Device to use for proxy generation",
        items=[
            ('CPU', 'CPU', 'Use CPU for processing'),
            ('GPU', 'GPU', 'Use GPU for processing')
        ],
        default='CPU'
    )

    # Render Engine
    render_engine: EnumProperty(
        name="HDRI Render Engine",
        description="Select the render engine for HDRI controls",
        items=[
            ('CYCLES', 'Cycles', 'Use Cycles render engine'),
            ('VRAY_RENDER_RT', 'V-Ray', 'Use V-Ray render engine'),
            ('octane', 'Octane', 'Use Octane render engine')
        ],
        default='CYCLES'
    )

    # Backup Settings
    enable_backups: BoolProperty(
        name="Enable Backups",
        description="Create a backup before performing updates",
        default=True
    )

    max_backup_files: IntProperty(
        name="Maximum Backup Files",
        description="Maximum number of backup files to keep",
        default=5,
        min=1,
        max=50
    )

    # Folder Pagination
    folders_per_page: IntProperty(
        name="Folders Per Page",
        description="Number of folders to display per page in the HDRI browser",
        default=6,
        min=2,
        max=20
    )

    show_folder_pagination: BoolProperty(
        name="Enable Folder Pagination",
        description="Enable pagination for folders in the HDRI browser",
        default=True
    )

    preview_resolution: IntProperty(
        name="Resolution Percentage",
        description="Percentage of base resolution (1024x768)",
        default=100,
        min=10,
        max=200,
        subtype='PERCENTAGE'
    )

    preview_generation_type: EnumProperty(
        name="Preview Generation Type",
        description="Method for generating HDRI previews",
        items=[
            ('SINGLE', 'Single HDRI', 'Generate preview for a single HDRI'),
            ('MULTIPLE', 'Multiple HDRIs', 'Generate previews for all HDRIs in a folder'),
            ('FULL_BATCH', 'Full Batch', 'Process all HDRIs in directory structure')
        ],
        default='SINGLE'
    )

    preview_single_file: StringProperty(
        name="HDRI File",
        description="Single HDRI file to generate preview for",
        subtype='FILE_PATH'
    )

    preview_multiple_folder: StringProperty(
        name="HDRI Folder",
        description="Folder containing HDRIs to generate previews for",
        subtype='DIR_PATH'
    )

    preview_samples: IntProperty(
        name="Render Samples",
        description="Number of samples for preview renders",
        default=32,
        min=1,
        max=999999
    )

    preview_image: StringProperty(
        name="Preview Image",
        description="Name of the currently displayed preview image",
        default=""
    )

    preview_render_device: EnumProperty(
        name="Render Device",
        description="Device to use for preview rendering",
        items=[
            ('CPU', 'CPU', 'Use CPU for rendering'),
            ('GPU', 'GPU', 'Use GPU for rendering')
        ],
        default='GPU'
    )

    preview_scene_type: EnumProperty(
        name="Scene Type",
        description="Objects to include in the preview scene",
        items=[
            ('ORBS_4', 'Orbs - 4', 'Use the four orbs collection'),
            ('ORBS_3', 'Orbs - 3', 'Use the three orbs collection'),
            ('TEAPOT', 'Teapot', 'Use the teapot collection')
        ],
        default='ORBS_4'
    )

    def update_panel_location(self, context):
        """Update handler for panel location changes"""
        try:
            from . import ui
            ui.unregister_ui()
            ui.register_ui()

            print(f"Panel moved to {self.panel_location}")
        except Exception as e:
            print(f"Error updating panel location: {str(e)}")

    # Panel Location
    panel_location: EnumProperty(
        name="Panel Location",
        description="Where to display the HDRI controls panel",
        items=[
            ('NONE', 'None (Shortcut Only)', 'No permanent panel - use keyboard shortcut only'),
            ('VIEW3D_HEADER', '3D Viewport Header', 'Show panel in 3D Viewport header (default)'),
            ('VIEW3D_UI', '3D Viewport Sidebar (N-Panel)', 'Show panel in 3D Viewport sidebar'),
            ('PROPERTIES_WORLD', 'Properties Panel - World', 'Show panel in World properties'),
            ('PROPERTIES_MATERIAL', 'Properties Panel - Material', 'Show panel in Material properties'),
            ('PROPERTIES_RENDER', 'Properties Panel - Render', 'Show panel in Render properties'),
            ('NODE_EDITOR', 'Shader Editor Sidebar', 'Show panel in Shader Editor sidebar'),
            ('IMAGE_EDITOR', 'Image Editor Sidebar', 'Show panel in Image Editor sidebar'),
        ],
        default='VIEW3D_HEADER',
        update=update_panel_location
    )

    # Statistics and Previews
    preview_stats_total: IntProperty(default=0)
    preview_stats_completed: IntProperty(default=0)
    preview_stats_failed: IntProperty(default=0)
    preview_stats_time: FloatProperty(default=0.0)
    preview_stats_current_file: StringProperty(default="")
    is_generating: BoolProperty(default=False)

    # Proxy Statistics
    proxy_stats_total: IntProperty(default=0)
    proxy_stats_completed: IntProperty(default=0)
    proxy_stats_failed: IntProperty(default=0)
    proxy_stats_time: FloatProperty(default=0.0)
    proxy_stats_current_file: StringProperty(default="")
    is_proxy_generating: BoolProperty(default=False)

    # Visibility toggles
    show_updates: BoolProperty(default=False)
    show_shortcuts: BoolProperty(default=False)
    show_interface: BoolProperty(default=False)
    show_filetypes: BoolProperty(default=False)
    show_hdri_settings: BoolProperty(default=False)
    show_conflicts: BoolProperty(default=False)
    show_preview_generation: BoolProperty(default=False)
    show_preview_thumbnails: BoolProperty(default=False)
    show_preview_generation_settings: BoolProperty(default=False)
    show_preview_limit_settings: BoolProperty(default=False)
    show_proxy_generation: BoolProperty(default=False)
    show_proxy: BoolProperty(default=False)
    show_generation_stats: BoolProperty(default=False)
    preview_stats_visible: BoolProperty(default=False)
    show_render_engine: BoolProperty(default=False)
    show_backup_settings: BoolProperty(default=False)
    show_documentation: BoolProperty(default=False)
    show_proxy_settings: BoolProperty(default=False)
    show_cache_settings: BoolProperty(default=False)
    show_advanced_settings: BoolProperty(default=False)
    show_preview_thumbnails: BoolProperty(default=False)
    show_preview_generation_settings: BoolProperty(default=False)
    show_preview_limit_settings: BoolProperty(default=False)

    def find_keymap_conflicts(self, context):
        """Find all keymap items that conflict with current shortcut settings"""
        conflicts = []
        seen_conflicts = set()  # Track unique conflicts

        # Get current shortcut settings
        is_mac = sys.platform == 'darwin'
        current_key = self.popup_key
        current_ctrl = self.popup_ctrl
        current_shift = self.popup_shift
        current_alt = self.popup_alt
        current_oskey = self.popup_ctrl if is_mac else False

        # Check all keyconfig categories
        wm = context.window_manager
        keyconfigs_to_check = [
            ('Blender', wm.keyconfigs.default),
            ('Blender User', wm.keyconfigs.user),
            ('Addons', wm.keyconfigs.addon)
        ]

        for config_name, keyconfig in keyconfigs_to_check:
            if keyconfig:
                for keymap in keyconfig.keymaps:
                    for kmi in keymap.keymap_items:
                        if kmi.type == current_key and \
                           kmi.ctrl == (current_ctrl if not is_mac else False) and \
                           kmi.shift == current_shift and \
                           kmi.alt == current_alt and \
                           kmi.oskey == (current_ctrl if is_mac else False) and \
                           kmi.active:  # Only check active shortcuts

                            # Don't report our own shortcut as a conflict
                            if kmi.idname != "world.hdri_popup_controls":
                                # Create a unique identifier for this conflict
                                conflict_id = f"{kmi.idname}_{keymap.name}"

                                if conflict_id not in seen_conflicts:
                                    seen_conflicts.add(conflict_id)
                                    conflicts.append({
                                        'config': config_name,
                                        'keymap': keymap.name,
                                        'name': kmi.name or kmi.idname,
                                        'type': kmi.type,
                                        'ctrl': kmi.ctrl,
                                        'shift': kmi.shift,
                                        'alt': kmi.alt,
                                        'oskey': kmi.oskey
                                    })

        # Sort conflicts by config name and then by keymap name for consistent display
        conflicts.sort(key=lambda x: (x['config'], x['keymap'], x['name']))

        return conflicts

    def update_shortcut(self, context):
        """Update the keyboard shortcut"""
        # Import at function level to avoid circular imports
        from . import utils

        # Get addon keymaps reference from the main module
        addon_name = __package__.split('.')[0]
        addon_keymaps = sys.modules[addon_name].addon_keymaps

        # Remove existing shortcut
        utils.clear_keymaps(addon_keymaps)
        addon_keymaps.clear()

        # Add new shortcut
        utils.setup_keymap(addon_keymaps)

    def switch_render_engine(self, context):
        import os
        import shutil

        # First verify if the target engine is actually available
        if self.render_engine == 'VRAY_RENDER_RT':
            # Check if V-Ray is available in render engines
            try:
                # Try to temporarily set render engine to V-Ray
                old_engine = context.scene.render.engine
                context.scene.render.engine = 'VRAY_RENDER_RT'
                # If we get here, V-Ray is available
                # Restore original engine
                context.scene.render.engine = old_engine
            except:
                def draw_vray_error(self, context):
                    layout = self.layout
                    layout.label(text="V-Ray is not installed!", icon='ERROR')
                    layout.label(text="Please install the V-Ray plugin first.")
                    layout.separator()
                    layout.operator("preferences.addon_show", text="Open Addon Preferences").module = __name__

                context.window_manager.popup_menu(draw_vray_error, title="Render Engine Error", icon='ERROR')
                self.render_engine = 'CYCLES'
                return {'CANCELLED'}

        elif self.render_engine == 'octane':  # Changed from 'OCTANE' to 'octane'
            # Check for Octane installation
            try:
                import _octane
            except ImportError:
                def draw_octane_error(self, context):
                    layout = self.layout
                    layout.label(text="Octane is not installed!", icon='ERROR')
                    layout.label(text="Please install the Octane plugin first.")
                    layout.separator()
                    layout.operator("preferences.addon_show", text="Open Addon Preferences").module = __name__

                context.window_manager.popup_menu(draw_octane_error, title="Render Engine Error", icon='ERROR')
                # Revert preference to Cycles since we know it's always available
                self.render_engine = 'CYCLES'
                return {'CANCELLED'}

        try:
            # Save current render engine preference
            import json
            current_script_path = os.path.dirname(os.path.realpath(__file__))
            preferences_path = os.path.join(current_script_path, "preferences.json")

            try:
                with open(preferences_path, 'w') as f:
                    json.dump({
                        'render_engine': self.render_engine
                    }, f)
            except Exception as e:
                print(f"Could not save render engine preference: {str(e)}")

            # Actually switch the render engine
            context.scene.render.engine = self.render_engine

            # Setup the HDRI system for the selected render engine
            if hasattr(bpy.ops.world, "setup_hdri_nodes"):
                bpy.ops.world.setup_hdri_nodes()

            return {'FINISHED'}

        except Exception as e:
            print(f"Failed to switch render engine: {str(e)}")
            return {'CANCELLED'}

    def get_preview_icon(self, context=None):
        """Get the preview icon ID for an image"""
        if not self.preview_image or not os.path.exists(self.preview_image):
            print(f"Preview image not found: {self.preview_image}")
            return 0

        try:
            # If image is not already loaded, load it
            if self.preview_image not in bpy.data.images:
                img = bpy.data.images.load(self.preview_image)
                print(f"Loaded preview image: {self.preview_image}")
            else:
                img = bpy.data.images[self.preview_image]
                # Reload to make sure we have the latest version
                img.reload()
                print(f"Using existing preview image: {self.preview_image}")

            # Ensure the preview is generated
            if not img.has_data:
                print(f"Image has no data: {self.preview_image}")
                return 0

            # Some images might not have previews yet, generate them
            if not hasattr(img, 'preview') or not img.preview:
                img.gl_load()
                print(f"Generated preview for: {self.preview_image}")

            # Now get the icon ID
            if hasattr(img, 'preview') and img.preview and hasattr(img.preview, 'icon_id'):
                icon_id = img.preview.icon_id
                if icon_id == 0:
                    print(f"Preview icon_id is 0 for: {self.preview_image}")
                else:
                    print(f"Using icon_id {icon_id} for: {self.preview_image}")
                return icon_id
            else:
                print(f"No valid preview for: {self.preview_image}")
                return 0

        except Exception as e:
            print(f"Failed to load preview image '{self.preview_image}': {str(e)}")
            return 0

    def draw(self, context):
        from . import utils

        layout = self.layout
        addon_name = "Quick-HDRI-Controls-main"

        # Get icon based on selected engine
        icon_id = 0  # Default fallback
        try:
            icons = utils.get_icons()

            # Select icon based on current render engine
            if self.render_engine == 'CYCLES':
                icon = icons.get("cycles_icon")
                icon_id = icon.icon_id if icon else 0
            elif self.render_engine == 'octane':
                icon = icons.get("octane_icon")
                icon_id = icon.icon_id if icon else 0
            elif self.render_engine == 'VRAY_RENDER_RT':
                icon = icons.get("vray_icon")
                icon_id = icon.icon_id if icon else 0
        except Exception as e:
            print(f"Error loading icon: {str(e)}")

        # HDRI Directory and Render Engine
        main_box = layout.box()
        row = main_box.row()
        row.scale_y = 1.2

        split = row.split(factor=0.5)

        # HDRI Directory column
        dir_col = split.column()
        if not self.hdri_directory:
            dir_col.alert = True
        dir_col.prop(self, "hdri_directory", text="Directory")

        # Render Engine column
        engine_col = split.column()
        row = engine_col.row(align=True)
        row.prop(self, "render_engine", text="Engine", icon_value=icon_id)
        # Only show the apply button when actually registered
        if hasattr(bpy.ops.world, "apply_render_engine"):
            op = row.operator("world.apply_render_engine", text="", icon='PLAY')
            # Set target_engine property if the operator has it
            if op and hasattr(op, "target_engine"):
                op.target_engine = self.render_engine

        # Updates Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_updates",
                   icon='TRIA_DOWN' if getattr(self, 'show_updates', True) else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)
        header.label(text="Updates & Information", icon='FILE_REFRESH')

        if getattr(self, 'show_updates', True):
            # Main container with more modern layout
            main_col = box.column(align=True)

            # === UPDATE STATUS & CONTROLS (Card-like layout) ===
            status_box = main_col.box()

            # Top row with check controls
            top_row = status_box.row(align=True)
            top_row.scale_y = 1.1

            # Icon + toggle in left side
            left = top_row.row()
            left.prop(self, "enable_auto_update_check", text="Auto-Check at Startup")

            # Check now button with some separation
            right = top_row.row()
            right.alignment = 'RIGHT'
            right.operator("world.check_hdri_updates", text="Check Now", icon='FILE_REFRESH')

            # Separator for visual rhythm
            status_box.separator(factor=0.5)

            # Status indicator - changes based on current state
            if self.update_available:
                # Update available - show card-like alert
                alert = status_box.box()
                alert.alert = True  # Red coloring

                # Bold header centered
                alert_header = alert.row()
                alert_header.alignment = 'CENTER'
                alert_header.scale_y = 1.3
                alert_header.label(text="Update Available", icon='ERROR')

                # Action buttons in side-by-side layout
                action_row = alert.row(align=True)
                action_row.scale_y = 1.3

                # Left button - download
                download_op = action_row.operator("world.download_hdri_update", text="Download", icon='IMPORT')

                # Right button - revert
                revert_op = action_row.operator("world.revert_hdri_version", text="Revert", icon='LOOP_BACK')
            else:
                # Still provide revert option
                revert_row = status_box.row()
                revert_row.scale_y = 1.1
                revert_row.operator("world.revert_hdri_version", text="Revert to Previous Version", icon='LOOP_BACK')

            # === BACKUP SETTINGS (Tab-like design) ===
            main_col.separator(factor=1.0)

            # Header row styled like a tab
            backup_header = main_col.row(align=True)
            backup_header.scale_y = 1.1
            backup_header.prop(self, "show_backup_settings",
                              icon='TRIA_DOWN' if getattr(self, 'show_backup_settings', False) else 'TRIA_RIGHT',
                              icon_only=True, emboss=False)
            backup_header.label(text="Backup Settings", icon='FILE_BACKUP')

            if getattr(self, 'show_backup_settings', False):
                backup_box = main_col.box()

                # Clean toggle for enabling backups
                enable_row = backup_box.row()
                enable_row.prop(self, "enable_backups", text="Create Backup Before Updates")

                # Only show settings if backups are enabled
                if self.enable_backups:
                    # Indented settings in a panel
                    settings = backup_box.box()

                    # Put max backups in a clean row with label on left, control on right
                    max_row = settings.row()
                    max_row.label(text="Maximum Backups:")
                    max_row.prop(self, "max_backup_files", text="")

                    # Try to calculate backup stats
                    backup_count = 0
                    backup_size = "0 bytes"
                    try:
                        import os
                        addon_dir = os.path.dirname(os.path.realpath(__file__))
                        backups_dir = os.path.join(addon_dir, "backups")
                        if os.path.exists(backups_dir):
                            backup_files = [f for f in os.listdir(backups_dir) if f.endswith('.zip')]
                            backup_count = len(backup_files)

                            # Calculate total size
                            total_size = 0
                            for backup_file in backup_files:
                                total_size += os.path.getsize(os.path.join(backups_dir, backup_file))

                            # Format size
                            if total_size > 1024*1024:
                                backup_size = f"{total_size/(1024*1024):.1f} MB"
                            elif total_size > 1024:
                                backup_size = f"{total_size/1024:.1f} KB"
                            else:
                                backup_size = f"{total_size} bytes"
                    except:
                        pass

                    # Show backup stats in a clean 2-column layout
                    if backup_count > 0:
                        stats = settings.row()
                        stats.alignment = 'CENTER'
                        stats.label(text=f"{backup_count} backups", icon='FILE_TICK')
                        stats.label(text=f"{backup_size}", icon='DISK_DRIVE')

                    # Add delete button as a clearly destructive action
                    delete_row = settings.row()
                    delete_row.scale_y = 1.2
                    delete_row.operator("world.cleanup_hdri_backups", text="Delete All Backups", icon='TRASH')

            # === DOCUMENTATION SECTION (Modern card-style) ===
            main_col.separator(factor=1.0)

            # Documentation header
            docs_header = main_col.row(align=True)
            docs_header.scale_y = 1.1
            docs_header.prop(self, "show_documentation",
                            icon='TRIA_DOWN' if getattr(self, 'show_documentation', False) else 'TRIA_RIGHT',
                            icon_only=True, emboss=False)
            docs_header.label(text="Documentation & Resources", icon='HELP')

            if getattr(self, 'show_documentation', False):
                docs_box = main_col.box()

                # Arrange links in a neat grid
                # First row - primary links
                row1 = docs_box.row(align=True)
                row1.scale_y = 1.2

                # Documentation
                docs_op = row1.operator("wm.url_open", text="Documentation", icon='URL')
                docs_op.url = "https://github.com/mdreece/Quick-HDRI-Controls/tree/main"

                # Issues
                issues_op = row1.operator("wm.url_open", text="Report Issue", icon='ERROR')
                issues_op.url = "https://github.com/mdreece/Quick-HDRI-Controls/issues"

                # Changelog
                changelog_op = row1.operator("wm.url_open", text="Changelog", icon='FILE_TEXT')
                changelog_op.url = "https://github.com/mdreece/Quick-HDRI-Controls/blob/main/CHANGELOG.md"

                # Second row - support links
                row2 = docs_box.row(align=True)
                row2.scale_y = 1.2

                # Blender Fund
                fund_op = row2.operator("wm.url_open", text="Blender Fund", icon='FUND')
                fund_op.url = "https://fund.blender.org/"

                # Market
                market_op = row2.operator("wm.url_open", text="Blender Market", icon='WORLD')
                market_op.url = "https://blendermarket.com/products/quick-hdri-controls"

                # Add a clean separator
                docs_box.separator()

                # Tips section with more engaging layout
                tips_header = docs_box.row()
                tips_header.alignment = 'CENTER'
                tips_header.label(text="Quick Tips", icon='INFO')

                # Two-column layout for tips
                tips = docs_box.column()

                # First row of tips
                row1 = tips.row()
                col1 = row1.column()
                col1.label(text="• Use keyboard shortcuts for access", icon='KEYINGSET')
                col1.label(text="• Create proxies for large HDRIs", icon='IMAGE_PLANE')

                col2 = row1.column()
                col2.label(text="• Organize HDRIs by category", icon='FILE_FOLDER')
                col2.label(text="• Use PNG thumbnails for speed", icon='IMAGE_DATA')

        # Preview Thumbnails Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_preview_thumbnails",
                  icon='TRIA_DOWN' if self.show_preview_thumbnails else 'TRIA_RIGHT',
                  icon_only=True, emboss=False)
        header_split = header.split(factor=0.7)
        header_split.label(text="Preview Thumbnails", icon='IMAGE_DATA')

        # Status indicator
        status_row = header_split.row(align=True)
        status_row.alignment = 'RIGHT'
        if self.is_generating:
            status_row.alert = True
            status_row.label(text="Processing", icon='TIME')
        else:
            status_row.label(text="Ready", icon='CHECKMARK')

        if self.show_preview_thumbnails:
            main_col = box.column(align=True)
            main_col.separator()

            if self.is_generating:
                # Generating status
                status_box = main_col.box()
                status_box.alert = True

                grid = status_box.grid_flow(row_major=True, columns=2, even_columns=True)

                grid.label(text="Progress:")
                grid.label(text=f"{self.preview_stats_completed}/{self.preview_stats_total}")

                grid.label(text="Current File:")
                grid.label(text=self.preview_stats_current_file or "N/A")

                grid.label(text="Time Elapsed:")
                grid.label(text=f"{self.preview_stats_time:.2f} seconds")

            else:
                # Preview Generation Options
                gen_box = main_col.box()
                gen_header = gen_box.row()
                gen_header.prop(self, "show_preview_generation_settings",
                              icon='TRIA_DOWN' if getattr(self, 'show_preview_generation_settings', False) else 'TRIA_RIGHT',
                              icon_only=True, emboss=False)
                gen_header.label(text="Preview Generation", icon='PRESET')

                if getattr(self, 'show_preview_generation_settings', False):
                    gen_col = gen_box.column(align=True)

                    # Processing Mode
                    mode_row = gen_col.row(align=True)
                    mode_row.label(text="Processing Mode:", icon='MODIFIER')
                    mode_row.prop(self, "preview_generation_type", text="")

                    # Source Selection
                    if self.preview_generation_type != 'FULL_BATCH':
                        source_row = gen_col.row(align=True)
                        source_row.label(text="Source:", icon='FILEBROWSER')

                        if self.preview_generation_type == 'SINGLE':
                            source_row.prop(self, "preview_single_file", text="")
                        else:
                            source_row.prop(self, "preview_multiple_folder", text="")

                    # Quality Settings
                    quality_box = gen_col.box()
                    quality_header = quality_box.row()
                    quality_header.label(text="Quality Settings", icon='SETTINGS')

                    # Quality settings grid
                    quality_grid = quality_box.grid_flow(row_major=True, columns=2, even_columns=True)

                    quality_grid.label(text="Scene Type:")
                    quality_grid.prop(self, "preview_scene_type", text="")

                    quality_grid.label(text="Render Device:")
                    quality_grid.prop(self, "preview_render_device", text="")

                    quality_grid.label(text="Resolution:")
                    quality_grid.prop(self, "preview_resolution", text="%")

                    quality_grid.label(text="Render Samples:")
                    quality_grid.prop(self, "preview_samples", text="")

                    # Output Resolution Info
                    res_box = quality_box.box()
                    res_box.scale_y = 0.9
                    actual_x = int(1024 * (self.preview_resolution / 100))
                    actual_y = int(768 * (self.preview_resolution / 100))
                    res_box.label(text=f"Output Resolution: {actual_x} × {actual_y} pixels")

                    # Generation Button
                    gen_col.separator()
                    action_row = gen_col.row(align=True)
                    action_row.scale_y = 1.5

                    button_text = {
                        'SINGLE': 'Generate Preview',
                        'MULTIPLE': 'Generate Previews',
                        'FULL_BATCH': 'Generate All Previews'
                    }.get(self.preview_generation_type)

                    action_row.operator(
                        "world.generate_hdri_previews",
                        text=button_text,
                        icon='RENDER_STILL'
                    )

                # Preview Limit section
                preview_limit_box = main_col.box()
                preview_limit_header = preview_limit_box.row()
                preview_limit_header.prop(self, "show_preview_limit_settings",
                            icon='TRIA_DOWN' if getattr(self, 'show_preview_limit_settings', False) else 'TRIA_RIGHT',
                            icon_only=True, emboss=False)
                preview_limit_header.label(text="Preview Limit", icon='IMAGE_DATA')

                if getattr(self, 'show_preview_limit_settings', False):
                    limit_col = preview_limit_box.column(align=True)

                    # Dropdown for preview limit
                    limit_row = limit_col.row()
                    limit_row.label(text="Maximum Previews:")
                    limit_row.prop(self, "preview_limit", text="")

                    # Explanation for preview limit
                    explanation_box = limit_col.box()
                    explanation_box.scale_y = 0.9
                    if self.preview_limit == 0:
                        explanation_box.label(text="No limit: All HDRIs will be loaded", icon='INFO')
                    else:
                        explanation_box.label(text=f"Only the first {self.preview_limit} HDRIs will be shown", icon='RESTRICT_VIEW_OFF')

                # Generation Status
                if self.preview_stats_total > 0 and self.show_generation_stats:
                    status_box = main_col.box()
                    status_header = status_box.row()
                    status_header.label(text="Generation Complete", icon='CHECKMARK')

                    status_grid = status_box.grid_flow(row_major=True, columns=2, even_columns=True)

                    status_grid.label(text="Completed:")
                    status_grid.label(text=f"{self.preview_stats_completed}/{self.preview_stats_total}")

                    status_grid.label(text="Total Time:")
                    status_grid.label(text=f"{self.preview_stats_time:.2f} seconds")

                    clear_row = status_box.row()
                    clear_row.operator("world.clear_preview_stats", text="Clear Results", icon='X')

        # Proxy Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_proxy",
                    icon='TRIA_DOWN' if getattr(self, 'show_proxy', True) else 'TRIA_RIGHT',
                    icon_only=True, emboss=False)
        header.label(text="Proxy Settings", icon='COPY_ID')
        if getattr(self, 'show_proxy', True):
            col = box.column(align=True)

            # Proxy Settings
            settings_col = col.column(align=True)
            settings_col.prop(self, "default_proxy_resolution", text="Default Resolution")
            settings_col.prop(self, "default_proxy_mode", text="Default Application")

            cache_header = settings_col.row()
            cache_header.prop(self, "show_cache_settings",
                              icon='TRIA_DOWN' if getattr(self, 'show_cache_settings', True) else 'TRIA_RIGHT',
                              icon_only=True, emboss=False)
            cache_header.label(text="Cache Settings", icon='FILE_CACHE')

            if getattr(self, 'show_cache_settings', True):
                cache_box = settings_col.box()
                cache_col = cache_box.column(align=True)
                cache_col.prop(self, "proxy_cache_limit", text="Cache Size Limit (MB)")
                cache_col.operator("world.cleanup_hdri_proxies", text="Clear Proxy Cache", icon='TRASH')

            # Proxy Generation
            gen_header = settings_col.row()
            gen_header.prop(self, "show_proxy_generation",
                            icon='TRIA_DOWN' if getattr(self, 'show_proxy_generation', True) else 'TRIA_RIGHT',
                            icon_only=True, emboss=False)
            gen_header.label(text="Batch Proxy Generation", icon='RENDER_STILL')

            if getattr(self, 'show_proxy_generation', True):
                gen_box = settings_col.box()
                gen_col = gen_box.column(align=True)

                # Directory Selection
                row = gen_col.row(align=True)
                row.prop(self, "proxy_generation_directory", text="Folder Batch")

                # Resolution Selection
                row = box.row()
                row.prop(self, "proxy_generation_resolution", text="Resolution")

                gen_col.separator()

                # Generation Status
                if self.is_proxy_generating:
                    status_box = gen_col.box()
                    status_box.alert = True
                    status_box.label(text="Generating Proxies...", icon='TIME')

                    status_row = status_box.row(align=True)
                    status_row.label(text="Current File:")
                    status_row.label(text=self.proxy_stats_current_file)

                    progress_row = status_box.row(align=True)
                    progress_row.label(text="Progress:")
                    progress_row.label(text=f"{self.proxy_stats_completed}/{self.proxy_stats_total}")

                    time_row = status_box.row(align=True)
                    time_row.label(text="Elapsed Time:")
                    time_row.label(text=f"{self.proxy_stats_time:.2f} seconds")
                else:
                    # Generation Buttons
                    row = box.row(align=True)
                    row.scale_y = 1.5
                    sub = row.split(factor=0.5)
                    sub.operator("world.generate_hdri_proxies", text="Generate Proxies")
                    sub.operator("world.full_batch_hdri_proxies", text="Full Batch Process")

                # Generation Results
                if self.proxy_stats_total > 0 and not self.is_proxy_generating:
                    result_box = gen_col.box()

                    total_row = result_box.row(align=True)
                    total_row.label(text="Total Files:")
                    total_row.label(text=str(self.proxy_stats_total))

                    completed_row = result_box.row(align=True)
                    completed_row.label(text="Completed:")
                    completed_row.label(text=str(self.proxy_stats_completed))

                    failed_row = result_box.row(align=True)
                    failed_row.label(text="Failed:")
                    failed_row.label(text=str(self.proxy_stats_failed))

                    time_row = result_box.row(align=True)
                    time_row.label(text="Total Time:")
                    time_row.label(text=f"{self.proxy_stats_time:.2f} seconds")

                    # Clear Results Button
                    clear_row = result_box.row(align=True)
                    clear_row.operator("world.clear_proxy_stats", text="Clear Results", icon='X')

        # Keyboard Shortcuts Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_shortcuts", icon='TRIA_DOWN' if getattr(self, 'show_shortcuts', True) else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)
        header.label(text="Keyboard Shortcuts", icon='KEYINGSET')

        if getattr(self, 'show_shortcuts', True):
            main_col = box.column(align=True)

            # Two-column layout for shortcut configuration
            split_layout = main_col.split(factor=0.6)

            # Left column for configuration
            config_col = split_layout.column()
            config_box = config_col.box()

            # Heading for configuration column
            config_box.label(text="Configure Shortcut", icon='MODIFIER')

            # Grid layout for key selection elements
            grid = config_box.grid_flow(row_major=True, columns=2, even_columns=True)

            # Modifier keys with labeled columns in grid
            grid.label(text="Modifiers:")
            mod_row = grid.row(align=True)
            mod_row.scale_y = 1.2

            # Platform-specific modifiers
            if sys.platform == 'darwin':
                mod_row.prop(self, "popup_ctrl", text="⌘ Command", toggle=True)
                mod_row.prop(self, "popup_shift", text="⇧ Shift", toggle=True)
                mod_row.prop(self, "popup_alt", text="⌥ Option", toggle=True)
            else:
                mod_row.prop(self, "popup_ctrl", text="Ctrl", toggle=True)
                mod_row.prop(self, "popup_shift", text="Shift", toggle=True)
                mod_row.prop(self, "popup_alt", text="Alt", toggle=True)

            # Key selection row in grid
            grid.label(text="Key:")
            key_row = grid.row()
            key_row.scale_y = 1.2
            key_row.prop(self, "popup_key", text="")

            # Apply button under the grid
            apply_row = config_box.row()
            apply_row.scale_y = 1.5
            apply_row.scale_x = 1.2
            apply_row.alignment = 'CENTER'
            apply_row.operator("world.update_hdri_shortcut", text="Apply Changes", icon='CHECKMARK')

            # Mouse button tip
            tip_row = config_box.row()
            tip_row.scale_y = 0.8
            tip_row.alignment = 'CENTER'
            tip_row.label(text="Tip: Mouse buttons can also be used", icon='MOUSE_LMB')

            # Right column for current shortcut and conflicts
            status_col = split_layout.column()

            # Current shortcut display
            current_box = status_col.box()
            current_row = current_box.row()
            current_row.scale_y = 1.2
            current_row.alignment = 'CENTER'
            current_row.label(text="Current Shortcut", icon='KEYINGSET')

            # Build the shortcut representation
            shortcut_parts = []
            if self.popup_ctrl:
                shortcut_parts.append("⌘ Command" if sys.platform == 'darwin' else "Ctrl")
            if self.popup_shift:
                shortcut_parts.append("⇧ Shift")
            if self.popup_alt:
                shortcut_parts.append("⌥ Option" if sys.platform == 'darwin' else "Alt")
            shortcut_parts.append(self.popup_key)

            # Visual key combination display
            combination_row = current_box.row(align=True)
            combination_row.scale_y = 1.5
            combination_row.alignment = 'CENTER'

            # Display each part of the shortcut as a separate "key"
            for i, part in enumerate(shortcut_parts):
                # Add a plus symbol between keys
                if i > 0:
                    combination_row.label(text="+")

                # Create a button-like appearance for each key
                key_button = combination_row.row()
                key_button.alignment = 'CENTER'
                key_button.ui_units_x = max(3, len(part) * 0.6)  # Width based on text length
                key_button.scale_y = 0.8
                key_button.operator("wm.tool_set_by_id", text=part, emboss=True).name = "builtin.select"

            # Conflict detection heading
            status_col.separator(factor=0.8)

            # Get conflicts
            conflicts = self.find_keymap_conflicts(context)

            # Conflicts section with colored status indicator
            conflict_box = status_col.box()
            conflict_header = conflict_box.row()
            conflict_header.scale_y = 1.2

            # Visual conflict status indicator (with or without dropdown)
            if conflicts:
                conflict_header.prop(self, "show_conflicts",
                              icon='TRIA_DOWN' if self.show_conflicts else 'TRIA_RIGHT',
                              icon_only=True, emboss=False)
                status_row = conflict_header.row()
                status_row.alert = True
                status_row.label(text="Conflicts Detected", icon='ERROR')
            else:
                status_row = conflict_header.row()
                status_row.label(text="No Conflicts", icon='CHECKMARK')

            # Show conflict details if expanded and conflicts exist
            if self.show_conflicts and conflicts:
                conflict_count = len(conflicts)
                conflict_label = conflict_box.row()
                conflict_label.alignment = 'CENTER'
                conflict_label.label(text=f"{conflict_count} {'conflict' if conflict_count == 1 else 'conflicts'} found")

                # List first few conflicts in a compact format
                max_conflicts_to_show = min(3, conflict_count)
                for i in range(max_conflicts_to_show):
                    conflict = conflicts[i]
                    conflict_item = conflict_box.box()

                    # Create shortcut text
                    keys = []
                    if conflict['ctrl']:
                        keys.append('Ctrl' if not sys.platform == 'darwin' else '⌘')
                    if conflict['shift']:
                        keys.append('Shift')
                    if conflict['alt']:
                        keys.append('Alt')
                    if conflict['oskey'] and not sys.platform == 'darwin':
                        keys.append('OS')
                    keys.append(conflict['type'])
                    shortcut = ' + '.join(keys)

                    # Show conflict name and shortcut
                    name_row = conflict_item.row()
                    name_row.label(text=conflict['name'], icon='TOOL_SETTINGS')

                    # Show keymap location and shortcut
                    info_row = conflict_item.row(align=True)
                    info_row.scale_y = 0.8
                    info_row.label(text=f"{shortcut} in {conflict['config']}")

                # If there are more conflicts, show a count
                if conflict_count > max_conflicts_to_show:
                    more_row = conflict_box.row()
                    more_row.alignment = 'CENTER'
                    more_row.scale_y = 0.8
                    more_row.label(text=f"and {conflict_count - max_conflicts_to_show} more...")

                # Add detail button to show all conflicts
                detail_row = conflict_box.row(align=True)
                detail_row.alignment = 'CENTER'
                detail_row.scale_y = 1.0
                detail_row.operator("world.show_hdri_shortcut_conflicts", text="View All Conflicts", icon='VIEWZOOM')

        # HDRI Settings Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_hdri_settings",
                   icon='TRIA_DOWN' if getattr(self, 'show_hdri_settings', True) else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)
        header.label(text="HDRI Settings", icon='WORLD_DATA')

        if getattr(self, 'show_hdri_settings', True):
            settings_col = box.column(align=True)
            # FILE TYPES - Card style with visual checkboxes
            files_box = settings_col.box()

            # Card header with icon
            files_header = files_box.row(align=True)
            files_header.label(text="Supported File Types", icon='IMAGE_DATA')

            # File types in a more visual grid
            grid = files_box.grid_flow(row_major=True, columns=2, even_columns=True)

            # Each file type with appropriate icon
            grid.prop(self, "use_hdr", text="HDR Files (.hdr)", icon='FILE_IMAGE')
            grid.prop(self, "use_exr", text="OpenEXR Files (.exr)", icon='FILE_IMAGE')
            grid.prop(self, "use_png", text="PNG Files (.png)", icon='FILE_IMAGE')
            grid.prop(self, "use_jpg", text="JPEG Files (.jpg, .jpeg)", icon='FILE_IMAGE')

            # Separator for visual groups
            settings_col.separator(factor=0.7)

            # ROTATION SETTINGS - Card style with grouping
            rotation_box = settings_col.box()

            # Card header with icon
            rotation_header = rotation_box.row(align=True)
            rotation_header.label(text="Rotation Settings", icon='DRIVER_ROTATIONAL_DIFFERENCE')

            # Keep rotation option
            row = rotation_box.row()
            row.prop(self, "keep_rotation", text="Keep Rotation When Switching HDRIs")

            # Rotation step in an easy-to-use slider layout
            step_row = rotation_box.row(align=True)
            step_row.label(text="Rotation Step Size:")
            step_row.prop(self, "rotation_increment", text="")

            # Show a small preview of the step value
            preview_row = rotation_box.row()
            preview_row.alignment = 'CENTER'
            preview_row.scale_y = 0.8
            preview_row.label(text=f"Each click rotates by {self.rotation_increment}°")

            # Separator for visual groups
            settings_col.separator(factor=0.7)

            # STRENGTH SETTINGS - Card style
            strength_box = settings_col.box()

            # Card header with icon
            strength_header = strength_box.row(align=True)
            strength_header.label(text="Strength Settings", icon='NODE_COMPOSITING')

            # Max strength value in a slider layout
            max_row = strength_box.row(align=True)
            max_row.label(text="Maximum Strength Value:")
            max_row.prop(self, "strength_max", text="")

            # Preview of current setting
            guide_row = strength_box.row()
            guide_row.alignment = 'CENTER'
            guide_row.scale_y = 0.8
            guide_row.label(text=f"Slider maximum will be {self.strength_max:.1f}")

            # Separator for visual groups
            settings_col.separator(factor=0.7)

            # UI SETTINGS - Card style
            ui_box = settings_col.box()

            # PANEL LOCATION - Card style
            location_box = settings_col.box()

            # Card header with icon
            location_header = location_box.row(align=True)
            location_header.label(text="Panel Location", icon='WORKSPACE')

            # Panel location dropdown
            location_row = location_box.row(align=True)
            location_row.label(text="Display Location:")
            location_row.prop(self, "panel_location", text="")

            # Show description of current location
            desc_row = location_box.row()
            desc_row.alignment = 'CENTER'
            desc_row.scale_y = 0.8

            location_descriptions = {
                'NONE': "No panel shown - access via keyboard shortcut only",
                'VIEW3D_HEADER': "Appears as a popup in the 3D Viewport header",
                'VIEW3D_UI': "Appears in the 3D Viewport sidebar (press N to toggle)",
                'PROPERTIES_WORLD': "Appears in the World properties panel",
                'PROPERTIES_MATERIAL': "Appears in the Material properties panel",
                'PROPERTIES_RENDER': "Appears in the Render properties panel",
                'NODE_EDITOR': "Appears in the Shader Editor sidebar",
                'IMAGE_EDITOR': "Appears in the Image Editor sidebar"
            }

            current_desc = location_descriptions.get(self.panel_location, "")
            desc_row.label(text=current_desc)

            # Show shortcut info if NONE is selected
            if self.panel_location == 'NONE':
                shortcut_box = location_box.box()
                shortcut_box.alert = True

                # Build current shortcut display
                shortcut_parts = []
                if self.popup_ctrl:
                    shortcut_parts.append("⌘ Command" if sys.platform == 'darwin' else "Ctrl")
                if self.popup_shift:
                    shortcut_parts.append("⇧ Shift")
                if self.popup_alt:
                    shortcut_parts.append("⌥ Option" if sys.platform == 'darwin' else "Alt")
                shortcut_parts.append(self.popup_key)

                current_shortcut = " + ".join(shortcut_parts)

                shortcut_info = shortcut_box.row()
                shortcut_info.alignment = 'CENTER'
                shortcut_info.scale_y = 1.2
                shortcut_info.label(text=f"Press: {current_shortcut}", icon='HAND')

                shortcut_note = shortcut_box.row()
                shortcut_note.alignment = 'CENTER'
                shortcut_note.scale_y = 0.8
                shortcut_note.label(text="Configure shortcut in Keyboard Shortcuts section above")

            # Card header with icon
            ui_header = ui_box.row(align=True)
            ui_header.label(text="UI Settings", icon='PREFERENCES')

            # Layout settings in a grid for better organization
            grid = ui_box.grid_flow(row_major=True, columns=2, even_columns=True)

            # Compact UI option
            grid.prop(self, "use_compact_ui", text="Use Compact UI")

            # Panel width with visual slider
            width_row = ui_box.row(align=True)
            width_row.label(text="Panel Width:")
            width_row.prop(self, "ui_scale", text="")

            # Preview size with visual slider
            preview_row = ui_box.row(align=True)
            preview_row.label(text="Preview Size:")
            preview_row.prop(self, "preview_scale", text="")

            # Button scale with slider
            button_row = ui_box.row(align=True)
            button_row.label(text="Button Scale:")
            button_row.prop(self, "button_scale", text="")

            # Spacing scale with slider
            spacing_row = ui_box.row(align=True)
            spacing_row.label(text="Spacing Scale:")
            spacing_row.prop(self, "spacing_scale", text="")

            # Separator for visual groups
            settings_col.separator(factor=0.7)

            # FOLDER BROWSING - Card style
            folder_box = settings_col.box()

            # Card header with icon
            folder_header = folder_box.row(align=True)
            folder_header.label(text="Folder Browsing", icon='FILE_FOLDER')

            # Preview limit and sorting
            limit_row = folder_box.row()
            limit_row.label(text="Preview Limit:")
            limit_row.prop(self, "preview_limit", text="")

            # Preview sort method, only if limit is not zero
            if self.preview_limit > 0:
                sort_row = folder_box.row()
                sort_row.label(text="Sort Method:")
                sort_row.prop(self, "preview_sort", text="")

            # Pagination toggle
            folder_box.prop(self, "show_folder_pagination", text="Enable Folder Pagination")

            # Pagination settings, only if enabled
            if self.show_folder_pagination:
                page_row = folder_box.row(align=True)
                page_row.label(text="Folders Per Page:")
                page_row.prop(self, "folders_per_page", text="")


def refresh_previews(context):
    """Utility function to refresh previews from preferences module"""
    # We import here to avoid circular imports
    from .utils import get_hdri_previews

    print("Refreshing HDRI previews")
    pcoll = get_hdri_previews()
    pcoll.clear()

    # Force a cache reset
    if hasattr(get_hdri_previews, "cached_dir"):
        get_hdri_previews.cached_dir = None
    if hasattr(get_hdri_previews, "cached_items"):
        get_hdri_previews.cached_items = []

    print("HDRI previews refreshed")

def register_preferences():
    print("Registering Quick HDRI Controls preferences")

    # Check if the class is already registered
    try:
        # Try to unregister first if it exists
        bpy.utils.unregister_class(QuickHDRIPreferences)
        print("Unregistered existing QuickHDRIPreferences class")
    except (ValueError, RuntimeError):
        # Class wasn't registered, which is fine
        pass

    # Now register the class
    try:
        bpy.utils.register_class(QuickHDRIPreferences)
        print("Quick HDRI Controls preferences registered successfully")
    except ValueError as e:
        print(f"Error registering preferences: {str(e)}")
        # If it's still registered as a subclass, try a different approach
        if "already registered as a subclass" in str(e):
            print("Attempting to reload addon classes...")
            # Force reload by trying to get the class from the module
            import importlib
            import sys

            # Get the current module
            current_module = sys.modules[__name__]

            # Reload the module to clear any cached class definitions
            importlib.reload(current_module)

            # Try to register again with the reloaded class
            try:
                bpy.utils.register_class(current_module.QuickHDRIPreferences)
                print("Successfully registered preferences after module reload")
            except Exception as e2:
                print(f"Failed to register after reload: {str(e2)}")
                raise e2
        else:
            raise e

def unregister_preferences():
    print("Unregistering Quick HDRI Controls preferences")
    try:
        bpy.utils.unregister_class(QuickHDRIPreferences)
        print("Quick HDRI Controls preferences unregistered successfully")
    except (ValueError, RuntimeError) as e:
        print(f"Error unregistering preferences (may not be registered): {str(e)}")
        pass
