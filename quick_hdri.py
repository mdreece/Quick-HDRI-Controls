bl_info = {
    "name": "Quick HDRI Controls",
    "author": "Dave Nectariad Rome",
    "version": (0, 6),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Header",
    "warning": "Alpha Version (in-development)",
    "description": "Quickly adjust world HDRI rotation and selection",
    "category": "3D View",
}

import urllib.request
import zipfile
import shutil
import tempfile
from datetime import datetime
import bpy
import os
from bpy.types import (Panel, Operator, AddonPreferences, PropertyGroup)
from bpy.props import (FloatProperty, StringProperty, EnumProperty, 
                      CollectionProperty, PointerProperty, IntProperty, 
                      BoolProperty, FloatVectorProperty)

def get_hdri_previews():
    if not hasattr(get_hdri_previews, "preview_collection"):
        pcoll = bpy.utils.previews.new()
        get_hdri_previews.preview_collection = pcoll
    return get_hdri_previews.preview_collection

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

def generate_previews(self, context):
    """Generate preview items for HDRIs in current folder"""
    enum_items = []
    
    if not hasattr(context.scene, "hdri_settings"):
        return enum_items
        
    current_dir = context.scene.hdri_settings.current_folder
    preferences = context.preferences.addons[__name__].preferences
    
    if not current_dir or not os.path.exists(current_dir):
        return enum_items
    
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

def update_background_strength(self, context):
    if context.scene.world and context.scene.world.use_nodes:
        for node in context.scene.world.node_tree.nodes:
            if node.type == 'BACKGROUND':
                node.inputs['Strength'].default_value = self.background_strength
 
