import urllib.request
import zipfile
import shutil
import tempfile
from datetime import datetime
from math import radians
import bpy
import subprocess
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
    "version": (2, 5, 3),
    "blender": (4, 3, 0),
    "location": "3D Viewport > Header",
    "warning": "Alpha Version (in-development)",
    "description": "Quickly adjust world HDRI rotation and selection",
    "category": "3D View",
}
# Stored keymap entries to remove them when unregistering
addon_keymaps = []
def get_hdri_previews():
    """Get or create the preview collection"""
    if not hasattr(get_hdri_previews, "preview_collection"):
        pcoll = bpy.utils.previews.new()
        get_hdri_previews.preview_collection = pcoll
        # Add cache for current directory
        get_hdri_previews.cached_dir = None
        get_hdri_previews.cached_items = []
    return get_hdri_previews.preview_collection
def generate_previews(self, context):
    """Generate preview items for HDRIs in current folder, using cache when possible"""
    # Early exit if no settings
    if not hasattr(context.scene, "hdri_settings"):
        return []
        
    preferences = context.preferences.addons[__name__].preferences
    base_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))
    current_dir = context.scene.hdri_settings.current_folder or base_dir
    current_dir = os.path.normpath(os.path.abspath(current_dir))
    
    # Check if using the cached directory
    if (hasattr(get_hdri_previews, "cached_dir") and 
        get_hdri_previews.cached_dir == current_dir and 
        get_hdri_previews.cached_items):
        return get_hdri_previews.cached_items
    
    # If here, generate new previews
    enum_items = []
    pcoll = get_hdri_previews()
    
    # Get enabled extensions
    extensions = []
    if preferences.use_hdr: extensions.append('.hdr')
    if preferences.use_exr: extensions.append('.exr')
    
    if not extensions:
        return enum_items
    
    # Add empty option
    enum_items.append(('', 'None', '', 0, 0))
    
    try:
        files = os.listdir(current_dir)
        
        # Collect HDR files
        hdri_files = []
        for filename in files:
            lower_name = filename.lower()
            if any(lower_name.endswith(ext) for ext in extensions):
                full_path = os.path.join(current_dir, filename)
                hdri_files.append((filename, full_path))
        
        # Collect thumbnails
        thumbnails = {}
        for filename in files:
            if filename.lower().endswith('_thumb.png'):
                base_name = os.path.splitext(filename)[0][:-6]
                thumbnails[base_name] = os.path.join(current_dir, filename)
        
        # Process each HDR file
        for idx, (filename, hdri_path) in enumerate(sorted(hdri_files), 1):
            try:
                base_name = os.path.splitext(filename)[0]
                base_name = base_name.rsplit('_', 1)[0] 
                
                preview_path = thumbnails.get(base_name, hdri_path)
                
                if hdri_path not in pcoll:
                    thumb = pcoll.load(hdri_path, preview_path, 'IMAGE')
                    if not thumb or not thumb.icon_id:
                        img = bpy.data.images.load(preview_path, check_existing=True)
                        img.gl_load()
                        thumb = pcoll.load(hdri_path, preview_path, 'IMAGE')
                        img.gl_free()
                        bpy.data.images.remove(img)
                else:
                    thumb = pcoll[hdri_path]
                
                if thumb and thumb.icon_id:
                    enum_items.append((
                        hdri_path,
                        base_name,
                        "Using thumbnail preview" if base_name in thumbnails else "",
                        thumb.icon_id,
                        idx
                    ))
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error scanning directory: {str(e)}")
    
    # Cache the results
    get_hdri_previews.cached_dir = current_dir
    get_hdri_previews.cached_items = enum_items
    
    return enum_items
    
    
def refresh_previews(context, new_directory=None):
    """Refresh the preview collection when settings change"""
    pcoll = get_hdri_previews()
    
    # Clear cache to force regeneration
    get_hdri_previews.cached_dir = None
    get_hdri_previews.cached_items = []
    
    # Clear preview collection
    pcoll.clear()
    
    if hasattr(context.scene, "hdri_settings"):
        current_settings = context.scene.hdri_settings
        
        # Update current folder if new directory is provided
        if new_directory is not None:
            current_settings.current_folder = new_directory
        
        # Force a single preview regeneration
        enum_items = generate_previews(None, context)
        if len(enum_items) > 1:
            current_settings.hdri_preview = enum_items[1][0]
        
        for area in context.screen.areas:
            area.tag_redraw()
def get_folders(context):
    """Get list of subfolders in HDRI directory"""
    preferences = context.preferences.addons[__name__].preferences
    base_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))
    
    # Ensure current_folder is within base directory
    if not context.scene.hdri_settings.current_folder:
        context.scene.hdri_settings.current_folder = base_dir
        
    current_dir = os.path.normpath(os.path.abspath(context.scene.hdri_settings.current_folder))
    
    # If somehow outside base directory, reset to base
    try:
        rel_path = os.path.relpath(current_dir, base_dir)
        if rel_path.startswith('..'):
            current_dir = base_dir
            context.scene.hdri_settings.current_folder = base_dir
    except ValueError:
        current_dir = base_dir
        context.scene.hdri_settings.current_folder = base_dir
    
    items = []
    
    # Only show parent folder button if we're in a subfolder AND not directly in base_dir
    if current_dir != base_dir:
        parent_dir = os.path.dirname(current_dir)
        # Only add parent navigation if it wouldn't take us outside base_dir
        if os.path.normpath(parent_dir) == os.path.normpath(base_dir) or \
           os.path.normpath(parent_dir).startswith(os.path.normpath(base_dir)):
            items.append(("parent", "", "Go to parent folder", 'FILE_PARENT', 0))
    
    # Add subfolders
    try:
        if os.path.exists(current_dir):
            for idx, dirname in enumerate(sorted(os.listdir(current_dir)), start=len(items)):
                full_path = os.path.join(current_dir, dirname)
                if os.path.isdir(full_path):
                    # Verify subfolder is within base directory
                    try:
                        rel_path = os.path.relpath(full_path, base_dir)
                        if not rel_path.startswith('..'):
                            items.append((full_path, dirname, "Enter folder", 'FILE_FOLDER', idx))
                    except ValueError:
                        continue
    except Exception as e:
        print(f"Error reading directory {current_dir}: {str(e)}")
    
    return items
    
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
                    if len(version_numbers) >= 3:
                        online_version = (int(version_numbers[0]), #Main Build
                                        int(version_numbers[1]), #Sub Build
                                        int(version_numbers[2])) #Patch Build 
                    break
        # If the online version is higher, set the alert in user preferences
        if online_version and online_version > current_version:
            preferences.update_available = True
        else:
            preferences.update_available = False
    except Exception as e:
        print(f"Startup update check error: {str(e)}")
def extract_addon_zips():
    """Extract any ZIP files found in the addon directory and clean up."""
    addon_dir = os.path.dirname(os.path.realpath(__file__))
    
    # Find all zip files in the addon directory
    zip_files = [f for f in os.listdir(addon_dir) if f.lower().endswith('.zip')]
    
    for zip_file in zip_files:
        zip_path = os.path.join(addon_dir, zip_file)
        try:
            # Create a temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract the ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Get the extracted folder (assuming only one folder in ZIP)
                extracted_items = os.listdir(temp_dir)
                if not extracted_items:
                    continue
                
                # If there's a single directory, use that as the source
                if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_items[0])):
                    source_dir = os.path.join(temp_dir, extracted_items[0])
                else:
                    source_dir = temp_dir
                
                # Copy all files to addon directory
                for item in os.listdir(source_dir):
                    src_path = os.path.join(source_dir, item)
                    dst_path = os.path.join(addon_dir, item)
                    
                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dst_path)
                    elif os.path.isdir(src_path):
                        if os.path.exists(dst_path):
                            shutil.rmtree(dst_path)
                        shutil.copytree(src_path, dst_path)
            
            # Remove the ZIP file
            os.remove(zip_path)
            print(f"Successfully extracted and cleaned up {zip_file}")
            
        except Exception as e:
            print(f"Error processing {zip_file}: {str(e)}")
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
    
    # Initialize both visibility systems
    if hasattr(world, "cycles_visibility"):
        world.cycles_visibility.camera = True
    
    if hasattr(world, "visibility"):
        world.visibility.camera = True
    
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
    
