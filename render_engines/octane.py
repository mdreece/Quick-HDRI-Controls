"""
Quick HDRI Controls - Octane-specific implementation
"""
import os
import bpy
import re
from bpy.utils import previews
from mathutils import Vector
from datetime import datetime
import tempfile
import shutil
from math import radians, degrees
import time

# Import from parent module
from ..utils import get_hdri_previews, create_hdri_proxy, get_proxy_directory
from ..core import original_paths

# Import common HDRI management functions
from .. import hdri_management

from ..utils import world_has_nodes, enable_world_nodes

# Re-export common functions with local references
# to maintain compatibility with existing code
generate_previews = hdri_management.generate_previews
has_hdri_files = hdri_management.has_hdri_files
has_active_hdri = hdri_management.has_active_hdri
get_folders = hdri_management.get_folders


def ensure_world_nodes():
    """Create and setup the required Octane nodes for HDRI control"""
    scene = bpy.context.scene

    # Create world if it doesn't exist
    if not scene.world:
        scene.world = bpy.data.worlds.new(name='octane_world')

    world = scene.world
    enable_world_nodes(world)

    # Set view transform to Raw
    if hasattr(scene.view_settings, "view_transform"):
        scene.view_settings.view_transform = 'Raw'

    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Clear existing nodes
    nodes.clear()

    # Create Octane nodes with specific positions
    # World Output
    node_world_output = nodes.new(type='OctaneEditorWorldOutputNode')
    node_world_output.location = (260.4977, 334.4536)

    # Texture Environment for Environment
    node_tex_env = nodes.new(type='OctaneTextureEnvironment')
    node_tex_env.location = (38.7377, 333.8394)

    # RGB Image node
    node_rgb_image = nodes.new(type='OctaneRGBImage')
    node_rgb_image.location = (-190.3312, 333.9641)

    # Spherical Projection
    node_spherical = nodes.new(type='OctaneSpherical')
    node_spherical.location = (-415.2154, 330.2407)

    # 3D Transformation
    node_transform = nodes.new(type='Octane3DTransformation')
    node_transform.location = (-641.9505, 327.6602)

    # Texture Environment for Visible Environment
    node_tex_env_visible = nodes.new(type='OctaneTextureEnvironment')
    node_tex_env_visible.location = (38.7377, 18.3493)

    # RGB Color node
    node_rgb_color = nodes.new(type='OctaneRGBColor')
    node_rgb_color.location = (-182.2112, 15.3167)
    node_rgb_color.a_value = (0, 0, 0)

    # Create links
    links.new(node_tex_env.outputs['Environment out'], node_world_output.inputs['Environment'])
    links.new(node_rgb_image.outputs['Texture out'], node_tex_env.inputs['Texture'])
    links.new(node_spherical.outputs['Projection out'], node_rgb_image.inputs['Projection'])
    links.new(node_transform.outputs['Transform out'], node_spherical.inputs['Sphere transformation'])
    links.new(node_tex_env_visible.outputs['Environment out'], node_world_output.inputs['Visible Environment'])
    links.new(node_rgb_color.outputs['Texture out'], node_tex_env_visible.inputs['Texture'])

    return node_transform, node_rgb_image, node_tex_env


def update_background_strength(self, context):
    """Update handler for background strength changes"""
    if context.scene.world and context.scene.world.use_nodes:
        world = context.scene.world
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # First find World Output node
        world_output = None
        for node in nodes:
            if node.bl_idname == 'OctaneEditorWorldOutputNode':
                world_output = node
                break

        # Find the primary Texture Environment node
        if world_output:
            for link in links:
                if (link.to_node == world_output and
                    link.to_socket.name == 'Environment'):

                    if link.from_node.bl_idname == 'OctaneTextureEnvironment':
                        tex_env = link.from_node
                        # Update the Power input
                        tex_env.inputs['Power'].default_value = self.background_strength

                        # Force updates
                        tex_env.update()
                        world.node_tree.update_tag()

                        # Force viewport update
                        for area in context.screen.areas:
                            if area.type == 'VIEW_3D':
                                area.tag_redraw()
                        break


