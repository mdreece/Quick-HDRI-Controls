import urllib.request
import zipfile
import shutil
import tempfile
from datetime import datetime
import bpy
import re
import os
from bpy.types import (Panel, Operator, AddonPreferences, PropertyGroup)
from bpy.props import (FloatProperty, StringProperty, EnumProperty, 
                      CollectionProperty, PointerProperty, IntProperty, 
                      BoolProperty, FloatVectorProperty)
                      
bl_info = {
    "name": "Quick HDRI Controls",
    "author": "Dave Nectariad Rome",
    "version": (1, 5),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Header",
    "warning": "Alpha Version (in-development)",
    "description": "Quickly adjust world HDRI rotation and selection",
    "category": "3D View",
}

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
    
    for i, fn in enumerate(sorted(image_paths)):
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
        version_url = "https://raw.githubusercontent.com/mdreece/Quick-HDRI-Controls/refs/heads/main/__init__.py"
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
 
class HDRI_OT_check_updates(Operator):
    bl_idname = "world.check_hdri_updates"
    bl_label = "Check for Updates"
    bl_description = "Check if a new version is available on GitHub"

    def get_online_version(self):
        """Fetch version info from GitHub"""
        try:
            # Create a request with appropriate headers
            version_url = "https://raw.githubusercontent.com/mdreece/Quick-HDRI-Controls/refs/heads/main/__init__.py"
            req = urllib.request.Request(
                version_url,
                headers={'User-Agent': 'Mozilla/5.0'}  # Add user agent to avoid rejection
            )
            
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
                
                # Find the version line in the content
                for line in content.split('\n'):
                    if '"version":' in line:
                        # Extract version numbers
                        import re
                        version_numbers = re.findall(r'\d+', line)
                        if len(version_numbers) >= 2:
                            return (int(version_numbers[0]), int(version_numbers[1]))
        except Exception as e:
            print(f"Update check error: {str(e)}")  # For debugging
            return None
        return None

    def execute(self, context):
        # Get current version from bl_info
        current_version = bl_info['version']
        
        # Get online version
        online_version = self.get_online_version()
        
        if online_version is None:
            self.report({'ERROR'}, "Could not connect to GitHub. Please check your internet connection.")
            return {'CANCELLED'}
        
        # Compare versions
        if online_version <= current_version:
            self.report({'INFO'}, f"Quick HDRI Controls is up to date (v{current_version[0]}.{current_version[1]})")
            return {'FINISHED'}
        
        # Ask user if they want to update
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
            # Create request with headers
            update_url = "https://github.com/mdreece/Quick-HDRI-Controls/archive/refs/heads/main.zip"
            req = urllib.request.Request(
                update_url,
                headers={'User-Agent': 'Mozilla/5.0'}  # Add user agent
            )
            
            # Download zip file to a temporary location
            self.report({'INFO'}, "Downloading update...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
                with urllib.request.urlopen(req) as response:
                    temp_zip.write(response.read())
                temp_zip_path = temp_zip.name
            
            # Extract the zip file
            self.report({'INFO'}, "Extracting update...")
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                temp_dir = tempfile.mkdtemp()
                zip_ref.extractall(temp_dir)
            
            # Locate the extracted files
            extracted_folder = os.path.join(temp_dir, "Quick-HDRI-Controls-main")
            
            # Verify the extracted folder exists
            if not os.path.exists(extracted_folder):
                self.report({'ERROR'}, "Update package has unexpected structure")
                return {'CANCELLED'}
            
            # Get addon path
            addon_path = os.path.dirname(os.path.realpath(__file__))
            
            # Copy and overwrite all files from extracted folder to the add-on path
            for root, dirs, files in os.walk(extracted_folder):
                rel_path = os.path.relpath(root, extracted_folder)
                dest_path = os.path.join(addon_path, rel_path)
                
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
                
                for file in files:
                    shutil.copy2(os.path.join(root, file), os.path.join(dest_path, file))
            
            # Clean up temporary files
            os.remove(temp_zip_path)
            shutil.rmtree(temp_dir)
            
            self.report({'INFO'}, "Update complete! Please restart Blender to apply changes.")
            return {'FINISHED'}
                
        except urllib.error.URLError as e:
            self.report({'ERROR'}, f"Connection error: {str(e)}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Update failed: {str(e)}")
            return {'CANCELLED'}
            
class HDRI_OT_change_folder(Operator):
    bl_idname = "world.change_hdri_folder"
    bl_label = "Change Folder"
    bl_description = "Change current HDRI folder"
    
    folder_path: StringProperty()
    
    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        base_dir = preferences.hdri_directory
        
        if self.folder_path == "parent":
            current = context.scene.hdri_settings.current_folder
            new_path = os.path.dirname(current)
            
            # Verify we're not going above base directory
            try:
                rel_path = os.path.relpath(new_path, base_dir)
                if rel_path.startswith('..'):
                    self.report({'WARNING'}, "Cannot navigate above HDRI directory")
                    return {'CANCELLED'}
            except ValueError:
                self.report({'WARNING'}, "Invalid path")
                return {'CANCELLED'}
                
            context.scene.hdri_settings.current_folder = new_path
        else:
            # Verify the new path is within base directory
            try:
                rel_path = os.path.relpath(self.folder_path, base_dir)
                if rel_path.startswith('..'):
                    self.report({'WARNING'}, "Cannot navigate outside HDRI directory")
                    return {'CANCELLED'}
                context.scene.hdri_settings.current_folder = self.folder_path
            except ValueError:
                self.report({'WARNING'}, "Invalid path")
                return {'CANCELLED'}
        
        # Clear previews to force regeneration
        pcoll = get_hdri_previews()
        pcoll.clear()
        
        # Force UI update
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        return {'FINISHED'}

def refresh_previews(self, context):
    """Refresh the preview collection when settings change"""
    pcoll = get_hdri_previews()
    pcoll.clear()
    
    # Reset current folder to base directory when HDRI directory changes
    if hasattr(context.scene, "hdri_settings"):
        context.scene.hdri_settings.current_folder = self.hdri_directory

class QuickHDRIPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    # Properties for auto-update and update alert
    enable_auto_update_check: bpy.props.BoolProperty(
        name="Enable Auto-Update Check on Startup",
        description="Automatically check for updates when Blender starts",
        default=False
    )
    update_available: bpy.props.BoolProperty(name="Update Available", default=False)

    # Directory and File Type Settings
    hdri_directory: bpy.props.StringProperty(
        name="HDRI Directory",
        subtype='DIR_PATH',
        description="Directory containing HDRI files",
        default=""
    )
    
    use_hdr: bpy.props.BoolProperty(
        name="HDR",
        description="Include .hdr files",
        default=True
    )
    
    use_exr: bpy.props.BoolProperty(
        name="EXR",
        description="Include .exr files",
        default=True
    )
    
    use_png: bpy.props.BoolProperty(
        name="PNG",
        description="Include .png files",
        default=True
    )
    
    use_jpg: bpy.props.BoolProperty(
        name="JPG",
        description="Include .jpg and .jpeg files",
        default=True
    )
    
    # UI Layout Settings
    ui_scale: bpy.props.IntProperty(
        name="Panel Width",
        description="Width of the HDRI control panel",
        default=10,
        min=1,
        max=30,
        subtype='PIXEL'
    )
    
    preview_scale: bpy.props.IntProperty(
        name="Preview Size",
        description="Size of HDRI preview thumbnails",
        default=8,
        min=1,
        max=20
    )
    
    button_scale: bpy.props.FloatProperty(
        name="Button Scale",
        description="Scale of UI buttons",
        default=1.0,
        min=0.5,
        max=2.0,
        step=0.05
    )
    
    spacing_scale: bpy.props.FloatProperty(
        name="Spacing Scale",
        description="Scale of UI element spacing",
        default=1.0,
        min=0.5,
        max=2.0,
        step=0.1
    )
    
    # Visual Settings
    use_compact_ui: bpy.props.BoolProperty(
        name="Compact UI",
        description="Use compact UI layout",
        default=True
    )
    
    show_file_path: bpy.props.BoolProperty(
        name="Show Full Path",
        description="Show full file path instead of relative path",
        default=False
    )
    
    # Interface Settings
    show_strength_slider: bpy.props.BoolProperty(
        name="Show Strength Slider",
        description="Show the strength slider in the main UI",
        default=True
    )
    
    show_rotation_values: bpy.props.BoolProperty(
        name="Show Rotation Values",
        description="Show numerical values for rotation",
        default=True
    )
    
    strength_max: bpy.props.FloatProperty(
        name="Max Strength",
        description="Maximum value for strength slider",
        default=2.0,
        min=1.0,
        max=10.0,
        step=0.1
    )
    
    rotation_increment: bpy.props.FloatProperty(
        name="Rotation Increment",
        description="Increment for rotation controls",
        default=5.0,
        min=0.1,
        max=45.0,
        step=0.1
    )

    def draw(self, context):
        layout = self.layout

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

        # Separator for visual spacing
        layout.separator()

        # User Interface Settings
        box = layout.box()
        box.label(text="User Interface Settings", icon='PREFERENCES')
        col = box.column(align=True)
        col.prop(self, "ui_scale", text="Panel Width")
        col.prop(self, "preview_scale", text="Preview Size")
        col.prop(self, "button_scale", text="Button Scale")
        col.prop(self, "spacing_scale", text="Spacing Scale")
        
        # Separator for visual spacing
        layout.separator()

        # File Filters & Settings
        box = layout.box()
        box.label(text="File Filters & Settings", icon='FILE_FOLDER')
        
        # Show full path and file types as toggles
        col = box.column(align=True)
        col.prop(self, "show_file_path", text="Show Full Path in Browser")
        
        row = box.row(align=True)
        row.prop(self, "use_hdr", toggle=True)
        row.prop(self, "use_exr", toggle=True)
        row.prop(self, "use_png", toggle=True)
        row.prop(self, "use_jpg", toggle=True)

        # Additional visual settings
        box = layout.box()
        box.label(text="Visual & Interaction Settings", icon='RESTRICT_VIEW_OFF')

        col = box.column(align=True)
        col.prop(self, "show_strength_slider", text="Display Strength Slider")
        col.prop(self, "strength_max", text="Max Strength")
        col.prop(self, "rotation_increment", text="Rotation Increment")



class HDRISettings(PropertyGroup):
    hdri_preview: EnumProperty(
        items=generate_previews,
        name="HDRI Preview"
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
        soft_max=2.0,
        step=0.1,
        precision=3,
        update=update_background_strength
    )
    
    show_browser: BoolProperty(
        name="Show Browser",
        description="Show/Hide Folder Browser section",
        default=True
    )

def refresh_previews(self, context):
    """Refresh the preview collection"""
    pcoll = get_hdri_previews()
    pcoll.clear()

def ensure_world_nodes():
    """Ensure world nodes exist and are properly connected"""
    scene = bpy.context.scene
    
    # Create world if it doesn't exist
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")
    
    world = scene.world
    world.use_nodes = True
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
        
# Ensure nodes exist
        mapping, env_tex, node_background = ensure_world_nodes()
        
        # Load the image
        img = bpy.data.images.load(filepath, check_existing=True)
        env_tex.image = img
        
        return {'FINISHED'}

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
        
        # If update available, highlight in red
        if preferences.update_available:
            row = layout.row()
            row.alert = True
            row.label(text="HDRI Controls - Update Available!", icon='ERROR')
            row.operator("world.download_hdri_update", text="Download Update")
        
        # Early returns with styled messages
        if not preferences.hdri_directory:
            box = layout.box()
            box.alert = True
            col = box.column(align=True)
            col.scale_y = 1.2 * preferences.button_scale
            col.label(text="HDRI Directory Not Set", icon='ERROR')
            col.operator("preferences.addon_show", text="Open Preferences", icon='PREFERENCES').module = __name__
            return
            
        world = context.scene.world
        if not world or not world.use_nodes:
            box = layout.box()
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
            box = layout.box()
            box.alert = True
            col = box.column(align=True)
            col.scale_y = 1.2 * preferences.button_scale
            col.operator("world.setup_hdri_nodes", 
                text="Repair HDRI System",
                icon='FILE_REFRESH')
            return

        # Main UI
        main_column = layout.column(align=True)

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
            
            row = preview_box.row(align=True)
            row.scale_y = 1.2 * preferences.button_scale
            row.operator("world.load_selected_hdri",
                text="Load Selected HDRI",
                icon='IMPORT')
        
        main_column.separator(factor=0.5 * preferences.spacing_scale)
        
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
        
            # Layout adjustments based on compact mode
            if preferences.use_compact_ui:
                # Compact layout
                col = rotation_box.column(align=True)
                col.scale_y = preferences.button_scale
                col.use_property_split = True
                
                if mapping:
                    col.prop(mapping.inputs['Rotation'], "default_value", index=0, text="X°")
                    col.prop(mapping.inputs['Rotation'], "default_value", index=1, text="Y°")
                    col.prop(mapping.inputs['Rotation'], "default_value", index=2, text="Z°")
                
                if preferences.show_strength_slider:
                    col.separator()
                    col.prop(hdri_settings, "background_strength", text="Strength")
            else:
                # Split layout for non-compact mode
                split = rotation_box.split(factor=0.5)
                
                # Rotation column
                col = split.column(align=True)
                col.scale_y = preferences.button_scale
                col.use_property_split = True
                col.label(text="Rotation:")
                
                if mapping:
                    col.prop(mapping.inputs['Rotation'], "default_value", index=0, text="X°")
                    col.prop(mapping.inputs['Rotation'], "default_value", index=1, text="Y°")
                    col.prop(mapping.inputs['Rotation'], "default_value", index=2, text="Z°")
                
                # Strength column
                if preferences.show_strength_slider:
                    col = split.column(align=True)
                    col.scale_y = preferences.button_scale
                    col.use_property_split = True
                    col.label(text="Strength:")
                    col.prop(hdri_settings, "background_strength", text="Value")
                    
        # Add separator before footer
        main_column.separator(factor=1.0 * preferences.spacing_scale)
        
        # Footer row with version and settings
        footer = main_column.row(align=True)
        footer.scale_y = 0.8  # Make the footer slightly smaller
        
        # Version number on the left
        footer.label(text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}")
        
        # Settings button on the right
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
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.hdri_settings = bpy.props.PointerProperty(type=HDRISettings)
    bpy.types.VIEW3D_HT_header.append(draw_hdri_menu)

    # Run update check at startup if enabled
    check_for_update_on_startup()

def unregister():
    bpy.types.VIEW3D_HT_header.remove(draw_hdri_menu)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.hdri_settings

    if hasattr(get_hdri_previews, "preview_collection"):
        bpy.utils.previews.remove(get_hdri_previews.preview_collection)

if __name__ == "__main__":
    register()