def cleanup_unused_images():
    """Remove unused HDRI images from memory"""
    # Get all environment texture nodes in use
    active_images = set()
    for world in bpy.data.worlds:
        if world.use_nodes:
            for node in world.node_tree.nodes:
                if node.type == 'TEX_ENVIRONMENT' and node.image:
                    active_images.add(node.image)
    # Remove unused images
    for img in bpy.data.images:
        if img.users == 0 and img not in active_images:
            bpy.data.images.remove(img)
def cleanup_preview_cache():
    """Clear the preview cache when switching folders"""
    for attr in dir(generate_previews):
        if attr.startswith('preview_cache_'):
            delattr(generate_previews, attr)
            
def get_hdri_metadata(image):
    """Extract metadata from HDRI image"""
    if not image:
        return None
        
    metadata = {
        'filename': os.path.basename(image.filepath) if image.filepath else image.name,
        'resolution': f"{image.size[0]}x{image.size[1]}",
        'color_space': image.colorspace_settings.name,
        'file_format': image.file_format,
        'channels': image.channels,
        'file_size': os.path.getsize(image.filepath) if image.filepath else 0,
        'filepath': image.filepath,
    }
    
    # Convert file size to human-readable format
    if metadata['file_size']:
        size_bytes = metadata['file_size']
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                metadata['file_size'] = f"{size_bytes:.1f} {unit}"
                break
            size_bytes /= 1024
            
    return metadata
            
class HDRI_OT_cleanup_unused(Operator):
    bl_idname = "world.cleanup_unused_hdri"
    bl_label = "Cleanup Unused HDRIs"
    bl_description = "Remove unused HDRI images from memory"
    
    def execute(self, context):
        try:
            initial_count = len(bpy.data.images)
            cleanup_unused_images()
            final_count = len(bpy.data.images)
            removed = initial_count - final_count
            
            if removed > 0:
                self.report({'INFO'}, f"Removed {removed} unused HDRI image{'s' if removed > 1 else ''}")
            else:
                self.report({'INFO'}, "No unused HDRI images found")
                
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Cleanup failed: {str(e)}")
            return {'CANCELLED'}
    
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
                        if len(version_numbers) >= 3:
                            return (int(version_numbers[0]), 
                                   int(version_numbers[1]), 
                                   int(version_numbers[2]))
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
        
        # Compare all three version numbers
        if online_version <= current_version:  # This will compare tuples element by element
            self.report({'INFO'}, f"Quick HDRI Controls is up to date (v{current_version[0]}.{current_version[1]}.{current_version[2]})")
            return {'FINISHED'}
        
        def draw_popup(self, context):
            self.layout.label(text=f"New version available: v{online_version[0]}.{online_version[1]}.{online_version[2]}")
            self.layout.label(text=f"Current version: v{current_version[0]}.{current_version[1]}.{current_version[2]}")
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
            
            # Delay the operator invocation until all classes are registered
            def invoke_restart_prompt():
                bpy.ops.world.restart_prompt('INVOKE_DEFAULT')
            bpy.app.timers.register(invoke_restart_prompt)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Update failed: {str(e)}")
            return {'CANCELLED'}
            
            
class HDRI_OT_restart_prompt(Operator):
    bl_idname = "world.restart_prompt"
    bl_label = "Restart Required"
    bl_description = "Prompt user to save and restart Blender"
    def execute(self, context):
        self.report({'INFO'}, "Please save your work and restart Blender.")
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    def draw(self, context):
        layout = self.layout
        layout.label(text="Update installed! Please save your work.")
        layout.label(text="Blender needs to restart to apply changes.")
class HDRI_OT_change_folder(Operator):
    bl_idname = "world.change_hdri_folder"
    bl_label = "Change Folder"
    bl_description = "Change current HDRI folder"
    
    folder_path: StringProperty()
    
    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        base_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))
        hdri_settings = context.scene.hdri_settings
        
        # Handle parent directory navigation
        if self.folder_path == "parent":
            current = os.path.normpath(os.path.abspath(hdri_settings.current_folder))
            new_path = os.path.dirname(current)
            
            # Only allow if new path is base_dir or within it
            if not (os.path.normpath(new_path) == os.path.normpath(base_dir) or \
                   os.path.normpath(new_path).startswith(os.path.normpath(base_dir))):
                self.report({'WARNING'}, "Cannot navigate above HDRI directory")
                return {'CANCELLED'}
                
            self.folder_path = new_path
        
        # Normalize target path
        target_path = os.path.normpath(os.path.abspath(self.folder_path))
        
        # Verify target is base_dir or within it
        if not (os.path.normpath(target_path) == os.path.normpath(base_dir) or \
               os.path.normpath(target_path).startswith(os.path.normpath(base_dir))):
            self.report({'WARNING'}, "Cannot navigate outside HDRI directory")
            return {'CANCELLED'}
        
        # Update current folder
        hdri_settings.current_folder = target_path
        
        # Clear preview cache for folder change
        get_hdri_previews.cached_dir = None
        get_hdri_previews.cached_items = []
        
        # Force UI update
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
      #hello fello helmo
class HDRI_OT_quick_rotate(Operator):
    bl_idname = "world.quick_rotate_hdri"
    bl_label = "HDRI Rotation"
    bl_description = "Adjust HDRI rotation"  # Default description
    
    axis: IntProperty(
        name="Axis",
        description="Rotation axis (0=X, 1=Y, 2=Z)",
        default=0
    )
    
    direction: IntProperty(
        name="Direction",
        description="Rotation direction (1 or -1, -99 for reset)",
        default=1
    )
    
    def get_axis_name(self):
        return ["X", "Y", "Z"][self.axis]
        
    @classmethod
    def description(cls, context, properties):
        # Get axis name (X, Y, or Z)
        axis_name = ["X", "Y", "Z"][properties.axis]
        
        # Get rotation increment from preferences
        preferences = context.preferences.addons[__name__].preferences
        increment = preferences.rotation_increment
        
        # Return appropriate description based on direction
        if properties.direction == -99:
            return f"Reset {axis_name} rotation to 0°"
        elif properties.direction == -1:
            return f"Decrease {axis_name} rotation by {increment}°"
        else:
            return f"Increase {axis_name} rotation by {increment}°"
    
    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        world = context.scene.world
        
        if world and world.use_nodes:
            for node in world.node_tree.nodes:
                if node.type == 'MAPPING':
                    current_rotation = list(node.inputs['Rotation'].default_value)
                    
                    if self.direction == -99:  # Reset
                        current_rotation[self.axis] = 0
                    else:  # Regular rotation
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
        preferences = context.preferences.addons[__name__].preferences
        hdri_settings = context.scene.hdri_settings
        
        # Verify HDRI directory exists and is accessible
        if not preferences.hdri_directory or not os.path.exists(preferences.hdri_directory):
            self.report({'ERROR'}, "HDRI directory not found. Please select a valid directory in preferences.")
            bpy.ops.preferences.addon_show(module=__name__)
            return {'CANCELLED'}
            
        # If current folder is not set or doesn't exist, reset to HDRI directory
        if not hdri_settings.current_folder or not os.path.exists(hdri_settings.current_folder):
            hdri_settings.current_folder = preferences.hdri_directory
            
        # Setup nodes
        mapping, env_tex, background = ensure_world_nodes()
        
        # Check if there are any HDRIs in the current directory
        if not has_hdri_files(context):
            self.report({'WARNING'}, "No supported HDRI files found in the current directory.")
            return {'FINISHED'}
            
        # Generate previews for the current directory
        enum_items = generate_previews(self, context)
        
        # If we have HDRIs, set the preview to the first one
        if len(enum_items) > 1:  # Skip 'None' item
            hdri_settings.hdri_preview = enum_items[1][0]
            
        # Force redraw of UI
        for area in context.screen.areas:
            area.tag_redraw()
            
        self.report({'INFO'}, "HDRI system initialized successfully")
        return {'FINISHED'}
            