def setup_hdri_system(context):
    """Set up the Octane HDRI system"""
    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences
    hdri_settings = context.scene.hdri_settings

    # Check if Octane is installed and available
    try:
        import _octane
    except ImportError:
        # Octane is not installed
        def draw_octane_error(self, context):
            layout = self.layout
            layout.label(text="Octane Render is not installed!", icon='ERROR')
            layout.label(text="Please switch to Cycles engine in preferences.")
            layout.separator()
            layout.operator("preferences.addon_show", text="Open Addon Preferences").module = addon_name

        context.window_manager.popup_menu(draw_octane_error, title="Render Engine Error", icon='ERROR')

        return {'ERROR'}, "Octane Render is not installed!"

    # Check render engine
    if context.scene.render.engine != 'octane':  # Note lowercase 'octane'
        # Automatically switch to Octane
        try:
            context.scene.render.engine = 'octane'  # Use lowercase 'octane' as registered in Blender
            return {'INFO'}, "Render engine switched to Octane"
        except TypeError as e:
            print(f"Error switching to Octane: {str(e)}")
            # Try to get available render engines for debugging
            available_engines = [e.identifier for e in context.scene.render.bl_rna.properties['engine'].enum_items]
            print(f"Available render engines: {available_engines}")
            return {'ERROR'}, f"Failed to switch to Octane. Available engines: {available_engines}"

    # Try to set the color transform, but don't break if it fails
    try:
        # Check if 'Raw' is available in the view transform options
        if 'Raw' in [item.identifier for item in context.scene.view_settings.bl_rna.properties['view_transform'].enum_items]:
            context.scene.view_settings.view_transform = 'Raw'
    except Exception as e:
        return {'WARNING'}, f"Could not set color transform: {str(e)}"

    # Verify HDRI directory exists and is accessible
    if not preferences.hdri_directory or not os.path.exists(preferences.hdri_directory):
        return {'ERROR'}, "HDRI directory not found. Please select a valid directory in preferences."

    # If current folder is not set or doesn't exist, reset to HDRI directory
    if not hdri_settings.current_folder or not os.path.exists(hdri_settings.current_folder):
        hdri_settings.current_folder = preferences.hdri_directory

    # Initialize proxy settings from preferences
    from ..utils import initialize_hdri_settings_from_preferences, update_proxy_handlers
    initialize_hdri_settings_from_preferences(context)

    # Setup nodes
    transform_node, rgb_image_node, tex_env_visible = ensure_world_nodes()

    # Check if there are any HDRIs in the current directory
    if not has_hdri_files(context):
        return {'WARNING'}, "(Only shows if no direct HDRIs are preset - Access folders)"

    # Generate previews for the current directory
    enum_items = generate_previews(None, context)

    # If we have HDRIs, set the preview to the first one
    if len(enum_items) > 1:
        hdri_settings.hdri_preview = enum_items[1][0]

    # Register handlers based on proxy mode
    # This replaces the old register_octane_handlers() call
    update_proxy_handlers(hdri_settings.proxy_mode)

    # Force redraw of UI
    for area in context.screen.areas:
        area.tag_redraw()

    return {'INFO'}, "HDRI system initialized successfully"


