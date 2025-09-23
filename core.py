"""
Quick HDRI Controls - Core
"""
import os
import bpy
from bpy.types import PropertyGroup
from bpy.props import (FloatProperty, StringProperty, EnumProperty,
                      CollectionProperty, PointerProperty, IntProperty,
                      BoolProperty, FloatVectorProperty)
import numpy as np

original_paths = {}

from . import hdri_management
from .utils import world_has_nodes, enable_world_nodes

class HDRISettings(PropertyGroup):

    def update_hdri_preview(self, context):
        """Automatically load HDRI when selected from preview - FIXED VISIBILITY RETENTION"""
        filepath = self.hdri_preview

        if not filepath or not isinstance(filepath, str) or filepath in ('0', '', 'NONE'):
            print(f"Warning: Invalid HDRI preview value: {filepath}")
            return

        if not os.path.exists(filepath):
            print(f"Warning: HDRI file not found: {filepath}")
            return

        render_engine = context.scene.render.engine

        if render_engine == 'VRAY_RENDER_RT':
            # V-Ray specific implementation - UPDATED FOR NEW API
            from .render_engines import vray
            vray.set_hdri(context, filepath)

        elif render_engine == 'octane':
            # Octane specific implementation
            world = context.scene.world
            if not world or not world.use_nodes:
                return
            rgb_node = None
            for node in world.node_tree.nodes:
                if node.bl_idname == 'OctaneRGBImage':
                    rgb_node = node
                    break

            if rgb_node:
                try:
                    current_visibility = True
                    if hasattr(self, 'hdri_visible'):
                        current_visibility = self.hdri_visible
                    else:
                        print("Warning: hdri_visible property not found, defaulting to True")

                    current_path = None
                    current_image = rgb_node.image

                    if current_image:
                        current_path = original_paths.get(current_image.name, rgb_node.a_filename)
                        self.previous_hdri_path = current_path

                    target_path = filepath
                    if self.proxy_resolution != 'ORIGINAL':
                        from .utils import create_hdri_proxy

                        proxy_dir = os.path.join(os.path.dirname(filepath), 'proxies')
                        base_name = os.path.splitext(os.path.basename(filepath))[0]
                        potential_proxy = os.path.join(proxy_dir, f"{base_name}_{self.proxy_resolution}.hdr")

                        if os.path.exists(potential_proxy):
                            target_path = potential_proxy
                        else:
                            proxy_path = create_hdri_proxy(filepath, self.proxy_resolution)
                            if proxy_path:
                                target_path = proxy_path

                    rgb_node.image = None

                    new_image = bpy.data.images.load(target_path, check_existing=True)

                    rgb_node.image = new_image
                    rgb_node.a_filename = target_path

                    if target_path != filepath:
                        original_paths[new_image.name] = filepath
                        original_paths[os.path.basename(target_path)] = filepath

                    if current_image and current_image.users == 0:
                        bpy.data.images.remove(current_image)

                    from .render_engines import octane
                    octane.set_hdri_visibility(context, current_visibility)

                    rgb_node.update()
                    world.node_tree.update_tag()

                    # Force UI update
                    for area in context.screen.areas:
                        area.tag_redraw()

                except Exception as e:
                    print(f"Failed to update HDRI: {str(e)}")
                    return

        else:
            # Default Cycles implementation - FIXED VISIBILITY RETENTION
            world = context.scene.world
            if not world or not world_has_nodes(world):
                return

            current_visibility = True  # Default to visible
            if hasattr(world, 'cycles_visibility') and hasattr(world.cycles_visibility, 'camera'):
                current_visibility = world.cycles_visibility.camera
            else:
                print("Warning: cycles_visibility.camera property not found, defaulting to True")

            for node in world.node_tree.nodes:
                if node.type == 'TEX_ENVIRONMENT' and node.image:
                    self.previous_hdri_path = node.image.filepath
                    self.previous_proxy_resolution = self.proxy_resolution
                elif node.type == 'MAPPING':
                    self.previous_rotation = node.inputs['Rotation'].default_value.copy()
                elif node.type == 'BACKGROUND':
                    self.previous_strength = node.inputs['Strength'].default_value

            addon_name = __package__.split('.')[0]
            preferences = context.preferences.addons[addon_name].preferences

            # Store current rotation if keep_rotation is enabled
            current_rotation = None
            if preferences.keep_rotation:
                for node in context.scene.world.node_tree.nodes:
                    if node.type == 'MAPPING':
                        current_rotation = node.inputs['Rotation'].default_value.copy()
                        break

            # Set up nodes
            from .render_engines import cycles
            mapping, env_tex, background = cycles.ensure_world_nodes()

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

            # Create a proxy if the user has a proxy resolution set
            if self.proxy_resolution != 'ORIGINAL':
                from .utils import create_hdri_proxy
                proxy_path = create_hdri_proxy(filepath, self.proxy_resolution)
                if proxy_path and proxy_path != env_tex.image.filepath:
                    # Clear existing image
                    current_image = env_tex.image
                    env_tex.image = None
                    if current_image.users == 0:
                        bpy.data.images.remove(current_image)
                    # Load proxy and store original path
                    img = bpy.data.images.load(proxy_path, check_existing=True)
                    original_paths[img.name] = filepath  # Store original path
                    env_tex.image = img

            # RESTORE visibility state after loading new HDRI - FIXED
            if hasattr(world, 'cycles_visibility') and hasattr(world.cycles_visibility, 'camera'):
                world.cycles_visibility.camera = current_visibility
                print(f"Cycles: Restored visibility to {current_visibility}")

    def update_background_strength(self, context):
        """Update handler for background strength changes"""
        print(f"Core update_background_strength called: strength={self.background_strength}")

        # Get the current render engine
        engine = context.scene.render.engine
        print(f"Current render engine: {engine}")

        # Call the engine-specific handler
        if engine == 'VRAY_RENDER_RT':
            print("Dispatching to V-Ray implementation")
            from .render_engines import vray
            vray.update_background_strength(self, context)
        elif engine == 'octane':
            print("Dispatching to Octane implementation")
            from .render_engines import octane
            octane.update_background_strength(self, context)
        else:
            print("Dispatching to Cycles implementation")
            if context.scene.world and world_has_nodes(context.scene.world):
                for node in context.scene.world.node_tree.nodes:
                    if node.type == 'BACKGROUND':
                        node.inputs['Strength'].default_value = self.background_strength
                        print(f"Set Cycles background strength to {self.background_strength}")
                        break

    def update_search_query(self, context):
        # Lock the search when text is entered
        if self.search_query.strip():
            self.search_locked = True
        # Don't unlock when clearing - that should only happen via the clear button

    def clear_hdri_search(self):
        """Clear the search query and reset preview cache"""
        from .utils import get_hdri_previews

        # Clear the search query
        self.search_query = ""

        # Clear preview cache
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
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    def update_hdri_proxy(self, context):
        """Update handler for proxy resolution and mode changes"""
        print(f"Core update_hdri_proxy called: proxy_resolution={self.proxy_resolution}, proxy_mode={self.proxy_mode}")

        # Determine the appropriate engine to handle the update based on current render engine
        render_engine = context.scene.render.engine

        if render_engine == 'VRAY_RENDER_RT':
            # Call V-Ray
            print("Dispatching to V-Ray implementation")
            from .render_engines import vray
            vray.update_hdri_proxy(self, context)
        elif render_engine == 'octane':
            # Call Octane
            print("Dispatching to Octane implementation")
            from .render_engines import octane
            octane.update_hdri_proxy(self, context)
        else:
            # Cycles
            print("Dispatching to Cycles implementation")
            from .utils import create_hdri_proxy

            if not context.scene.world or not world_has_nodes(context.scene.world):
                print("No world or no nodes, skipping proxy update")
                return

            # Find environment texture node
            env_tex = None
            for node in context.scene.world.node_tree.nodes:
                if node.type == 'TEX_ENVIRONMENT':
                    env_tex = node
                    break

            if not env_tex or not env_tex.image:
                print("No environment texture or image, skipping proxy update")
                return

            settings = context.scene.hdri_settings

            # Close proxy settings on any resolution or mode change
            context.scene.hdri_settings.show_proxy_settings = False

            # Get the original path - check in multiple places
            current_image = env_tex.image
            original_path = None

            # First check original_paths using image name
            if current_image.name in original_paths:
                original_path = original_paths[current_image.name]
                print(f"Found original path from image name: {original_path}")
            # Then check original_paths using basename of filepath
            elif os.path.basename(current_image.filepath) in original_paths:
                original_path = original_paths[os.path.basename(current_image.filepath)]
                print(f"Found original path from filepath basename: {original_path}")
            # Finally use current filepath
            else:
                original_path = current_image.filepath
                print(f"Using image filepath as original path: {original_path}")

            # Always clear current image to force reload
            env_tex.image = None
            if current_image.users == 0:
                bpy.data.images.remove(current_image)
                print("Removed old image")

            try:
                if settings.proxy_resolution == 'ORIGINAL':
                    # Load original file
                    print(f"Loading original file: {original_path}")
                    img = bpy.data.images.load(original_path, check_existing=True)
                    img.reload()  # Force reload of the image
                    env_tex.image = img
                    # Clean up original_paths entries
                    if img.name in original_paths:
                        del original_paths[img.name]
                    if os.path.basename(original_path) in original_paths:
                        del original_paths[os.path.basename(original_path)]
                else:
                    # Create and load proxy
                    print(f"Creating proxy at resolution {settings.proxy_resolution}")
                    proxy_path = create_hdri_proxy(original_path, settings.proxy_resolution)
                    if proxy_path:
                        print(f"Created proxy at {proxy_path}")
                        # Force reload even if image exists
                        if proxy_path in bpy.data.images:
                            bpy.data.images[proxy_path].reload()
                            img = bpy.data.images[proxy_path]
                        else:
                            img = bpy.data.images.load(proxy_path, check_existing=True)

                        original_paths[img.name] = original_path
                        original_paths[os.path.basename(proxy_path)] = original_path
                        env_tex.image = img
                    else:
                        # Fallback to original if proxy creation fails
                        print("Failed to create proxy, using original")
                        img = bpy.data.images.load(original_path, check_existing=True)
                        env_tex.image = img

            except Exception as e:
                print(f"Error updating HDRI proxy: {str(e)}")
                # Try to restore original if something fails
                try:
                    img = bpy.data.images.load(original_path, check_existing=True)
                    env_tex.image = img
                except Exception as e2:
                    print(f"Failed to restore original image: {str(e2)}")

            # Handle render update - only use handlers for 'VIEWPORT' mode
            from .utils import update_proxy_handlers
            update_proxy_handlers(settings.proxy_mode)
            print(f"Updated proxy handlers for mode: {settings.proxy_mode}")

            # Force redraw of viewport
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()


    # Common properties for all render engines
    hdri_preview: EnumProperty(
        name="HDRI Preview",
        description="Preview of available HDRIs",
        items=hdri_management.generate_previews,
        update=update_hdri_preview
    )

    hdri_visible: BoolProperty(
        name="HDRI Visible",
        description="Whether the HDRI background is visible in the viewport and render",
        default=True
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

    proxy_resolution: EnumProperty(
        name="Proxy Resolution",
        description="Resolution to use for HDRI",
        items=[
            ('ORIGINAL', 'Original', 'Use original resolution'),
            ('1K', '1K', 'Use 1K resolution'),
            ('2K', '2K', 'Use 2K resolution'),
            ('4K', '4K', 'Use 4K resolution'),
        ],
        default='ORIGINAL',
        update=update_hdri_proxy
    )

    proxy_mode: EnumProperty(
        name="Proxy Mode",
        description="Where to apply proxy resolution",
        items=[
            ('VIEWPORT', 'Viewport Only', 'Apply proxy resolution only in viewport'),
            ('BOTH', 'Both', 'Apply proxy resolution to both viewport and render'),
        ],
        default='VIEWPORT',
        update=update_hdri_proxy
    )

    show_proxy_settings: BoolProperty(
        name="Show Proxy Settings",
        description="Close this tab after selection for faster performance"
    )

    previous_proxy_resolution: EnumProperty(
        name="Previous Proxy Resolution",
        description="Previously used proxy resolution",
        items=[
            ('ORIGINAL', 'Original', 'Use original resolution'),
            ('1K', '1K', 'Use 1K resolution'),
            ('2K', '2K', 'Use 2K resolution'),
            ('4K', '4K', 'Use 4K resolution'),
        ],
        default='ORIGINAL'
    )

    show_color_management: BoolProperty(
        name="Show Color Management",
        description="Show/Hide Color Management controls",
        default=False
    )

    search_query: StringProperty(
        name="Search HDRIs",
        description="Search HDRIs by filename",
        default="",
        update=update_search_query
    )

    search_locked: BoolProperty(
        name="Search Locked",
        description="Whether the search box is locked",
        default=False
    )

    folder_page: IntProperty(
        name="Folder Page",
        description="Current page of folders",
        default=0,
        min=0
    )

    show_search_bar: BoolProperty(
        name="Show Search Bar",
        description="Show or hide the HDRI search bar",
        default=False
    )

    show_favorites_only: BoolProperty(
        name="Show Favorites Only",
        description="Show only favorite HDRIs",
        default=False
    )

    # ADDED: Flag to track if initialization has been done
    proxy_initialized: BoolProperty(
        name="Proxy Initialized",
        description="Internal flag to track if proxy settings have been initialized",
        default=False,
        options={'HIDDEN'}
    )


def initialize_proxy_settings_from_preferences(scene):
    """Initialize proxy settings from preferences for a scene"""
    if not hasattr(scene, "hdri_settings"):
        return False

    hdri_settings = scene.hdri_settings

    # Check if already initialized
    if hdri_settings.proxy_initialized:
        return False

    try:
        addon_name = __package__.split('.')[0]
        preferences = bpy.context.preferences.addons[addon_name].preferences

        # Set the values directly
        hdri_settings.proxy_resolution = preferences.default_proxy_resolution
        hdri_settings.proxy_mode = preferences.default_proxy_mode

        # Mark as initialized
        hdri_settings.proxy_initialized = True

        print(f"Initialized proxy settings: resolution={preferences.default_proxy_resolution}, mode={preferences.default_proxy_mode}")
        return True

    except Exception as e:
        print(f"Error initializing proxy settings: {str(e)}")
        return False


def register_core():
    """Register core components for Quick HDRI Controls"""
    print("Registering HDRISettings class...")

    # Try to unregister first if it exists
    try:
        bpy.utils.unregister_class(HDRISettings)
        print("Unregistered existing HDRISettings class")
    except (ValueError, RuntimeError):
        # Class wasn't registered, which is fine
        pass

    # Register the class
    bpy.utils.register_class(HDRISettings)
    print("HDRISettings class registered")

    # Add property to scene
    bpy.types.Scene.hdri_settings = PointerProperty(type=HDRISettings)
    print("hdri_settings added to Scene type")

    # Add initialization handler
    @bpy.app.handlers.persistent
    def initialize_scene_proxy_settings(dummy):
        """Initialize proxy settings for new scenes"""
        try:
            for scene in bpy.data.scenes:
                initialize_proxy_settings_from_preferences(scene)
        except Exception as e:
            print(f"Error in scene proxy initialization handler: {str(e)}")

    # Register the handler
    if initialize_scene_proxy_settings not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(initialize_scene_proxy_settings)

    # Initialize current scene with a timer (context not available during registration)
    def delayed_initialization():
        try:
            if bpy.context.scene:
                initialize_proxy_settings_from_preferences(bpy.context.scene)
                # ADD THIS: Register handlers based on current proxy mode
                settings = bpy.context.scene.hdri_settings
                from .utils import update_proxy_handlers
                update_proxy_handlers(settings.proxy_mode)
                print(f"Registered handlers for proxy mode: {settings.proxy_mode}")
        except Exception as e:
            print(f"Error in delayed proxy initialization: {str(e)}")
        return None  # Don't repeat the timer

    bpy.app.timers.register(delayed_initialization, first_interval=0.1)

    print("Core registration complete")

def unregister_core():
    del bpy.types.Scene.hdri_settings
    bpy.utils.unregister_class(HDRISettings)
