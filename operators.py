"""
Quick HDRI Controls - Operators
"""
import os
import re
import bpy
import sys
import urllib.request
import zipfile
import shutil
import tempfile
import threading
import glob
from datetime import datetime
from math import radians, degrees
from bpy.types import Operator
from bpy.props import (FloatProperty, StringProperty, EnumProperty,
                     IntProperty, BoolProperty, FloatVectorProperty)

class HDRI_OT_popup_controls(Operator):
    bl_idname = "world.hdri_popup_controls"
    bl_label = "HDRI Quick Controls"
    bl_description = "Show HDRI controls at cursor position"
    bl_options = {'REGISTER'}

    def draw(self, context):
        # Import locally to avoid circular imports
        from .ui import HDRI_PT_controls
        layout = self.layout
        HDRI_PT_controls.draw(self, context)

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        addon_name = __package__.split('.')[0]
        prefs = context.preferences.addons[addon_name].preferences
        wm = context.window_manager
        return wm.invoke_popup(self, width=prefs.ui_scale * 20)

class HDRI_OT_setup_nodes(Operator):
    bl_idname = "world.setup_hdri_nodes"
    bl_label = "Setup HDRI Nodes"
    bl_description = "Create and setup the required nodes for HDRI control"

    def execute(self, context):
        # Get the appropriate engine module based on the current render engine
        engine_name = context.scene.render.engine
        
        # Import at function level to avoid circular imports
        if engine_name == 'CYCLES':
            from .render_engines import cycles
            engine_module = cycles
        elif engine_name == 'VRAY_RENDER_RT':
            from .render_engines import vray
            engine_module = vray
        elif engine_name == 'octane':
            from .render_engines import octane
            engine_module = octane
        else:
            # Default to cycles if engine is not supported
            from .render_engines import cycles
            engine_module = cycles
            # Set render engine to cycles if current engine is not supported
            context.scene.render.engine = 'CYCLES'
        
        # Setup HDRI system using the appropriate engine module
        severity, message = engine_module.setup_hdri_system(context)
        self.report(severity, message)

        if severity == {'ERROR'}:
            if message == "HDRI directory not found. Please select a valid directory in preferences.":
                bpy.ops.preferences.addon_show(module=__package__.split('.')[0])
            return {'CANCELLED'}

        return {'FINISHED'}

class HDRI_OT_reset_rotation(Operator):
    bl_idname = "world.reset_hdri_rotation"
    bl_label = "Reset HDRI Rotation"
    bl_description = "Reset all rotation values to 0"

    def execute(self, context):
        # Get the current render engine to determine which implementation to use
        render_engine = context.scene.render.engine
        print(f"Reset rotation called for render engine: {render_engine}")
        
        if render_engine == 'VRAY_RENDER_RT':
            print("Dispatching to V-Ray implementation")
            from .render_engines import vray
            return vray.reset_rotation(context)
        elif render_engine == 'octane':
            print("Dispatching to Octane implementation")
            from .render_engines import octane
            return octane.reset_rotation(context)
        else:
            # Default Cycles implementation
            print("Dispatching to Cycles implementation")
            world = context.scene.world
            if world and world.use_nodes:
                mapping = None
                for node in world.node_tree.nodes:
                    if node.type == 'MAPPING':
                        mapping = node
                        break

                if mapping:
                    mapping.inputs['Rotation'].default_value = (0, 0, 0)
                    print("Reset Cycles rotation to (0, 0, 0)")

            return {'FINISHED'}

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
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        increment = preferences.rotation_increment

        # Return appropriate description based on direction
        if properties.direction == -99:
            return f"Reset {axis_name} rotation to 0°"
        elif properties.direction == -1:
            return f"Decrease {axis_name} rotation by {increment}°"
        else:
            return f"Increase {axis_name} rotation by {increment}°"

    def execute(self, context):
        # Get the current render engine
        render_engine = context.scene.render.engine
        print(f"Quick rotate called for engine {render_engine}, axis {self.axis}, direction {self.direction}")
        
        if render_engine == 'VRAY_RENDER_RT':
            # Use V-Ray specific implementation
            print("Dispatching to V-Ray implementation")
            from .render_engines import vray
            return vray.quick_rotate_hdri(context, self.axis, self.direction)
        elif render_engine == 'octane':
            # Use Octane specific implementation
            print("Dispatching to Octane implementation")
            from .render_engines import octane
            return octane.quick_rotate_hdri(context, self.axis, self.direction)
        else:
            # Default to Cycles implementation
            print("Dispatching to Cycles implementation")
            addon_name = __package__.split('.')[0]
            preferences = context.preferences.addons[addon_name].preferences
            world = context.scene.world

            if world and world.use_nodes:
                for node in world.node_tree.nodes:
                    if node.type == 'MAPPING':
                        current_rotation = list(node.inputs['Rotation'].default_value)

                        if self.direction == -99:  # Reset
                            current_rotation[self.axis] = 0
                            print(f"Reset Cycles axis {self.axis} to 0")
                        else:  # Regular rotation
                            increment_in_radians = radians(preferences.rotation_increment)
                            current_rotation[self.axis] += (self.direction * increment_in_radians)
                            print(f"Adjusted Cycles axis {self.axis} by {self.direction * preferences.rotation_increment}°")

                        node.inputs['Rotation'].default_value = current_rotation
                        break

            return {'FINISHED'}

class HDRI_OT_reset_strength(Operator):
    bl_idname = "world.reset_hdri_strength"
    bl_label = "Reset HDRI Strength"
    bl_description = "Reset strength value to 1.0"

    def execute(self, context):
        if context.scene.render.engine == 'VRAY_RENDER_RT':
            from .render_engines import vray
            return vray.reset_strength(context)
        else:
            # Default Cycles implementation
            context.scene.hdri_settings.background_strength = 1.0
            return {'FINISHED'}

class HDRI_OT_change_folder(Operator):
    bl_idname = "world.change_hdri_folder"
    bl_label = "Change Folder"
    bl_description = "Change current HDRI folder"

    folder_path: StringProperty()

    def execute(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        base_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))
        hdri_settings = context.scene.hdri_settings

        # Handle parent directory navigation
        if self.folder_path == "parent":
            current = os.path.normpath(os.path.abspath(hdri_settings.current_folder))
            new_path = os.path.dirname(current)

            # Only allow if new path is base_dir or within it
            if not (os.path.normpath(new_path) == os.path.normpath(base_dir) or
                   os.path.normpath(new_path).startswith(os.path.normpath(base_dir))):
                self.report({'WARNING'}, "Cannot navigate above HDRI directory")
                return {'CANCELLED'}

            self.folder_path = new_path

        # Normalize target path
        target_path = os.path.normpath(os.path.abspath(self.folder_path))

        # Verify target is base_dir or within it
        if not (os.path.normpath(target_path) == os.path.normpath(base_dir) or
               os.path.normpath(target_path).startswith(os.path.normpath(base_dir))):
            self.report({'WARNING'}, "Cannot navigate outside HDRI directory")
            return {'CANCELLED'}

        # Update current folder
        hdri_settings.current_folder = target_path

        # Reset folder page to 0 when changing directories
        hdri_settings.folder_page = 0

        # Clear preview cache for folder change
        from .utils import get_hdri_previews
        get_hdri_previews.cached_dir = None
        get_hdri_previews.cached_items = []

        # Force UI update
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}