def set_hdri(context, filepath):
    """Load a new HDRI into Octane"""
    print(f"Octane set_hdri called with filepath: {filepath}")

    world = context.scene.world
    if not world or not world.use_nodes:
        print("No world or no nodes")
        return False

    # Find RGB Image node
    rgb_node = None
    for node in world.node_tree.nodes:
        if node.bl_idname == 'OctaneRGBImage':
            rgb_node = node
            break

    if not rgb_node:
        print("No RGB Image node found")
        return False

    # Get settings
    hdri_settings = context.scene.hdri_settings
    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences

    # Check if keep_rotation is enabled in preferences
    keep_rotation_enabled = preferences.keep_rotation
    print(f"Keep rotation preference: {keep_rotation_enabled}")

    # Store previous state - Always store the original file path, not proxy
    current_path = None
    if rgb_node.image:
        current_path = original_paths.get(rgb_node.image.name, rgb_node.image.filepath)
        if not current_path and hasattr(rgb_node, 'a_filename'):
            current_path = rgb_node.a_filename

    if current_path and current_path != filepath:
        # Store previous state using original file path
        hdri_settings.previous_hdri_path = current_path

    # Find the transform node
    transform_node = None
    for node in world.node_tree.nodes:
        if node.bl_idname == 'Octane3DTransformation':
            transform_node = node
            break

    # Store current rotation ONLY if keep_rotation is enabled
    current_rotation = None
    if transform_node and keep_rotation_enabled:
        current_rotation = transform_node.inputs['Rotation'].default_value.copy()
        print(f"Stored current rotation: {current_rotation}")

    # Always store the original filepath in our tracking
    original_paths[os.path.basename(filepath)] = filepath

    try:
        # If using proxies, check for existing or create new proxy
        if hdri_settings.proxy_resolution != 'ORIGINAL':
            proxy_path = create_hdri_proxy(filepath, hdri_settings.proxy_resolution)
            if proxy_path and os.path.exists(proxy_path):
                # Store original path mapping before loading proxy
                original_paths[os.path.basename(proxy_path)] = filepath
                target_path = proxy_path
                print(f"Octane: Using proxy at {proxy_path}")
            else:
                print(f"Octane: Failed to find/create proxy, using original file: {filepath}")
                target_path = filepath
        else:
            # Use original directly
            target_path = filepath

        # Clear existing image
        if rgb_node.image:
            old_image = rgb_node.image
            rgb_node.image = None
            if old_image.users == 0:
                bpy.data.images.remove(old_image)
                print("Octane: Removed old image")

        # Load new image
        img = bpy.data.images.load(target_path, check_existing=True)
        rgb_node.image = img
        if hasattr(rgb_node, 'a_filename'):
            rgb_node.a_filename = target_path
            print(f"Octane: Set a_filename to {target_path}")

        # Store original path mapping using image name for render handlers
        # This is critical for viewport-only proxy mode to work correctly
        original_paths[img.name] = filepath
        print(f"Octane: Stored original path mapping: {img.name} -> {filepath}")

        # Handle rotation based on keep_rotation setting
        if transform_node:
            if keep_rotation_enabled and current_rotation is not None:
                # Keep the previous rotation
                print(f"Applying stored rotation: {current_rotation}")
                transform_node.inputs['Rotation'].default_value = current_rotation
            else:
                # Reset rotation to zero
                print("Resetting rotation to zero")
                transform_node.inputs['Rotation'].default_value = (0, 0, 0)

                # Force the update by changing and then changing back
                # This is a workaround for UI update issues
                temp_rotation = (0.00001, 0.00001, 0.00001)
                transform_node.inputs['Rotation'].default_value = temp_rotation
                transform_node.update()
                transform_node.inputs['Rotation'].default_value = (0, 0, 0)

        # Force updates
        rgb_node.update()
        if transform_node:
            transform_node.update()
        world.node_tree.update_tag()

        # Force viewport update
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
            elif area.type == 'PROPERTIES':
                area.tag_redraw()

        return True
    except Exception as e:
        print(f"Error setting HDRI: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def update_hdri_proxy(self, context):
    """Update handler for proxy resolution and mode changes"""
    print(f"Octane update_hdri_proxy called: proxy_resolution={self.proxy_resolution}, proxy_mode={self.proxy_mode}")

    # Make sure we have a valid world with nodes
    if not context.scene.world or not context.scene.world.use_nodes:
        print("No world or no nodes, skipping proxy update - user must initialize first")
        return

    # Find RGB Image node - but don't create it if it doesn't exist
    rgb_node = None
    for node in context.scene.world.node_tree.nodes:
        if node.bl_idname == 'OctaneRGBImage':
            rgb_node = node
            break

    # If no RGB node exists, the system is not initialized - don't create nodes automatically
    if not rgb_node:
        print("Octane HDRI system not initialized - user must click 'Initialize HDRI System' first")
        return

    # Check if we have an image or filename to work with
    has_image = rgb_node.image is not None
    has_filename = hasattr(rgb_node, 'a_filename') and rgb_node.a_filename

    if not (has_image or has_filename):
        print("No image in RGB node, can't update proxy")
        return

    settings = context.scene.hdri_settings

    # Close proxy settings on any resolution or mode change
    context.scene.hdri_settings.show_proxy_settings = False

    # Get the original path - check multiple sources
    original_path = None

    # First check original_paths using image name if image exists
    if has_image and rgb_node.image.name in original_paths:
        original_path = original_paths[rgb_node.image.name]
        print(f"Found original path from image name: {original_path}")
    # Then check original_paths using basename of filepath
    elif has_filename and os.path.basename(rgb_node.a_filename) in original_paths:
        original_path = original_paths[os.path.basename(rgb_node.a_filename)]
        print(f"Found original path from a_filename basename: {original_path}")
    # Finally use current filepath as a fallback
    else:
        if has_filename:
            original_path = rgb_node.a_filename
            print(f"Using a_filename as original path: {original_path}")
        elif has_image and rgb_node.image.filepath:
            original_path = rgb_node.image.filepath
            print(f"Using image filepath as original path: {original_path}")

    if not original_path or not os.path.exists(original_path):
        print(f"Original path not found or does not exist: {original_path}")
        return

    try:
        target_path = original_path

        # Handle proxy creation/selection based on resolution setting
        if settings.proxy_resolution != 'ORIGINAL':
            # Check for existing proxy first
            proxy_dir = os.path.join(os.path.dirname(original_path), 'proxies')
            base_name = os.path.splitext(os.path.basename(original_path))[0]
            potential_proxy = os.path.join(proxy_dir, f"{base_name}_{settings.proxy_resolution}.hdr")

            if os.path.exists(potential_proxy):
                print(f"Found existing proxy: {potential_proxy}")
                target_path = potential_proxy
            else:
                # Create a new proxy - use the imported function from utils
                print(f"Creating new proxy at resolution {settings.proxy_resolution}")
                # Import the function from utils to avoid the error
                from ..utils import create_hdri_proxy
                proxy_path = create_hdri_proxy(original_path, settings.proxy_resolution)
                if proxy_path and os.path.exists(proxy_path):
                    print(f"Created new proxy: {proxy_path}")
                    target_path = proxy_path
                else:
                    print(f"Failed to create proxy, using original: {original_path}")
        else:
            print(f"Using original file (no proxy): {original_path}")

        # Update the RGB node with the appropriate image
        try:
            print(f"Loading {'proxy' if target_path != original_path else 'original'} image: {target_path}")

            # Clear existing image to ensure clean load
            if rgb_node.image:
                current_image = rgb_node.image
                rgb_node.image = None
                if current_image.users == 0:
                    bpy.data.images.remove(current_image)
                    print("Removed old image")

            # Load new image
            img = bpy.data.images.load(target_path, check_existing=True)
            rgb_node.image = img
            if hasattr(rgb_node, 'a_filename'):
                rgb_node.a_filename = target_path
                print(f"Set a_filename to {target_path}")

            # Update path tracking if using proxy
            if target_path != original_path:  # If using proxy
                original_paths[img.name] = original_path
                original_paths[os.path.basename(target_path)] = original_path
                print(f"Updated original_paths mapping for {img.name} and {os.path.basename(target_path)}")

            # Force updates
            rgb_node.update()
            context.scene.world.node_tree.update_tag()
            print("Updated nodes and tagged for redraw")

        except Exception as e:
            print(f"Error loading image: {str(e)}")
            # Try to restore original if something fails
            try:
                img = bpy.data.images.load(original_path, check_existing=True)
                rgb_node.image = img
                if hasattr(rgb_node, 'a_filename'):
                    rgb_node.a_filename = original_path
                print("Restored original image after error")
            except Exception as e2:
                print(f"Failed to restore original image: {str(e2)}")

    except Exception as e:
        print(f"Error updating proxy: {str(e)}")
        import traceback
        traceback.print_exc()

    # Handle render update - only use handlers for 'VIEWPORT' mode
    from ..utils import update_proxy_handlers
    update_proxy_handlers(settings.proxy_mode)
    print(f"Updated proxy handlers for mode: {settings.proxy_mode}")

    # Force viewport update
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

    print("Octane update_hdri_proxy completed")


def reset_rotation(context):
    """Reset the rotation of the Octane transformation node to zero"""
    world = context.scene.world
    if world and world.use_nodes:
        for node in world.node_tree.nodes:
            if node.bl_idname == 'Octane3DTransformation':
                node.inputs['Rotation'].default_value = (0, 0, 0)
                break
    return {'FINISHED'}


def reset_strength(context):
    """Reset the strength of the Octane environment texture to 1.0"""
    world = context.scene.world
    if world and world.use_nodes:
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # Find World Output node first
        world_output = None
        for node in nodes:
            if node.bl_idname == 'OctaneEditorWorldOutputNode':
                world_output = node
                break

        # Find the Texture Environment node connected to Environment input
        if world_output:
            for link in links:
                if (link.to_node == world_output and
                    link.to_socket.name == 'Environment' and
                    link.from_node.bl_idname == 'OctaneTextureEnvironment'):
                    # Reset power of the texture environment node
                    tex_env_node = link.from_node
                    tex_env_node.inputs['Power'].default_value = 1.0

                    # Update the UI property
                    context.scene.hdri_settings.background_strength = 1.0

                    # Force updates
                    tex_env_node.update()
                    world.node_tree.update_tag()
                    break

        # Force viewport update
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    return {'FINISHED'}


def quick_rotate_hdri(context, axis, direction):
    """Quick rotate the HDRI for Octane"""
    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences

    world = context.scene.world
    if world and world.use_nodes:
        transform_node = None
        for node in world.node_tree.nodes:
            if node.bl_idname == 'Octane3DTransformation':
                transform_node = node
                break

        if transform_node:
            rotation_input = transform_node.inputs['Rotation']
            current_rotation = list(rotation_input.default_value)

            if direction == -99:  # Reset
                # For reset, just set the value directly to 0
                current_rotation[axis] = 0
            else:
                # Get the increment directly from preferences
                increment = preferences.rotation_increment

                # Apply the increment directly to the current value
                # This works whether the UI shows degrees or radians
                if direction > 0:
                    # Increase by increment
                    current_rotation[axis] += increment
                else:
                    # Decrease by increment
                    current_rotation[axis] -= increment

            # Apply the new rotation
            rotation_input.default_value = current_rotation

            # Log the change
            print(f"Changed axis {axis} rotation to {current_rotation[axis]}")

            # Force updates
            transform_node.update()
            world.node_tree.update_tag()

            # Force viewport update
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

    return {'FINISHED'}


def get_hdri_visible(context):
    """Check if the HDRI is visible in Octane"""
    print("Octane get_hdri_visible called")
    world = context.scene.world
    if world and world.use_nodes:
        for node in world.node_tree.nodes:
            if node.bl_idname == 'OctaneTextureEnvironment':
                # Find the one connected to Visible Environment
                for output in node.outputs:
                    for link in output.links:
                        if link.to_socket.name == 'Visible Environment':
                            visible = node.inputs['Backplate'].default_value
                            print(f"Octane HDRI visibility: {visible} (Backplate value)")
                            return visible

    # Default to visible if not found or can't determine
    print("Octane: No environment node found, defaulting visibility to True")
    return True


def toggle_hdri_visibility(context):
    """Toggle the visibility of the HDRI in Octane"""
    print("Octane toggle_hdri_visibility called")
    world = context.scene.world
    if world and world.use_nodes:
        tex_env_node = None
        for node in world.node_tree.nodes:
            if node.bl_idname == 'OctaneTextureEnvironment':
                # Find the one connected to Visible Environment
                for output in node.outputs:
                    for link in output.links:
                        if link.to_socket.name == 'Visible Environment':
                            tex_env_node = node
                            break
                    if tex_env_node:
                        break
                if tex_env_node:
                    break

        if tex_env_node:
            # Print all available inputs to understand what we're working with
            print("Available inputs for OctaneTextureEnvironment node:")
            for i, input in enumerate(tex_env_node.inputs):
                print(f"  Input {i}: {input.name if hasattr(input, 'name') else 'unnamed'}")

            # Toggle Backplate value
            current_value = tex_env_node.inputs['Backplate'].default_value
            print(f"Current Backplate value: {current_value}")
            new_value = not current_value
            tex_env_node.inputs['Backplate'].default_value = new_value
            print(f"New Backplate value: {new_value}")

            # Force updates
            tex_env_node.update()
            world.node_tree.update_tag()

            # Force viewport update
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

            return new_value  # Return the new visibility state

    print("Octane: No environment node found to toggle visibility")
    return False

def delete_world(context):
    """Delete the current Octane world"""
    if context.scene.world:
        world = context.scene.world
        bpy.data.worlds.remove(world, do_unlink=True)
        return True
    return False


def reset_hdri(context):
    """Reset to previously selected HDRI in Octane - FIXED TOGGLING WITH SWAP LOGIC"""
    hdri_settings = context.scene.hdri_settings
    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences
    world = context.scene.world

    # Check if we have a previous HDRI to restore
    if not hdri_settings.previous_hdri_path:
        return {'WARNING'}, "No previous HDRI to restore"

    # Verify the file still exists
    if not os.path.exists(hdri_settings.previous_hdri_path):
        return {'ERROR'}, "Previous HDRI file could not be found"

    try:
        # First make sure we have an Octane world setup
        # Check if RGB Image node exists by bl_idname, not by name
        rgb_node = None
        if world and world.use_nodes:
            for node in world.node_tree.nodes:
                if node.bl_idname == 'OctaneRGBImage':
                    rgb_node = node
                    break

        if not rgb_node:
            print("Setting up Octane nodes for reset_hdri - no RGB node found")
            transform_node, rgb_node, tex_env = ensure_world_nodes()

        # FIXED TOGGLING LOGIC: Get current path BEFORE we load the new image
        current_original_path = None

        print("=" * 60)
        print("OCTANE RESET DEBUG - BEFORE LOADING NEW IMAGE")
        print("=" * 60)

        if rgb_node.image:
            print(f"rgb_node.image exists: {rgb_node.image}")
            print(f"rgb_node.image.name: {rgb_node.image.name}")
            print(f"rgb_node.image.filepath: {rgb_node.image.filepath if rgb_node.image.filepath else 'EMPTY'}")
            if hasattr(rgb_node, 'a_filename'):
                print(f"rgb_node.a_filename: {rgb_node.a_filename}")

            # Try multiple ways to get the original path for the currently loaded image
            # 1. Check original_paths by image name
            current_original_path = original_paths.get(rgb_node.image.name)
            print(f"1. Lookup by image.name '{rgb_node.image.name}': {current_original_path}")

            # 2. If not found, check by filepath basename
            if not current_original_path and rgb_node.image.filepath:
                current_original_path = original_paths.get(os.path.basename(rgb_node.image.filepath))
                print(f"2. Lookup by filepath basename '{os.path.basename(rgb_node.image.filepath)}': {current_original_path}")

            # 3. If still not found, check a_filename attribute
            if not current_original_path and hasattr(rgb_node, 'a_filename') and rgb_node.a_filename:
                current_original_path = original_paths.get(os.path.basename(rgb_node.a_filename))
                print(f"3. Lookup by a_filename basename '{os.path.basename(rgb_node.a_filename)}': {current_original_path}")

            # 4. Final fallback: use the actual filepath/a_filename as-is
            if not current_original_path:
                if hasattr(rgb_node, 'a_filename') and rgb_node.a_filename:
                    current_original_path = rgb_node.a_filename
                    print(f"4. Fallback to a_filename directly: {current_original_path}")
                elif rgb_node.image.filepath:
                    current_original_path = rgb_node.image.filepath
                    print(f"4. Fallback to image.filepath directly: {current_original_path}")

            # 5. If it's a proxy path, try to get the original
            if current_original_path and '/proxies/' in current_original_path:
                print(f"5. Detected proxy path, attempting to reconstruct original")
                # It's a proxy, try to reconstruct original path
                proxy_dir = os.path.dirname(current_original_path)
                parent_dir = os.path.dirname(proxy_dir)
                base_name = os.path.basename(current_original_path)
                # Remove resolution suffix (e.g., "_1K", "_2K", "_4K")
                for res in ['_1K', '_2K', '_4K', '_ORIGINAL']:
                    if res in base_name:
                        base_name = base_name.replace(res, '')
                        break
                potential_original = os.path.join(parent_dir, base_name)
                if os.path.exists(potential_original):
                    current_original_path = potential_original
                    print(f"5. Reconstructed original path: {current_original_path}")

            print(f"\nFINAL current_original_path (before switch): {current_original_path}")
        else:
            print("rgb_node.image is None!")

        # The target is what's stored in previous_hdri_path
        target_original_path = hdri_settings.previous_hdri_path
        print(f"Target path (from previous_hdri_path): {target_original_path}")
        print(f"Are they the same? {current_original_path == target_original_path}")
        print("=" * 60)

        # IMPORTANT: Save current_original_path NOW before we load the new image
        # This will become the new previous_hdri_path after the switch
        path_to_save_as_previous = current_original_path
        print(f"Saved path_to_save_as_previous: {path_to_save_as_previous}")

        # Store the directory info for later
        previous_dir = os.path.dirname(target_original_path)

        # Determine actual target path (original or proxy based on current settings)
        target_path = target_original_path
        if hdri_settings.proxy_resolution != 'ORIGINAL':
            proxy_path = create_hdri_proxy(target_original_path, hdri_settings.proxy_resolution)
            if proxy_path:
                target_path = proxy_path
                print(f"Octane Reset: Using proxy: {target_path}")

        # Clear existing image
        if rgb_node.image:
            old_image = rgb_node.image
            rgb_node.image = None
            if old_image.users == 0:
                bpy.data.images.remove(old_image)

        # Load new image
        img = bpy.data.images.load(target_path, check_existing=True)
        rgb_node.image = img
        if hasattr(rgb_node, 'a_filename'):
            rgb_node.a_filename = target_path

        print("\n" + "=" * 60)
        print("OCTANE RESET DEBUG - AFTER LOADING NEW IMAGE")
        print("=" * 60)
        print(f"Loaded image name: {img.name}")
        print(f"Loaded image filepath: {img.filepath if img.filepath else 'EMPTY'}")
        print(f"Set a_filename to: {target_path}")

        # CRITICAL: Always store path mappings to ensure future toggles work
        # Store by image name
        original_paths[img.name] = target_original_path
        # Store by basename of actual loaded path (proxy or original)
        original_paths[os.path.basename(target_path)] = target_original_path
        # Also store by basename of original path
        original_paths[os.path.basename(target_original_path)] = target_original_path
        print(f"\nStored path mappings:")
        print(f"  original_paths['{img.name}'] = '{target_original_path}'")
        print(f"  original_paths['{os.path.basename(target_path)}'] = '{target_original_path}'")
        print(f"  original_paths['{os.path.basename(target_original_path)}'] = '{target_original_path}'")

        # Only update current folder if there's no active search
        if not hdri_settings.search_query:
            # Update current folder to the directory of the target HDRI
            base_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))
            try:
                rel_path = os.path.relpath(previous_dir, base_dir)
                if not rel_path.startswith('..'):
                    hdri_settings.current_folder = previous_dir
                else:
                    hdri_settings.current_folder = base_dir
            except ValueError:
                hdri_settings.current_folder = base_dir

        # Update preview selection to show which HDRI is now loaded
        # This is safe now because update_hdri_preview checks if the HDRI is already loaded
        # and skips the update if so, preserving our previous_hdri_path
        enum_items = generate_previews(None, context)
        found_match = False
        for item in enum_items:
            if item[0] == target_original_path:
                hdri_settings.hdri_preview = item[0]
                found_match = True
                break

        # If no match found, try matching by basename
        if not found_match:
            base_name = os.path.basename(target_original_path)
            for item in enum_items:
                if os.path.basename(item[0]) == base_name:
                    hdri_settings.hdri_preview = item[0]
                    break

        # FIXED: Set up proper toggling - use the path we saved BEFORE loading new image
        if path_to_save_as_previous:
            # Only update if we're actually switching to a different HDRI
            if path_to_save_as_previous != target_original_path:
                hdri_settings.previous_hdri_path = path_to_save_as_previous
                print(f"Octane Reset: Set previous_hdri_path to {path_to_save_as_previous} for next toggle")
            else:
                # We're loading the same HDRI - this shouldn't normally happen
                # but keep previous_hdri_path as is so user can still toggle back
                print(f"Octane Reset: Target same as current, keeping previous_hdri_path unchanged")
        else:
            # If we couldn't determine current path before the switch
            print(f"Octane Reset: Warning - could not determine current original path before switch")
            print(f"Octane Reset: Keeping previous_hdri_path as {hdri_settings.previous_hdri_path}")

        # Force updates
        rgb_node.update()
        world.node_tree.update_tag()

        # Force UI update
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
            elif area.type == 'PROPERTIES':
                area.tag_redraw()

        return {'INFO'}, "HDRI reset successful"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'ERROR'}, f"Failed to reset HDRI: {str(e)}"


