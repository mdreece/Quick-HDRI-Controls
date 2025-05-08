"""
Quick HDRI Controls - UI components
"""
import os
import bpy
from bpy.types import Panel
from . import utils
from . import hdri_management
from .utils import get_icons

class HDRI_PT_controls(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "HDRI Controls"
    bl_ui_units_x = 10

    last_engine = None

    def draw(self, context):
        """Draw HDRI controls panel"""
        try:
            print(f"HDRI Controls UI draw: Engine={context.scene.render.engine}, temp_engine={context.scene.temp_engine}")
            
            # Get addon name and preferences
            addon_name = "Quick-HDRI-Controls-main"  # Use hardcoded path to match bl_idname
            preferences = context.preferences.addons[addon_name].preferences
            self.bl_ui_units_x = preferences.ui_scale
            
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            hdri_settings = context.scene.hdri_settings
            
            main_column = layout.column(align=True)
            
            # Get current engine
            current_engine = context.scene.render.engine
            
            # Only log debug info when changed
            if current_engine != HDRI_PT_controls.last_engine:
                # Update the last engine
                HDRI_PT_controls.last_engine = current_engine
            
            # Get icons without debug printing
            icons = get_icons()
            
            # Create engine selector dropdown with icons
            header_row = main_column.row(align=True)
            header_row.scale_y = 1.2 
            
            # Check if temp_engine property exists on scene, if not create it
            if not hasattr(context.scene, "temp_engine"):
                # First time, initialize from current engine
                context.scene.temp_engine = context.scene.render.engine
            
            # Create the engine selector
            engine_row = header_row.row(align=True)
            
            # Get icon ID based on current engine
            icon_id = 0  # Default fallback
            if current_engine == 'CYCLES':
                cycles_icon = icons.get("cycles_icon") 
                icon_id = cycles_icon.icon_id if cycles_icon else 0
            elif current_engine == 'VRAY_RENDER_RT':
                vray_icon = icons.get("vray_icon")
                icon_id = vray_icon.icon_id if vray_icon else 0
            elif current_engine == 'octane':
                octane_icon = icons.get("octane_icon")
                icon_id = octane_icon.icon_id if octane_icon else 0
            
            # Display icon and dropdown
            engine_row.label(text="", icon_value=icon_id)
            engine_row.prop(context.scene, "temp_engine", text="")
            
            # Apply button next to dropdown
            apply_btn = engine_row.row(align=True)
            
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
                        text="v2.8.2 - Update Available",
                        emboss=False
                    )
                else:
                    version_row.label(text="v2.8.2")
                return
                
            # Check if a render engine has been explicitly saved to preferences.json
            preferences_saved = False
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
            except Exception as e:
                # If any error occurs, assume no preferences are saved
                preferences_saved = False
            
            # Only continue if preferences are saved
            if not preferences_saved:
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
                        text="v2.8.2 - Update Available",
                        emboss=False
                    )
                else:
                    version_row.label(text="v2.8.2")
                return
                
            # Check if HDRI system is already initialized for the current engine
            is_initialized = False
            
            if current_engine == 'CYCLES':
                world = context.scene.world
                if world and world.use_nodes:
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
                if world and world.use_nodes:
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
                        text="v2.8.2 - Update Available",
                        emboss=False
                    )
                else:
                    version_row.label(text="v2.8.2")
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

            # Add search button directly in the header
            search_btn = browser_header.row(align=True)
            search_btn.alignment = 'RIGHT'
            search_btn.operator("world.toggle_hdri_search_bar",
                               text="",
                               icon='VIEWZOOM',
                               emboss=False)

            if hdri_settings.show_browser:
                # Show search bar in a separate row when expanded
                if hdri_settings.show_search_bar:
                    search_row = browser_box.row(align=True)
                    search_row.scale_y = 0.9  # Slightly smaller to look compact

                    # Search field
                    search_field = search_row.row(align=True)
                    search_field.enabled = not hdri_settings.search_locked
                    search_field.prop(hdri_settings, "search_query", text="", icon='VIEWZOOM')

                    # Clear button when there's search text
                    if hdri_settings.search_query.strip():
                        clear_btn = search_row.operator("world.clear_hdri_search", text="", icon='X')

                # Only show folders if there's no active search
                if not hdri_settings.search_query:
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
            if hdri_management.has_hdri_files(context) or hdri_settings.search_query:
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

                # Always show preview content if there's a search query
                if hdri_settings.show_preview or hdri_settings.search_query:
                    preview_box.scale_y = preferences.button_scale

                    # HDRI preview grid
                    preview_box.template_icon_view(
                        hdri_settings, "hdri_preview",
                        show_labels=True,
                        scale=preferences.preview_scale
                    )

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
                        # V-Ray implementation (unchanged)
                        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
                        if vray_collection:
                            for obj in vray_collection.objects:
                                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                                    node_tree = obj.data.node_tree
                                    bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
                                    if bitmap_node and hasattr(bitmap_node, 'BitmapBuffer') and bitmap_node.BitmapBuffer.file:
                                        name_row.label(text=os.path.basename(bitmap_node.BitmapBuffer.file))
                                        break
                            else:
                                name_row.label(text="No HDRI")
                        else:
                            name_row.label(text="No HDRI")
                    elif context.scene.render.engine == 'octane':
                        # Octane implementation (new code)
                        world = context.scene.world
                        if world and world.use_nodes:
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
                        if world and world.use_nodes:
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
                if world and world.use_nodes:
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
                # Rotation controls section
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
                    sub.prop(preferences, "keep_rotation",
                        text="",
                        icon='LINKED' if preferences.keep_rotation else 'UNLINKED'
                    )

                    # Add visibility toggle with different handling for V-Ray and Cycles
                    is_visible = True
                    if context.scene.render.engine == 'VRAY_RENDER_RT':
                        # For V-Ray - check visibility using get_hdri_visible function
                        from .render_engines import vray
                        is_visible = vray.get_hdri_visible(context)
                        
                        # Create the visibility toggle button
                        toggle_op = sub.operator("world.toggle_hdri_visibility",
                            text="",
                            icon='HIDE_OFF' if is_visible else 'HIDE_ON',
                            depress=is_visible)
                    elif context.scene.render.engine == 'octane':
                        # For Octane - check visibility using get_hdri_visible function
                        from .render_engines import octane
                        is_visible = octane.get_hdri_visible(context)
                        
                        # Create the visibility toggle button
                        toggle_op = sub.operator("world.toggle_hdri_visibility",
                            text="",
                            icon='HIDE_ON' if is_visible else 'HIDE_OFF',
                            depress=is_visible)
                    else:
                        # For Cycles - check cycles visibility
                        if context.scene.world:
                            is_visible = context.scene.world.cycles_visibility.camera
                            
                        sub.operator("world.toggle_hdri_visibility",
                            text="",
                            icon='HIDE_OFF' if is_visible else 'HIDE_ON',
                            depress=is_visible)
                    # Layout based on compact mode - adapted for both engines
                    if preferences.use_compact_ui:
                        # Compact layout
                        col = rotation_box.column(align=True)
                        col.scale_y = preferences.button_scale
                        col.use_property_split = True

                        if context.scene.render.engine == 'VRAY_RENDER_RT':
                            # For V-Ray - rotation is on the dome light object
                            vray_collection = bpy.data.collections.get("vRay HDRI Controls")
                            dome_light = None
                            for obj in vray_collection.objects:
                                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                                    dome_light = obj
                                    break
                                    
                            if dome_light:
                                # X Rotation controls
                                row = col.row(align=True)
                                row.prop(dome_light, "rotation_euler", index=0, text="X°")
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
                                row.prop(dome_light, "rotation_euler", index=1, text="Y°")
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
                                row.prop(dome_light, "rotation_euler", index=2, text="Z°")
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
                                
                        elif context.scene.render.engine == 'octane':
                            # Octane rotation code (new)
                            world = context.scene.world
                            if world and world.use_nodes:
                                transform_node = None
                                for node in world.node_tree.nodes:
                                    if node.bl_idname == 'Octane3DTransformation':
                                        transform_node = node
                                        break
                                        
                                if transform_node:
                                    # X Rotation controls
                                    row = col.row(align=True)
                                    row.prop(transform_node.inputs['Rotation'], "default_value", index=0, text="X°")
                                    sub = row.row(align=True)
                                    sub.scale_x = 1.0

                                    op = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                                    op.axis = 0
                                    op.direction = 1

                                    op = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                                    op.axis = 0
                                    op.direction = -1

                                    op = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                                    op.axis = 0
                                    op.direction = -99

                                    # Y Rotation controls
                                    row = col.row(align=True)
                                    row.prop(transform_node.inputs['Rotation'], "default_value", index=2, text="Y°")
                                    sub = row.row(align=True)
                                    sub.scale_x = 1.0

                                    op = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                                    op.axis = 2
                                    op.direction = 1

                                    op = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                                    op.axis = 2
                                    op.direction = -1

                                    op = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                                    op.axis = 2
                                    op.direction = -99
                                    
                                    # Z Rotation controls
                                    row = col.row(align=True)
                                    row.prop(transform_node.inputs['Rotation'], "default_value", index=1, text="Z°")
                                    sub = row.row(align=True)
                                    sub.scale_x = 1.0

                                    op = sub.operator("world.quick_rotate_hdri", text="", icon='ADD')
                                    op.axis = 1
                                    op.direction = 1

                                    op = sub.operator("world.quick_rotate_hdri", text="", icon='REMOVE')
                                    op.axis = 1
                                    op.direction = -1

                                    op = sub.operator("world.quick_rotate_hdri", text="", icon='LOOP_BACK')
                                    op.axis = 1
                                    op.direction = -99
                        else:
                            # For Cycles - rotation is on the mapping node
                            world = context.scene.world
                            if world and world.use_nodes:
                                mapping = None
                                for node in world.node_tree.nodes:
                                    if node.type == 'MAPPING':
                                        mapping = node
                                        break
                                        
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

                        # strength slider
                        if preferences.show_strength_slider:
                            col.separator()
                            row = col.row(align=True)
                            sub_row = row.row(align=True)
                            sub_row.prop(hdri_settings, "background_strength", text="Strength")
                            # Reset button
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

            # Version number - Modified to show update alert
            version_row = footer.row(align=True)
            if preferences.update_available:
                version_row.alert = True
                version_row.operator(
                    "world.download_hdri_update",
                    text="v2.8.2 - Update Available",
                    emboss=False
                )
            else:
                version_row.label(text="v2.8.2")

            # Delete world button with different handling for V-Ray and Cycles
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
    layout.popover(panel="HDRI_PT_controls", text="HDRI Controls")


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
    
    # Register the main panel class
    bpy.utils.register_class(HDRI_PT_controls)
    
    # Add UI to the header menu
    bpy.types.VIEW3D_HT_header.append(draw_hdri_menu)
    
    print("HDRI Controls UI registered successfully")


def unregister_ui():
    """Unregister UI components for Quick HDRI Controls"""
    print("Unregistering Quick HDRI Controls UI")
    
    # Remove UI from header menu first
    bpy.types.VIEW3D_HT_header.remove(draw_hdri_menu)
    
    # Then unregister the panel class
    bpy.utils.unregister_class(HDRI_PT_controls)
    
    # Remove the temp_engine property
    if hasattr(bpy.types.Scene, "temp_engine"):
        del bpy.types.Scene.temp_engine
    
    print("HDRI Controls UI unregistered successfully")