class HDRI_OT_change_folder_page(Operator):
    bl_idname = "world.change_folder_page"
    bl_label = "Change Folder Page"
    bl_description = "Navigate to different pages of folders"

    page: IntProperty(
        name="Page",
        description="Page number or offset",
        default=0
    )

    go_to_page: BoolProperty(
        name="Go To Page",
        description="Go to absolute page number instead of relative offset",
        default=False
    )

    def execute(self, context):
        hdri_settings = context.scene.hdri_settings
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences

        # Get total number of folders and calculate max pages
        from .render_engines import cycles
        folders = cycles.get_folders(context)
        total_folders = len(folders)
        items_per_page = preferences.folders_per_page
        total_pages = max(1, (total_folders + items_per_page - 1) // items_per_page)  # At least 1 page

        # Calculate the new page number with proper bounds
        if self.go_to_page:
            # Absolute page navigation (first/last)
            new_page = max(0, min(self.page, total_pages - 1))
        else:
            # Relative page navigation (prev/next)
            new_page = max(0, min(hdri_settings.folder_page + self.page, total_pages - 1))

        # Update the page property
        hdri_settings.folder_page = new_page

        return {'FINISHED'}

class HDRI_OT_toggle_visibility(Operator):
    bl_idname = "world.toggle_hdri_visibility"
    bl_label = "Toggle HDRI Visibility"
    bl_description = "Toggle HDRI background visibility"

    def execute(self, context):
        # Get the current render engine
        render_engine = context.scene.render.engine
        print(f"Toggle visibility called for render engine: {render_engine}")
        
        if render_engine == 'VRAY_RENDER_RT':
            # Use V-Ray specific implementation
            print("Dispatching to V-Ray implementation")
            from .render_engines import vray
            is_visible = vray.toggle_hdri_visibility(context)
            self.report({'INFO'}, f"Visibility set to: {'Visible' if is_visible else 'Invisible'}")
            
            # Force a redraw of the 3D view
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
                    
            return {'FINISHED'}
        elif render_engine == 'octane':
            # Use Octane specific implementation
            print("Dispatching to Octane implementation")
            from .render_engines import octane
            is_visible = octane.toggle_hdri_visibility(context)
            self.report({'INFO'}, f"Visibility set to: {'Visible' if is_visible else 'Invisible'}")
            
            # Force a redraw of the 3D view
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
                    
            return {'FINISHED'}
        else:
            # Default Cycles implementation
            print("Dispatching to Cycles implementation")
            world = context.scene.world
            if world:
                # Toggle visibility
                world.cycles_visibility.camera = not world.cycles_visibility.camera
                
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
        # Choose the appropriate delete method based on render engine
        if context.scene.render.engine == 'VRAY_RENDER_RT':
            # Use the V-Ray specific implementation
            from .render_engines import vray
            success = vray.delete_world(context)
            if success:
                self.report({'INFO'}, "V-Ray HDRI setup deleted")
            else:
                self.report({'WARNING'}, "V-Ray HDRI setup not found")
        else:
            # Default Cycles implementation
            if context.scene.world:
                world = context.scene.world
                bpy.data.worlds.remove(world, do_unlink=True)
                self.report({'INFO'}, "World deleted")
            else:
                self.report({'WARNING'}, "No world to delete")
                
        return {'FINISHED'}

class HDRI_OT_previous_hdri(Operator):
    bl_idname = "world.previous_hdri"
    bl_label = "Previous HDRI"
    bl_description = "Load the previous HDRI in the current folder"

    def execute(self, context):
        from .render_engines import cycles

        hdri_settings = context.scene.hdri_settings
        enum_items = cycles.generate_previews(self, context)

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
        from .render_engines import cycles

        hdri_settings = context.scene.hdri_settings
        enum_items = cycles.generate_previews(self, context)

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

class HDRI_OT_reset_hdri(Operator):
    bl_idname = "world.reset_hdri"
    bl_label = "Reset HDRI"
    bl_description = "Toggle between current and previous HDRI"

    def execute(self, context):
        # Get the current render engine to use the appropriate implementation
        render_engine = context.scene.render.engine
        
        # Import at function level to avoid circular imports
        from . import utils
        
        # Get active engine module directly using utils function
        # This ensures we're using the correct module for the current render engine
        engine_module = utils.get_active_engine_module()
        
        # Call the engine-specific reset_hdri function
        if render_engine == 'VRAY_RENDER_RT':
            # Use V-Ray specific implementation 
            from .render_engines import vray
            severity, message = vray.reset_hdri(context)
            self.report(severity, message)
            return {'FINISHED'} if severity == {'INFO'} else {'CANCELLED'}
        elif render_engine == 'octane':
            # Use Octane specific implementation
            from .render_engines import octane
            severity, message = octane.reset_hdri(context)
            self.report(severity, message)
            return {'FINISHED'} if severity == {'INFO'} else {'CANCELLED'}
        else:
            # Default to Cycles implementation
            hdri_settings = context.scene.hdri_settings
            from .utils import create_hdri_proxy
            from .core import original_paths
            from .render_engines import cycles
            
            # Check if we have a previous HDRI to restore
            if not hdri_settings.previous_hdri_path:
                self.report({'WARNING'}, "No previous HDRI to restore")
                return {'CANCELLED'}

            # Verify the file still exists
            if not os.path.exists(hdri_settings.previous_hdri_path):
                self.report({'ERROR'}, "Previous HDRI file could not be found")
                return {'CANCELLED'}

            try:
                # Store current state before making changes
                current_path = None
                current_image = None
                world = context.scene.world
                
                if world and world.use_nodes:
                    # Only check cycles_visibility if it exists
                    current_visibility = False
                    if hasattr(world, 'cycles_visibility') and hasattr(world.cycles_visibility, 'camera'):
                        current_visibility = world.cycles_visibility.camera
                        
                    for node in world.node_tree.nodes:
                        if node.type == 'TEX_ENVIRONMENT' and node.image:
                            current_image = node.image
                            current_path = original_paths.get(current_image.name, node.image.filepath)
                            break

                # Set up nodes
                mapping, env_tex, background = cycles.ensure_world_nodes()

                # Store the path we're resetting to
                reset_to_path = original_paths.get(os.path.basename(hdri_settings.previous_hdri_path),
                                               hdri_settings.previous_hdri_path)

                # Load the appropriate version (proxy or original)
                if hdri_settings.proxy_resolution != 'ORIGINAL':
                    # Create and load proxy
                    proxy_path = create_hdri_proxy(reset_to_path, hdri_settings.proxy_resolution)
                    if proxy_path:
                        # Clear existing image
                        if env_tex.image:
                            old_image = env_tex.image
                            env_tex.image = None
                            if old_image.users == 0:
                                bpy.data.images.remove(old_image)

                        # Load proxy
                        img = bpy.data.images.load(proxy_path, check_existing=True)
                        original_paths[img.name] = reset_to_path  # Store original path
                        env_tex.image = img
                    else:
                        # If proxy creation fails, load original
                        img = bpy.data.images.load(reset_to_path, check_existing=True)
                        env_tex.image = img
                else:
                    # Load original
                    img = bpy.data.images.load(reset_to_path, check_existing=True)
                    env_tex.image = img

                # Update the preview selection
                enum_items = cycles.generate_previews(self, context)
                for item in enum_items:
                    if item[0] == reset_to_path:
                        hdri_settings.hdri_preview = item[0]
                        break

                # Update previous HDRI path to the one we just replaced
                if current_path:
                    hdri_settings.previous_hdri_path = current_path
                    # Ensure we maintain the original path in our tracking
                    if current_image and current_image.name in original_paths:
                        original_paths[os.path.basename(current_path)] = original_paths[current_image.name]

                # Only update current folder if there's no active search
                if not hdri_settings.search_query:
                    # Update current folder to the directory of the previous HDRI
                    previous_hdri_dir = os.path.dirname(reset_to_path)
                    addon_name = __package__.split('.')[0]
                    preferences = context.preferences.addons[addon_name].preferences
                    base_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))

                    # Ensure the new folder is within the base HDRI directory
                    try:
                        rel_path = os.path.relpath(previous_hdri_dir, base_dir)
                        if not rel_path.startswith('..'):
                            hdri_settings.current_folder = previous_hdri_dir
                        else:
                            # If somehow outside base directory, reset to base
                            hdri_settings.current_folder = base_dir
                    except ValueError:
                        # Fallback if path comparison fails
                        hdri_settings.current_folder = base_dir

                # Clear preview cache for folder change
                from .utils import get_hdri_previews
                get_hdri_previews.cached_dir = None
                get_hdri_previews.cached_items = []

                # Restore visibility state if it exists
                if world and hasattr(world, 'cycles_visibility') and hasattr(world.cycles_visibility, 'camera'):
                    world.cycles_visibility.camera = current_visibility

                # Force redraw of viewport
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()

                self.report({'INFO'}, "HDRI reset successful")
                return {'FINISHED'}

            except Exception as e:
                self.report({'ERROR'}, f"Failed to reset HDRI: {str(e)}")
                import traceback
                traceback.print_exc()
                return {'CANCELLED'}