@bpy.app.handlers.persistent
def reload_original_for_render(dummy):
    """Handler to reload original image for rendering - FIXED FOR OCTANE"""
    context = bpy.context
    if context.scene.world and context.scene.world.use_nodes:
        rgb_node = None
        for node in context.scene.world.node_tree.nodes:
            if node.bl_idname == 'OctaneRGBImage':
                rgb_node = node
                break

        if rgb_node and rgb_node.image:
            settings = context.scene.hdri_settings

            # Only reload original for 'VIEWPORT' mode
            if settings.proxy_mode == 'VIEWPORT':
                # Get original path from multiple sources
                original_path = original_paths.get(rgb_node.image.name)
                if not original_path and hasattr(rgb_node, 'a_filename'):
                    original_path = original_paths.get(os.path.basename(rgb_node.a_filename))

                # Store current proxy path for restoration
                current_proxy_path = rgb_node.image.filepath
                if hasattr(rgb_node, 'a_filename'):
                    current_proxy_path = rgb_node.a_filename

                # Store for later restoration
                if not hasattr(context.scene, "octane_proxy_restore_path"):
                    bpy.types.Scene.octane_proxy_restore_path = bpy.props.StringProperty()
                context.scene.octane_proxy_restore_path = current_proxy_path

                if original_path and original_path != current_proxy_path:
                    print(f"Octane: Swapping to original for render: {original_path}")

                    # Clear existing image
                    current_image = rgb_node.image
                    rgb_node.image = None
                    if current_image.users == 0:
                        bpy.data.images.remove(current_image)

                    # Load original image
                    img = bpy.data.images.load(original_path, check_existing=True)
                    rgb_node.image = img
                    if hasattr(rgb_node, 'a_filename'):
                        rgb_node.a_filename = original_path

                    # Force updates
                    rgb_node.update()
                    context.scene.world.node_tree.update_tag()