class HDRI_OT_browse_directory(Operator):
    bl_idname = "wm.directory_browse"
    bl_label = "Browse Directory"
    
    directory: StringProperty(
        name="Search Directory",
        description="Directory to search for HDRIs",
        subtype='DIR_PATH'
    )
    
    property_name: StringProperty(
        name="Property Name",
        description="Name of the property to update"
    )
    
    property_owner: StringProperty(
        name="Property Owner",
        description="Owner of the property to update"
    )
    
    def execute(self, context):
        # Update the appropriate property
        if self.property_owner == "preferences":
            preferences = context.preferences.addons[__name__].preferences
            setattr(preferences, self.property_name, self.directory)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
class HDRI_OT_update_shortcut(Operator):
    bl_idname = "world.update_hdri_shortcut"
    bl_label = "Update Shortcut"
    bl_description = "Apply the new keyboard shortcut"
    
    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        preferences.update_shortcut(context)
        self.report({'INFO'}, "Shortcut updated successfully")
        return {'FINISHED'}
        
def find_keymap_conflicts(self, context):
    """Find all keymap items that conflict with current shortcut settings"""
    conflicts = []
    
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
                        if kmi.idname != HDRI_OT_popup_controls.bl_idname:
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
    
    return conflicts
class HDRI_OT_show_shortcut_conflicts(Operator):
    bl_idname = "world.show_hdri_shortcut_conflicts"
    bl_label = "Show Shortcut Conflicts"
    bl_description = "Show any conflicts with the current keyboard shortcut"
    
    def draw(self, context):
        layout = self.layout
        preferences = context.preferences.addons[__name__].preferences
        
        # Find conflicts
        conflicts = preferences.find_keymap_conflicts(context)
        
        if conflicts:
            layout.label(text="The following shortcuts conflict:", icon='ERROR')
            
            # Group conflicts by keyconfig
            for config_name in ['Blender', 'Blender User', 'Addons']:
                config_conflicts = [c for c in conflicts if c['config'] == config_name]
                if config_conflicts:
                    box = layout.box()
                    box.label(text=config_name, icon='KEYINGSET')
                    
                    for conflict in config_conflicts:
                        row = box.row()
                        # Format shortcut description
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
                        
                        row.label(text=f"{conflict['name']} ({shortcut})")
                        sub = row.row()
                        sub.label(text=f"in {conflict['keymap']}")
        else:
            layout.label(text="No conflicts found!", icon='CHECKMARK')
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
        