class HDRI_OT_update_shortcut(Operator):
    bl_idname = "world.update_hdri_shortcut"
    bl_label = "Update Shortcut"
    bl_description = "Apply the new keyboard shortcut"

    def execute(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        preferences.update_shortcut(context)
        self.report({'INFO'}, "Shortcut updated successfully")
        return {'FINISHED'}

class HDRI_OT_show_shortcut_conflicts(Operator):
    bl_idname = "world.show_hdri_shortcut_conflicts"
    bl_label = "Show Shortcut Conflicts"
    bl_description = "Show any conflicts with the current keyboard shortcut"

    def draw(self, context):
        layout = self.layout
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences

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

class HDRI_OT_clear_hdri_search(Operator):
    bl_idname = "world.clear_hdri_search"
    bl_label = "Clear HDRI Search"
    bl_description = "Clear the current HDRI search query"

    def execute(self, context):
        # Clear the search query and unlock
        context.scene.hdri_settings.search_query = ""
        context.scene.hdri_settings.search_locked = False

        # Clear preview cache
        from .utils import get_hdri_previews
        if hasattr(get_hdri_previews, "cached_dir"):
            get_hdri_previews.cached_dir = None
        if hasattr(get_hdri_previews, "cached_items"):
            get_hdri_previews.cached_items = []
        if hasattr(get_hdri_previews, "last_search_query"):
            get_hdri_previews.last_search_query = ""

        # Clear the preview collection
        pcoll = get_hdri_previews()
        pcoll.clear()

        # Force UI update
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}

class HDRI_OT_toggle_search_bar(Operator):
    bl_idname = "world.toggle_hdri_search_bar"
    bl_label = "Toggle Search Bar"
    bl_description = "Show or hide the HDRI search bar"

    def execute(self, context):
        hdri_settings = context.scene.hdri_settings

        # Toggle the search bar visibility
        hdri_settings.show_search_bar = not hdri_settings.show_search_bar

        # If we're hiding the search bar and there's a search active, clear it
        if not hdri_settings.show_search_bar and hdri_settings.search_query:
            bpy.ops.world.clear_hdri_search()

        return {'FINISHED'}

class HDRI_OT_cleanup_unused(Operator):
    bl_idname = "world.cleanup_unused_hdri"
    bl_label = "Cleanup Unused HDRIs"
    bl_description = "Remove unused HDRI images from memory"

    def execute(self, context):
        try:
            from .utils import cleanup_unused_images

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

class HDRI_OT_cleanup_hdri_proxies(Operator):
    bl_idname = "world.cleanup_hdri_proxies"
    bl_label = "Clean Proxy Cache"
    bl_description = "Remove proxy folders from HDRI directories"

    def execute(self, context):
        try:
            addon_name = __package__.split('.')[0]
            preferences = context.preferences.addons[addon_name].preferences
            hdri_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))

            # Remove all proxy subfolders
            for root, dirs, files in os.walk(hdri_dir):
                for dir in dirs:
                    if dir == 'proxies':
                        proxy_dir = os.path.join(root, dir)
                        try:
                            shutil.rmtree(proxy_dir)
                            self.report({'INFO'}, f"Removed proxy folder: {proxy_dir}")
                        except Exception as e:
                            self.report({'ERROR'}, f"Failed to remove proxy folder: {proxy_dir} ({str(e)})")

            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to clean proxy cache: {str(e)}")
            return {'CANCELLED'}