@bpy.app.handlers.persistent
def reset_proxy_after_render(dummy):
    """Handler to reset proxy image after render cancellation"""
    context = bpy.context
    if context.scene.world and context.scene.world.use_nodes:
        rgb_node = None
        for node in context.scene.world.node_tree.nodes:
            if node.bl_idname == 'OctaneRGBImage':
                rgb_node = node
                break

        if rgb_node and rgb_node.image:
            settings = context.scene.hdri_settings
            original_path = original_paths.get(rgb_node.image.name)
            if not original_path and hasattr(rgb_node, 'a_filename'):
                original_path = original_paths.get(os.path.basename(rgb_node.a_filename))

            # Reset to proxy only for 'VIEWPORT' mode
            if original_path and settings.proxy_mode == 'VIEWPORT':
                proxy_path = create_hdri_proxy(original_path, settings.proxy_resolution)
                if proxy_path:
                    # Clear existing image
                    current_image = rgb_node.image
                    rgb_node.image = None
                    if current_image.users == 0:
                        bpy.data.images.remove(current_image)

                    # Load proxy image
                    img = bpy.data.images.load(proxy_path, check_existing=True)
                    rgb_node.image = img
                    if hasattr(rgb_node, 'a_filename'):
                        rgb_node.a_filename = proxy_path

                    # Store original path mapping
                    original_paths[img.name] = original_path
                    original_paths[os.path.basename(proxy_path)] = original_path

                    # Force updates
                    rgb_node.update()
                    context.scene.world.node_tree.update_tag()


