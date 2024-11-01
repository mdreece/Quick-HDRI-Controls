import urllib.request
import zipfile
import shutil
import tempfile
from datetime import datetime
from math import radians
import bpy
import re
import os
import sys
from bpy.types import (Panel, Operator, AddonPreferences, PropertyGroup)
from bpy.props import (FloatProperty, StringProperty, EnumProperty, 
                      CollectionProperty, PointerProperty, IntProperty, 
                      BoolProperty, FloatVectorProperty)
from bpy.app.handlers import persistent

bl_info = {
    "name": "Quick HDRI Controls",
    "author": "Dave Nectariad Rome",
    "version": (2, 3),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Header",
    "warning": "Alpha Version (in-development)",
    "description": "Quickly adjust world HDRI rotation and selection",
    "category": "3D View",
}

# Store keymap entries to remove them when unregistering
addon_keymaps = []

def get_hdri_previews():
    if not hasattr(get_hdri_previews, "preview_collection"):
        pcoll = bpy.utils.previews.new()
        get_hdri_previews.preview_collection = pcoll
    return get_hdri_previews.preview_collection

def generate_previews(self, context):
    """Generate preview items for HDRIs in current folder"""
    enum_items = []
    
    if not hasattr(context.scene, "hdri_settings"):
        return enum_items
        
    preferences = context.preferences.addons[__name__].preferences
    base_dir = preferences.hdri_directory
    
    # Use current_folder if set, otherwise use base directory
    current_dir = context.scene.hdri_settings.current_folder or base_dir
    
    if not current_dir or not os.path.exists(current_dir):
        return enum_items
        
    # Verify current directory is within base directory
    try:
        rel_path = os.path.relpath(current_dir, base_dir)
        if rel_path.startswith('..'):
            context.scene.hdri_settings.current_folder = base_dir
            current_dir = base_dir
    except ValueError:
        context.scene.hdri_settings.current_folder = base_dir
        current_dir = base_dir
    
    pcoll = get_hdri_previews()
    
    # Get enabled file types from preferences
    extensions = set()
    if preferences.use_hdr:
        extensions.add('.hdr')
    if preferences.use_exr:
        extensions.add('.exr')
    if preferences.use_png:
        extensions.add('.png')
    if preferences.use_jpg:
        extensions.update(('.jpg', '.jpeg'))
    
    # If no extensions are enabled, return empty list
    if not extensions:
        return enum_items
    
    image_paths = []
    
    # Only look for images in the current directory (not in subfolders)
    for fn in os.listdir(current_dir):
        if fn.lower().endswith(tuple(extensions)):
            image_paths.append(fn)
    
    # Add an empty option as the first item
    enum_items.append(('', 'None', '', 0, 0))
    
    # Add HDRIs
    for i, fn in enumerate(sorted(image_paths), 1):  # Start from 1 since 0 is used for empty
        filepath = os.path.join(current_dir, fn)
        
        if filepath not in pcoll:
            thumb = pcoll.load(filepath, filepath, 'IMAGE')
        else:
            thumb = pcoll[filepath]
            
        enum_items.append((
            filepath,
            os.path.splitext(fn)[0],
            "",
            thumb.icon_id,
            i
        ))
            
    return enum_items

def refresh_previews(self, context):
    """Refresh the preview collection when settings change"""
    pcoll = get_hdri_previews()
    pcoll.clear()
    
    # Reset current folder and preview when HDRI directory changes
    if hasattr(context.scene, "hdri_settings"):
        context.scene.hdri_settings.current_folder = self.hdri_directory
        context.scene.hdri_settings.hdri_preview = ''

def get_folders(context):
    """Get list of subfolders in HDRI directory"""
    preferences = context.preferences.addons[__name__].preferences
    base_dir = preferences.hdri_directory
    current_dir = context.scene.hdri_settings.current_folder

    if not current_dir:
        current_dir = base_dir
    
    items = []
    if not os.path.exists(current_dir):
        return items

    # Check if current directory is actually inside base directory
    try:
        rel_path = os.path.relpath(current_dir, base_dir)
        if rel_path.startswith('..'):
            # If we somehow got outside the base directory, reset to base
            context.scene.hdri_settings.current_folder = base_dir
            current_dir = base_dir
    except ValueError:
        # If on different drive or invalid path, reset to base
        context.scene.hdri_settings.current_folder = base_dir
        current_dir = base_dir

    # Add parent directory option only if we're in a subfolder of base_dir
    if current_dir != base_dir:
        items.append(("parent", "..", "Go to parent folder", 'FILE_PARENT', 0))

    # Add subfolders
    for i, dirname in enumerate(sorted(os.listdir(current_dir)), 1):
        full_path = os.path.join(current_dir, dirname)
        if os.path.isdir(full_path):
            # Verify this subdirectory is still within base_dir
            try:
                rel_path = os.path.relpath(full_path, base_dir)
                if not rel_path.startswith('..'):
                    items.append((full_path, dirname, "Enter folder", 'FILE_FOLDER', i))
            except ValueError:
                continue
    
    return items
    
def update_background_strength(self, context):
    if context.scene.world and context.scene.world.use_nodes:
        for node in context.scene.world.node_tree.nodes:
            if node.type == 'BACKGROUND':
                node.inputs['Strength'].default_value = self.background_strength

