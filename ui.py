"""
Quick HDRI Controls - UI components
"""
import os
import bpy
from bpy.types import Panel
from . import utils
from . import hdri_management
from .utils import get_icons
from . import utils

from .utils import world_has_nodes, enable_world_nodes

def get_vray_current_hdri_name(context):
    """FOR NEW API"""
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                node_tree = obj.data.node_tree
                bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
                if bitmap_node:
                    if hasattr(bitmap_node, 'texture') and bitmap_node.texture and bitmap_node.texture.image:
                        image_path = bitmap_node.texture.image.filepath
                        if image_path:
                            return os.path.basename(image_path)

                    elif hasattr(bitmap_node, 'BitmapBuffer') and bitmap_node.BitmapBuffer.file:
                        return os.path.basename(bitmap_node.BitmapBuffer.file)
                break
    return "No HDRI"

_current_panel_class = None
_current_menu_function = None

class HDRI_PT_controls_header(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "HDRI Controls"
    bl_ui_units_x = 10

    def draw(self, context):
        draw_hdri_controls(self, context)

class HDRI_PT_controls_sidebar(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "HDRI"
    bl_label = "HDRI Controls"

    def draw(self, context):
        draw_hdri_controls(self, context)

class HDRI_PT_controls_world(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"
    bl_label = "HDRI Controls"

    def draw(self, context):
        draw_hdri_controls(self, context)

class HDRI_PT_controls_material(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    bl_label = "HDRI Controls"

    def draw(self, context):
        draw_hdri_controls(self, context)

class HDRI_PT_controls_render(Panel):
    """HDRI Controls panel for Render Properties"""
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_label = "HDRI Controls"

    def draw(self, context):
        draw_hdri_controls(self, context)

class HDRI_PT_controls_shader_editor(Panel):
    """HDRI Controls panel for Shader Editor"""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "HDRI"
    bl_label = "HDRI Controls"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        draw_hdri_controls(self, context)

class HDRI_PT_controls_image_editor(Panel):
    """HDRI Controls panel for Image Editor"""
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "HDRI"
    bl_label = "HDRI Controls"

    def draw(self, context):
        draw_hdri_controls(self, context)

def draw_hdri_controls(self, context):
    """Shared draw function for HDRI controls panel"""
    try:
        # Only print debug info when the engine changes
        current_engine = context.scene.render.engine
        if not hasattr(draw_hdri_controls, "_last_engine") or draw_hdri_controls._last_engine != current_engine:
            print(f"HDRI Controls UI draw: Engine changed from {getattr(draw_hdri_controls, '_last_engine', 'None')} to {current_engine}")
            draw_hdri_controls._last_engine = current_engine

        # Get addon name and preferences
        addon_name = utils.get_addon_name()
        preferences = context.preferences.addons[addon_name].preferences

        # Set UI units for header panels only
        if hasattr(self, 'bl_region_type') and self.bl_region_type == 'HEADER':
            self.bl_ui_units_x = preferences.ui_scale

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        hdri_settings = context.scene.hdri_settings

        main_column = layout.column(align=True)

        # Get icons without debug printing
        icons = get_icons()

        # Create engine selector with name on left and compact dropdown on right
        header_row = main_column.row(align=True)
        header_row.scale_y = 1.2

        # Note: We don't set temp_engine here because writing to scene properties
        # during draw is not allowed. The load_preferred_engine handler will sync it.

        # Left side: Engine name with icon (takes up more space for easier clicking/dragging)
        engine_name_row = header_row.row(align=True)
        engine_name_row.scale_x = 2.0  # Give it more space

        # Get icon ID and name based on current engine
        icon_id = 0  # Default fallback
        engine_name = "Unknown Engine"

        if current_engine == 'CYCLES':
            cycles_icon = icons.get("cycles_icon")
            icon_id = cycles_icon.icon_id if cycles_icon else 0
            engine_name = "Cycles"
        elif current_engine == 'BLENDER_EEVEE':
            eevee_icon = icons.get("eevee_icon")
            icon_id = eevee_icon.icon_id if eevee_icon else 0
            engine_name = "Eevee"
        elif current_engine == 'BLENDER_EEVEE_NEXT':
            eevee_next_icon = icons.get("eevee_next_icon")
            icon_id = eevee_next_icon.icon_id if eevee_next_icon else 0
            engine_name = "Eevee Next"
        elif current_engine == 'VRAY_RENDER_RT':
            vray_icon = icons.get("vray_icon")
            icon_id = vray_icon.icon_id if vray_icon else 0
            engine_name = "V-Ray"
        elif current_engine == 'octane':
            octane_icon = icons.get("octane_icon")
            icon_id = octane_icon.icon_id if octane_icon else 0
            engine_name = "Octane"

        # Display current engine name with icon (larger clickable area)
        engine_name_row.label(text=engine_name, icon_value=icon_id)

        # Right side: Compact engine selector dropdown (icon-only)
        engine_selector_row = header_row.row(align=True)
        engine_selector_row.scale_x = 0.8  # Make it more compact

        # Custom property UI that shows only icons in the dropdown
        engine_selector_row.prop(context.scene, "temp_engine", text="", icon_only=True)

        # Apply button (compact)
        apply_btn = header_row.row(align=True)
        apply_btn.scale_x = 0.9  # Make it smaller

        # Check if engines match
        engines_match = (context.scene.temp_engine == context.scene.render.engine)

        # Make the button red if engines don't match
        if not engines_match:
            apply_btn.alert = True  # This makes the button red

        apply_btn.operator("world.apply_render_engine", text="", icon='CHECKMARK')

        main_column.separator(factor=0.5 * preferences.spacing_scale)

        # Check if HDRI directory is set
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
                icon='PREFERENCES').module = addon_name

            # Browse button
            op = row.operator("wm.directory_browse",
                text="Browse",
                icon='FILE_FOLDER')
            op.directory = preferences.hdri_directory
            op.property_name = "hdri_directory"
            op.property_owner = "preferences"

            # Add footer
            main_column.separator(factor=1.0 * preferences.spacing_scale)
            footer = main_column.row(align=True)
            footer.scale_y = 0.8
            footer.operator(
                "preferences.addon_show",
                text="",
                icon='PREFERENCES',
                emboss=False
            ).module = addon_name

            # Version display in the footer
            version_row = footer.row(align=True)
            if preferences.update_available:
                version_row.alert = True
                version_row.operator(
                    "world.download_hdri_update",
                    text=f"{utils.get_version_string()} - Update Available",
                    emboss=False
                )
            else:
                version_row.label(text=utils.get_version_string())
            return

        # Check if a render engine has been explicitly saved to preferences.json
        # OR if the current render engine is already compatible
        current_engine = context.scene.render.engine
        preferences_saved = False
        preference_engine = None

        # Initialize tracking variables if they don't exist
        if not hasattr(draw_hdri_controls, "_last_preference_check"):
            draw_hdri_controls._last_preference_check = (None, None)
        if not hasattr(draw_hdri_controls, "_last_compatible"):
            draw_hdri_controls._last_compatible = None
        if not hasattr(draw_hdri_controls, "_last_saved"):
            draw_hdri_controls._last_saved = None

        try:
            # Direct check of preferences.json file
            import json
            import os
            preferences_path = os.path.join(
                bpy.utils.user_resource('SCRIPTS'),
                "addons",
                addon_name,
                "preferences.json"
            )

            if os.path.exists(preferences_path):
                with open(preferences_path, 'r') as f:
                    prefs_data = json.load(f)
                    # Check if render_engine is explicitly set in the file
                    if 'render_engine' in prefs_data:
                        preferences_saved = True
                        preference_engine = prefs_data['render_engine']

                        # Only print if something changed
                        if draw_hdri_controls._last_preference_check != (current_engine, preference_engine):
                            # Also check if current engine matches preference
                            if preference_engine == current_engine:
                                print(f"Current engine '{current_engine}' matches preference")
                            else:
                                print(f"Current engine '{current_engine}' differs from preference '{preference_engine}'")
                            draw_hdri_controls._last_preference_check = (current_engine, preference_engine)
        except Exception as e:
            # If any error occurs, log it
            print(f"Error checking preferences: {str(e)}")
            # Assume preferences are not saved
            preferences_saved = False

        # Check if the current engine is already compatible with the addon
        # (even if not explicitly saved in preferences)
        is_compatible = current_engine in ['CYCLES', 'VRAY_RENDER_RT', 'octane']

        # Only print if compatibility state changed
        if draw_hdri_controls._last_compatible != is_compatible:
            if is_compatible:
                print(f"Current engine '{current_engine}' is compatible with addon")
            else:
                print(f"Current engine '{current_engine}' is not compatible with addon")
            draw_hdri_controls._last_compatible = is_compatible

        if is_compatible:
            # Check if we should save this to preferences for future use
            if not preferences_saved and draw_hdri_controls._last_saved != current_engine:
                try:
                    # Save current engine to preferences
                    print(f"Saving current engine '{current_engine}' to preferences")
                    draw_hdri_controls._last_saved = current_engine
                    import json
                    import os
                    preferences_path = os.path.join(
                        bpy.utils.user_resource('SCRIPTS'),
                        "addons",
                        addon_name,
                        "preferences.json"
                    )
                    prefs_data = {}
                    if os.path.exists(preferences_path):
                        try:
                            with open(preferences_path, 'r') as f:
                                prefs_data = json.load(f)
                        except:
                            pass

                    # Update the render engine preference
                    prefs_data['render_engine'] = current_engine

                    # Save to preferences.json
                    with open(preferences_path, 'w') as f:
                        json.dump(prefs_data, f, indent=4)

                    # We've now saved the preference
                    preferences_saved = True
                except Exception as e:
                    print(f"Error saving current engine to preferences: {str(e)}")

        # Only show warning prompt if no preferences saved AND current engine isn't compatible
        if not (preferences_saved or current_engine in ['CYCLES', 'VRAY_RENDER_RT', 'octane']):
            box = main_column.box()
            box.alert = True
            col = box.column(align=True)
            col.scale_y = 1.2 * preferences.button_scale
            col.label(text="Apply a Render Engine", icon='ERROR')

            # Footer
            main_column.separator(factor=1.0 * preferences.spacing_scale)
            footer = main_column.row(align=True)
            footer.scale_y = 0.8
            footer.operator(
                "preferences.addon_show",
                text="",
                icon='PREFERENCES',
                emboss=False
            ).module = addon_name

            # Version display in the footer
            version_row = footer.row(align=True)
            if preferences.update_available:
                version_row.alert = True
                version_row.operator(
                    "world.download_hdri_update",
                    text=f"{utils.get_version_string()} - Update Available",
                    emboss=False
                )
            else:
                version_row.label(text=utils.get_version_string())
            return

        # Check if HDRI system is already initialized for the current engine
        is_initialized = False

        if current_engine == 'CYCLES':
            world = context.scene.world
            if world and world_has_nodes(world):
                # Look for environment texture node
                for node in world.node_tree.nodes:
                    if node.type == 'TEX_ENVIRONMENT':
                        is_initialized = True
                        break

        elif current_engine == 'VRAY_RENDER_RT':
            # Check for V-Ray dome light
            vray_collection = bpy.data.collections.get("vRay HDRI Controls")
            if vray_collection:
                for obj in vray_collection.objects:
                    if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                        is_initialized = True
                        break

        elif current_engine == 'octane':
            # Octane-specific check
            world = context.scene.world
            if world and world_has_nodes(world):
                # Look for the required Octane nodes
                rgb_node = None
                transform_node = None
                tex_env_node = None

                for node in world.node_tree.nodes:
                    if node.bl_idname == 'OctaneRGBImage':
                        rgb_node = node
                    elif node.bl_idname == 'Octane3DTransformation':
                        transform_node = node
                    elif node.bl_idname == 'OctaneTextureEnvironment':
                        tex_env_node = node

                if rgb_node and transform_node and tex_env_node:
                    is_initialized = True
                    print(f"Octane HDRI system is initialized: RGB={rgb_node}, Transform={transform_node}, TexEnv={tex_env_node}")
                else:
                    print("Octane HDRI system is not fully initialized")

        # If not initialized, show the initialize button
        if not is_initialized:
            box = main_column.box()
            box.alert = True
            col = box.column(align=True)
            col.scale_y = 1.2 * preferences.button_scale
            col.label(text="HDRI System Not Initialized", icon='WORLD_DATA')
            col.operator("world.setup_hdri_nodes",
                text="Initialize HDRI System",
                icon='WORLD_DATA')

            # Add footer
            main_column.separator(factor=1.0 * preferences.spacing_scale)
            footer = main_column.row(align=True)
            footer.scale_y = 0.8
            footer.operator(
                "preferences.addon_show",
                text="",
                icon='PREFERENCES',
                emboss=False
            ).module = addon_name

            # Version display in the footer
            version_row = footer.row(align=True)
            if preferences.update_available:
                version_row.alert = True
                version_row.operator(
                    "world.download_hdri_update",
                    text=f"{utils.get_version_string()} - Update Available",
                    emboss=False
                )
            else:
                version_row.label(text=utils.get_version_string())
            return


        # Main UI
        # Folder Browser Section
        browser_box = main_column.box()
        browser_header = browser_box.row(align=True)
        browser_header.prop(hdri_settings, "show_browser",
                            icon='TRIA_DOWN' if hdri_settings.show_browser else 'TRIA_RIGHT',
                            icon_only=True)
        header_row = browser_header.row()
        sub = header_row.row(align=True)
        sub.alert = False
        sub.active = hdri_settings.show_browser
        sub.label(text="HDRI Browser", icon='FILE_FOLDER')

        #Favorites toggle
        favorites_row = browser_header.row(align=True)
        favorites_row.alignment = 'RIGHT'
        if hdri_settings.show_favorites_only:
            favorites_row.alert = True  # Make red when active
        favorites_row.prop(hdri_settings, "show_favorites_only",
                        text="",
                        icon='HEART',
                        emboss=False)

        # Add search button directly in the header
        search_btn = browser_header.row(align=True)
        search_btn.alignment = 'RIGHT'
        search_btn.operator("world.toggle_hdri_search_bar",
                        text="",
                        icon='VIEWZOOM',
                        emboss=False)

        if hdri_settings.show_browser:
            # Always show search bar if enabled, regardless of favorites mode
            if hdri_settings.show_search_bar:
                search_box = browser_box.box()
                search_row = search_box.row(align=True)

                # Search field
                search_field = search_row.row(align=True)
                search_field.scale_x = 0.8
                search_field.enabled = not hdri_settings.search_locked
                search_field.prop(hdri_settings, "search_query", text="", icon='VIEWZOOM')

                # Clear button - only show if search has text
                if hdri_settings.search_query:
                    clear_btn = search_row.operator("world.clear_hdri_search", text="", icon='X')

            # Only show folders if there's no active search AND favorites only is not enabled
            if not hdri_settings.search_query and not hdri_settings.show_favorites_only:
                # Get current path information
                current_folder = context.scene.hdri_settings.current_folder
                base_dir = preferences.hdri_directory

                if current_folder and os.path.exists(current_folder):
                    # Show improved breadcrumb navigation
                    try:
                        # Normalize paths for comparison
                        current_norm = os.path.normpath(current_folder)
                        base_norm = os.path.normpath(base_dir)

                        # Only show navigation if we're not in the root directory
                        if current_norm != base_norm:
                            bread_box = browser_box.box()
                            bread_row = bread_box.row(align=True)
                            bread_row.scale_y = 0.9

                            # Home button (always first)
                            home_btn = bread_row.operator("world.change_hdri_folder", text="", icon='HOME')
                            home_btn.folder_path = base_dir

                            # Show current folder name
                            current_folder_name = os.path.basename(current_folder)
                            if not current_folder_name:  # In case of root directories
                                current_folder_name = "Root"

                            # Add separator
                            bread_row.label(text="›")

                            # Show just the immediate parent if it's not the base directory
                            parent_dir = os.path.dirname(current_folder)
                            parent_norm = os.path.normpath(parent_dir)

                            if parent_norm != base_norm and parent_norm != current_norm:
                                # Show parent folder button
                                parent_name = os.path.basename(parent_dir)
                                if not parent_name:
                                    parent_name = "Parent"

                                parent_btn = bread_row.operator("world.change_hdri_folder", text=parent_name)
                                parent_btn.folder_path = parent_dir
                                bread_row.label(text="›")

                            # Current folder (not clickable)
                            bread_row.label(text=current_folder_name)

                    except Exception as e:
                        print(f"Error creating breadcrumb navigation: {str(e)}")

                    # Display folders only if they exist
                    folders = hdri_management.get_folders(context)
                    if folders:
                        # Check if pagination is enabled in preferences
                        if preferences.show_folder_pagination and len(folders) > preferences.folders_per_page:
                            # Calculate pagination
                            total_folders = len(folders)
                            items_per_page = preferences.folders_per_page
                            total_pages = max(1, (total_folders + items_per_page - 1) // items_per_page)

                            # Use current page (read-only)
                            current_page = hdri_settings.folder_page

                            # Ensure we're using a valid page number for display purposes only
                            # Note: We don't modify the property here, just calculate valid indices
                            current_page = max(0, min(current_page, total_pages - 1))

                            # Calculate slice for current page
                            start_idx = current_page * items_per_page
                            end_idx = min(start_idx + items_per_page, total_folders)
                            current_folders = folders[start_idx:end_idx]

                            # Show pagination controls
                            nav_row = browser_box.row(align=True)

                            # First page
                            first_op = nav_row.operator("world.change_folder_page", text="", icon='REW')
                            first_op.page = 0
                            first_op.go_to_page = True

                            # Previous page - disable if on first page
                            prev_row = nav_row.row(align=True)
                            prev_row.enabled = (current_page > 0)
                            prev_op = prev_row.operator("world.change_folder_page", text="", icon='TRIA_LEFT')
                            prev_op.page = -1
                            prev_op.go_to_page = False

                            # Page indicator
                            nav_row.label(text=f"Page {current_page + 1}/{total_pages}")

                            # Next page - disable if on last page
                            next_row = nav_row.row(align=True)
                            next_row.enabled = (current_page < total_pages - 1)
                            next_op = next_row.operator("world.change_folder_page", text="", icon='TRIA_RIGHT')
                            next_op.page = 1
                            next_op.go_to_page = False

                            # Last page
                            last_op = nav_row.operator("world.change_folder_page", text="", icon='FF')
                            last_op.page = total_pages - 1
                            last_op.go_to_page = True
                        else:
                            # If pagination is disabled or not needed, show all folders
                            current_folders = folders

                        # Create grid flow for folders
                        num_columns = min(2, len(current_folders))  # Use fewer columns if needed
                        if num_columns > 0:  # Only create grid if we have folders
                            grid = browser_box.grid_flow(
                                row_major=True,
                                columns=num_columns,
                                even_columns=True,
                                even_rows=False,
                                align=True
                            )

                            # Add folders to grid
                            for folder_path, name, tooltip, icon, _ in current_folders:
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
        if hdri_management.has_hdri_files(context) or hdri_settings.search_query or hdri_settings.show_favorites_only:
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

            # Always show preview content if there's a search query or favorites filter active
            if hdri_settings.show_preview or hdri_settings.search_query or hdri_settings.show_favorites_only:
                preview_box.scale_y = preferences.button_scale

                # Special case: Check if we're in favorites mode but have no favorites
                if hdri_settings.show_favorites_only:
                    from . import favorites
                    favorites_list = favorites.load_favorites()

                    if not favorites_list:
                        # Display message that no favorites exist - NO PREVIEW GRID
                        no_favs_box = preview_box.box()
                        row = no_favs_box.row()
                        row.alignment = 'CENTER'
                        row.label(text="No favorites added yet", icon='INFO')

                        hint_row = no_favs_box.row()
                        hint_row.alignment = 'CENTER'
                        hint_row.scale_y = 0.8
                        hint_row.label(text="Use the heart icon to add favorites")

                        btn_row = no_favs_box.row()
                        btn_row.alignment = 'CENTER'
                        btn_row.scale_y = 1.2
                        op = btn_row.operator("world.toggle_hdri_favorite_mode", text="Show All HDRIs", icon='RESTRICT_VIEW_OFF')

                    else:
                        preview_box.template_icon_view(
                            hdri_settings, "hdri_preview",
                            show_labels=True,
                            scale=preferences.preview_scale
                        )
                else:
                    # Normal mode - always show preview grid
                    preview_box.template_icon_view(
                        hdri_settings, "hdri_preview",
                        show_labels=True,
                        scale=preferences.preview_scale
                    )

                # Only show navigation controls if we have favorites or not in favorites mode
                if not hdri_settings.show_favorites_only or (hdri_settings.show_favorites_only and favorites_list):
                    # Navigation controls based on the render engine
                    nav_box = preview_box.box()
                    nav_row = nav_box.row(align=True)

                    # Reset to previous HDRI (only show if available)
                    if hdri_settings.previous_hdri_path and os.path.exists(hdri_settings.previous_hdri_path):
                        reset_sub = nav_row.row(align=True)
                        reset_sub.scale_x = 0.9
                        reset_sub.operator(
                            "world.reset_hdri",
                            text="",
                            icon='LOOP_BACK'
                        )
                    nav_row.separator(factor=1.0)

                    # Previous button
                    prev_sub = nav_row.row(align=True)
                    prev_sub.scale_x = 1.2
                    prev_sub.operator(
                        "world.previous_hdri",
                        text="",
                        icon='TRIA_LEFT',
                        emboss=True
                    )

                    # HDRI name - different handling for V-Ray vs Cycles
                    name_row = nav_row.row(align=True)
                    name_row.alignment = 'CENTER'
                    name_row.scale_x = 2.2

                    if context.scene.render.engine == 'VRAY_RENDER_RT':
                        # V-Ray implementation - UPDATED FOR NEW API
                        hdri_name = get_vray_current_hdri_name(context)
                        name_row.label(text=hdri_name)
                    elif context.scene.render.engine == 'octane':
                        # Octane implementation (unchanged)
                        world = context.scene.world
                        if world and world_has_nodes(world):
                            rgb_node = None
                            for node in world.node_tree.nodes:
                                if node.bl_idname == 'OctaneRGBImage':
                                    rgb_node = node
                                    break

                            if rgb_node and rgb_node.image:
                                # Display the filename from the image path
                                name_row.label(text=os.path.basename(rgb_node.image.filepath))
                            elif rgb_node and hasattr(rgb_node, 'a_filename') and rgb_node.a_filename:
                                # Fallback to a_filename if image isn't set
                                name_row.label(text=os.path.basename(rgb_node.a_filename))
                            else:
                                name_row.label(text="No HDRI")
                        else:
                            name_row.label(text="No HDRI")
                    else:
                        # Cycles and other engines (unchanged)
                        world = context.scene.world
                        if world and world_has_nodes(world):
                            env_tex = None
                            for node in world.node_tree.nodes:
                                if node.type == 'TEX_ENVIRONMENT':
                                    env_tex = node
                                    break

                            if env_tex and env_tex.image:
                                name_row.label(text=os.path.basename(env_tex.image.filepath))
                            else:
                                name_row.label(text="No HDRI")
                        else:
                            name_row.label(text="No HDRI")

                    # Next button
                    next_sub = nav_row.row(align=True)
                    next_sub.scale_x = 1.2
                    next_sub.operator(
                        "world.next_hdri",
                        text="",
                        icon='TRIA_RIGHT',
                        emboss=True
                    )

                    # Add a small space after Next button
                    nav_row.separator(factor=0.5)

                    # Favorites toggle for current HDRI (positioned after Next button)
                    if hdri_settings.hdri_preview:  # Only show if an HDRI is selected
                        from . import favorites
                        is_fav = favorites.is_favorite(hdri_settings.hdri_preview)

                        # Create separate row for the favorite button to control color
                        fav_row = nav_row.row(align=True)
                        if is_fav:
                            fav_row.alert = True  # Make red when it's a favorite

                        fav_btn = fav_row.operator(
                            "world.toggle_hdri_favorite",
                            text="",
                            icon="HEART",
                            emboss=True
                        )
                        fav_btn.hdri_path = hdri_settings.hdri_preview

        # Proxy dropdown
        proxy_row = main_column.row(align=True)
        proxy_row.label(text="Proxies", icon='RENDER_RESULT')
        proxy_row.scale_y = 1.0
        proxy_row.prop(hdri_settings, "show_proxy_settings",
            icon='TRIA_DOWN' if hdri_settings.show_proxy_settings else 'TRIA_RIGHT',
            icon_only=True,
            emboss=False)
        if hdri_settings.show_proxy_settings:
            proxy_box = main_column.box()
            proxy_col = proxy_box.column(align=True)
            proxy_col.scale_y = 0.9
            settings = context.scene.hdri_settings

            split = proxy_col.split(factor=0.5)

            mode_col = split.column()
            mode_col.prop(settings, "proxy_mode", text="Mode")

            res_col = split.column()
            res_col.prop(settings, "proxy_resolution", text="Resolution")

        main_column.separator(factor=0.5 * preferences.spacing_scale)

        # Color Management Section
        color_mgmt_row = main_column.row(align=True)
        color_mgmt_row.label(text="Color Management", icon='COLOR')
        color_mgmt_row.scale_y = 1.0
        color_mgmt_row.prop(hdri_settings, "show_color_management",
            icon='TRIA_DOWN' if hdri_settings.show_color_management else 'TRIA_RIGHT',
            icon_only=True,
            emboss=False)
        if hdri_settings.show_color_management:
            color_mgmt_box = main_column.box()
            color_mgmt_col = color_mgmt_box.column(align=True)
            color_mgmt_col.scale_y = 0.9

            split = color_mgmt_col.split(factor=0.5)

            transform_col = split.column()
            transform_col.prop(context.scene.view_settings, "view_transform", text="Transform")

            look_col = split.column()
            look_col.prop(context.scene.view_settings, "look", text="Look")

        # HDRI Settings Section - adjusted to work with all engines
        has_active = False

        # Check if there's an active HDRI based on current render engine
        if context.scene.render.engine == 'VRAY_RENDER_RT':
            # V-Ray code (unchanged)
            vray_collection = bpy.data.collections.get("vRay HDRI Controls")
            if vray_collection:
                for obj in vray_collection.objects:
                    if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                        node_tree = obj.data.node_tree
                        bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
                        if bitmap_node and hasattr(bitmap_node, 'BitmapBuffer') and bitmap_node.BitmapBuffer.file:
                            has_active = True
                            break
        elif context.scene.render.engine == 'octane':
            # Octane-specific code (new)
            world = context.scene.world
            if world and world_has_nodes(world):
                # Check for the required Octane nodes
                rgb_node = None
                transform_node = None

                for node in world.node_tree.nodes:
                    if node.bl_idname == 'OctaneRGBImage':
                        rgb_node = node
                    elif node.bl_idname == 'Octane3DTransformation':
                        transform_node = node

                # If both required nodes exist and image is loaded, consider it active
                if rgb_node and transform_node and (rgb_node.image or (hasattr(rgb_node, 'a_filename') and rgb_node.a_filename)):
                    has_active = True
        else:
            # For Cycles and other engines
            has_active = hdri_management.has_active_hdri(context)

        # If HDRI is active, display the rotation controls
        if has_active:
            # Settings box matching other main sections
            settings_box = main_column.box()
            header_row = settings_box.row(align=True)
            header_row.scale_y = preferences.button_scale

            # Toggle arrow - matches other section headers
            header_row.prop(hdri_settings, "show_rotation",
                    icon='TRIA_DOWN' if hdri_settings.show_rotation else 'TRIA_RIGHT',
                    icon_only=True)

            # Header text
            header_text = header_row.row()
            header_text.alert = False
            header_text.active = hdri_settings.show_rotation
            header_text.label(text="Settings", icon='DRIVER_ROTATIONAL_DIFFERENCE')

            # Optional buttons in header
            if hdri_settings.show_rotation:
                # Keep rotation toggle
                header_row.prop(preferences, "keep_rotation",
                    text="",
                    icon='LINKED' if preferences.keep_rotation else 'UNLINKED'
                )

                # Visibility toggle
                is_visible = True
                if context.scene.render.engine == 'VRAY_RENDER_RT':
                    from .render_engines import vray
                    is_visible = vray.get_hdri_visible(context)

                    header_row.operator("world.toggle_hdri_visibility",
                        text="",
                        icon='HIDE_OFF' if is_visible else 'HIDE_ON',
                        depress=is_visible)
                elif context.scene.render.engine == 'octane':
                    from .render_engines import octane
                    is_visible = octane.get_hdri_visible(context)

                    header_row.operator("world.toggle_hdri_visibility",
                        text="",
                        icon='HIDE_ON' if is_visible else 'HIDE_OFF',
                        depress=is_visible)
                else:
                    if context.scene.world:
                        is_visible = context.scene.world.cycles_visibility.camera

                    header_row.operator("world.toggle_hdri_visibility",
                        text="",
                        icon='HIDE_OFF' if is_visible else 'HIDE_ON',
                        depress=is_visible)

            # Content when expanded
            if hdri_settings.show_rotation:
                # Content column
                col = settings_box.column(align=True)
                col.scale_y = preferences.button_scale
                col.use_property_split = True

                # Rotation controls based on render engine
                if context.scene.render.engine == 'VRAY_RENDER_RT':
                    # V-Ray implementation
                    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
                    dome_light = None

                    if vray_collection:
                        for obj in vray_collection.objects:
                            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                                dome_light = obj
                                break

                    if dome_light:
                        # X Rotation
                        row = col.row(align=True)
                        row.prop(dome_light, "rotation_euler", index=0, text="X°")
                        sub = row.row(align=True)
                        sub.scale_x = 1.0

                        # Buttons
                        inc_x = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                        inc_x.axis = 0
                        inc_x.direction = 1

                        dec_x = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                        dec_x.axis = 0
                        dec_x.direction = -1

                        reset_x = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                        reset_x.axis = 0
                        reset_x.direction = -99

                        # Y Rotation
                        row = col.row(align=True)
                        row.prop(dome_light, "rotation_euler", index=1, text="Y°")
                        sub = row.row(align=True)
                        sub.scale_x = 1.0

                        # Buttons
                        inc_y = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                        inc_y.axis = 1
                        inc_y.direction = 1

                        dec_y = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                        dec_y.axis = 1
                        dec_y.direction = -1

                        reset_y = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                        reset_y.axis = 1
                        reset_y.direction = -99

                        # Z Rotation
                        row = col.row(align=True)
                        row.prop(dome_light, "rotation_euler", index=2, text="Z°")
                        sub = row.row(align=True)
                        sub.scale_x = 1.0

                        # Buttons
                        inc_z = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                        inc_z.axis = 2
                        inc_z.direction = 1

                        dec_z = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                        dec_z.axis = 2
                        dec_z.direction = -1

                        reset_z = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                        reset_z.axis = 2
                        reset_z.direction = -99

                elif context.scene.render.engine == 'octane':
                    # Octane implementation
                    world = context.scene.world
                    if world and world_has_nodes(world):
                        transform_node = None
                        for node in world.node_tree.nodes:
                            if node.bl_idname == 'Octane3DTransformation':
                                transform_node = node
                                break

                        if transform_node:
                            # X Rotation
                            row = col.row(align=True)
                            row.prop(transform_node.inputs['Rotation'], "default_value", index=0, text="X°")
                            sub = row.row(align=True)
                            sub.scale_x = 1.0

                            # Buttons
                            inc_x = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                            inc_x.axis = 0
                            inc_x.direction = 1

                            dec_x = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                            dec_x.axis = 0
                            dec_x.direction = -1

                            reset_x = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                            reset_x.axis = 0
                            reset_x.direction = -99

                            # Y Rotation (index 2 in Octane)
                            row = col.row(align=True)
                            row.prop(transform_node.inputs['Rotation'], "default_value", index=2, text="Y°")
                            sub = row.row(align=True)
                            sub.scale_x = 1.0

                            # Buttons
                            inc_y = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                            inc_y.axis = 2
                            inc_y.direction = 1

                            dec_y = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                            inc_y.axis = 2
                            dec_y.direction = -1

                            reset_y = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                            reset_y.axis = 2
                            reset_y.direction = -99

                            # Z Rotation (index 1 in Octane)
                            row = col.row(align=True)
                            row.prop(transform_node.inputs['Rotation'], "default_value", index=1, text="Z°")
                            sub = row.row(align=True)
                            sub.scale_x = 1.0

                            # Buttons
                            inc_z = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                            inc_z.axis = 1
                            inc_z.direction = 1

                            dec_z = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                            dec_z.axis = 1
                            dec_z.direction = -1

                            reset_z = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                            reset_z.axis = 1
                            reset_z.direction = -99

                else:
                    # Cycles implementation
                    world = context.scene.world
                    if world and world_has_nodes(world):
                        mapping = None
                        for node in world.node_tree.nodes:
                            if node.type == 'MAPPING':
                                mapping = node
                                break

                        if mapping:
                            # X Rotation
                            row = col.row(align=True)
                            row.prop(mapping.inputs['Rotation'], "default_value", index=0, text="X°")
                            sub = row.row(align=True)
                            sub.scale_x = 1.0

                            # Buttons
                            inc_x = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                            inc_x.axis = 0
                            inc_x.direction = 1

                            dec_x = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                            dec_x.axis = 0
                            dec_x.direction = -1

                            reset_x = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                            reset_x.axis = 0
                            reset_x.direction = -99

                            # Y Rotation
                            row = col.row(align=True)
                            row.prop(mapping.inputs['Rotation'], "default_value", index=1, text="Y°")
                            sub = row.row(align=True)
                            sub.scale_x = 1.0

                            # Buttons
                            inc_y = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                            inc_y.axis = 1
                            inc_y.direction = 1

                            dec_y = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                            dec_y.axis = 1
                            dec_y.direction = -1

                            reset_y = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                            reset_y.axis = 1
                            reset_y.direction = -99

                            # Z Rotation
                            row = col.row(align=True)
                            row.prop(mapping.inputs['Rotation'], "default_value", index=2, text="Z°")
                            sub = row.row(align=True)
                            sub.scale_x = 1.0

                            # Buttons
                            inc_z = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                            inc_z.axis = 2
                            inc_z.direction = 1

                            dec_z = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                            dec_z.axis = 2
                            dec_z.direction = -1

                            reset_z = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                            reset_z.axis = 2
                            reset_z.direction = -99

                # Strength slider (after rotation controls)
                if preferences.show_strength_slider:
                    col.separator()
                    strength_row = col.row(align=True)
                    strength_row.prop(hdri_settings, "background_strength", text="Strength")

                    # Reset button
                    reset_btn = strength_row.operator("world.reset_hdri_strength", text="", icon='LOOP_BACK')

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

        # Version display in the footer
        version_row = footer.row(align=True)
        if preferences.update_available:
            version_row.alert = True
            version_row.operator(
                "world.download_hdri_update",
                text=f"{utils.get_version_string()} - Update Available",
                emboss=False
            )
        else:
            version_row.label(text=utils.get_version_string())

        delete_btn = footer.operator(
            "world.delete_hdri_world",
            text="",
            icon='TRASH',
            emboss=False
        )
        settings_btn.module = addon_name
    except Exception as e:
        # Handle any exceptions in the draw method
        layout = self.layout
        layout.label(text=f"Error drawing HDRI Controls: {str(e)}", icon='ERROR')
        # Print more detailed error info to console
        import traceback
        traceback.print_exc()

def draw_hdri_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.popover(panel="HDRI_PT_controls_header", text="HDRI Controls")

def get_panel_class_for_location(location):
    """Get the appropriate panel class for the given location"""
    panel_classes = {
        'VIEW3D_HEADER': HDRI_PT_controls_header,
        'VIEW3D_UI': HDRI_PT_controls_sidebar,
        'PROPERTIES_WORLD': HDRI_PT_controls_world,
        'PROPERTIES_MATERIAL': HDRI_PT_controls_material,
        'PROPERTIES_RENDER': HDRI_PT_controls_render,
        'NODE_EDITOR': HDRI_PT_controls_shader_editor,
        'IMAGE_EDITOR': HDRI_PT_controls_image_editor,
    }
    return panel_classes.get(location, HDRI_PT_controls_header)

def get_menu_function_for_location(location):
    """Get the appropriate menu function for the given location"""
    if location == 'VIEW3D_HEADER':
        return draw_hdri_menu
    return None

def register_ui():
    """Register UI components for Quick HDRI Controls"""
    print("Registering Quick HDRI Controls UI")

    # Create the temp_engine property for render engine selection
    bpy.types.Scene.temp_engine = bpy.props.EnumProperty(
        name="Render Engine",
        description="Select the render engine for HDRI controls",
        items=[
            ('CYCLES', "Cycles", "Use Cycles render engine"),
            ('VRAY_RENDER_RT', "V-Ray", "Use V-Ray render engine"),
            ('octane', "Octane", "Use Octane render engine")
        ],
        default='CYCLES'
    )

    # Get the user's preferred panel location
    addon_name = utils.get_addon_name()
    try:
        preferences = bpy.context.preferences.addons[addon_name].preferences
        panel_location = preferences.panel_location
    except:
        panel_location = 'VIEW3D_HEADER'  # Default fallback

    # Register the appropriate panel class
    panel_class = get_panel_class_for_location(panel_location)
    bpy.utils.register_class(panel_class)

    # Store reference to the registered panel
    global _current_panel_class
    _current_panel_class = panel_class

    # Add menu function if needed (only for header location)
    menu_function = get_menu_function_for_location(panel_location)
    if menu_function:
        bpy.types.VIEW3D_HT_header.append(menu_function)
        global _current_menu_function
        _current_menu_function = menu_function

    print(f"HDRI Controls UI registered successfully at location: {panel_location}")

def unregister_ui():
    """Unregister UI components for Quick HDRI Controls"""
    print("Unregistering Quick HDRI Controls UI")

    global _current_panel_class, _current_menu_function

    # Remove menu function if it was added
    if _current_menu_function:
        try:
            bpy.types.VIEW3D_HT_header.remove(_current_menu_function)
        except:
            pass
        _current_menu_function = None

    # Unregister the current panel class
    if _current_panel_class:
        try:
            bpy.utils.unregister_class(_current_panel_class)
        except:
            pass
        _current_panel_class = None

    # Remove the temp_engine property
    if hasattr(bpy.types.Scene, "temp_engine"):
        del bpy.types.Scene.temp_engine

    print("HDRI Controls UI unregistered successfully")