class HDRISettings(PropertyGroup):
    def update_hdri_preview(self, context):
        """Automatically load HDRI when selected from preview"""
        filepath = self.hdri_preview
        
        if not filepath:
            return
            
        if not os.path.exists(filepath):
            return
        
        # Store current state as previous
        world = context.scene.world
        if world and world.use_nodes:
            for node in world.node_tree.nodes:
                if node.type == 'TEX_ENVIRONMENT' and node.image:
                    self.previous_hdri_path = node.image.filepath
                elif node.type == 'MAPPING':
                    self.previous_rotation = node.inputs['Rotation'].default_value.copy()
                elif node.type == 'BACKGROUND':
                    self.previous_strength = node.inputs['Strength'].default_value
        
        preferences = context.preferences.addons[__name__].preferences
        
        # Store current rotation if keep_rotation is enabled
        current_rotation = None
        if preferences.keep_rotation:
            for node in context.scene.world.node_tree.nodes:
                if node.type == 'MAPPING':
                    current_rotation = node.inputs['Rotation'].default_value.copy()
                    break
        
        # Set up nodes
        mapping, env_tex, node_background = ensure_world_nodes()
        
        # Load the new image
        try:
            img = bpy.data.images.load(filepath, check_existing=True)
            env_tex.image = img
        except Exception as e:
            print(f"Failed to load HDRI: {str(e)}")
            return
        
        # Apply rotation based on keep_rotation setting
        if preferences.keep_rotation and current_rotation is not None:
            mapping.inputs['Rotation'].default_value = current_rotation
        else:
            mapping.inputs['Rotation'].default_value = (0, 0, 0)
    # Properties
    hdri_preview: EnumProperty(
        items=generate_previews,
        name="HDRI Preview",
        description="Preview of available HDRIs",
        update=update_hdri_preview
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
    
    show_metadata: BoolProperty(
        name="Show Metadata",
        description="Show/Hide HDRI metadata information",
        default=False
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
    #Show Conflicts
    show_conflicts: BoolProperty(
        name="Show Conflicts",
        description="Show keyboard shortcut conflicts",
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
    # Directory
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
        max=1000
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
    
    hdri_directory: StringProperty(
        name="HDRI Directory",
        subtype='DIR_PATH',
        description="Directory containing HDRI files",
        default="",
        update=lambda self, context: refresh_previews(context, self.hdri_directory)
    )
    
    preview_resolution: IntProperty(
        name="Resolution Percentage",
        description="Percentage of base resolution (1024x768)",
        default=100,
        min=10,
        max=1000,
        subtype='PERCENTAGE'
    )

    preview_generation_type: EnumProperty(
        name="Preview Generation Type",
        description="Choose whether to generate preview for a single HDRI or multiple",
        items=[
            ('SINGLE', 'Single HDRI', 'Generate preview for a single HDRI'),
            ('MULTIPLE', 'Multiple HDRIs', 'Generate previews for all HDRIs in a folder')
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
    

    # Preview display with image loading
    def get_preview_icon(self, context=None):
        """Get the preview icon ID for an image"""
        if self.preview_image and os.path.exists(self.preview_image):
            try:
                # Load or get existing image
                if self.preview_image not in bpy.data.images:
                    preview_img = bpy.data.images.load(self.preview_image)
                else:
                    preview_img = bpy.data.images[self.preview_image]
                
                # Force a reload of the image
                preview_img.reload()
                
                # Return the preview icon ID
                return preview_img.preview.icon_id
                
            except Exception as e:
                print(f"Failed to load preview image: {str(e)}")
                return 0
        return 0

    
    # Statistics
    preview_stats_total: IntProperty(default=0)
    preview_stats_completed: IntProperty(default=0)
    preview_stats_failed: IntProperty(default=0)
    preview_stats_time: FloatProperty(default=0.0)
    preview_stats_current_file: StringProperty(default="")
    is_generating: BoolProperty(default=False)
    
    
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
                            if kmi.idname != HDRI_OT_popup_controls.bl_idname:
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
        
        # HDRI Directory (Always visible as it's critical!!!!!!)
        main_box = layout.box()
        row = main_box.row()
        row.scale_y = 1.2
        # Make the directory field red
        if not self.hdri_directory:
            row.alert = True
        row.prop(self, "hdri_directory", text="HDRI Directory")
        
        # Updates Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_updates", 
                   icon='TRIA_DOWN' if getattr(self, 'show_updates', True) else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)
                   
        # Add version info to header
        header_text = header.split(factor=0.7)
        header_text.label(text="Updates & Information", icon='FILE_REFRESH')
        version_text = header_text.row()
        version_text.alignment = 'RIGHT'
        version_text.label(text=f"Current Version: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}")
        
        if getattr(self, 'show_updates', True):
            update_box = box.box()
            
            # Status and auto-check row
            status_row = update_box.row()
            status_sub = status_row.row(align=True)
            status_sub.prop(self, "enable_auto_update_check", 
                          text="Check for Updates on Startup",
                          icon='TIME')
            
            # Check now button
            check_row = status_sub.row(align=True)
            check_row.operator("world.check_hdri_updates", 
                             text="Check Now",
                             icon='FILE_REFRESH')
            
            # Show update status if available
            if self.update_available:
                alert_box = update_box.box()
                alert_box.alert = True
                alert_row = alert_box.row()
                alert_row.label(text="New Update Available!", icon='ERROR')
                alert_row.operator("world.download_hdri_update", 
                                 text="Download Update",
                                 icon='IMPORT')
            
            # Documentation section
            docs_box = box.box()
            docs_col = docs_box.column(align=True)
            
            # Documentation header
            doc_header = docs_col.row()
            doc_header.label(text="Documentation & Resources", icon='HELP')
            
            # Documentation links
            links_row = docs_col.row(align=True)
            links_row.scale_y = 1.2
            links_row.operator("wm.url_open", 
                             text="Documentation",
                             icon='URL').url = "https://github.com/mdreece/Quick-HDRI-Controls/tree/main"
            links_row.operator("wm.url_open",
                             text="Report Issue",
                             icon='ERROR').url = "https://github.com/mdreece/Quick-HDRI-Controls/issues"
            
            # Tips section
            tips_box = box.box()
            tips_col = tips_box.column(align=True)
            tips_col.label(text="Quick Tips:", icon='INFO')
            tips_col.label(text="• Use keyboard shortcut for quick access")
            tips_col.label(text="• Organize HDRI directory")
            tips_col.label(text="• Use PNG thumbnails for HDRs to ease resources usage")
            tips_col.label(text="• Check for updates regularly (make features suggestions")
        
        # Keyboard Shortcuts Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_shortcuts", icon='TRIA_DOWN' if getattr(self, 'show_shortcuts', True) else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)
        header.label(text="Keyboard Shortcuts", icon='KEYINGSET')
        
        if getattr(self, 'show_shortcuts', True):
            col = box.column(align=True)
            
            # Current shortcut display
            current_shortcut = []
            if self.popup_ctrl:
                current_shortcut.append("⌘ Command" if sys.platform == 'darwin' else "Ctrl")
            if self.popup_shift:
                current_shortcut.append("⇧ Shift")
            if self.popup_alt:
                current_shortcut.append("⌥ Option" if sys.platform == 'darwin' else "Alt")
            current_shortcut.append(self.popup_key)
            
            # Current shortcut row
            row = col.row()
            row.label(text="Current Shortcut: " + " + ".join(current_shortcut))
            
            # Modifier keys
            row = col.row(align=True)
            if sys.platform == 'darwin':
                row.prop(self, "popup_ctrl", text="⌘ Command", toggle=True)
                row.prop(self, "popup_shift", text="⇧ Shift", toggle=True)
                row.prop(self, "popup_alt", text="⌥ Option", toggle=True)
            else:
                row.prop(self, "popup_ctrl", text="Ctrl", toggle=True)
                row.prop(self, "popup_shift", text="Shift", toggle=True)
                row.prop(self, "popup_alt", text="Alt", toggle=True)
                
            # Key selection
            col.prop(self, "popup_key", text="Key")
            col.separator()
            
            # Apply button
            col.operator("world.update_hdri_shortcut", text="Apply Shortcut Change")
            col.separator()
            
            # Get conflicts
            conflicts = self.find_keymap_conflicts(context)
            
            # Conflicts section with status-based header
            conflict_box = col.box()
            header_row = conflict_box.row()
            header_row.prop(self, "show_conflicts", 
                          icon='TRIA_DOWN' if self.show_conflicts else 'TRIA_RIGHT',
                          icon_only=True, emboss=False)
            
            status_row = header_row.row()
            if conflicts:
                status_row.alert = True
                status_row.label(text="Conflicts Found", icon='ERROR')
            else:
                status_row.label(text="No Conflicts Found", icon='CHECKMARK')
                status_row.alert = False
            
            if self.show_conflicts:
                if conflicts:
                    # Group conflicts by keyconfig
                    for config_name in ['Blender', 'Blender User', 'Addons']:
                        config_conflicts = [c for c in conflicts if c['config'] == config_name]
                        if config_conflicts:
                            sub_box = conflict_box.box()
                            row = sub_box.row()
                            row.label(text=config_name + ":", icon='KEYINGSET')
                            
                            for conflict in config_conflicts:
                                # Format shortcut description
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
                                
                                row = sub_box.row()
                                split = row.split(factor=0.7)
                                split.label(text=conflict['name'])
                                split.label(text=shortcut)
                                
                                # Show keymap in smaller text
                                row = sub_box.row()
                                row.scale_y = 0.8
                                row.label(text=f"Found in: {conflict['keymap']}")
                                sub_box.separator(factor=0.5)
        
        # Interface Settings Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_interface", icon='TRIA_DOWN' if getattr(self, 'show_interface', True) else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)
        header.label(text="Interface Settings", icon='PREFERENCES')
        
        if getattr(self, 'show_interface', True):
            col = box.column(align=True)
            col.prop(self, "preview_scale", text="Preview Size")
            col.prop(self, "button_scale", text="Button Scale")
            col.prop(self, "spacing_scale", text="Spacing Scale")
            col.separator()
            col.prop(self, "show_strength_slider", text="Show Strength Slider")
            col.prop(self, "show_rotation_values", text="Show Rotation Values")
        
        # File Types Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_filetypes", icon='TRIA_DOWN' if getattr(self, 'show_filetypes', True) else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)
        header.label(text="Supported File Types", icon='FILE_FOLDER')
        
        if getattr(self, 'show_filetypes', True):
            row = box.row(align=True)
            row.prop(self, "use_hdr", toggle=True)
            row.prop(self, "use_exr", toggle=True)
            row.prop(self, "use_png", toggle=True)
            row.prop(self, "use_jpg", toggle=True)
            
            # Preview limit
            row = box.row()
            row.prop(self, "preview_limit")
            
            # Sort method (only shown if preview limit is enabled)
            if self.preview_limit > 0:
                row = box.row()
                row.prop(self, "preview_sort")
        
        # HDRI Settings Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_hdri_settings", icon='TRIA_DOWN' if getattr(self, 'show_hdri_settings', True) else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)
        header.label(text="HDRI Settings", icon='WORLD_DATA')
        
        if getattr(self, 'show_hdri_settings', True):
            col = box.column(align=True)
            col.prop(self, "keep_rotation", text="Keep Rotation When Switching HDRIs")
            col.prop(self, "strength_max", text="Maximum Strength Value")
            col.prop(self, "rotation_increment", text="Rotation Step Size")
            
        # Preview Generation Section
        section_box = layout.box()
        header = section_box.row(align=True)
        header.prop(self, "show_preview_generation", 
                   icon='TRIA_DOWN' if self.show_preview_generation else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)
        
        # Main header with status indicator
        header_split = header.split(factor=0.7)
        title_row = header_split.row()
        title_row.label(text="Preview Generation", icon='IMAGE_DATA')
        
        # Status indicator
        status_row = header_split.row(align=True)
        status_row.alignment = 'RIGHT'
        if self.is_generating:
            status_row.alert = True
            status_row.label(text="●", icon='SORTTIME')
            status_row.label(text="Processing")
        else:
            status_row.label(text="●", icon='CHECKMARK')
            status_row.label(text="Ready")

        if self.show_preview_generation:
            # Main container
            main_container = section_box.column()
            main_container.separator(factor=0.5)

            # Active Job Status Panel (if processing or has results)
            if self.is_generating or (self.preview_stats_total > 0 and not self.is_generating):
                status_panel = main_container.box()
                status_panel.alert = self.is_generating
                
                # Status Panel Header
                status_header = status_panel.row()
                status_header.scale_y = 1.2
                if self.is_generating:
                    status_header.label(text="Active Job Status", icon='RENDER_STILL')
                else:
                    status_header.label(text="Last Job Results", icon='FILE_TICK')
                
                status_panel.separator(factor=0.5)
                
                # Progress Information Grid
                grid = status_panel.grid_flow(row_major=True, columns=2, even_columns=True)
                
                # Current File (when generating)
                if self.is_generating and self.preview_stats_current_file:
                    file_row = grid.row()
                    file_row.label(text="Current File:")
                    file_row.label(text=os.path.basename(self.preview_stats_current_file))
                
                # Progress Statistics
                if self.preview_stats_total > 0:
                    # Completion Status
                    progress = self.preview_stats_completed / self.preview_stats_total
                    prog_row = grid.row()
                    prog_row.label(text="Completion:")
                    prog_row.label(text=f"{progress:.1%} ({self.preview_stats_completed}/{self.preview_stats_total})")
                    
                    # Time Elapsed
                    if self.preview_stats_time > 0:
                        minutes = int(self.preview_stats_time // 60)
                        seconds = int(self.preview_stats_time % 60)
                        time_row = grid.row()
                        time_row.label(text="Time Elapsed:")
                        time_row.label(text=f"{minutes:02d}:{seconds:02d}")
                    
                    # Failed Items
                    if self.preview_stats_failed > 0:
                        fail_row = grid.row()
                        fail_row.alert = True
                        fail_row.label(text="Failed Jobs:")
                        fail_row.label(text=str(self.preview_stats_failed))
                
                # Clear Results Button (when not generating)
                if not self.is_generating and self.preview_stats_total > 0:
                    status_panel.separator(factor=0.5)
                    clear_row = status_panel.row()
                    clear_row.alignment = 'RIGHT'
                    clear_op = clear_row.operator("world.clear_preview_stats", 
                                                text="Clear History",
                                                icon='X')

            # Configuration Panels
            if not self.is_generating:
                main_container.separator(factor=1.0)
                
                # Job Configuration Panel
                config_panel = main_container.box()
                config_panel.label(text="Job Configuration", icon='PREFERENCES')
                
                # Type Selection
                type_box = config_panel.box()
                type_row = type_box.row(align=True)
                type_row.scale_y = 1.2
                type_row.label(text="Processing Type:", icon='MODIFIER')
                type_grid = type_row.grid_flow(row_major=True, columns=2, even_columns=True)
                type_grid.prop_enum(self, "preview_generation_type", 'SINGLE',
                                  text="Single File", icon='IMAGE_DATA')
                type_grid.prop_enum(self, "preview_generation_type", 'MULTIPLE',
                                  text="Batch Process", icon='FILE_FOLDER')
                
                # Source Selection
                source_box = config_panel.box()
                source_col = source_box.column()
                source_col.label(text="Source Selection:", icon='FILEBROWSER')
                source_col.separator(factor=0.3)
                
                # File/Folder Selection
                source_row = source_col.row(align=True)
                if self.preview_generation_type == 'SINGLE':
                    source_row.prop(self, "preview_single_file", text="")
                else:
                    source_row.prop(self, "preview_multiple_folder", text="")
                
                # Source Information
                info_box = source_col.box()
                info_box.scale_y = 0.9
                if self.preview_generation_type == 'SINGLE':
                    if self.preview_single_file:
                        info_box.label(text=f"Selected: {os.path.basename(self.preview_single_file)}")
                    else:
                        info_box.label(text="No file selected")
                else:
                    if self.preview_multiple_folder:
                        file_count = len([f for f in os.listdir(self.preview_multiple_folder) 
                                        if f.lower().endswith(('.hdr', '.exr'))])
                        info_box.label(text=f"Found {file_count} HDRI file{'s' if file_count != 1 else ''}")
                    else:
                        info_box.label(text="No folder selected")
                
                # Quality Settings Panel
                main_container.separator(factor=1.0)
                quality_panel = main_container.box()
                quality_panel.label(text="Quality Settings", icon='SETTINGS')
                
                # Settings Grid
                quality_box = quality_panel.box()
                quality_grid = quality_box.grid_flow(row_major=True, columns=2, even_columns=True)
                
                # Resolution Column
                res_col = quality_grid.column(align=True)
                res_col.label(text="Resolution Scale:")
                res_col.prop(self, "preview_resolution", text="%")
                
                # Samples Column
                sample_col = quality_grid.column(align=True)
                sample_col.label(text="Render Samples:")
                sample_col.prop(self, "preview_samples", text="")
                
                # Output Resolution Info
                res_box = quality_panel.box()
                res_box.scale_y = 0.9
                actual_x = int(1024 * (self.preview_resolution / 100))
                actual_y = int(768 * (self.preview_resolution / 100))
                res_box.label(text=f"Output Resolution: {actual_x} × {actual_y} pixels")
                
                # Action Section
                main_container.separator(factor=1.0)
                action_box = main_container.box()
                
                # Generate Button
                action_row = action_box.row(align=True)
                action_row.scale_y = 1.5
                action_row.operator(
                    "world.generate_hdri_previews",
                    text="Generate Preview" if self.preview_generation_type == 'SINGLE' 
                         else "Start Batch Process",
                    icon='RENDER_STILL'
                )
           
        
    # Add the properties to control section visibility
    show_updates: BoolProperty(default=False)
    show_shortcuts: BoolProperty(default=False)
    show_interface: BoolProperty(default=False)
    show_filetypes: BoolProperty(default=False)
    show_hdri_settings: BoolProperty(default=False)
    show_conflicts: BoolProperty(default=False)
    show_preview_generation: BoolProperty(default=False)
        
class HDRI_OT_toggle_visibility(Operator):
    bl_idname = "world.toggle_hdri_visibility"
    bl_label = "Toggle HDRI Visibility"
    bl_description = "Toggle HDRI background visibility in camera (Ray Visibility)"
    
    def execute(self, context):
        world = context.scene.world
        if world:
            # Print current state
            print(f"Current visibility state: {world.cycles_visibility.camera}")
            
            # Toggle visibility
            world.cycles_visibility.camera = not world.cycles_visibility.camera
            
            # Print new state
            print(f"New visibility state: {world.cycles_visibility.camera}")
            
            # Force update
            context.scene.world.update_tag()
            for area in context.screen.areas:
                area.tag_redraw()
            
            # Report the change to the UI
            self.report({'INFO'}, f"Camera visibility set to: {world.cycles_visibility.camera}")
            
            return {'FINISHED'}
        return {'CANCELLED'}
        
class HDRI_OT_delete_world(Operator):
    bl_idname = "world.delete_hdri_world"
    bl_label = "Delete World"
    bl_description = "Delete the current world"
    
    def invoke(self, context, event):
        # Show confirmation dialog
        return context.window_manager.invoke_confirm(
            self, 
            event, 
            title="Delete World?"
        )
    
    def execute(self, context):
        if context.scene.world:
            world = context.scene.world
            bpy.data.worlds.remove(world, do_unlink=True)
            self.report({'INFO'}, "World deleted")
        return {'FINISHED'}
        
class HDRI_OT_reset_to_previous(Operator):
    bl_idname = "world.reset_to_previous_hdri"
    bl_label = "Reset to Previous HDRI"
    bl_description = "Reset to the previously loaded HDRI"
    
    def execute(self, context):
        hdri_settings = context.scene.hdri_settings
        preferences = context.preferences.addons[__name__].preferences
        
        if not hdri_settings.previous_hdri_path or not os.path.exists(hdri_settings.previous_hdri_path):
            self.report({'WARNING'}, "No previous HDRI available")
            return {'CANCELLED'}
        
        # Update current folder to the directory of the previous HDRI
        previous_hdri_dir = os.path.dirname(hdri_settings.previous_hdri_path)
        hdri_settings.current_folder = previous_hdri_dir
        
        # Force regeneration of previews for the new directory
        get_hdri_previews.cached_dir = None
        get_hdri_previews.cached_items = []
        
        # Regenerate previews
        enum_items = generate_previews(self, context)
        
        # Check if the previous HDRI path exists in the new preview list
        if any(item[0] == hdri_settings.previous_hdri_path for item in enum_items):
            hdri_settings.hdri_preview = hdri_settings.previous_hdri_path
        else:
            # If the exact path is not found, try to find a match based on filename
            previous_filename = os.path.basename(hdri_settings.previous_hdri_path)
            for item in enum_items:
                if os.path.basename(item[0]) == previous_filename:
                    hdri_settings.hdri_preview = item[0]
                    break
            else:
                # If no match is found, use the first HDRI in the list (skipping 'None')
                if len(enum_items) > 1:
                    hdri_settings.hdri_preview = enum_items[1][0]
                else:
                    self.report({'WARNING'}, "Could not find previous HDRI in the new directory")
                    return {'CANCELLED'}
        
        # Rest of the existing reset logic remains the same
        # Store current state as previous
        world = context.scene.world
        if world and world.use_nodes:
            for node in world.node_tree.nodes:
                if node.type == 'TEX_ENVIRONMENT' and node.image:
                    self.previous_hdri_path = node.image.filepath
                elif node.type == 'MAPPING':
                    self.previous_rotation = node.inputs['Rotation'].default_value.copy()
                elif node.type == 'BACKGROUND':
                    self.previous_strength = node.inputs['Strength'].default_value
        
        # Set up nodes
        mapping, env_tex, node_background = ensure_world_nodes()
        
        # Load the new image
        try:
            img = bpy.data.images.load(hdri_settings.hdri_preview, check_existing=True)
            env_tex.image = img
        except Exception as e:
            print(f"Failed to load HDRI: {str(e)}")
            return {'CANCELLED'}
        
        # Force redraw of areas
        for area in context.screen.areas:
            area.tag_redraw()
        
        return {'FINISHED'}
            
class HDRI_OT_previous_hdri(Operator):
    bl_idname = "world.previous_hdri"
    bl_label = "Previous HDRI"
    bl_description = "Load the previous HDRI in the current folder"
    
    def execute(self, context):
        hdri_settings = context.scene.hdri_settings
        enum_items = generate_previews(self, context)
        
        # Find current HDRI index
        current_index = -1
        for i, item in enumerate(enum_items):
            if item[0] == hdri_settings.hdri_preview:
                current_index = i
                break
        
        # Get previous HDRI (skip the first 'None' item)
        if current_index > 1:
            hdri_settings.hdri_preview = enum_items[current_index - 1][0]
        elif current_index == 1:  # If at first HDRI, wrap to last
            hdri_settings.hdri_preview = enum_items[-1][0]
            
        return {'FINISHED'}
class HDRI_OT_next_hdri(Operator):
    bl_idname = "world.next_hdri"
    bl_label = "Next HDRI"
    bl_description = "Load the next HDRI in the current folder"
    
    def execute(self, context):
        hdri_settings = context.scene.hdri_settings
        enum_items = generate_previews(self, context)
        
        # Find current HDRI index
        current_index = -1
        for i, item in enumerate(enum_items):
            if item[0] == hdri_settings.hdri_preview:
                current_index = i
                break
        
        # Get next HDRI (skip the first 'None' item)
        if current_index >= 0 and current_index < len(enum_items) - 1:
            hdri_settings.hdri_preview = enum_items[current_index + 1][0]
        elif current_index == len(enum_items) - 1:  # If at last HDRI, wrap to first
            hdri_settings.hdri_preview = enum_items[1][0]  # Skip 'None' item
            
        return {'FINISHED'}      


class HDRI_OT_generate_previews(Operator):
    bl_idname = "world.generate_hdri_previews"
    bl_label = "Generate HDRI Previews"
    bl_description = "Generate thumbnails for HDRI files"
    
    def get_thumb_path(self, hdri_path):
        # Ensure we're using the full, absolute path
        hdri_path = os.path.abspath(hdri_path)
        
        # Get the directory of the original HDRI
        directory = os.path.dirname(hdri_path)
        
        # Get the original filename and remove resolution suffixes
        filename = os.path.basename(hdri_path)
        
        # Remove resolution suffixes like 2k, 4k, 8k (case insensitive)
        # Replace underscores with hyphens
        clean_filename = re.sub(r'(_\d+[kK])?(\.[^.]+)$', '', filename).replace('_', '-')
        
        # Construct the new thumbnail path
        thumb_path = os.path.join(directory, f"{clean_filename}_thumb.png")
        
        return thumb_path
        
    def initialize_stats(self, context):
        preferences = context.preferences.addons[__name__].preferences
        preferences.preview_stats_total = len(self._preview_files)
        preferences.preview_stats_completed = 0
        preferences.preview_stats_failed = 0
        preferences.preview_stats_time = 0.0
        preferences.preview_stats_current_file = ""
        preferences.is_generating = True
        preferences.preview_image = ""  # Clear any existing preview
        self._start_time = datetime.now()
        
    def update_stats(self, context, success, current_file):
        """Update stats and handle preview image loading"""
        preferences = context.preferences.addons[__name__].preferences
        if success:
            preferences.preview_stats_completed += 1
            
            # Load and display the newly generated thumbnail
            thumb_path = self.get_thumb_path(current_file)
            if os.path.exists(thumb_path):
                # Update the preview image path
                preferences.preview_image = thumb_path
                
                # Force UI update
                for window in context.window_manager.windows:
                    for area in window.screen.areas:
                        if area.type == 'PREFERENCES':
                            area.tag_redraw()
        else:
            preferences.preview_stats_failed += 1
        
        preferences.preview_stats_current_file = os.path.basename(current_file)
        preferences.preview_stats_time = (datetime.now() - self._start_time).total_seconds()
        
        # Force redraw of preferences
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'PREFERENCES':
                    area.tag_redraw()

    def modal(self, context, event):
        preferences = context.preferences.addons[__name__].preferences
        
        if event.type == 'TIMER':
            if self._current_file_index >= self._total_files:
                self.finish_preview_generation(context)
                return {'FINISHED'}
            
            current_hdri = self._preview_files[self._current_file_index]
            success = self.generate_single_preview(context, current_hdri)
            
            if not success:
                self._failed_files.append(current_hdri)
            
            # Update statistics
            self.update_stats(context, success, current_hdri)
            
            # Update progress
            progress = (self._current_file_index + 1) / self._total_files
            context.window_manager.progress_update(progress * 100)
            
            self._current_file_index += 1
            
            # Force redraw of preferences window
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'PREFERENCES':
                        area.tag_redraw()
                    elif area.type == 'VIEW_3D':
                        area.tag_redraw()
        
        return {'RUNNING_MODAL'}

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        
        self._failed_files = []
        self._current_file_index = 0
        
        if preferences.preview_generation_type == 'SINGLE':
            self._preview_files = [preferences.preview_single_file]
        else:
            self._preview_files = self.get_hdri_files(preferences.preview_multiple_folder)
        
        self._total_files = len(self._preview_files)
        
        # Initialize statistics
        self.initialize_stats(context)
        
        wm = context.window_manager
        wm.progress_begin(0, 100)
        
        # Use a shorter timer interval for more frequent updates
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def finish_preview_generation(self, context):
        preferences = context.preferences.addons[__name__].preferences
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        
        # Calculate total completed
        total_completed = self._current_file_index
        total_failed = len(self._failed_files)
        total_successful = total_completed - total_failed
        
        # Update final statistics
        preferences.preview_stats_completed = total_successful
        preferences.preview_stats_failed = total_failed
        preferences.is_generating = False
        
        if self._failed_files:
            failed_names = [os.path.basename(f) for f in self._failed_files]
            self.report({'WARNING'}, 
                f"Generated {total_successful} previews with {total_failed} failures")
        else:
            self.report({'INFO'}, 
                f"Successfully generated {total_successful} previews")
        
        # Clear the preview collection to force a clean reload
        if hasattr(get_hdri_previews, "preview_collection"):
            get_hdri_previews.preview_collection.clear()
            get_hdri_previews.cached_dir = None
            get_hdri_previews.cached_items = []
        
        # Force redraw of UI to show new thumbnails
        for area in context.screen.areas:
            area.tag_redraw()

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()

    def get_hdri_files(self, folder):
        supported_extensions = ['.hdr', '.exr']
        return [
            os.path.join(folder, f) 
            for f in os.listdir(folder) 
            if os.path.isfile(os.path.join(folder, f)) 
            and os.path.splitext(f)[1].lower() in supported_extensions
        ]

    def generate_single_preview(self, context, hdri_path):
        # Rename the HDRI file to replace underscores with hyphens
        directory = os.path.dirname(hdri_path)
        filename = os.path.basename(hdri_path)
        new_filename = filename.replace('_', '-')
        new_hdri_path = os.path.join(directory, new_filename)
        
        # Rename the file if the new filename is different
        if new_filename != filename:
            try:
                os.rename(hdri_path, new_hdri_path)
                hdri_path = new_hdri_path  # Update to the new filename
            except Exception as e:
                print(f"Could not rename file {hdri_path}: {str(e)}")
        
        preferences = context.preferences.addons[__name__].preferences
        preview_blend_path = os.path.join(os.path.dirname(__file__), "Preview.blend")
        
        # Generate thumbnail path
        thumb_path = self.get_thumb_path(hdri_path)
        
        try:
            # Open the blend file
            with bpy.data.libraries.load(preview_blend_path, link=False) as (data_from, data_to):
                data_to.scenes = [s for s in data_from.scenes if s == "Preview"]
            
            # Get the preview scene
            preview_scene = bpy.data.scenes.get("Preview")
            if not preview_scene:
                print("Could not find Preview scene")
                return False
            
            # Load the HDRI image
            try:
                hdri_image = bpy.data.images.load(hdri_path, check_existing=True)
            except Exception as e:
                print(f"Failed to load HDRI image: {e}")
                return False
            
            # Find the environment texture node and HDRI_Plane
            world = preview_scene.world
            hdri_plane = None
            
            for obj in preview_scene.objects:
                if obj.name == "HDRI_PLANE":
                    hdri_plane = obj
                    break
            
            # Setup world environment texture
            if world and world.use_nodes:
                for node in world.node_tree.nodes:
                    if node.type == 'TEX_ENVIRONMENT':
                        node.image = hdri_image
            
            # Setup HDRI_Plane material
            if hdri_plane and hdri_plane.active_material:
                for node in hdri_plane.active_material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        node.image = hdri_image
            
            # Set up render settings with fixed base resolution
            preview_scene.render.resolution_x = 1024
            preview_scene.render.resolution_y = 768
            preview_scene.render.resolution_percentage = preferences.preview_resolution
            preview_scene.cycles.samples = preferences.preview_samples
            
            # Set output path
            preview_scene.render.filepath = thumb_path
            
            # Render
            bpy.ops.render.render(write_still=True, scene=preview_scene.name)
            
            return True
        
        except Exception as e:
            print(f"Error generating preview for {hdri_path}: {str(e)}")
            return False
            
class HDRI_OT_clear_preview_stats(Operator):
    bl_idname = "world.clear_preview_stats"
    bl_label = "Clear Statistics"
    bl_description = "Clear preview generation statistics"

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        preferences.preview_stats_total = 0
        preferences.preview_stats_completed = 0
        preferences.preview_stats_failed = 0
        preferences.preview_stats_time = 0.0
        preferences.preview_stats_current_file = ""
        preferences.preview_image = ""
        preferences.show_generation_stats = False
        return {'FINISHED'}

# Update the finish_preview_generation method in HDRI_OT_generate_previews:
    def finish_preview_generation(self, context):
        preferences = context.preferences.addons[__name__].preferences
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        
        # Update final statistics
        preferences.is_generating = False
        preferences.show_generation_stats = True
        
        # Ensure the last preview is set
        if self._preview_files and self._current_file_index > 0:
            last_file = self._preview_files[self._current_file_index - 1]
            last_thumb = self.get_thumb_path(last_file)
            if os.path.exists(last_thumb):
                preferences.preview_image = last_thumb
        
        if self._failed_files:
            failed_names = [os.path.basename(f) for f in self._failed_files]
            self.report({'WARNING'}, 
                f"Generated {preferences.preview_stats_completed} previews with {len(self._failed_files)} failures")
        else:
            self.report({'INFO'}, 
                f"Successfully generated {preferences.preview_stats_completed} previews")

        
            
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
            
            # Add row for buttons
            row = col.row(align=True)
            row.scale_y = 1.2
            
            # Preferences button
            row.operator("preferences.addon_show", 
                text="Open Preferences", 
                icon='PREFERENCES').module = __name__
                
            # Browse button
            op = row.operator("wm.directory_browse",
                text="Browse",
                icon='FILE_FOLDER')
            op.directory = preferences.hdri_directory
            # Set the property to update when directory is selected
            op.property_name = "hdri_directory"
            op.property_owner = "preferences"
            return
            
        world = context.scene.world
        if not world or not world.use_nodes:
            box = main_column.box()
            col = box.column(align=True)
            col.scale_y = 1.2 * preferences.button_scale
            # Only show Initialize button if HDRI directory is set
            if preferences.hdri_directory:
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
        browser_header = browser_box.row(align=True)
        browser_header.prop(hdri_settings, "show_browser", 
                           icon='TRIA_DOWN' if hdri_settings.show_browser else 'TRIA_RIGHT',
                           icon_only=True)
        header_row = browser_header.row()
        header_row.label(text="HDRI Browser", icon='FILE_FOLDER')
        if hdri_settings.show_browser:
            # Get current path information
            current_folder = context.scene.hdri_settings.current_folder
            base_dir = preferences.hdri_directory
            
            if current_folder and os.path.exists(current_folder):
                # Show breadcrumb navigation
                try:
                    rel_path = os.path.relpath(current_folder, base_dir)
                    if rel_path != '.':  # Only show if not in root
                        bread_box = browser_box.box()
                        bread_row = bread_box.row(align=True)
                        bread_row.scale_y = 0.9
                        
                        # Start with HDRI root
                        op = bread_row.operator("world.change_hdri_folder", text="HDRI")
                        op.folder_path = base_dir
                        
                        # Add path components
                        if rel_path != '.':
                            path_parts = rel_path.split(os.sep)
                            current_path = base_dir
                            for i, part in enumerate(path_parts):
                                bread_row.label(text="›")
                                current_path = os.path.join(current_path, part)
                                if i < len(path_parts) - 1:
                                    op = bread_row.operator("world.change_hdri_folder", text=part)
                                    op.folder_path = current_path
                                else:
                                    bread_row.label(text=part)
                except:
                    pass
                
                # Display folders only if they exist
                folders = get_folders(context)
                if folders:
                    # Calculate grid layout
                    num_items = len(folders)
                    num_columns = 2 if num_items > 2 else 1
                    
                    # Create grid flow
                    grid = browser_box.grid_flow(
                        row_major=True,
                        columns=num_columns,
                        even_columns=True,
                        even_rows=False,
                        align=True
                    )
                    
                    # Add folders to grid
                    for folder_path, name, tooltip, icon, _ in folders:
                        if folder_path != "parent":
                            row = grid.row(align=True)
                            row.scale_y = 1.2
                            row.scale_x = 1.0
                            
                            op = row.operator(
                                "world.change_hdri_folder",
                                text=name,
                                icon='FILE_FOLDER'
                            )
                            op.folder_path = folder_path
        
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
            sub.label(text="HDRI Select", icon='IMAGE_DATA')
            
            if hdri_settings.show_preview:
                preview_box.scale_y = preferences.button_scale
                
                # HDRI preview grid
                preview_box.template_icon_view(
                    hdri_settings, "hdri_preview",
                    show_labels=True,
                    scale=preferences.preview_scale
                )
                
                # Then show navigation controls if HDRI is active
                if env_tex and env_tex.image and has_active_hdri(context):
                    nav_box = preview_box.box()
                    nav_row = nav_box.row(align=True)
                    
                    # Previous button
                    prev_sub = nav_row.row(align=True)
                    prev_sub.scale_x = 1.2
                    prev_op = prev_sub.operator(
                        "world.previous_hdri", 
                        text="", 
                        icon='TRIA_LEFT',
                        emboss=True
                    )
                    
                    # HDRI name in center
                    name_row = nav_row.row(align=True)
                    name_row.alignment = 'CENTER'
                    name_row.scale_x = 2.0
                    name_row.label(text=env_tex.image.name)
                    
                    # Next button
                    next_sub = nav_row.row(align=True)
                    next_sub.scale_x = 1.2
                    next_op = next_sub.operator(
                        "world.next_hdri", 
                        text="", 
                        icon='TRIA_RIGHT',
                        emboss=True
                    )
                
                # Only keep the Reset button
                row = preview_box.row(align=True)
                row.scale_y = 1.2 * preferences.button_scale
                
                # Reset button
                sub_row = row.row(align=True)
                sub_row.enabled = bool(hdri_settings.previous_hdri_path)
                sub_row.operator("world.reset_to_previous_hdri",
                    text="Reset",
                    icon='LOOP_BACK')
            
            main_column.separator(factor=0.5 * preferences.spacing_scale)
                    
            # Metadata dropdown
            meta_row = preview_box.row(align=True)
            meta_row.label(text="HDRI Metadata", icon='INFO')
            meta_row.scale_y = 0.3
            meta_row.prop(hdri_settings, "show_metadata",
                icon='TRIA_DOWN' if hdri_settings.show_metadata else 'TRIA_RIGHT',
                icon_only=True,
                emboss=False)
            
            if hdri_settings.show_metadata and env_tex and env_tex.image:
                meta_box = preview_box.box()
                meta_col = meta_box.column(align=True)
                meta_col.scale_y = 0.9
                metadata = get_hdri_metadata(env_tex.image)
                
                if metadata:
                    # Filename (new!)
                    row = meta_col.row(align=True)
                    row.label(text="File:", icon='FILE_IMAGE')
                    row.label(text=metadata['filename'])
                  
                    # Resolution
                    row = meta_col.row(align=True)
                    row.label(text="Resolution:", icon='TEXTURE')
                    row.label(text=metadata['resolution'])
                    
                    # Color Space
                    row = meta_col.row(align=True)
                    row.label(text="Color Space:", icon='COLOR')
                    row.label(text=metadata['color_space'])
                    
                    # Channels
                    row = meta_col.row(align=True)
                    row.label(text="Channels:", icon='NODE_COMPOSITING')
                    row.label(text=str(metadata['channels']))
                    
                    # File Size
                    row = meta_col.row(align=True)
                    row.label(text="File Size:", icon='FILE_BLANK')
                    row.label(text=metadata['file_size'])
                    
                    # File Format
                    row = meta_col.row(align=True)
                    row.label(text="Format:", icon='FILE')
                    row.label(text=metadata['file_format'])
        
        # HDRI Settings Section
        if has_active_hdri(context):
            rotation_box = main_column.box()
            row = rotation_box.row(align=True)
            row.scale_y = preferences.button_scale
            row.prop(hdri_settings, "show_rotation", 
                    icon='TRIA_DOWN' if hdri_settings.show_rotation else 'TRIA_RIGHT',
                    icon_only=True)
            sub = row.row(align=True)
            sub.alert = False
            sub.active = hdri_settings.show_rotation
            sub.label(text="Settings", icon='DRIVER_ROTATIONAL_DIFFERENCE')
            
            if hdri_settings.show_rotation:
                # Move keep rotation toggle to the header row with other controls
                sub.prop(preferences, "keep_rotation",
                    text="",
                    icon='LINKED' if preferences.keep_rotation else 'UNLINKED'
                )
                
                # Add visibility toggle
                is_visible = True
                if context.scene.world:
                    is_visible = context.scene.world.cycles_visibility.camera
                
                sub.operator("world.toggle_hdri_visibility",
                    text="",
                    icon='HIDE_OFF' if is_visible else 'HIDE_ON',
                    depress=is_visible)
               
                # Layout based on compact mode
                if preferences.use_compact_ui:
                    # Compact layout
                    col = rotation_box.column(align=True)
                    col.scale_y = preferences.button_scale
                    col.use_property_split = True
                    
                    if mapping:
                        # X Rotation controls
                        row = col.row(align=True)
                        row.prop(mapping.inputs['Rotation'], "default_value", index=0, text="X°")
                        sub = row.row(align=True)
                        sub.scale_x = 1.0 
                        
                        # Increase X rotation
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                        op.axis = 0
                        op.direction = 1
                        
                        # Decrease X rotation
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                        op.axis = 0
                        op.direction = -1                        
                        
                        # Reset X rotation
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                        op.axis = 0
                        op.direction = -99
                        
                        # Y Rotation controls
                        row = col.row(align=True)
                        row.prop(mapping.inputs['Rotation'], "default_value", index=1, text="Y°")
                        sub = row.row(align=True)
                        sub.scale_x = 1.0
                        # Increase Y rotation
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                        op.axis = 1
                        op.direction = 1                      
                        
                        # Decrease Y rotation
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                        op.axis = 1
                        op.direction = -1
                        
                        # Reset Y rotation
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                        op.axis = 1
                        op.direction = -99                        
                        
                        # Z Rotation controls
                        row = col.row(align=True)
                        row.prop(mapping.inputs['Rotation'], "default_value", index=2, text="Z°")
                        sub = row.row(align=True)
                        sub.scale_x = 1.0   
                        # Increase Z rotation
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                        op.axis = 2
                        op.direction = 1                        
                        
                        # Decrease Z rotation
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                        op.axis = 2
                        op.direction = -1
                                               
                        # Reset Z rotation
                        op = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                        op.axis = 2
                        op.direction = -99
                    
                    # Add strength slider in compact mode
                    if preferences.show_strength_slider:
                        col.separator()
                        row = col.row(align=True)
                        sub_row = row.row(align=True)
                        sub_row.prop(hdri_settings, "background_strength", text="Strength")
                        # Reset button with adjusted scale
                        sub = row.row(align=True)
                        sub.scale_x = 1.0
                        sub.scale_y = 1.0
                        sub.operator("world.reset_hdri_strength", text="", icon='LOOP_BACK')
                        
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
                            sub.scale_x = 1.0  # Updated to match comp mode
                            # Add reset button for rotation
                            reset_op = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                            reset_op.axis = i
                            reset_op.direction = -99
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
                        # Modified strength row with reset button
                        row = col.row(align=True)
                        sub_row = row.row(align=True)
                        sub_row.prop(hdri_settings, "background_strength", text="Value")
                        # Reset button with adjusted scale
                        sub = row.row(align=True)
                        sub.scale_x = 1.0
                        sub.scale_y = 1.0
                        sub.operator("world.reset_hdri_strength", text="", icon='LOOP_BACK')
        
        main_column.separator(factor=1.0 * preferences.spacing_scale)
        
        # Footer
        footer = main_column.row(align=True)
        footer.scale_y = 0.8
        
        # Settings button
        settings_btn = footer.operator(
            "preferences.addon_show",
            text="",
            icon='PREFERENCES',
            emboss=False
        )
        # Version number
        footer.label(text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}")
        # Add delete world button
        delete_btn = footer.operator(
            "world.delete_hdri_world",
            text="",
            icon='TRASH',
            emboss=False
        )
        settings_btn.module = __name__
                    
def draw_hdri_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.popover(panel="HDRI_PT_controls", text="HDRI Controls")
    
# Registration
classes = (
    QuickHDRIPreferences,
    HDRI_OT_cleanup_unused,
    HDRISettings,
    HDRI_OT_reset_rotation,
    HDRI_OT_reset_strength,
    HDRI_OT_setup_nodes,
    HDRI_OT_change_folder,
    HDRI_PT_controls,
    HDRI_OT_check_updates,
    HDRI_OT_download_update,
    HDRI_OT_popup_controls,
    HDRI_OT_update_shortcut,
    HDRI_OT_quick_rotate,
    HDRI_OT_reset_to_previous,
    HDRI_OT_toggle_visibility,
    HDRI_OT_browse_directory,
    HDRI_OT_restart_prompt,
    HDRI_OT_delete_world,
    HDRI_OT_show_shortcut_conflicts,
    HDRI_OT_previous_hdri,
    HDRI_OT_next_hdri,
    HDRI_OT_generate_previews,
    HDRI_OT_clear_preview_stats,
)
def register():
    extract_addon_zips()
    
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
    
    # Safely clean up preview collection
    if hasattr(get_hdri_previews, "preview_collection"):
        try:
            preview_collection = get_hdri_previews.preview_collection
            if preview_collection:
                bpy.utils.previews.remove(preview_collection)
            del get_hdri_previews.preview_collection
        except Exception as e:
            print(f"Note: Preview collection cleanup - {str(e)}")
            
if __name__ == "__main__":
    register()