@bpy.app.handlers.persistent
def reset_proxy_after_render_complete(dummy):
    """Handler to reset proxy image after rendering completes - FIXED"""
    context = bpy.context
    if context.scene.world and context.scene.world.use_nodes:
        rgb_node = None
        for node in context.scene.world.node_tree.nodes:
            if node.bl_idname == 'OctaneRGBImage':
                rgb_node = node
                break

        if rgb_node and rgb_node.image:
            settings = context.scene.hdri_settings

            if settings.proxy_mode == 'VIEWPORT':
                # Check if we stored a proxy path for restoration
                if hasattr(context.scene, "octane_proxy_restore_path") and context.scene.octane_proxy_restore_path:
                    proxy_path = context.scene.octane_proxy_restore_path

                    if proxy_path and os.path.exists(proxy_path):
                        print(f"Octane: Restoring proxy after render: {proxy_path}")

                        # Get the original path BEFORE clearing the current image
                        # The current image is the full resolution one we used for rendering
                        current_image = rgb_node.image
                        original_path = original_paths.get(current_image.name)
                        if not original_path and hasattr(rgb_node, 'a_filename'):
                            original_path = original_paths.get(os.path.basename(rgb_node.a_filename))
                        # If still not found, try using the a_filename directly as it should point to the original
                        if not original_path and hasattr(rgb_node, 'a_filename'):
                            if os.path.exists(rgb_node.a_filename):
                                original_path = rgb_node.a_filename
                        print(f"Octane: Found original path for proxy restoration: {original_path}")

                        # Clear existing image
                        rgb_node.image = None
                        if current_image.users == 0:
                            bpy.data.images.remove(current_image)

                        # Load proxy image
                        img = bpy.data.images.load(proxy_path, check_existing=True)
                        rgb_node.image = img
                        if hasattr(rgb_node, 'a_filename'):
                            rgb_node.a_filename = proxy_path

                        # Store original path mapping so subsequent renders can find it
                        if original_path:
                            original_paths[img.name] = original_path
                            original_paths[os.path.basename(proxy_path)] = original_path
                            print(f"Octane: Restored proxy mapping: {img.name} -> {original_path}")

                        # Clear the stored path
                        context.scene.octane_proxy_restore_path = ""

                        # Force updates
                        rgb_node.update()
                        context.scene.world.node_tree.update_tag()

                        # Force viewport update (only if screen context is available)
                        if context.screen:
                            for area in context.screen.areas:
                                if area.type == 'VIEW_3D':
                                    area.tag_redraw()


def register_octane_handlers():
    """Register Octane specific handlers"""
    # Remove any existing handlers first to avoid duplicates
    unregister_octane_handlers()

    # Register the handlers
    bpy.app.handlers.render_init.append(reload_original_for_render)
    bpy.app.handlers.render_cancel.append(reset_proxy_after_render)
    bpy.app.handlers.render_complete.append(reset_proxy_after_render_complete)


def unregister_octane_handlers():
    """Unregister Octane specific handlers"""
    if reload_original_for_render in bpy.app.handlers.render_init:
        bpy.app.handlers.render_init.remove(reload_original_for_render)
    if reset_proxy_after_render in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.remove(reset_proxy_after_render)
    if reset_proxy_after_render_complete in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(reset_proxy_after_render_complete)