def check_for_update_on_startup():
    """Check for updates on Blender startup if enabled in preferences."""
    preferences = bpy.context.preferences.addons[__name__].preferences
    if not preferences.enable_auto_update_check:
        return  # Exit if auto-update is not enabled

    current_version = bl_info['version']
    online_version = None
    try:
        # Fetch online version from GitHub
        version_url = "https://raw.githubusercontent.com/mdreece/Quick-HDRI-Controls/main/__init__.py"
        req = urllib.request.Request(version_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            for line in content.split('\n'):
                if '"version":' in line:
                    version_numbers = re.findall(r'\d+', line)
                    if len(version_numbers) >= 2:
                        online_version = (int(version_numbers[0]), int(version_numbers[1]))
                    break

        # If the online version is higher, set the alert in user preferences
        if online_version and online_version > current_version:
            preferences.update_available = True
        else:
            preferences.update_available = False
    except Exception as e:
        print(f"Startup update check error: {str(e)}")

@persistent
def load_handler(dummy):
    """Ensure keyboard shortcuts are properly set after file load"""
    # Clear existing keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    # Re-add keymap with current preferences
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
        preferences = bpy.context.preferences.addons[__name__].preferences
        is_mac = sys.platform == 'darwin'
        
        kmi = km.keymap_items.new(
            HDRI_OT_popup_controls.bl_idname,
            type=preferences.popup_key,
            value='PRESS',
            oskey=preferences.popup_ctrl if is_mac else False,
            ctrl=preferences.popup_ctrl if not is_mac else False,
            shift=preferences.popup_shift,
            alt=preferences.popup_alt
        )
        addon_keymaps.append((km, kmi))

def ensure_world_nodes():
    """Ensure world nodes exist and are properly connected"""
    scene = bpy.context.scene
    
    # Create world if it doesn't exist
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")
    
    world = scene.world
    world.use_nodes = True
    
    # Set up world cycles settings
    if hasattr(world, "cycles"):
        world.cycles.sampling_method = 'MANUAL'
    
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    # Clear all nodes
    nodes.clear()
    
    # Create nodes
    node_output = nodes.new('ShaderNodeOutputWorld')
    node_background = nodes.new('ShaderNodeBackground')
    node_env = nodes.new('ShaderNodeTexEnvironment')
    node_mapping = nodes.new('ShaderNodeMapping')
    node_coord = nodes.new('ShaderNodeTexCoord')
    
    # Set initial strength
    if hasattr(scene, "hdri_settings"):
        node_background.inputs['Strength'].default_value = scene.hdri_settings.background_strength
    
    # Link nodes
    links.new(node_coord.outputs['Generated'], node_mapping.inputs['Vector'])
    links.new(node_mapping.outputs['Vector'], node_env.inputs['Vector'])
    links.new(node_env.outputs['Color'], node_background.inputs['Color'])
    links.new(node_background.outputs['Background'], node_output.inputs['Surface'])
    
    # Arrange nodes
    node_output.location = (600, 300)
    node_background.location = (300, 300)
    node_env.location = (0, 300)
    node_mapping.location = (-300, 300)
    node_coord.location = (-600, 300)
    
    return node_mapping, node_env, node_background

def has_hdri_files(context):
    """Check if current folder has any supported HDRI files"""
    preferences = context.preferences.addons[__name__].preferences
    current_dir = context.scene.hdri_settings.current_folder or preferences.hdri_directory
    
    if not current_dir or not os.path.exists(current_dir):
        return False
    
    # Get enabled file types
    extensions = set()
    if preferences.use_hdr:
        extensions.add('.hdr')
    if preferences.use_exr:
        extensions.add('.exr')
    if preferences.use_png:
        extensions.add('.png')
    if preferences.use_jpg:
        extensions.update(('.jpg', '.jpeg'))
    
    # Check if any files with supported extensions exist
    for fn in os.listdir(current_dir):
        if fn.lower().endswith(tuple(extensions)):
            return True
    
    return False

def has_active_hdri(context):
    """Check if there is an active HDRI loaded"""
    if context.scene.world and context.scene.world.use_nodes:
        for node in context.scene.world.node_tree.nodes:
            if node.type == 'TEX_ENVIRONMENT' and node.image:
                return True
    return False
    
class HDRI_OT_popup_controls(Operator):
    bl_idname = "world.hdri_popup_controls"
    bl_label = "HDRI Quick Controls"
    bl_description = "Show HDRI controls at cursor position"
    bl_options = {'REGISTER'}

    def draw(self, context):
        layout = self.layout
        # Use the panel's draw method for consistency
        HDRI_PT_controls.draw(self, context)

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        prefs = context.preferences.addons[__name__].preferences
        wm = context.window_manager
        return wm.invoke_popup(self, width=prefs.ui_scale * 20)

class HDRI_OT_check_updates(Operator):
    bl_idname = "world.check_hdri_updates"
    bl_label = "Check for Updates"
    bl_description = "Check if a new version is available on GitHub"

    def get_online_version(self):
        """Fetch version info from GitHub"""
        try:
            version_url = "https://raw.githubusercontent.com/mdreece/Quick-HDRI-Controls/main/__init__.py"
            req = urllib.request.Request(
                version_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
                
                for line in content.split('\n'):
                    if '"version":' in line:
                        version_numbers = re.findall(r'\d+', line)
                        if len(version_numbers) >= 2:
                            return (int(version_numbers[0]), int(version_numbers[1]))
        except Exception as e:
            print(f"Update check error: {str(e)}")
            return None
        return None

    def execute(self, context):
        current_version = bl_info['version']
        online_version = self.get_online_version()
        
        if online_version is None:
            self.report({'ERROR'}, "Could not connect to GitHub. Please check your internet connection.")
            return {'CANCELLED'}
        
        if online_version <= current_version:
            self.report({'INFO'}, f"Quick HDRI Controls is up to date (v{current_version[0]}.{current_version[1]})")
            return {'FINISHED'}
        
        def draw_popup(self, context):
            self.layout.label(text=f"New version available: v{online_version[0]}.{online_version[1]}")
            self.layout.label(text=f"Current version: v{current_version[0]}.{current_version[1]}")
            self.layout.operator("world.download_hdri_update", text="Download Update")
            
        context.window_manager.popup_menu(draw_popup, title="Update Available", icon='INFO')
        return {'FINISHED'}

class HDRI_OT_download_update(Operator):
    bl_idname = "world.download_hdri_update"
    bl_label = "Download Update"
    bl_description = "Download and install the latest version"
    
    def execute(self, context):
        try:
            addon_path = os.path.dirname(os.path.realpath(__file__))
            addon_name = os.path.basename(addon_path)
            
            update_url = "https://github.com/mdreece/Quick-HDRI-Controls/archive/main.zip"
            req = urllib.request.Request(
                update_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            self.report({'INFO'}, "Downloading update...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
                with urllib.request.urlopen(req) as response:
                    temp_zip.write(response.read())
                temp_zip_path = temp_zip.name
            
            self.report({'INFO'}, "Extracting update...")
            temp_dir = tempfile.mkdtemp()
            
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            extracted_folder = os.path.join(temp_dir, "Quick-HDRI-Controls-main")
            
            if not os.path.exists(extracted_folder):
                self.report({'ERROR'}, f"Could not find extracted folder at {extracted_folder}")
                return {'CANCELLED'}
            
            for root, dirs, files in os.walk(extracted_folder):
                rel_path = os.path.relpath(root, extracted_folder)
                dest_path = os.path.join(addon_path, rel_path)
                
                os.makedirs(dest_path, exist_ok=True)
                
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dest_path, file)
                    try:
                        shutil.copy2(src_file, dst_file)
                    except Exception as e:
                        self.report({'ERROR'}, f"Failed to copy {file}: {str(e)}")
            
            try:
                os.remove(temp_zip_path)
                shutil.rmtree(temp_dir)
            except Exception as e:
                self.report({'WARNING'}, f"Failed to clean up temporary files: {str(e)}")
            
            self.report({'INFO'}, "Update complete! Please restart Blender to apply changes.")
            return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Update failed: {str(e)}")
            print(f"Detailed error: {str(e)}")
            return {'CANCELLED'}

class HDRI_OT_change_folder(Operator):
    bl_idname = "world.change_hdri_folder"
    bl_label = "Change Folder"
    bl_description = "Change current HDRI folder"
    
    folder_path: StringProperty()
    
    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        base_dir = preferences.hdri_directory
        hdri_settings = context.scene.hdri_settings
        
        if self.folder_path == "parent":
            current = hdri_settings.current_folder
            new_path = os.path.dirname(current)
            
            try:
                rel_path = os.path.relpath(new_path, base_dir)
                if rel_path.startswith('..'):
                    self.report({'WARNING'}, "Cannot navigate above HDRI directory")
                    return {'CANCELLED'}
            except ValueError:
                self.report({'WARNING'}, "Invalid path")
                return {'CANCELLED'}
                
            hdri_settings.current_folder = new_path
        else:
            try:
                rel_path = os.path.relpath(self.folder_path, base_dir)
                if rel_path.startswith('..'):
                    self.report({'WARNING'}, "Cannot navigate outside HDRI directory")
                    return {'CANCELLED'}
                hdri_settings.current_folder = self.folder_path
            except ValueError:
                self.report({'WARNING'}, "Invalid path")
                return {'CANCELLED'}
        
        # Clear previews
        pcoll = get_hdri_previews()
        pcoll.clear()
        
        # Get the first available HDRI in the new folder
        current_dir = hdri_settings.current_folder
        if current_dir and os.path.exists(current_dir):
            extensions = set()
            if preferences.use_hdr:
                extensions.add('.hdr')
            if preferences.use_exr:
                extensions.add('.exr')
            if preferences.use_png:
                extensions.add('.png')
            if preferences.use_jpg:
                extensions.update(('.jpg', '.jpeg'))
            
            for fn in sorted(os.listdir(current_dir)):
                if fn.lower().endswith(tuple(extensions)):
                    hdri_settings.hdri_preview = os.path.join(current_dir, fn)
                    break
        
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        return {'FINISHED'}

class HDRI_OT_reset_rotation(Operator):
    bl_idname = "world.reset_hdri_rotation"
    bl_label = "Reset HDRI Rotation"
    bl_description = "Reset all rotation values to 0"
    
    def execute(self, context):
        world = context.scene.world
        if world and world.use_nodes:
            mapping = None
            for node in world.node_tree.nodes:
                if node.type == 'MAPPING':
                    mapping = node
                    break
            
            if mapping:
                mapping.inputs['Rotation'].default_value = (0, 0, 0)
        
        return {'FINISHED'}

class HDRI_OT_reset_to_previous(Operator):
    bl_idname = "world.reset_to_previous_hdri"
    bl_label = "Reset to Previous HDRI"
    bl_description = "Reset to the previously loaded HDRI"
    
    def execute(self, context):
        hdri_settings = context.scene.hdri_settings
        
        if not hdri_settings.previous_hdri_path:
            self.report({'WARNING'}, "No previous HDRI available")
            return {'CANCELLED'}
        
        # Restore previous state
        mapping, env_tex, node_background = ensure_world_nodes()
        
        if hdri_settings.previous_hdri_path:
            img = bpy.data.images.load(hdri_settings.previous_hdri_path, check_existing=True)
            env_tex.image = img
            
        mapping.inputs['Rotation'].default_value = hdri_settings.previous_rotation
        node_background.inputs['Strength'].default_value = hdri_settings.previous_strength
        
        return {'FINISHED'}

class HDRI_OT_quick_rotate(Operator):
    bl_idname = "world.quick_rotate_hdri"
    bl_label = "Quick Rotate HDRI"
    bl_description = "Rotate HDRI by the increment set in preferences"
    
    axis: IntProperty(
        name="Axis",
        description="Rotation axis (0=X, 1=Y, 2=Z)",
        default=0
    )
    
    direction: IntProperty(
        name="Direction",
        description="Rotation direction (1 or -1)",
        default=1
    )
    
    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        world = context.scene.world
        
        if world and world.use_nodes:
            for node in world.node_tree.nodes:
                if node.type == 'MAPPING':
                    current_rotation = list(node.inputs['Rotation'].default_value)
                    increment_in_radians = radians(preferences.rotation_increment)
                    current_rotation[self.axis] += (self.direction * increment_in_radians)
                    node.inputs['Rotation'].default_value = current_rotation
                    break
                    
        return {'FINISHED'}

class HDRI_OT_reset_strength(Operator):
    bl_idname = "world.reset_hdri_strength"
    bl_label = "Reset HDRI Strength"
    bl_description = "Reset strength value to 1.0"
    
    def execute(self, context):
        context.scene.hdri_settings.background_strength = 1.0
        return {'FINISHED'}

class HDRI_OT_setup_nodes(Operator):
    bl_idname = "world.setup_hdri_nodes"
    bl_label = "Setup HDRI Nodes"
    bl_description = "Create and setup the required nodes for HDRI control"
    
    def execute(self, context):
        ensure_world_nodes()
        return {'FINISHED'}

class HDRI_OT_load_selected(Operator):
    bl_idname = "world.load_selected_hdri"
    bl_label = "Load Selected HDRI"
    bl_description = "Load the selected HDRI"
    
    def execute(self, context):
        filepath = context.scene.hdri_settings.hdri_preview
        
        if not filepath:
            self.report({'INFO'}, "No HDRI selected")
            return {'CANCELLED'}
            
        if not os.path.exists(filepath):
            self.report({'ERROR'}, "HDRI file not found")
            return {'CANCELLED'}
        
        hdri_settings = context.scene.hdri_settings
        
        # Store current state as previous
        world = context.scene.world
        if world and world.use_nodes:
            for node in world.node_tree.nodes:
                if node.type == 'TEX_ENVIRONMENT' and node.image:
                    hdri_settings.previous_hdri_path = node.image.filepath
                elif node.type == 'MAPPING':
                    hdri_settings.previous_rotation = node.inputs['Rotation'].default_value.copy()
                elif node.type == 'BACKGROUND':
                    hdri_settings.previous_strength = node.inputs['Strength'].default_value
        
        # Set up nodes
        mapping, env_tex, node_background = ensure_world_nodes()
        
        # Load the new image
        img = bpy.data.images.load(filepath, check_existing=True)
        env_tex.image = img
        
        # Keep rotation if enabled
        preferences = context.preferences.addons[__name__].preferences
        if not preferences.keep_rotation:
            mapping.inputs['Rotation'].default_value = (0, 0, 0)
        
        return {'FINISHED'}

class HDRI_OT_update_shortcut(Operator):
    bl_idname = "world.update_hdri_shortcut"
    bl_label = "Update Shortcut"
    bl_description = "Apply the new keyboard shortcut"
    
    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        preferences.update_shortcut(context)
        self.report({'INFO'}, "Shortcut updated successfully")
        return {'FINISHED'}
        
class HDRISettings(PropertyGroup):
    hdri_preview: EnumProperty(
        items=generate_previews,
        name="HDRI Preview",
        description="Preview of available HDRIs",
        update=None 
    )
    
    current_folder: StringProperty(
        name="Current Folder",
        description="Current HDRI folder being viewed",
        default="",
        subtype='DIR_PATH'
    )
    
    show_preview: BoolProperty(
        name="Show Preview",
        description="Show/Hide HDRI Preview section",
        default=True
    )
    
    show_rotation: BoolProperty(
        name="Show Rotation",
        description="Show/Hide Rotation Controls section",
        default=True
    )
    
    background_strength: FloatProperty(
        name="Strength",
        description="Background strength multiplier",
        default=1.0,
        min=0.0,
        soft_max=100.0,
        step=0.1,
        precision=3,
        update=update_background_strength
    )
    
    show_browser: BoolProperty(
        name="Show Browser",
        description="Show/Hide Folder Browser section",
        default=True
    )
    
    # Store previous HDRI state
    previous_hdri_path: StringProperty(
        name="Previous HDRI Path",
        description="Path to the previously loaded HDRI",
        default=""
    )
    
    previous_rotation: FloatVectorProperty(
        name="Previous Rotation",
        description="Previous rotation values",
        size=3,
        default=(0.0, 0.0, 0.0)
    )
    
    previous_strength: FloatProperty(
        name="Previous Strength",
        description="Previous strength value",
        default=1.0
    )

class QuickHDRIPreferences(AddonPreferences):
    bl_idname = __name__

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

    # Keyboard shortcut properties
    popup_key: EnumProperty(
        name="Key",
        description="Key for the popup menu shortcut",
        items=[
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

    # Directory and File Type Settings
    hdri_directory: StringProperty(
        name="HDRI Directory",
        subtype='DIR_PATH',
        description="Directory containing HDRI files",
        default="",
        update=lambda self, context: refresh_previews(self, context)
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
        max=2.0,
        step=0.05
    )
    
    spacing_scale: FloatProperty(
        name="Spacing Scale",
        description="Scale of UI element spacing",
        default=1.0,
        min=0.5,
        max=2.0,
        step=0.1
    )
    
    # Visual Settings
    use_compact_ui: BoolProperty(
        name="Compact UI",
        description="Use compact UI layout",
        default=True
    )
    
    show_file_path: BoolProperty(
        name="Show Full Path",
        description="Show full file path instead of relative path",
        default=False
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

    def update_shortcut(self, context):
        """Update the keyboard shortcut"""
        # Remove existing shortcut
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
        addon_keymaps.clear()
        
        # Add new shortcut
        wm = context.window_manager
        kc = wm.keyconfigs.addon
        if kc:
            km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
            
            # Handle platform-specific keys
            is_mac = sys.platform == 'darwin'
            
            kmi = km.keymap_items.new(
                HDRI_OT_popup_controls.bl_idname,
                type=self.popup_key,
                value='PRESS',
                oskey=self.popup_ctrl if is_mac else False,  # Command key for MacOS
                ctrl=self.popup_ctrl if not is_mac else False,  # Ctrl key for Windows/Linux
                shift=self.popup_shift,
                alt=self.popup_alt
            )
            addon_keymaps.append((km, kmi))

    def draw(self, context):
        layout = self.layout
        is_mac = sys.platform == 'darwin'

        # Header with introduction and quick access to the directory
        box = layout.box()
        box.label(text="Quick HDRI Controls", icon='WORLD')
        box.label(text="Easily adjust world HDRI rotation and selection.")
        box.prop(self, "hdri_directory", text="HDRI Directory")

        # Automatic Updates & Information
        box = layout.box()
        box.label(text="Automatic Updates & Information", icon='SYSTEM')
    
        # Auto-update and documentation links
        row = box.row(align=True)
        row.prop(self, "enable_auto_update_check", text="Auto-Check for Updates")
        row.operator(
            "wm.url_open",
            text="Documentation",
            icon='URL'
        ).url = "https://github.com/mdreece/Quick-HDRI-Controls/tree/main"
    
        # Check and download updates if available
        row = box.row(align=True)
        row.operator("world.check_hdri_updates", text="Check for Updates", icon='FILE_REFRESH')
        if self.update_available:
            row.operator("world.download_hdri_update", text="Download Update")

        # Keyboard Shortcuts
        box = layout.box()
        box.label(text="Keyboard Shortcuts", icon='KEYINGSET')
    
        # Current shortcut display
        current_shortcut = []
        if self.popup_ctrl:
            current_shortcut.append("⌘ Command" if is_mac else "Ctrl")
        if self.popup_shift:
            current_shortcut.append("⇧ Shift")
        if self.popup_alt:
            current_shortcut.append("⌥ Option" if is_mac else "Alt")
        current_shortcut.append(self.popup_key)
    
        row = box.row()
        row.label(text="Current Shortcut: " + " + ".join(current_shortcut))
    
        # Shortcut configuration
        col = box.column(align=True)
        row = col.row(align=True)
    
        if is_mac:
            row.prop(self, "popup_ctrl", text="⌘ Command", toggle=True)
            row.prop(self, "popup_shift", text="⇧ Shift", toggle=True)
            row.prop(self, "popup_alt", text="⌥ Option", toggle=True)
        else:
            row.prop(self, "popup_ctrl", text="Ctrl", toggle=True)
            row.prop(self, "popup_shift", text="Shift", toggle=True)
            row.prop(self, "popup_alt", text="Alt", toggle=True)
    
        row = col.row()
        row.prop(self, "popup_key", text="Key")
    
        # Apply button
        box.operator("world.update_hdri_shortcut", text="Apply Shortcut Change")

        # User Interface Settings
        box = layout.box()
        box.label(text="User Interface Settings", icon='PREFERENCES')
    
        # UI Layout Settings
        col = box.column(align=True)
        col.label(text="Layout Settings:")
        col.prop(self, "ui_scale", text="Panel Width")
        col.prop(self, "preview_scale", text="Preview Size")
        col.prop(self, "button_scale", text="Button Scale")
        col.prop(self, "spacing_scale", text="Spacing Scale")
    
        # Visual Settings
        col = box.column(align=True)
        col.label(text="Visual Settings:")
        col.prop(self, "show_file_path", text="Show Full Path in Browser")
        col.prop(self, "show_strength_slider", text="Show Strength Slider")
        col.prop(self, "show_rotation_values", text="Show Rotation Values")

        # File Filters & Settings
        box = layout.box()
        box.label(text="File Filters & Settings", icon='FILE_FOLDER')
    
        # File type toggles
        row = box.row(align=True)
        row.label(text="Supported File Types:")
        row = box.row(align=True)
        row.prop(self, "use_hdr", toggle=True)
        row.prop(self, "use_exr", toggle=True)
        row.prop(self, "use_png", toggle=True)
        row.prop(self, "use_jpg", toggle=True)

        # HDRI Settings
        box = layout.box()
        box.label(text="HDRI Settings", icon='WORLD_DATA')
    
        col = box.column(align=True)
        col.prop(self, "keep_rotation", text="Keep Rotation When Switching HDRIs")
        col.prop(self, "strength_max", text="Maximum Strength Value")
        col.prop(self, "rotation_increment", text="Rotation Step Size")
        
class HDRI_OT_toggle_visibility(Operator):
    bl_idname = "world.toggle_hdri_visibility"
    bl_label = "Toggle HDRI Visibility"
    bl_description = "Toggle HDRI background visibility in render"
    
    def execute(self, context):
        world = context.scene.world
        if world and world.use_nodes:
            # Toggle visibility in world settings
            world.cycles.sampling_method = 'MANUAL'  # Ensure we can modify visibility
            
            # Get current state from background node
            background_node = None
            for node in world.node_tree.nodes:
                if node.type == 'BACKGROUND':
                    background_node = node
                    break
            
            if background_node:
                # Toggle visibility by connecting/disconnecting from output
                world_output = None
                for node in world.node_tree.nodes:
                    if node.type == 'OUTPUT_WORLD':
                        world_output = node
                        break
                
                if world_output:
                    # Check if currently connected
                    is_connected = False
                    for link in world.node_tree.links:
                        if (link.from_node == background_node and 
                            link.to_node == world_output and 
                            link.to_socket.name == 'Surface'):
                            is_connected = True
                            world.node_tree.links.remove(link)
                            break
                    
                    if not is_connected:
                        # Reconnect if it was disconnected
                        world.node_tree.links.new(
                            background_node.outputs['Background'],
                            world_output.inputs['Surface']
                        )
                    
                    # Force viewport update
                    for area in context.screen.areas:
                        area.tag_redraw()
                    
                    return {'FINISHED'}
        
        return {'CANCELLED'}
            
class HDRI_PT_controls(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "HDRI Controls"
    
    def draw(self, context):
        preferences = context.preferences.addons[__name__].preferences
        self.bl_ui_units_x = preferences.ui_scale
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        hdri_settings = context.scene.hdri_settings
        
        main_column = layout.column(align=True)
        
        # Footer at the start
        footer = main_column.row(align=True)
        footer.scale_y = 0.8
        
        # Add separator after footer
        main_column.separator(factor=0.5 * preferences.spacing_scale)
        
        # Update available notification
        if preferences.update_available:
            row = main_column.row()
            row.alert = True
            row.label(text="HDRI Controls - Update Available!", icon='ERROR')
            row.operator("world.download_hdri_update", text="Download Update")
        
        # Early returns with styled messages
        if not preferences.hdri_directory:
            box = main_column.box()
            box.alert = True
            col = box.column(align=True)
            col.scale_y = 1.2 * preferences.button_scale
            col.label(text="HDRI Directory Not Set", icon='ERROR')
            col.operator("preferences.addon_show", text="Open Preferences", icon='PREFERENCES').module = __name__
            return
            
        world = context.scene.world
        if not world or not world.use_nodes:
            box = main_column.box()
            col = box.column(align=True)
            col.scale_y = 1.2 * preferences.button_scale
            col.operator("world.setup_hdri_nodes", 
                text="Initialize HDRI System",
                icon='WORLD_DATA')
            return

        # Get node references
        mapping = None
        env_tex = None
        background = None
        
        for node in world.node_tree.nodes:
            if node.type == 'MAPPING':
                mapping = node
            elif node.type == 'TEX_ENVIRONMENT':
                env_tex = node
            elif node.type == 'BACKGROUND':
                background = node

        if not mapping or not env_tex:
            box = main_column.box()
            box.alert = True
            col = box.column(align=True)
            col.scale_y = 1.2 * preferences.button_scale
            col.operator("world.setup_hdri_nodes", 
                text="Repair HDRI System",
                icon='FILE_REFRESH')
            return

        # Main UI
        # Folder Browser Section
        browser_box = main_column.box()
        row = browser_box.row(align=True)
        row.scale_y = preferences.button_scale
        row.prop(hdri_settings, "show_browser", 
                icon='TRIA_DOWN' if hdri_settings.show_browser else 'TRIA_RIGHT',
                icon_only=True)
        sub = row.row(align=True)
        sub.alert = False
        sub.active = hdri_settings.show_browser
        sub.label(text="Folder Browser", icon='FILE_FOLDER')

        if hdri_settings.show_browser:
            browser_box.scale_y = preferences.button_scale
        
            # Current path display
            current_folder = context.scene.hdri_settings.current_folder
            base_dir = preferences.hdri_directory
        
            if current_folder:
                try:
                    if os.path.normpath(current_folder) == os.path.normpath(base_dir):
                        display_path = "/ HDRI" if not preferences.show_file_path else base_dir
                        browser_box.label(text=display_path, icon='WORLD_DATA')
                    else:
                        if preferences.show_file_path:
                            display_path = current_folder
                        else:
                            rel_path = os.path.relpath(current_folder, base_dir)
                            display_path = f"/ {rel_path}"
                        browser_box.label(text=display_path, icon='FILE_FOLDER')
                except ValueError:
                    context.scene.hdri_settings.current_folder = base_dir
                    browser_box.label(text="/ Home", icon='HOME')
        
            # Folder navigation grid
            folders = get_folders(context)
            if folders:
                grid = browser_box.grid_flow(row_major=True, columns=3, align=True)
                grid.scale_y = preferences.button_scale
                for folder_path, name, _, icon, _ in folders:
                    op = grid.operator("world.change_hdri_folder",
                        text=name,
                        icon=icon,
                        depress=(folder_path == current_folder))
                    op.folder_path = folder_path

        main_column.separator(factor=0.5 * preferences.spacing_scale)
        
        # HDRI Preview Section
        if has_hdri_files(context):
            preview_box = main_column.box()
            row = preview_box.row(align=True)
            row.scale_y = preferences.button_scale
            row.prop(hdri_settings, "show_preview", 
                    icon='TRIA_DOWN' if hdri_settings.show_preview else 'TRIA_RIGHT',
                    icon_only=True)
            sub = row.row(align=True)
            sub.alert = False
            sub.active = hdri_settings.show_preview
            sub.label(text="HDRI Selection", icon='IMAGE_DATA')
            
            if hdri_settings.show_preview:
                preview_box.scale_y = preferences.button_scale
                
                # Show current HDRI name
                if env_tex and env_tex.image:
                    row = preview_box.row()
                    row.alert = False
                    row.alignment = 'CENTER'
                    row.scale_y = preferences.button_scale
                    row.label(text=env_tex.image.name, icon='CHECKMARK')
                    preview_box.separator(factor=0.5 * preferences.spacing_scale)
                
                preview_box.template_icon_view(
                    hdri_settings, "hdri_preview",
                    show_labels=True,
                    scale=preferences.preview_scale
                )
                
                # Load and Reset buttons row
                row = preview_box.row(align=True)
                row.scale_y = 1.2 * preferences.button_scale
                
                # Load button
                row.operator("world.load_selected_hdri",
                    text="Load HDRI",
                    icon='IMPORT')
                
                # Reset button
                sub_row = row.row(align=True)
                sub_row.enabled = bool(hdri_settings.previous_hdri_path)
                sub_row.operator("world.reset_to_previous_hdri",
                    text="Reset HDRI",
                    icon='LOOP_BACK')
            
            main_column.separator(factor=0.5 * preferences.spacing_scale)
        
        # HDRI Settings Section (when an HDRI is loaded)
        if has_active_hdri(context):
            # Rotation Controls Section
            rotation_box = main_column.box()
            row = rotation_box.row(align=True)
            row.scale_y = preferences.button_scale
            row.prop(hdri_settings, "show_rotation", 
                    icon='TRIA_DOWN' if hdri_settings.show_rotation else 'TRIA_RIGHT',
                    icon_only=True)
            sub = row.row(align=True)
            sub.alert = False
            sub.active = hdri_settings.show_rotation
            sub.label(text="HDRI Settings", icon='DRIVER_ROTATIONAL_DIFFERENCE')
            
            if hdri_settings.show_rotation:
                sub.operator("world.reset_hdri_rotation", text="", icon='LOOP_BACK')
                if preferences.show_strength_slider:
                    sub.operator("world.reset_hdri_strength", text="", icon='FILE_REFRESH')
                
                # Add visibility toggle
                # Check if background is connected to determine visibility
                is_visible = False
                if context.scene.world and context.scene.world.use_nodes:
                    background_node = None
                    world_output = None
                    for node in context.scene.world.node_tree.nodes:
                        if node.type == 'BACKGROUND':
                            background_node = node
                        elif node.type == 'OUTPUT_WORLD':
                            world_output = node
                    
                    if background_node and world_output:
                        for link in context.scene.world.node_tree.links:
                            if (link.from_node == background_node and 
                                link.to_node == world_output and 
                                link.to_socket.name == 'Surface'):
                                is_visible = True
                                break
                
                sub.operator("world.toggle_hdri_visibility",
                    text="",
                    icon='HIDE_OFF' if is_visible else 'HIDE_ON',
                    depress=is_visible)

                # Keep Rotation toggle
                row = rotation_box.row(align=True)
                row.prop(preferences, "keep_rotation", 
                    text="",
                    icon='LINKED' if preferences.keep_rotation else 'UNLINKED'
                )
            
                # Layout based on compact mode
                if preferences.use_compact_ui:
                    # Compact layout
                    col = rotation_box.column(align=True)
                    col.scale_y = preferences.button_scale
                    col.use_property_split = True
                    
                    if mapping:
                        # X Rotation
                        row = col.row(align=True)
                        row.prop(mapping.inputs['Rotation'], "default_value", index=0, text="X°")
                        sub = row.row(align=True)
                        sub.scale_x = 1.0
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                        op.axis = 0
                        op.direction = -1
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                        op.axis = 0
                        op.direction = 1
                        
                        # Y Rotation
                        row = col.row(align=True)
                        row.prop(mapping.inputs['Rotation'], "default_value", index=1, text="Y°")
                        sub = row.row(align=True)
                        sub.scale_x = 1.0
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                        op.axis = 1
                        op.direction = -1
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                        op.axis = 1
                        op.direction = 1
                        
                        # Z Rotation
                        row = col.row(align=True)
                        row.prop(mapping.inputs['Rotation'], "default_value", index=2, text="Z°")
                        sub = row.row(align=True)
                        sub.scale_x = 1.0
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                        op.axis = 2
                        op.direction = -1
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                        op.axis = 2
                        op.direction = 1
                    
                    if preferences.show_strength_slider:
                        col.separator()
                        col.prop(hdri_settings, "background_strength", text="Strength")
                else:
                    # Split layout
                    split = rotation_box.split(factor=0.5)
                    
                    # Rotation column
                    col = split.column(align=True)
                    col.scale_y = preferences.button_scale
                    col.use_property_split = True
                    col.label(text="Rotation:")
                    
                    if mapping:
                        for i, axis in enumerate(['X°', 'Y°', 'Z°']):
                            row = col.row(align=True)
                            row.prop(mapping.inputs['Rotation'], "default_value", index=i, text=axis)
                            sub = row.row(align=True)
                            sub.scale_x = 0.5
                            op = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                            op.axis = i
                            op.direction = -1
                            op = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                            op.axis = i
                            op.direction = 1
                    
                    # Strength column
                    if preferences.show_strength_slider:
                        col = split.column(align=True)
                        col.scale_y = preferences.button_scale
                        col.use_property_split = True
                        col.label(text="Strength:")
                        col.prop(hdri_settings, "background_strength", text="Value")
        
        main_column.separator(factor=1.0 * preferences.spacing_scale)
        
        # Footer
        footer = main_column.row(align=True)
        footer.scale_y = 0.8
        footer.label(text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}")
        
        settings_btn = footer.operator(
            "preferences.addon_show",
            text="",
            icon='PREFERENCES',
            emboss=False,
        )
        settings_btn.module = __name__
                    
def draw_hdri_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.popover(panel="HDRI_PT_controls", text="HDRI Controls")
    
# Registration
classes = (
    QuickHDRIPreferences,
    HDRISettings,
    HDRI_OT_reset_rotation,
    HDRI_OT_reset_strength,
    HDRI_OT_setup_nodes,
    HDRI_OT_load_selected,
    HDRI_OT_change_folder,
    HDRI_PT_controls,
    HDRI_OT_check_updates,
    HDRI_OT_download_update,
    HDRI_OT_popup_controls,
    HDRI_OT_update_shortcut,
    HDRI_OT_quick_rotate,
    HDRI_OT_reset_to_previous,
    HDRI_OT_toggle_visibility,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.hdri_settings = PointerProperty(type=HDRISettings)
    bpy.types.VIEW3D_HT_header.append(draw_hdri_menu)

    # Add keymap entry
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
        
        # Get saved preferences
        preferences = bpy.context.preferences.addons[__name__].preferences
        is_mac = sys.platform == 'darwin'
        
        kmi = km.keymap_items.new(
            HDRI_OT_popup_controls.bl_idname,
            type=preferences.popup_key,
            value='PRESS',
            oskey=preferences.popup_ctrl if is_mac else False,  
            ctrl=preferences.popup_ctrl if not is_mac else False, 
            shift=preferences.popup_shift,
            alt=preferences.popup_alt
        )
        addon_keymaps.append((km, kmi))

    bpy.app.handlers.load_post.append(load_handler)
    
    # Run update check at startup if enabled
    check_for_update_on_startup()
    
def unregister():
    # Remove load handler
    bpy.app.handlers.load_post.remove(load_handler)
    
    # Remove keymap entries
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # Remove menu item
    bpy.types.VIEW3D_HT_header.remove(draw_hdri_menu)
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    # Remove scene properties
    del bpy.types.Scene.hdri_settings
    
    # Clean up preview collection
    if hasattr(get_hdri_previews, "preview_collection"):
        bpy.utils.previews.remove(get_hdri_previews.preview_collection)

if __name__ == "__main__":
    register()
