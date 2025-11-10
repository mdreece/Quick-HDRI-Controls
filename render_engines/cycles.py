"""
Quick HDRI Controls - Cycles-specific implementation
"""
import os
import bpy
import re
from bpy.utils import previews
from mathutils import Vector
from ..utils import get_hdri_previews, create_hdri_proxy
from ..core import original_paths

# Import common HDRI management functions
from .. import hdri_management

from ..utils import world_has_nodes, enable_world_nodes

# Explicitly declare what we're exporting
__all__ = [
    'ensure_world_nodes',
    'setup_hdri_system',
    'reload_original_for_render',
    'reset_proxy_after_render',
    'reset_proxy_after_render_complete'
]

# Re-export common functions with local references
# to maintain compatibility with existing code
generate_previews = hdri_management.generate_previews
has_hdri_files = hdri_management.has_hdri_files
has_active_hdri = hdri_management.has_active_hdri
get_folders = hdri_management.get_folders

def parse_changelog(changelog_path, current_version):
    """Parse CHANGELOG.md and return the entry for the current version"""
    try:
        with open(changelog_path, 'r') as f:
            content = f.read()

        # Convert version tuple to string format
        version_str = f"V{'.'.join(map(str, current_version))}"

        # Split content into version blocks
        version_blocks = content.split('\n## ')

        for block in version_blocks:
            # Skip empty blocks
            if not block.strip():
                continue

            # Check if this block matches our version
            if version_str in block:
                # Return the entire block
                return block.strip()

        return None
    except Exception as e:
        print(f"Error reading changelog: {str(e)}")
        return None

def ensure_world_nodes():
    """Ensure world nodes exist and are properly connected for Cycles"""
    scene = bpy.context.scene

    # Create world if it doesn't exist
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")

    world = scene.world
    enable_world_nodes(world)

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

    # Set up proxy handling
    if hasattr(scene, "hdri_settings"):
        hdri_settings = scene.hdri_settings
        addon_name = __package__.split('.')[0]
        preferences = bpy.context.preferences.addons[addon_name].preferences

        # Initialize proxy settings from preferences if not already set
        if not hdri_settings.is_property_set("proxy_resolution"):
            hdri_settings.proxy_resolution = preferences.default_proxy_resolution
        if not hdri_settings.is_property_set("proxy_mode"):
            hdri_settings.proxy_mode = preferences.default_proxy_mode

    return node_mapping, node_env, node_background

def setup_hdri_system(context):
    """Set up the Cycles HDRI system without automatically loading an HDRI"""
    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences
    hdri_settings = context.scene.hdri_settings

    # Check render engine
    if context.scene.render.engine != 'CYCLES':
        # Automatically switch to Cycles
        context.scene.render.engine = 'CYCLES'
        return {'INFO'}, "Render engine switched to Cycles"

    # Try to set the view transform but don't error if it's not available
    try:
        # Check if 'AgX' is available in the view transform options
        if 'AgX' in [item.identifier for item in context.scene.view_settings.bl_rna.properties['view_transform'].enum_items]:
            context.scene.view_settings.view_transform = 'AgX'
            return {'INFO'}, "View transform set to AgX"
        # If not available, we'll leave it as is
    except Exception as e:
        return {'WARNING'}, f"Could not set color transform: {str(e)}"

    # Verify HDRI directory exists and is accessible
    if not preferences.hdri_directory or not os.path.exists(preferences.hdri_directory):
        return {'ERROR'}, "HDRI directory not found. Please select a valid directory in preferences."

    # If current folder is not set or doesn't exist, reset to HDRI directory
    if not hdri_settings.current_folder or not os.path.exists(hdri_settings.current_folder):
        hdri_settings.current_folder = preferences.hdri_directory

    # Setup nodes but don't load any HDRI
    mapping, env_tex, background = ensure_world_nodes()

    # Initialize proxy settings from preferences
    from ..utils import initialize_hdri_settings_from_preferences
    initialize_hdri_settings_from_preferences(context)

    # Check if there are any HDRIs in the current directory
    if not hdri_management.has_hdri_files(context):
        return {'WARNING'}, "(Only shows if no direct HDRIs are preset - Access folders)"

    # Force redraw of viewport
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

    return {'INFO'}, "HDRI system initialized successfully"

@bpy.app.handlers.persistent
def reload_original_for_render(dummy):
    """Handler to replace proxy with full-quality HDRI before rendering"""
    context = bpy.context
    if context.scene.world and world_has_nodes(context.scene.world):  # FIXED: Use compatibility function
        for node in context.scene.world.node_tree.nodes:
            if node.type == 'TEX_ENVIRONMENT' and node.image:
                settings = context.scene.hdri_settings
                original_path = original_paths.get(node.image.name)

                # Only reload original for 'VIEWPORT' mode
                if original_path and settings.proxy_mode == 'VIEWPORT':
                    node.image = bpy.data.images.load(original_path, check_existing=True)
                break

def reset_proxy_after_render(dummy):
    """Handler to reset proxy image after render cancellation in Cycles"""
    context = bpy.context
    if context.scene.world and world_has_nodes(context.scene.world):  # FIXED: Use compatibility function
        for node in context.scene.world.node_tree.nodes:
            if node.type == 'TEX_ENVIRONMENT' and node.image:
                settings = context.scene.hdri_settings
                original_path = original_paths.get(node.image.name)

                # Reset to proxy only for 'VIEWPORT' mode
                if original_path and settings.proxy_mode == 'VIEWPORT':
                    proxy_path = create_hdri_proxy(original_path, settings.proxy_resolution)
                    if proxy_path:
                        node.image = bpy.data.images.load(proxy_path, check_existing=True)
                break

def reset_proxy_after_render_complete(dummy):
    """Handler to reset proxy image after rendering completes in Cycles"""
    context = bpy.context
    if context.scene.world and world_has_nodes(context.scene.world):  # FIXED: Use compatibility function
        env_tex = None
        for node in context.scene.world.node_tree.nodes:
            if node.type == 'TEX_ENVIRONMENT':
                env_tex = node
                break

        if env_tex and env_tex.image:
            settings = context.scene.hdri_settings
            original_path = original_paths.get(env_tex.image.name, env_tex.image.filepath)

            if settings.proxy_mode == 'VIEWPORT':
                proxy_path = create_hdri_proxy(original_path, settings.proxy_resolution)
                if proxy_path:
                    # Clear existing image to ensure clean reload
                    current_image = env_tex.image
                    env_tex.image = None
                    if current_image.users == 0:
                        bpy.data.images.remove(current_image)

                    # Load proxy
                    env_tex.image = bpy.data.images.load(proxy_path, check_existing=True)