class HDRI_OT_check_updates(Operator):
    bl_idname = "world.check_hdri_updates"
    bl_label = "Check for Updates"
    bl_description = "Check and download updates from GitHub"
    
    def execute(self, context):
        update_url = "https://raw.githubusercontent.com/mdreece/Quick-HDRI-Controls/main/quick_hdri.py"
        addon_path = os.path.dirname(os.path.realpath(__file__))
        
        try:
            # Create backup of current version
            backup_dir = os.path.join(os.path.dirname(addon_path), 
                                    f"quick_hdri_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(backup_dir, exist_ok=True)
            
            current_file = os.path.join(addon_path, "quick_hdri.py")
            backup_file = os.path.join(backup_dir, "quick_hdri.py")
            
            # Backup current version
            self.report({'INFO'}, "Creating backup...")
            shutil.copy2(current_file, backup_file)
            
            # Download new version
            self.report({'INFO'}, "Downloading update...")
            urllib.request.urlretrieve(update_url, current_file)
            
            self.report({'INFO'}, "Update complete! Please restart Blender to apply changes.")
            return {'FINISHED'}
                
        except urllib.error.URLError:
            self.report({'ERROR'}, "Could not connect to GitHub. Please check your internet connection.")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Update failed: {str(e)}")
            return {'CANCELLED'}
 
class QuickHDRIPreferences(AddonPreferences):
    bl_idname = __name__

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
        default=15,
        min=1,
        max=30,
        subtype='PIXEL'
    )
    
    preview_scale: IntProperty(
        name="Preview Size",
        description="Size of HDRI preview thumbnails",
        default=5,
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
    
    grid_columns: IntProperty(
        name="Grid Columns",
        description="Number of columns in folder grid",
        default=3,
        min=1,
        max=6
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
    
    # Animation Settings
    enable_smooth_rotation: BoolProperty(
        name="Smooth Rotation",
        description="Enable smooth rotation animation",
        default=False
    )
    
    rotation_speed: FloatProperty(
        name="Rotation Speed",
        description="Speed of rotation animation",
        default=1.0,
        min=0.1,
        max=5.0,
        step=0.1
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
    
    use_radians: BoolProperty(
        name="Use Radians",
        description="Display rotation values in radians instead of degrees",
        default=False
    )
    
    strength_max: FloatProperty(
        name="Max Strength",
        description="Maximum value for strength slider",
        default=2.0,
        min=1.0,
        max=10.0,
        step=0.1
    )
    
    rotation_increment: FloatProperty(
        name="Rotation Increment",
        description="Increment for rotation controls",
        default=5.0,
        min=0.1,
        max=45.0,
        step=0.1
    )

    def draw(self, context):
        layout = self.layout
        
        #Update Options
        box = layout.box()
        box.label(text="Updates:", icon='URL')
        row = box.row(align=True)
        row.scale_y = 1.2
        update_op = row.operator("world.check_hdri_updates", 
                                text="Check for Updates", 
                                icon='FILE_REFRESH')
        
        layout.separator()
        
        # File Settings
        box = layout.box()
        box.label(text="File Settings:", icon='FILE_FOLDER')
        
        # HDRI Directory with file type filters
        col = box.column(align=True)
        col.prop(self, "hdri_directory")
        
        # File type filters in a row
        row = box.row()
        row.label(text="File Types:")
        row = box.row(align=True)
        row.prop(self, "use_hdr", toggle=True)
        row.prop(self, "use_exr", toggle=True)
        row.prop(self, "use_png", toggle=True)
        row.prop(self, "use_jpg", toggle=True)
        
        # UI Layout Settings
        box = layout.box()
        box.label(text="Layout Settings:", icon='PREFERENCES')
        
        col = box.column(align=True)
        col.prop(self, "ui_scale")
        col.prop(self, "preview_scale")
        col.prop(self, "button_scale")
        col.prop(self, "spacing_scale")
        col.prop(self, "grid_columns")
        
        # Visual Settings
        box = layout.box()
        box.label(text="Visual Settings:", icon='RESTRICT_VIEW_OFF')
        
        col = box.column(align=True)
        row = col.row()
        row.prop(self, "show_file_path")
        
        # Animation Settings
        box = layout.box()
        box.label(text="Animation Settings:", icon='ACTION')
        
        col = box.column(align=True)
        col.prop(self, "enable_smooth_rotation")
        if self.enable_smooth_rotation:
            col.prop(self, "rotation_speed")
        
        # Interface Settings
        box = layout.box()
        box.label(text="Interface Settings:", icon='WINDOW')
        
        col = box.column(align=True)
        col.prop(self, "show_strength_slider")
        col.prop(self, "use_radians")
        
        col.prop(self, "strength_max")
        col.prop(self, "rotation_increment")

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
    
    show_browser: BoolProperty(
        name="Show Browser",
        description="Show/Hide HDRI Browser section",
        default=True
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

def refresh_previews(self, context):
    """Refresh the preview collection"""
    pcoll = get_hdri_previews()
    pcoll.clear()
    
    if hasattr(context.scene, "hdri_settings"):
        context.scene.hdri_settings.current_folder = self.hdri_directory

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
        
        # Clear previews
        pcoll = get_hdri_previews()
        pcoll.clear()
        
        # Force UI update
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
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
        
        # Scale factors from preferences
        button_scale = preferences.button_scale
        spacing = preferences.spacing_scale
        use_compact = preferences.use_compact_ui
        show_strength = preferences.show_strength_slider
        show_rotation = preferences.show_rotation_values
        use_radians = preferences.use_radians
        
        # Early returns with styled messages
        if not preferences.hdri_directory:
            box = layout.box()
            box.alert = True
            col = box.column(align=True)
            col.scale_y = 1.2 * button_scale
            col.label(text="HDRI Directory Not Set", icon='ERROR')
            col.operator("preferences.addon_show", text="Open Preferences", icon='PREFERENCES').module = __name__
            return
            
        world = context.scene.world
        if not world or not world.use_nodes:
            box = layout.box()
            col = box.column(align=True)
            col.scale_y = 1.2 * button_scale
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
            col.scale_y = 1.2 * button_scale
            col.operator("world.setup_hdri_nodes", 
                text="Repair HDRI System",
                icon='FILE_REFRESH')
            return

        # Main UI
        main_column = layout.column(align=True)
        
        # Folder Navigation Section
        browser_box = main_column.box()
        row = browser_box.row(align=True)
        row.scale_y = button_scale
        row.prop(hdri_settings, "show_browser", 
                icon='TRIA_DOWN' if hdri_settings.show_browser else 'TRIA_RIGHT',
                icon_only=True)
        sub = row.row(align=True)
        sub.alert = False
        sub.active = hdri_settings.show_browser
        sub.label(text="HDRI Browser", icon='FILEBROWSER')
        
        if hdri_settings.show_browser:
            browser_box.scale_y = button_scale
            
            # Current path display with path preference
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
            
            # Grid with preference columns
            folders = get_folders(context)
            if folders:
                folder_grid = browser_box.grid_flow(
                    row_major=True, 
                    columns=preferences.grid_columns,
                    align=True
                )
                folder_grid.scale_y = button_scale
                for folder_path, name, _, icon, _ in folders:
                    op = folder_grid.operator("world.change_hdri_folder",
                        text=name,
                        icon=icon,
                        depress=(folder_path == current_folder))
                    op.folder_path = folder_path
        
        main_column.separator(factor=0.5 * spacing)
        
        # HDRI Preview Section
        preview_box = main_column.box()
        row = preview_box.row(align=True)
        row.scale_y = button_scale
        row.prop(hdri_settings, "show_preview", 
                icon='TRIA_DOWN' if hdri_settings.show_preview else 'TRIA_RIGHT',
                icon_only=True)
        sub = row.row(align=True)
        sub.alert = False
        sub.active = hdri_settings.show_preview
        sub.label(text="HDRI Selection", icon='IMAGE_DATA')
        
        if hdri_settings.show_preview:
            preview_box.scale_y = button_scale
            
            # Show current HDRI name
            if env_tex and env_tex.image:
                row = preview_box.row()
                row.alert = False
                row.alignment = 'CENTER'
                row.scale_y = button_scale
                row.label(text=env_tex.image.name, icon='CHECKMARK')
                preview_box.separator(factor=0.5 * spacing)
            
            preview_box.template_icon_view(
                hdri_settings, "hdri_preview",
                show_labels=True,
                scale=preferences.preview_scale
            )
            
            row = preview_box.row(align=True)
            row.scale_y = 1.2 * button_scale
            row.operator("world.load_selected_hdri",
                text="Load Selected HDRI",
                icon='IMPORT')
        
        main_column.separator(factor=0.5 * spacing)
        
        # Rotation Controls Section
        rotation_box = main_column.box()
        row = rotation_box.row(align=True)
        row.scale_y = button_scale
        row.prop(hdri_settings, "show_rotation", 
                icon='TRIA_DOWN' if hdri_settings.show_rotation else 'TRIA_RIGHT',
                icon_only=True)
        sub = row.row(align=True)
        sub.alert = False
        sub.active = hdri_settings.show_rotation
        sub.label(text="HDRI Settings", icon='DRIVER_ROTATIONAL_DIFFERENCE')
        
        if hdri_settings.show_rotation:
            sub.operator("world.reset_hdri_rotation", text="", icon='LOOP_BACK')
            if show_strength:
                sub.operator("world.reset_hdri_strength", text="", icon='FILE_REFRESH')
        
            # Layout adjustments based on compact mode
            if use_compact:
                # Compact layout
                col = rotation_box.column(align=True)
                col.scale_y = button_scale
                col.use_property_split = True
                
                if mapping:
                    if use_radians:
                        col.prop(mapping.inputs['Rotation'], "default_value", index=0, text="X (rad)")
                        col.prop(mapping.inputs['Rotation'], "default_value", index=1, text="Y (rad)")
                        col.prop(mapping.inputs['Rotation'], "default_value", index=2, text="Z (rad)")
                    else:
                        col.prop(mapping.inputs['Rotation'], "default_value", index=0, text="X°")
                        col.prop(mapping.inputs['Rotation'], "default_value", index=1, text="Y°")
                        col.prop(mapping.inputs['Rotation'], "default_value", index=2, text="Z°")
                
                if show_strength:
                    col.separator()
                    col.prop(hdri_settings, "background_strength", text="Strength")
            else:
                # Split layout for non-compact mode
                split = rotation_box.split(factor=0.5)
                
                # Rotation column
                col = split.column(align=True)
                col.scale_y = button_scale
                col.use_property_split = True
                col.label(text="Rotation:")
                
                if mapping:
                    if use_radians:
                        col.prop(mapping.inputs['Rotation'], "default_value", index=0, text="X (rad)")
                        col.prop(mapping.inputs['Rotation'], "default_value", index=1, text="Y (rad)")
                        col.prop(mapping.inputs['Rotation'], "default_value", index=2, text="Z (rad)")
                    else:
                        col.prop(mapping.inputs['Rotation'], "default_value", index=0, text="X°")
                        col.prop(mapping.inputs['Rotation'], "default_value", index=1, text="Y°")
                        col.prop(mapping.inputs['Rotation'], "default_value", index=2, text="Z°")
                
                # Strength column
                if show_strength:
                    col = split.column(align=True)
                    col.scale_y = button_scale
                    col.use_property_split = True
                    col.label(text="Strength:")
                    col.prop(hdri_settings, "background_strength", text="Value")       
        
        # Settings button and version
        if not use_compact:
            main_column.separator(factor=0.3 * spacing)
        row = main_column.row()
        
        # Version label on the left
        version_sub = row.row()
        version_sub.alignment = 'LEFT'
        version_sub.scale_y = button_scale * 0.8
        version_text = f"v{bl_info['version'][0]}.{bl_info['version'][1]}"
        version_sub.label(text=version_text)
        
        # Settings button on the right
        settings_sub = row.row()
        settings_sub.alignment = 'RIGHT'
        settings_sub.scale_y = button_scale * 0.8
        settings_sub.operator("preferences.addon_show",
            text="",
            icon='PREFERENCES').module = __name__

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
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.hdri_settings = PointerProperty(type=HDRISettings)
    bpy.types.VIEW3D_HT_header.append(draw_hdri_menu)

def unregister():
    bpy.types.VIEW3D_HT_header.remove(draw_hdri_menu)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.hdri_settings
    
    if hasattr(get_hdri_previews, "preview_collection"):
        bpy.utils.previews.remove(get_hdri_previews.preview_collection)

if __name__ == "__main__":
    register()