class HDRI_OT_clear_proxy_stats(Operator):
    bl_idname = "world.clear_proxy_stats"
    bl_label = "Clear Proxy Generation Stats"
    bl_description = "Clear proxy generation statistics"

    def execute(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        preferences.proxy_stats_total = 0
        preferences.proxy_stats_completed = 0
        preferences.proxy_stats_failed = 0
        preferences.proxy_stats_time = 0.0
        preferences.proxy_stats_current_file = ""
        preferences.is_proxy_generating = False
        return {'FINISHED'}

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
        # Instead of trying to access bl_info from the addon instance,
        # import it directly from the main __init__.py file
        try:
            # Method 1: Import bl_info from the main module
            addon_name = __package__.split('.')[0]
            import importlib
            main_module = importlib.import_module(addon_name)
            current_version = main_module.bl_info['version']
        except (ImportError, AttributeError):
            # Method 2: Fallback to hardcoded version if import fails
            current_version = (2, 8, 2)  # Update this to your current version

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

def draw_update_progress(self, context):
    layout = self.layout

    # Get the operator instance if it's running
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'PREFERENCES':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = context.copy()
                        override['area'] = area
                        override['region'] = region

                        # Find the running operator
                        for operator in context.window_manager.operators:
                            if operator.bl_idname == "world.download_hdri_update":
                                op = operator

                                # Display progress information
                                box = layout.box()
                                box.label(text=f"Update Progress: {op._phase}")

                                # Progress bar
                                progress_row = box.row()
                                progress_row.prop(op, "_progress", text="")

                                return

    # If no operator is running or we couldn't find it
    layout.label(text="No update in progress")

class HDRI_OT_download_update(Operator):
    bl_idname = "world.download_hdri_update"
    bl_label = "Download Update"
    bl_description = "Download and install the latest version"

    # Add property to track progress
    _timer = None
    _progress = 0
    _downloading = False
    _extracting = False
    _copying = False
    _phase = "Not started"
    _temp_zip_path = ""
    _temp_dir = ""
    _error_message = ""

    def invoke(self, context, event):
        # Show confirmation dialog
        return context.window_manager.invoke_confirm(
            self,
            event,
            message="Download and install the latest update? Blender will need to restart afterward."
        )

    def modal(self, context, event):
        if event.type == 'TIMER':
            # Update the progress displayed in UI
            for area in context.screen.areas:
                if area.type == 'PREFERENCES':
                    area.tag_redraw()

            # Check if we're done or have an error
            if self._error_message:
                self.report({'ERROR'}, self._error_message)
                self.cleanup()
                return {'CANCELLED'}

            # If we're done
            if self._progress >= 100:
                self.report({'INFO'}, "Update complete! Please restart Blender to apply changes.")
                self.cleanup()

                # Delay the operator invocation until all classes are registered
                def invoke_restart_prompt():
                    bpy.ops.world.restart_prompt('INVOKE_DEFAULT')
                bpy.app.timers.register(invoke_restart_prompt)

                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        # Register a timer for modal and start the process in a separate thread
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)

        # Start the process in a separate thread
        import threading
        self._progress = 0
        threading.Thread(target=self.download_and_install, args=(context,)).start()

        return {'RUNNING_MODAL'}

    def download_and_install(self, context):
        """Main download and install function, runs in a thread"""
        try:
            # Get the addon path
            addon_path = os.path.dirname(os.path.realpath(__file__))

            # Update progress and phase
            self._progress = 5
            self._phase = "Initializing"

            # Backup current render engine preference
            addon_name = __package__.split('.')[0]
            preferences = context.preferences.addons[addon_name].preferences

            # Save current render engine preference
            self._phase = "Saving preferences"
            preferences_path = os.path.join(addon_path, "preferences.json")
            try:
                import json
                with open(preferences_path, 'w') as f:
                    json.dump({
                        'render_engine': preferences.render_engine
                    }, f)
            except Exception as e:
                print(f"Could not save render engine preference: {str(e)}")

            # Update progress
            self._progress = 10

            # Backup the current version before updating
            self._phase = "Creating backup"
            if not self.backup_current_version(addon_path):
                self._error_message = "Failed to create backup before update"
                return

            # Update progress
            self._progress = 20

            # Start downloading the update
            self._phase = "Downloading update"
            self._downloading = True

            update_url = "https://github.com/mdreece/Quick-HDRI-Controls/archive/main.zip"
            req = urllib.request.Request(
                update_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            self._temp_zip_path = ""
            try:
                # Download with progress tracking
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
                    self._temp_zip_path = temp_zip.name
                    with urllib.request.urlopen(req) as response:
                        file_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        block_size = 8192

                        while True:
                            buffer = response.read(block_size)
                            if not buffer:
                                break

                            downloaded += len(buffer)
                            temp_zip.write(buffer)

                            # Update progress (20% to 50%)
                            if file_size > 0:
                                download_progress = int(30 * downloaded / file_size)
                                self._progress = 20 + download_progress
            except Exception as e:
                self._error_message = f"Download failed: {str(e)}"
                return

            # Update progress
            self._progress = 50
            self._downloading = False
            self._extracting = True
            self._phase = "Extracting update"

            # Extract the downloaded zip
            self._temp_dir = tempfile.mkdtemp()
            try:
                with zipfile.ZipFile(self._temp_zip_path, 'r') as zip_ref:
                    total_files = len(zip_ref.infolist())
                    for i, zipinfo in enumerate(zip_ref.infolist()):
                        zip_ref.extract(zipinfo, self._temp_dir)
                        # Update progress (50% to 70%)
                        if total_files > 0:
                            extract_progress = int(20 * (i + 1) / total_files)
                            self._progress = 50 + extract_progress
            except Exception as e:
                self._error_message = f"Extraction failed: {str(e)}"
                return

            # Update progress
            self._progress = 70
            self._extracting = False
            self._copying = True
            self._phase = "Cleaning old files"

            # Find the extracted folder
            extracted_folder = os.path.join(self._temp_dir, "Quick-HDRI-Controls-main")
            if not os.path.exists(extracted_folder):
                self._error_message = f"Could not find extracted folder at {extracted_folder}"
                return

            # Clear existing addon files (except backups directory and Preview.blend)
            try:
                self._progress = 75
                self._phase = "Removing old files"

                # List of directories and files to preserve
                preserved_items = ["backups", "preferences.json"]

                # Remove all files and directories except preserved ones
                for item in os.listdir(addon_path):
                    item_path = os.path.join(addon_path, item)

                    # Skip preserved items
                    if item in preserved_items:
                        continue

                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"Warning: Failed to remove {item}: {str(e)}")
            except Exception as e:
                self._error_message = f"Failed to clean old files: {str(e)}"
                return

            # Update progress
            self._progress = 80
            self._phase = "Installing update"

            # Copy files to the addon directory
            try:
                total_items = 0
                for root, dirs, files in os.walk(extracted_folder):
                    total_items += len(files)

                copied_items = 0
                for root, dirs, files in os.walk(extracted_folder):
                    rel_path = os.path.relpath(root, extracted_folder)
                    dest_path = os.path.join(addon_path, rel_path)

                    os.makedirs(dest_path, exist_ok=True)

                    for file in files:
                        src_file = os.path.join(root, file)
                        dst_file = os.path.join(dest_path, file)
                        try:
                            shutil.copy2(src_file, dst_file)
                            copied_items += 1

                            # Update progress (80% to 90%)
                            if total_items > 0:
                                copy_progress = int(10 * copied_items / total_items)
                                self._progress = 80 + copy_progress
                        except Exception as e:
                            print(f"Failed to copy {file}: {str(e)}")
            except Exception as e:
                self._error_message = f"Installation failed: {str(e)}"
                return

            # Update progress
            self._progress = 90
            self._phase = "Finalizing"

            # Switch to the preferred render engine
            try:
                from .utils import switch_to_preferred_render_engine
                switch_to_preferred_render_engine(addon_path)
            except Exception as e:
                print(f"Warning: Failed to switch render engine: {str(e)}")

            # Clean up
            try:
                if self._temp_zip_path and os.path.exists(self._temp_zip_path):
                    os.remove(self._temp_zip_path)
                if self._temp_dir and os.path.exists(self._temp_dir):
                    shutil.rmtree(self._temp_dir)
            except Exception as e:
                print(f"Warning: Failed to clean up temporary files: {str(e)}")

            # Complete
            self._progress = 100
            self._phase = "Complete"

        except Exception as e:
            # Catch any unexpected errors
            self._error_message = f"Update failed: {str(e)}"

    def cleanup(self):
        """Clean up resources"""
        if self._timer:
            bpy.context.window_manager.event_timer_remove(self._timer)
            self._timer = None

        # Clean up any temporary files that might still exist
        try:
            if self._temp_zip_path and os.path.exists(self._temp_zip_path):
                os.remove(self._temp_zip_path)
            if self._temp_dir and os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir)
        except:
            pass

    def backup_current_version(self, addon_path):
        """Create a backup of the current addon version, with configurable settings"""
        addon_name = __package__.split('.')[0]
        preferences = bpy.context.preferences.addons[addon_name].preferences

        # Check if backups are enabled
        if not preferences.enable_backups:
            print("Backups are disabled. Skipping backup.")
            return True

        import os
        import zipfile
        import time
        import glob

        backups_dir = os.path.join(addon_path, "backups")

        # Create backups directory if it doesn't exist
        os.makedirs(backups_dir, exist_ok=True)

        # Cleanup old backups if max backup count is exceeded
        backup_files = glob.glob(os.path.join(backups_dir, "quick_hdri_controls_v*_*.zip"))
        backup_files.sort(key=os.path.getctime)

        while len(backup_files) >= preferences.max_backup_files and backup_files:
            oldest_backup = backup_files.pop(0)
            try:
                os.unlink(oldest_backup)
            except Exception as e:
                print(f"Could not remove old backup {oldest_backup}: {str(e)}")

        # Get version - we need to import it or use a hardcoded fallback
        try:
            import importlib
            main_module = importlib.import_module(addon_name)
            version_tuple = main_module.bl_info['version']
            version = ".".join(str(x) for x in version_tuple)
        except (ImportError, AttributeError):
            # Fallback to hardcoded version
            version = "2.8.2"  # Update this to match your current version

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"quick_hdri_controls_v{version}_{timestamp}.zip"
        backup_path = os.path.join(backups_dir, backup_filename)

        try:
            # Create a zip file with improved performance settings
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=5) as zipf:
                # Walk through all files and directories in the addon folder
                for root, dirs, files in os.walk(addon_path):
                    # Skip __pycache__ and backups directories
                    dirs[:] = [d for d in dirs if d not in ['__pycache__', 'backups']]

                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate relative path to preserve directory structure
                        relative_path = os.path.relpath(file_path, addon_path)
                        zipf.write(file_path, arcname=relative_path)

            print(f"Backed up current version to {backup_path}")
            return True

        except Exception as e:
            print(f"Failed to create backup: {str(e)}")
            return False

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

class HDRI_OT_revert_version(Operator):
    bl_idname = "world.revert_hdri_version"
    bl_label = "Version Reset"
    bl_description = "Revert to the previously backed up version of the add-on"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(
            self,
            event,
            message="Are you sure you want to revert to the previous version?"
        )

    def execute(self, context):
        addon_dir = os.path.dirname(__file__)
        addon_dir = os.path.dirname(addon_dir)  # Go up one level
        backups_dir = os.path.join(addon_dir, "backups")

        if not os.path.exists(backups_dir):
            self.report({'WARNING'}, "No backups directory found")
            return {'CANCELLED'}

        # Find all backup files in the backups directory
        backup_files = glob.glob(os.path.join(backups_dir, "quick_hdri_controls_v*.zip"))

        if backup_files:
            # Sort backup files by modification time (newest first)
            latest_backup = max(backup_files, key=os.path.getctime)

            try:
                # Remove existing addon files (except backups folder and Preview.blend)
                for item in os.listdir(addon_dir):
                    if item not in ["backups", "Preview.blend"]:
                        item_path = os.path.join(addon_dir, item)
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)

                # Extract backup
                with zipfile.ZipFile(latest_backup, 'r') as zip_ref:
                    zip_ref.extractall(addon_dir)

                # Extract version from backup filename
                version_match = re.search(r'v([\d\.]+)_', os.path.basename(latest_backup))
                if version_match:
                    version = version_match.group(1)
                    self.report({'INFO'}, f"Reverted to version: {version}")
                else:
                    self.report({'INFO'}, f"Successfully reverted to backup: {os.path.basename(latest_backup)}")

                return {'FINISHED'}
            except Exception as e:
                self.report({'ERROR'}, f"Failed to revert: {str(e)}")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "No backup files found in backups directory")
            return {'CANCELLED'}

class HDRI_OT_cleanup_backups(Operator):
    bl_idname = "world.cleanup_hdri_backups"
    bl_label = "Clean Backup Files"
    bl_description = "Remove all backup files for the addon"

    def execute(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        addon_dir = os.path.dirname(__file__)
        addon_dir = os.path.dirname(addon_dir)  # Go up one level
        backups_dir = os.path.join(addon_dir, "backups")

        try:
            if os.path.exists(backups_dir):
                # Remove all files in the backups directory
                for filename in os.listdir(backups_dir):
                    file_path = os.path.join(backups_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        self.report({'WARNING'}, f"Could not remove {filename}: {str(e)}")

                self.report({'INFO'}, "All backup files have been deleted")
            else:
                self.report({'INFO'}, "No backup directory found")

            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to clean backups: {str(e)}")
            return {'CANCELLED'}

    target_engine: StringProperty(default='')

    @classmethod
    def poll(cls, context):
        addon_name = __package__.split('.')[0]
        return context.preferences.addons[addon_name].preferences is not None

    def execute(self, context):
        # Get target engine from temp_engine property or target_engine parameter
        target_engine = self.target_engine or context.scene.temp_engine
        
        # Skip if no change
        if target_engine == context.scene.render.engine:
            return {'CANCELLED'}
        
        # Get addon name
        addon_name = "Quick-HDRI-Controls-main"  # Hardcoded for reliability
        
        # Use the direct addon path - this is the most reliable method
        addon_dir = os.path.join(bpy.utils.user_resource('SCRIPTS'), 
                               "addons", 
                               addon_name)
        
        print(f"Saving preferences to addon dir: {addon_dir}")
        
        # Make sure the directory exists
        if not os.path.exists(addon_dir):
            self.report({'ERROR'}, f"Addon directory not found: {addon_dir}")
            return {'CANCELLED'}
        
        # Save current render engine preference to JSON file
        preferences_path = os.path.join(addon_dir, "preferences.json")
        try:
            import json
            
            # Create or load existing preferences
            prefs_data = {}
            if os.path.exists(preferences_path):
                try:
                    with open(preferences_path, 'r') as f:
                        prefs_data = json.load(f)
                except Exception as e:
                    print(f"Error loading existing preferences: {str(e)}")
            
            # Update the render engine preference
            prefs_data['render_engine'] = target_engine
            
            # Save the updated preferences
            with open(preferences_path, 'w') as f:
                json.dump(prefs_data, f, indent=4)
            
            print(f"✅ Saved render engine preference: {target_engine} to {preferences_path}")
        except Exception as e:
            self.report({'WARNING'}, f"Could not save preferences: {str(e)}")
        
        # Set the preferences to match
        preferences = context.preferences.addons[addon_name].preferences
        preferences.render_engine = target_engine
        
        # Set the render engine in Blender
        previous_engine = context.scene.render.engine
        context.scene.render.engine = target_engine
        
        # Only try to setup HDRI system if a directory is specified
        if preferences.hdri_directory and os.path.exists(preferences.hdri_directory):
            bpy.ops.world.setup_hdri_nodes()
        
        # Report success
        self.report({'INFO'}, f"Switched from {previous_engine} to {target_engine}")
        
        return {'FINISHED'}

class HDRI_OT_show_changelog(Operator):
    bl_idname = "world.show_hdri_changelog"
    bl_label = "Quick HDRI Controls Update"
    bl_description = "Show changelog for the latest update"

    def draw(self, context):
        layout = self.layout
        changes = context.window_manager.hdri_changelog

        if not changes:
            layout.label(text="No changelog information available")
            return

        # Header
        header_box = layout.box()
        header_box.label(text="What's New", icon='TEXT')

        # Version and Date
        version_date_box = header_box.box()
        first_line = changes.split('\n')[0]
        version_date_box.label(text=first_line)

        # Content
        content_box = layout.box()

        section_colors = {
            "Features": (0.2, 0.8, 0.2, 1),  # Green
            "Fixes": (0.8, 0.8, 0.2, 1),     # Yellow
            "Known Issues": (0.8, 0.2, 0.2, 1)  # Red
        }

        current_section = None

        for line in changes.split('\n'):
            line = line.strip()

            if not line or line.startswith('# ') and 'CHANGELOG' in line:
                continue

            if line.startswith('### '):
                section_name = line.replace('### ', '').strip()

                if current_section:
                    content_box.separator()

                section_box = content_box.box()
                section_box.label(text=section_name, icon='DOT')

                if section_name in section_colors:
                    section_box.label(text="")
                    section_box.label(text="")
                    section_box.alert = True
                    section_box.alignment = 'CENTER'
                    section_color = section_colors[section_name]
                    section_box.label(text=section_name, icon='BLANK1', text_color=section_color)

                current_section = section_name

            elif line.startswith('•'):
                if not current_section:
                    continue

                text = line.strip()
                while text:
                    if len(text) <= 60:
                        content_box.label(text=text)
                        break

                    split_idx = text[:60].rfind(' ')
                    if split_idx == -1:
                        split_idx = 60

                    content_box.label(text=text[:split_idx])
                    text = text[split_idx:].lstrip()

        # Footer
        layout.separator()
        footer_box = layout.box()
        footer_box.label(text="Thank you for using Quick HDRI Controls!", icon='FUND')
        footer_box.label(text="Enjoy the new features and improvements.")

        row = footer_box.row()
        row.alignment = 'CENTER'
        row.operator("wm.url_open", text="Documentation", icon='HELP').url = "https://github.com/mdreece/Quick-HDRI-Controls"
        row.operator("wm.url_open", text="Report Issue", icon='URL').url = "https://github.com/mdreece/Quick-HDRI-Controls/issues"
        row.operator("wm.url_open", text="Change log", icon='INFO').url = "https://github.com/mdreece/Quick-HDRI-Controls/blob/main/CHANGELOG.md"
        row.operator("wm.url_open", text="Blender Fund", icon='BLENDER').url = "https://fund.blender.org/"
        row.operator("wm.url_open", text="BM", icon = 'BLENDER').url = "https://blendermarket.com/products/quick-hdri-controls"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=450)

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
            addon_name = __package__.split('.')[0]
            preferences = context.preferences.addons[addon_name].preferences
            setattr(preferences, self.property_name, self.directory)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

# New moved operators from utils.py
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
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
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
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences

        if success:
            preferences.preview_stats_completed += 1
        else:
            preferences.preview_stats_failed += 1

        preferences.preview_stats_current_file = os.path.basename(current_file)
        preferences.preview_stats_time = (datetime.now() - self._start_time).total_seconds()

        # Force redraw of all UI
        for window in context.window_manager.windows:
            window.cursor_modal_set('DEFAULT')
            for area in window.screen.areas:
                area.tag_redraw()

    def modal(self, context, event):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences

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
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences

        if preferences.preview_generation_type == 'FULL_BATCH':
            return bpy.ops.world.full_batch_hdri_previews('INVOKE_DEFAULT')

        # Input validation
        if preferences.preview_generation_type == 'SINGLE':
            if not preferences.preview_single_file:
                self.report({'ERROR'}, "Please select an HDRI file first")
                return {'CANCELLED'}
            if not os.path.exists(preferences.preview_single_file):
                self.report({'ERROR'}, "Selected file does not exist")
                return {'CANCELLED'}
            if not preferences.preview_single_file.lower().endswith(('.hdr', '.exr')):
                self.report({'ERROR'}, "Selected file must be an HDR or EXR file")
                return {'CANCELLED'}
        else:  # MULTIPLE mode
            if not preferences.preview_multiple_folder:
                self.report({'ERROR'}, "Please select a folder first")
                return {'CANCELLED'}
            if not os.path.exists(preferences.preview_multiple_folder):
                self.report({'ERROR'}, "Selected folder does not exist")
                return {'CANCELLED'}
            if not os.path.isdir(preferences.preview_multiple_folder):
                self.report({'ERROR'}, "Selected path is not a folder")
                return {'CANCELLED'}

        self._failed_files = []
        self._current_file_index = 0

        if preferences.preview_generation_type == 'SINGLE':
            self._preview_files = [preferences.preview_single_file]
        else:
            self._preview_files = self.get_hdri_files(preferences.preview_multiple_folder)
            if not self._preview_files:
                self.report({'ERROR'}, "No HDR or EXR files found in selected folder")
                return {'CANCELLED'}

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
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        preferences.show_generation_stats = True
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
        from .utils import get_hdri_previews
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

        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences

        # Get the Preview.blend path
        from .utils import get_preview_blend_path
        preview_blend_path = get_preview_blend_path()

        if not preview_blend_path or not os.path.exists(preview_blend_path):
            self.report({'ERROR'}, f"Preview.blend not found")
            return False

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

            # Set render device based on preference
            if preferences.preview_render_device == 'CPU':
                preview_scene.cycles.device = 'CPU'
            else:
                preview_scene.cycles.device = 'GPU'

            # Load the HDRI image
            hdri_image = None
            try:
                hdri_image = bpy.data.images.load(hdri_path, check_existing=True)
            except Exception as e:
                print(f"Failed to load HDRI image: {e}")
                return False

            # Set collection visibility based on scene type preference
            for collection in preview_scene.collection.children:
                if collection.name == 'Orbs - 4':
                    collection.hide_render = preferences.preview_scene_type != 'ORBS_4'
                    collection.hide_viewport = preferences.preview_scene_type != 'ORBS_4'
                elif collection.name == 'Orbs - 3':
                    collection.hide_render = preferences.preview_scene_type != 'ORBS_3'
                    collection.hide_viewport = preferences.preview_scene_type != 'ORBS_3'
                elif collection.name == 'Teapot':
                    collection.hide_render = preferences.preview_scene_type != 'TEAPOT'
                    collection.hide_viewport = preferences.preview_scene_type != 'TEAPOT'

            # Additional object visibility handling for specific objects
            for obj in preview_scene.objects:
                if preferences.preview_scene_type == 'ORBS_4':
                    # Show GROUND_PLANE and HDRI_PLANE_ORBS for Orbs-4
                    if obj.name in ['GROUND_PLANE', 'HDRI_PLANE_ORBS']:
                        obj.hide_render = False
                        obj.hide_viewport = False

                    # Ensure HDRI is applied to HDRI_PLANE_ORBS
                    if obj.name == 'HDRI_PLANE_ORBS' and hdri_image:
                        for material in obj.data.materials:
                            for node in material.node_tree.nodes:
                                if node.type == 'TEX_IMAGE':
                                    node.image = hdri_image

                elif preferences.preview_scene_type == 'ORBS_3':
                    # Show GROUND_PLANE and HDRI_PLANE_ORBS for Orbs-3
                    if obj.name in ['GROUND_PLANE', 'HDRI_PLANE_ORBS']:
                        obj.hide_render = False
                        obj.hide_viewport = False

                    # Ensure HDRI is applied to HDRI_PLANE_ORBS
                    if obj.name == 'HDRI_PLANE_ORBS' and hdri_image:
                        for material in obj.data.materials:
                            for node in material.node_tree.nodes:
                                if node.type == 'TEX_IMAGE':
                                    node.image = hdri_image

                elif preferences.preview_scene_type == 'TEAPOT':
                    # Show GROUND_PLANE and HDRI_PLANE_ORBS for Teapot
                    if obj.name in ['GROUND_PLANE', 'HDRI_PLANE_ORBS']:
                        obj.hide_render = False
                        obj.hide_viewport = False

                    # Ensure HDRI is applied to HDRI_PLANE_ORBS
                    if obj.name == 'HDRI_PLANE_ORBS' and hdri_image:
                        for material in obj.data.materials:
                            for node in material.node_tree.nodes:
                                if node.type == 'TEX_IMAGE':
                                    node.image = hdri_image
            # Setup world environment texture (outside of scene type blocks)
            world = preview_scene.world
            if world and world.use_nodes:
                for node in world.node_tree.nodes:
                    if node.type == 'TEX_ENVIRONMENT':
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

class HDRI_OT_full_batch_previews(Operator):
    bl_idname = "world.full_batch_hdri_previews"
    bl_label = "Full Batch Preview Generation"
    bl_description = "Generate previews for all HDRIs in all subfolders"

    def invoke(self, context, event):
        message = (
            "⚠️ Batch Process can take several minutes to hours ⚠️\n"
            "• Network speeds affect processing time if using NAS\n\n"
            "🔄 Process Details 🔄\n"
            "• Creates thumbnails for ALL .hdr and .exr files\n"
            "• Searches entire HDRI directory structure\n\n"
            "📝 Settings 📝\n"
            "• Remember to adjust Quality settings!\n\n"
            "Would you like to continue?"
        )

        return context.window_manager.invoke_confirm(
            self,
            event,
            message=message
        )

    def get_all_hdri_files(self, base_dir):
        hdri_files = []
        for root, dirs, files in os.walk(base_dir):
            # Skip 'proxies' folders
            if 'proxies' in dirs:
                dirs.remove('proxies')

            for f in files:
                if f.lower().endswith(('.hdr', '.exr')):
                    hdri_files.append(os.path.join(root, f))
        return hdri_files

    def execute(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        base_dir = preferences.hdri_directory

        if not base_dir or not os.path.exists(base_dir):
            self.report({'ERROR'}, "HDRI directory not set or invalid")
            return {'CANCELLED'}

        # Get all HDRI files recursively
        self._preview_files = self.get_all_hdri_files(base_dir)
        if not self._preview_files:
            self.report({'ERROR'}, "No HDR or EXR files found")
            return {'CANCELLED'}

        self._failed_files = []
        self._current_file_index = 0
        self._total_files = len(self._preview_files)

        # Initialize statistics
        self.initialize_stats(context)

        wm = context.window_manager
        wm.progress_begin(0, 100)
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    # Inherit other methods from HDRI_OT_generate_previews
    initialize_stats = HDRI_OT_generate_previews.initialize_stats
    update_stats = HDRI_OT_generate_previews.update_stats
    modal = HDRI_OT_generate_previews.modal
    finish_preview_generation = HDRI_OT_generate_previews.finish_preview_generation
    generate_single_preview = HDRI_OT_generate_previews.generate_single_preview
    get_thumb_path = HDRI_OT_generate_previews.get_thumb_path
    cancel = HDRI_OT_generate_previews.cancel

class HDRI_OT_clear_preview_stats(Operator):
    bl_idname = "world.clear_preview_stats"
    bl_label = "Clear Statistics"
    bl_description = "Clear preview generation statistics"

    def execute(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        preferences.preview_stats_total = 0
        preferences.preview_stats_completed = 0
        preferences.preview_stats_failed = 0
        preferences.preview_stats_time = 0.0
        preferences.preview_stats_current_file = ""
        preferences.show_generation_stats = False
        return {'FINISHED'}

class HDRI_OT_generate_proxies(Operator):
    bl_idname = "world.generate_hdri_proxies"
    bl_label = "Generate HDRI Proxies"
    bl_description = "Generate proxies for selected folder"

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()

        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        preferences.is_proxy_generating = False

        self.report({'INFO'}, "Proxy generation cancelled")

    def initialize_stats(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        preferences.proxy_stats_total = len(self._hdri_files)
        preferences.proxy_stats_completed = 0
        preferences.proxy_stats_failed = 0
        preferences.proxy_stats_time = 0.0
        preferences.proxy_stats_current_file = ""
        preferences.is_proxy_generating = True
        self._start_time = datetime.now()

    def update_stats(self, context, success, current_file):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        if success:
            preferences.proxy_stats_completed += 1
        else:
            preferences.proxy_stats_failed += 1

        preferences.proxy_stats_current_file = os.path.basename(current_file)
        preferences.proxy_stats_time = (datetime.now() - self._start_time).total_seconds()

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'PREFERENCES':
                    area.tag_redraw()

    def modal(self, context, event):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences

        if event.type == 'TIMER':
            if self._current_file_index >= len(self._hdri_files):
                self.finish_proxy_generation(context)
                return {'FINISHED'}

            current_hdri = self._hdri_files[self._current_file_index]
            success = self.generate_single_proxy(context, current_hdri)

            self.update_stats(context, success, current_hdri)

            progress = (self._current_file_index + 1) / len(self._hdri_files)
            context.window_manager.progress_update(progress * 100)

            self._current_file_index += 1

            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'PREFERENCES':
                        area.tag_redraw()

        return {'RUNNING_MODAL'}

    def execute(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences

        if not preferences.proxy_generation_directory:
            self.report({'ERROR'}, "Please select a directory for proxy generation")
            return {'CANCELLED'}

        self._hdri_files = self.get_hdri_files(preferences.proxy_generation_directory)

        if not self._hdri_files:
            self.report({'ERROR'}, "No HDRI files found in the selected directory")
            return {'CANCELLED'}

        self._current_file_index = 0

        self.initialize_stats(context)

        wm = context.window_manager
        wm.progress_begin(0, 100)

        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def finish_proxy_generation(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        preferences.is_proxy_generating = False
        if preferences.proxy_stats_failed > 0:
            self.report({'WARNING'},
                        f"Generated {preferences.proxy_stats_completed} proxies with {preferences.proxy_stats_failed} failures")
        else:
            self.report({'INFO'},
                        f"Successfully generated {preferences.proxy_stats_completed} proxies")
        # Use a popup dialog or menu to display the button
        def draw_callback(self, context):
            layout = self.layout
            layout.label(text="Proxy Generation Completed")
            layout.operator("world.clear_proxy_stats", text="Clear Results", icon='X')
        context.window_manager.popup_menu(draw_callback, title="Proxy Generation Results", icon='INFO')

    def get_hdri_files(self, directory):
        extensions = ('.hdr', '.exr')
        return [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if f.lower().endswith(extensions)
        ]

    def generate_single_proxy(self, context, hdri_path):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        target_resolution = preferences.proxy_generation_resolution

        try:
            from .utils import create_hdri_proxy
            proxy_path = create_hdri_proxy(hdri_path, target_resolution)
            return proxy_path is not None
        except Exception as e:
            print(f"Error generating proxy for {hdri_path}: {str(e)}")
            return False


class HDRI_OT_full_batch_proxies(Operator):
    bl_idname = "world.full_batch_hdri_proxies"
    bl_label = "Full Batch Proxy Generation"
    bl_description = "Generate proxies for all HDRIs in all subfolders"

    def invoke(self, context, event):
        message = (
            "⚠️ Batch Process can take several minutes to hours ⚠️\n"
            "• Network speeds affect processing time if using NAS\n\n"
            "🔄 Process Details 🔄\n"
            "• Creates proxies for ALL .hdr and .exr files\n"
            "• Searches entire HDRI directory structure\n\n"
            "Would you like to continue?"
        )

        return context.window_manager.invoke_confirm(
            self,
            event,
            message=message
        )

    def get_all_hdri_files(self, base_dir):
        hdri_files = []
        for root, dirs, files in os.walk(base_dir):
            # Skip 'proxies' folders
            if 'proxies' in dirs:
                dirs.remove('proxies')

            for f in files:
                if f.lower().endswith(('.hdr', '.exr')):
                    hdri_files.append(os.path.join(root, f))
        return hdri_files

    def execute(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences

        if not preferences.hdri_directory:
            self.report({'ERROR'}, "Please set HDRI directory first")
            return {'CANCELLED'}

        self._hdri_files = self.get_all_hdri_files(preferences.hdri_directory)

        if not self._hdri_files:
            self.report({'ERROR'}, "No HDRI files found")
            return {'CANCELLED'}

        self._current_file_index = 0

        self.initialize_stats(context)

        wm = context.window_manager
        wm.progress_begin(0, 100)
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def initialize_stats(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        preferences.proxy_stats_total = len(self._hdri_files)
        preferences.proxy_stats_completed = 0
        preferences.proxy_stats_failed = 0
        preferences.proxy_stats_time = 0.0
        preferences.proxy_stats_current_file = ""
        preferences.is_proxy_generating = True
        self._start_time = datetime.now()

    def update_stats(self, context, success, current_file):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        if success:
            preferences.proxy_stats_completed += 1
        else:
            preferences.proxy_stats_failed += 1

        preferences.proxy_stats_current_file = os.path.basename(current_file)
        preferences.proxy_stats_time = (datetime.now() - self._start_time).total_seconds()

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'PREFERENCES':
                    area.tag_redraw()

    def modal(self, context, event):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences

        if event.type == 'TIMER':
            if self._current_file_index >= len(self._hdri_files):
                self.finish_proxy_generation(context)
                return {'FINISHED'}

            current_hdri = self._hdri_files[self._current_file_index]
            success = self.generate_single_proxy(context, current_hdri)

            self.update_stats(context, success, current_hdri)

            progress = (self._current_file_index + 1) / len(self._hdri_files)
            context.window_manager.progress_update(progress * 100)

            self._current_file_index += 1

            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'PREFERENCES':
                        area.tag_redraw()

        return {'RUNNING_MODAL'}

    def finish_proxy_generation(self, context):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        preferences.is_proxy_generating = False
        if preferences.proxy_stats_failed > 0:
            self.report({'WARNING'},
                      f"Generated {preferences.proxy_stats_completed} proxies with {preferences.proxy_stats_failed} failures")
        else:
            self.report({'INFO'},
                      f"Successfully generated {preferences.proxy_stats_completed} proxies")
        # Use a popup dialog or menu to display the button
        def draw_callback(self, context):
            layout = self.layout
            layout.label(text="Proxy Generation Completed")
            layout.operator("world.clear_proxy_stats", text="Clear Results", icon='X')
        context.window_manager.popup_menu(draw_callback, title="Proxy Generation Results", icon='INFO')

    def generate_single_proxy(self, context, hdri_path):
        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        target_resolution = preferences.proxy_generation_resolution

        try:
            from .utils import create_hdri_proxy
            proxy_path = create_hdri_proxy(hdri_path, target_resolution)
            return proxy_path is not None
        except Exception as e:
            print(f"Error generating proxy for {hdri_path}: {str(e)}")
            return False

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()

        addon_name = __package__.split('.')[0]
        preferences = context.preferences.addons[addon_name].preferences
        preferences.is_proxy_generating = False

        self.report({'INFO'}, "Proxy generation cancelled")
        
        
class HDRI_OT_apply_render_engine(Operator):
    bl_idname = "world.apply_render_engine"
    bl_label = "Apply Render Engine"
    bl_description = "Switch between render engines"

    target_engine: StringProperty(default='')

    @classmethod
    def poll(cls, context):
        addon_name = __package__.split('.')[0]
        return context.preferences.addons[addon_name].preferences is not None

    def execute(self, context):
        # Get target engine from temp_engine property or target_engine parameter
        target_engine = self.target_engine or context.scene.temp_engine
        
        # Skip if no change
        if target_engine == context.scene.render.engine:
            return {'CANCELLED'}
        
        # Get addon name
        addon_name = "Quick-HDRI-Controls-main"  # Hardcoded for reliability
        
        # Use the direct addon path - this is the most reliable method
        addon_dir = os.path.join(bpy.utils.user_resource('SCRIPTS'), 
                               "addons", 
                               addon_name)
        
        # Make sure the directory exists
        if not os.path.exists(addon_dir):
            self.report({'ERROR'}, f"Addon directory not found: {addon_dir}")
            return {'CANCELLED'}
        
        # Save current render engine preference to JSON file
        preferences_path = os.path.join(addon_dir, "preferences.json")
        try:
            import json
            
            # Create or load existing preferences
            prefs_data = {}
            if os.path.exists(preferences_path):
                try:
                    with open(preferences_path, 'r') as f:
                        prefs_data = json.load(f)
                except Exception as e:
                    print(f"Error loading existing preferences: {str(e)}")
            
            # Update the render engine preference
            prefs_data['render_engine'] = target_engine
            
            # Save the updated preferences
            with open(preferences_path, 'w') as f:
                json.dump(prefs_data, f, indent=4)
        except Exception as e:
            self.report({'WARNING'}, f"Could not save preferences: {str(e)}")
        
        # Set the preferences to match
        preferences = context.preferences.addons[addon_name].preferences
        preferences.render_engine = target_engine
        
        # Set the render engine in Blender - ensure lowercase for Octane
        previous_engine = context.scene.render.engine
        context.scene.render.engine = target_engine
        
        # Report success
        self.report({'INFO'}, f"Switched from {previous_engine} to {target_engine}")
        
        return {'FINISHED'}

# Dictionary mapping all operators for registration
operators = {
    HDRI_OT_popup_controls,
    HDRI_OT_setup_nodes,
    HDRI_OT_reset_rotation,
    HDRI_OT_quick_rotate,
    HDRI_OT_reset_strength,
    HDRI_OT_change_folder,
    HDRI_OT_change_folder_page,
    HDRI_OT_toggle_visibility,
    HDRI_OT_delete_world,
    HDRI_OT_previous_hdri,
    HDRI_OT_next_hdri,
    HDRI_OT_reset_hdri,
    HDRI_OT_update_shortcut,
    HDRI_OT_show_shortcut_conflicts,
    HDRI_OT_clear_hdri_search,
    HDRI_OT_toggle_search_bar,
    HDRI_OT_cleanup_unused,
    HDRI_OT_cleanup_hdri_proxies,
    HDRI_OT_clear_proxy_stats,
    HDRI_OT_check_updates,
    HDRI_OT_download_update,
    HDRI_OT_restart_prompt,
    HDRI_OT_revert_version,
    HDRI_OT_cleanup_backups,
    HDRI_OT_apply_render_engine,
    HDRI_OT_show_changelog,
    HDRI_OT_browse_directory,
    HDRI_OT_generate_previews,
    HDRI_OT_generate_proxies,
    HDRI_OT_full_batch_previews,
    HDRI_OT_full_batch_proxies,
    HDRI_OT_clear_preview_stats,
}

def register_operators():
    for operator in operators:
        bpy.utils.register_class(operator)

def unregister_operators():
    for operator in reversed(list(operators)):
        bpy.utils.unregister_class(operator)
