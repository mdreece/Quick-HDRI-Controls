"""
Quick HDRI Controls - Utility functions
"""
import os
import time
import sys
import bpy
import re
import urllib.request
import zipfile
import shutil
import tempfile
import glob
from datetime import datetime
from math import radians, degrees
from bpy.app.handlers import persistent
from bpy.utils import previews
from bpy.types import Operator

# Store handler references for easy management
handler_references = {
    'load_post': [],
    'render_init': [],
    'render_cancel': [],
    'render_complete': []
}

def world_has_nodes(world):
    """
    Compatibility function for checking if world has nodes.
    Blender 5.0+ change. Funny enough I already updated this for BforArtists lol then realized the reason why is their 4.5.0 has 5.0.0 alpha in it, so redoing that ish so that everything from 4.X to 5.X will work
    """
    if world is None:
        return False

    # For Blender 5.0+, world nodes are always enabled
    if hasattr(world, 'use_nodes'):
        return world.use_nodes
    else:
        # Blender 5.0+ - nodes are always available
        return True

def enable_world_nodes(world):
    if world is None:
        return

    # Only set use_nodes if the attribute exists (pre-5.0)
    if hasattr(world, 'use_nodes'):
        world.use_nodes = True
    # In Blender 5.0+, nodes are always enabled, so no action needed

@bpy.app.handlers.persistent
def ensure_proxy_handlers_on_load(dummy):
    """Ensure proxy handlers are registered when scenes load"""
    try:
        if bpy.context.scene and hasattr(bpy.context.scene, 'hdri_settings'):
            settings = bpy.context.scene.hdri_settings
            update_proxy_handlers(settings.proxy_mode)
            print(f"Ensured handlers registered for proxy mode: {settings.proxy_mode}")
    except Exception as e:
        print(f"Error ensuring proxy handlers: {str(e)}")

def get_icons():
    if not hasattr(get_icons, "icon_collection"):
        pcoll = previews.new()
        get_icons.icon_collection = pcoll

        # Define addon name explicitly
        addon_name = get_addon_name()

        # Get the addon directory directly
        scripts_path = bpy.utils.user_resource('SCRIPTS')
        addon_dir = os.path.join(scripts_path, "addons", addon_name)

        # Define the path to icons directory (which already exists)
        icons_dir = os.path.join(addon_dir, "misc", "icons")

        print(f"Loading icons from: {icons_dir}")

        # Check if files exist before trying to load them
        cycles_icon_path = os.path.join(icons_dir, "cycles_icon.png")
        octane_icon_path = os.path.join(icons_dir, "octane_icon.png")
        vray_icon_path = os.path.join(icons_dir, "vray_icon.png")

        # Load each icon with error handling
        if os.path.exists(cycles_icon_path):
            pcoll.load("cycles_icon", cycles_icon_path, 'IMAGE')
            print(f"Successfully loaded: cycles_icon")
        else:
            print(f"ERROR: Could not find {cycles_icon_path}")

        if os.path.exists(octane_icon_path):
            pcoll.load("octane_icon", octane_icon_path, 'IMAGE')
            print(f"Successfully loaded: octane_icon")
        else:
            print(f"ERROR: Could not find {octane_icon_path}")

        if os.path.exists(vray_icon_path):
            pcoll.load("vray_icon", vray_icon_path, 'IMAGE')
            print(f"Successfully loaded: vray_icon")
        else:
            print(f"ERROR: Could not find {vray_icon_path}")

    return get_icons.icon_collection

def get_addon_name():
    """Get addon name consistently"""
    return "Quick-HDRI-Controls-main"

def get_current_version():
    """Get current addon version from bl_info"""
    addon_name = get_addon_name()
    try:
        import importlib
        main_module = importlib.import_module(addon_name)
        return main_module.bl_info['version']
    except (ImportError, AttributeError):
        # Fallback to hardcoded version - update this when changing version
        return (2, 8, 9)  # Make sure this matches the current version in __init__.py

def format_version(version_tuple):
    """Format version tuple to string"""
    return f"v{version_tuple[0]}.{version_tuple[1]}.{version_tuple[2]}"

def get_version_string():
    """Get formatted version string"""
    return format_version(get_current_version())

def get_online_version():
    """Fetch version info from GitHub"""
    try:
        import urllib.request
        import re

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

def check_for_update():
    """Check if an update is available"""
    current_version = get_current_version()
    online_version = get_online_version()

    if online_version is None:
        return False, current_version, None

    # Compare versions
    needs_update = online_version > current_version
    return needs_update, current_version, online_version

def get_hdri_previews():
    """Get or create the preview collection"""
    if not hasattr(get_hdri_previews, "preview_collection"):
        pcoll = previews.new()
        get_hdri_previews.preview_collection = pcoll
        get_hdri_previews.cached_dir = None
        get_hdri_previews.cached_items = []
        get_hdri_previews.last_update_time = time.time()
    return get_hdri_previews.preview_collection

def refresh_previews(context, new_directory=None):
    """Refresh the preview collection when settings change"""
    from .render_engines import cycles

    pcoll = get_hdri_previews()

    # Store current selection before refreshing
    current_selection = None
    if hasattr(context.scene, "hdri_settings"):
        current_selection = context.scene.hdri_settings.hdri_preview

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

        # Force regeneration of previews
        enum_items = cycles.generate_previews(None, context)

        # Important: Reset hdri_preview to empty string first to avoid invalid enum warnings
        try:
            current_settings.hdri_preview = ''
        except:
            pass

        # If we had a selection, try to restore it
        if current_selection and len(enum_items) > 0:
            # Check if previous selection still exists
            found = False
            for item in enum_items:
                if item[0] == current_selection:
                    try:
                        current_settings.hdri_preview = current_selection
                        found = True
                        break
                    except:
                        pass

            # If not found and we have items, select the first valid one
            if not found and len(enum_items) > 1:
                try:
                    current_settings.hdri_preview = enum_items[1][0]  # Skip the 'None' item
                except:
                    pass
        # If we had no selection but have items now, select the first one
        elif len(enum_items) > 1:
            try:
                current_settings.hdri_preview = enum_items[1][0]  # Skip the 'None' item
            except:
                pass

        # Force UI update
        for area in context.screen.areas:
            area.tag_redraw()

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

def cleanup_previews():
    """Clean up preview collections when unregistering the addon"""
    if hasattr(get_icons, "icon_collection"):
        try:
            previews.remove(get_icons.icon_collection)
            delattr(get_icons, "icon_collection")
        except:
            pass

    if hasattr(get_hdri_previews, "preview_collection"):
        try:
            previews.remove(get_hdri_previews.preview_collection)
            delattr(get_hdri_previews, "preview_collection")
        except:
            pass

def get_proxy_directory(filepath):
    """Get or create the proxy directory for the given HDRI file"""
    hdri_dir = os.path.dirname(filepath)
    proxy_dir = os.path.join(hdri_dir, 'proxies')
    os.makedirs(proxy_dir, exist_ok=True)
    return proxy_dir

def create_hdri_proxy(original_path, target_resolution):
    """Create a proxy version of an HDRI at the specified resolution."""
    resolution_map = {
        '1K': 1024,
        '2K': 2048,
        '4K': 4096,
        '6K': 6144,
        '8K': 8192,
        '16K': 16384
    }

    target_width = resolution_map.get(target_resolution)
    if not target_width:
        return None

    # Get proxy directory in same folder as HDRI
    proxy_dir = get_proxy_directory(original_path)

    # Generate proxy filename
    base_name = os.path.splitext(os.path.basename(original_path))[0]
    proxy_name = f"{base_name}_{target_resolution}.hdr"
    proxy_path = os.path.join(proxy_dir, proxy_name)

    # Check if proxy already exists
    if os.path.exists(proxy_path):
        return proxy_path

    try:
        # Load original image
        original_img = bpy.data.images.load(original_path, check_existing=True)
        original_width = original_img.size[0]

        # Don't create proxy if target resolution is higher than original
        if target_width >= original_width:
            if original_img.users == 0:
                bpy.data.images.remove(original_img)
            return original_path

        # Calculate new dimensions
        aspect_ratio = original_img.size[1] / original_img.size[0]
        target_height = int(target_width * aspect_ratio)

        # Create resized image
        original_img.scale(target_width, target_height)

        # Save with proper keyword argument
        original_img.save(filepath=proxy_path)

        # Clean up
        if original_img.users == 0:
            bpy.data.images.remove(original_img)

        return proxy_path
    except Exception as e:
        print(f"Error creating proxy: {str(e)}")
        return None

def cleanup_legacy_files():
    """
    Checks for and removes legacy __init__ files in render engine directories.
    These files can cause import conflicts after updates.
    """
    import os
    import sys
    import bpy

    print("\n=== CHECKING FOR LEGACY FILES ===")

    # Get the addon directory path
    addon_name = get_addon_name()
    addon_dir = os.path.join(bpy.utils.user_resource('SCRIPTS'),
                             "addons",
                             addon_name)

    # Define the legacy files to check for
    legacy_files = [
        os.path.join(addon_dir, "render_engines", "__init__cycles.py"),
        os.path.join(addon_dir, "render_engines", "__init__octane.py"),
        os.path.join(addon_dir, "render_engines", "__init__vray.py")
    ]

    # Check each file and delete if it exists
    files_deleted = 0
    for file_path in legacy_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✓ Removed legacy file: {os.path.basename(file_path)}")
                files_deleted += 1
            except Exception as e:
                print(f"⚠️ Failed to remove {os.path.basename(file_path)}: {str(e)}")

    if files_deleted > 0:
        print(f"Successfully removed {files_deleted} legacy file(s)")
    else:
        print("No legacy files found")

    print("=== LEGACY FILE CHECK COMPLETE ===\n")

    return files_deleted > 0  # Return True if any files were deleted

def check_for_update_on_startup():
    """Check for updates on Blender startup if enabled in preferences."""
    try:
        import bpy
        addon_name = get_addon_name()
        preferences = bpy.context.preferences.addons[addon_name].preferences

        if not preferences.enable_auto_update_check:
            return  # Exit if auto-update is not enabled

        needs_update, current_version, online_version = check_for_update()

        # Update preferences flag
        if needs_update:
            preferences.update_available = True
        else:
            preferences.update_available = False

    except Exception as e:
        print(f"Error checking for updates on startup: {str(e)}")

def extract_addon_zips():
    """Extract any ZIP files found in the addon directory and clean up."""
    # Log start of function for better debugging
    print("\n=== CHECKING FOR ADDON ZIP FILES ===")

    # Get the absolute path of the addon directory using multiple methods
    # Method 1: From utils.py location
    utils_dir = os.path.dirname(os.path.realpath(__file__))
    addon_dir = utils_dir

    # Print the paths we're using
    print(f"Addon directory (from utils.py): {addon_dir}")

    # Alternative method to try and find the addon directory
    addon_name = get_addon_name()
    alt_addon_dir = os.path.join(bpy.utils.user_resource('SCRIPTS'), "addons", addon_name)
    print(f"Alternative addon path: {alt_addon_dir}")

    # Check if both exist, use the one that contains ZIPs
    if os.path.exists(alt_addon_dir):
        # Count ZIP files in each location
        utils_zips = len([f for f in os.listdir(addon_dir) if f.lower().endswith('.zip')])
        alt_zips = len([f for f in os.listdir(alt_addon_dir) if f.lower().endswith('.zip')])

        print(f"Found {utils_zips} ZIPs in utils dir and {alt_zips} ZIPs in addon dir")

        # Use the directory with more ZIP files
        if alt_zips > utils_zips:
            addon_dir = alt_addon_dir
            print(f"Using alternative addon directory: {addon_dir}")

    # Find all zip files in the addon directory
    try:
        zip_files = [f for f in os.listdir(addon_dir) if f.lower().endswith('.zip')]
        print(f"Found {len(zip_files)} ZIP files: {zip_files}")
    except Exception as e:
        print(f"Error listing directory {addon_dir}: {str(e)}")
        print("=== ZIP CHECK FAILED ===\n")
        return False

    # No ZIP files found
    if not zip_files:
        print("No ZIP files found to extract")
        print("=== ZIP CHECK COMPLETE ===\n")
        return False

    # Flag to track if we actually extracted any updates
    update_installed = False

    for zip_file in zip_files:
        zip_path = os.path.join(addon_dir, zip_file)
        print(f"Processing ZIP file: {zip_path}")

        try:
            # Verify ZIP file exists and is readable
            if not os.path.exists(zip_path):
                print(f"ZIP file does not exist: {zip_path}")
                continue

            # Check if file is a valid ZIP
            if not zipfile.is_zipfile(zip_path):
                print(f"File is not a valid ZIP: {zip_path}")
                continue

            print(f"Extracting ZIP: {zip_file}")

            # Create a temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"Created temp directory: {temp_dir}")

                # Extract the ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_contents = zip_ref.namelist()
                    print(f"ZIP contains {len(zip_contents)} files")
                    zip_ref.extractall(temp_dir)

                # Get the extracted folder contents
                extracted_items = os.listdir(temp_dir)
                print(f"Extracted items: {extracted_items}")

                if not extracted_items:
                    print("ZIP extracted but contains no files")
                    continue

                # If there's a single directory, use that as the source
                if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_items[0])):
                    source_dir = os.path.join(temp_dir, extracted_items[0])
                    print(f"Using subdirectory as source: {extracted_items[0]}")
                else:
                    source_dir = temp_dir
                    print("Using temp directory directly as source")

                # List files to be copied
                source_items = os.listdir(source_dir)
                print(f"Source items to copy: {source_items}")

                # Copy all files to addon directory
                copied_items = 0
                for item in source_items:
                    src_path = os.path.join(source_dir, item)
                    dst_path = os.path.join(addon_dir, item)

                    print(f"Copying {item} to {dst_path}")

                    try:
                        if os.path.isfile(src_path):
                            shutil.copy2(src_path, dst_path)
                            copied_items += 1
                        elif os.path.isdir(src_path):
                            if os.path.exists(dst_path):
                                print(f"Removing existing directory: {dst_path}")
                                shutil.rmtree(dst_path)
                            shutil.copytree(src_path, dst_path)
                            copied_items += 1
                    except Exception as copy_error:
                        print(f"Error copying {item}: {str(copy_error)}")

                print(f"Copied {copied_items} items to addon directory")

            # Try to remove the ZIP file
            try:
                os.remove(zip_path)
                print(f"Removed original ZIP file: {zip_file}")
            except Exception as rm_error:
                print(f"Could not remove ZIP file, will retry: {str(rm_error)}")
                # Try alternative approach using os.unlink
                try:
                    os.unlink(zip_path)
                    print("Removed ZIP file using unlink")
                except Exception as unlink_error:
                    print(f"Still cannot remove ZIP file: {str(unlink_error)}")

            update_installed = True
            print(f"Successfully extracted and processed {zip_file}")

        except Exception as e:
            print(f"Error processing {zip_file}: {str(e)}")
            import traceback
            traceback.print_exc()

    print(f"ZIP extraction complete. Updates installed: {update_installed}")
    print("=== ZIP CHECK COMPLETE ===\n")

    return update_installed

def show_changelog():
    """Show the changelog dialog if an update was just installed"""
    try:
        addon_dir = os.path.dirname(os.path.realpath(__file__))
        addon_dir = os.path.dirname(addon_dir)  # Go up one level from utils.py
        changelog_path = os.path.join(addon_dir, "CHANGELOG.md")

        if os.path.exists(changelog_path):
            # Get current version from bl_info
            current_version = bpy.context.preferences.addons[__package__.split('.')[0]].bl_info['version']

            # Parse changelog for current version (use the function defined in this file)
            changes = parse_changelog(changelog_path, current_version)

            if changes:
                # Store changes in window manager property
                bpy.context.window_manager.hdri_changelog = changes

                # Show dialog
                bpy.ops.world.show_hdri_changelog('INVOKE_DEFAULT')

    except Exception as e:
        print(f"Error showing changelog: {str(e)}")

@persistent
def load_handler(dummy):
    """Ensure keyboard shortcuts are properly set after file load"""
    addon_name = get_addon_name()
    # Get addon keymaps reference from the main module
    addon_keymaps = sys.modules[addon_name].addon_keymaps

    # Clear existing keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # Re-add keymap with current preferences
    setup_keymap(addon_keymaps)

def setup_keymap(addon_keymaps):
    """Set up keyboard shortcuts based on preferences"""
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
        addon_name = get_addon_name()
        preferences = bpy.context.preferences.addons[addon_name].preferences
        is_mac = sys.platform == 'darwin'

        kmi = km.keymap_items.new(
            "world.hdri_popup_controls",
            type=preferences.popup_key,
            value='PRESS',
            oskey=preferences.popup_ctrl if is_mac else False,
            ctrl=preferences.popup_ctrl if not is_mac else False,
            shift=preferences.popup_shift,
            alt=preferences.popup_alt
        )
        addon_keymaps.append((km, kmi))

def clear_keymaps(addon_keymaps):
    """Clear all keyboard shortcuts"""
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)

def update_proxy_handlers(proxy_mode):
    """Update the render handlers based on proxy mode and current render engine"""
    # Get current render engine
    render_engine = bpy.context.scene.render.engine

    # Import handlers based on render engine
    if render_engine == 'octane':
        from .render_engines.octane import (
            reload_original_for_render,
            reset_proxy_after_render,
            reset_proxy_after_render_complete
        )
    elif render_engine == 'VRAY_RENDER_RT':
        from .render_engines.vray import (
            reload_original_for_render,
            reset_proxy_after_render,
            reset_proxy_after_render_complete
        )
    else:
        # Default to Cycles
        from .render_engines.cycles import (
            reload_original_for_render,
            reset_proxy_after_render,
            reset_proxy_after_render_complete
        )

    # Handle render update - only use handlers for 'VIEWPORT' mode
    if proxy_mode == 'VIEWPORT':
        # Add handlers if not already present
        if reload_original_for_render not in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.append(reload_original_for_render)
        if reset_proxy_after_render not in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.append(reset_proxy_after_render)
        if reset_proxy_after_render_complete not in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.append(reset_proxy_after_render_complete)
    else:
        # Remove handlers
        if reload_original_for_render in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.remove(reload_original_for_render)
        if reset_proxy_after_render in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(reset_proxy_after_render)
        if reset_proxy_after_render_complete in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(reset_proxy_after_render_complete)

def initialize_hdri_settings_from_preferences(context):
    """Initialize HDRI settings from preferences for a new scene"""
    if not hasattr(context.scene, "hdri_settings"):
        return

    hdri_settings = context.scene.hdri_settings
    addon_name = get_addon_name()

    # Make sure addon preferences exist
    if addon_name not in context.preferences.addons:
        return

    preferences = context.preferences.addons[addon_name].preferences

    # Check if already initialized to avoid overriding user changes
    if hasattr(hdri_settings, 'proxy_initialized') and hdri_settings.proxy_initialized:
        return

    # Initialize proxy settings from preferences
    try:
        hdri_settings.proxy_resolution = preferences.default_proxy_resolution
        hdri_settings.proxy_mode = preferences.default_proxy_mode

        # Mark as initialized
        hdri_settings.proxy_initialized = True

        print(f"Initialized proxy_resolution to {preferences.default_proxy_resolution}")
        print(f"Initialized proxy_mode to {preferences.default_proxy_mode}")
    except Exception as e:
        print(f"Error initializing proxy settings: {str(e)}")


@persistent
def init_hdri_settings_handler(dummy):
    """Initialize HDRI settings from preferences when a new scene is loaded"""
    # This ensures that proxy settings are initialized from preferences for new scenes
    initialize_hdri_settings_from_preferences(bpy.context)

def setup_handlers():
    """Set up all the handlers needed by the addon"""
    # Note: Render handlers (render_init, render_cancel, render_complete) are now
    # registered by update_proxy_handlers() based on the active render engine
    # We only register the load_post handlers here

    # Store references to load_post handlers
    handler_references['load_post'].append(load_handler)
    handler_references['load_post'].append(init_hdri_settings_handler)

    # Register load_post handlers
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)

    if init_hdri_settings_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(init_hdri_settings_handler)

    if ensure_proxy_handlers_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(ensure_proxy_handlers_on_load)

def remove_handlers():
    """Remove all handlers registered by the addon"""
    # Load post handlers
    for handler in handler_references['load_post']:
        if handler in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(handler)

    # Remove render handlers from all engines
    # We need to import all handlers to properly clean them up
    try:
        from .render_engines.cycles import (
            reload_original_for_render as cycles_reload,
            reset_proxy_after_render as cycles_reset,
            reset_proxy_after_render_complete as cycles_complete
        )
        # Remove Cycles handlers
        if cycles_reload in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.remove(cycles_reload)
        if cycles_reset in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(cycles_reset)
        if cycles_complete in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(cycles_complete)
    except:
        pass

    try:
        from .render_engines.octane import (
            reload_original_for_render as octane_reload,
            reset_proxy_after_render as octane_reset,
            reset_proxy_after_render_complete as octane_complete
        )
        # Remove Octane handlers
        if octane_reload in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.remove(octane_reload)
        if octane_reset in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(octane_reset)
        if octane_complete in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(octane_complete)
    except:
        pass

    try:
        from .render_engines.vray import (
            reload_original_for_render as vray_reload,
            reset_proxy_after_render as vray_reset,
            reset_proxy_after_render_complete as vray_complete
        )
        # Remove V-Ray handlers
        if vray_reload in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.remove(vray_reload)
        if vray_reset in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(vray_reset)
        if vray_complete in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(vray_complete)
    except:
        pass

    # Clear references
    for key in handler_references:
        handler_references[key].clear()

def get_support_blend_path():
    """
    Get the path to the support.blend file using a more reliable method.
    """
    import os
    import bpy

    # Method 1: Try to get the addon directory using bpy.utils
    addon_name = get_addon_name()
    addon_dir = os.path.join(bpy.utils.user_resource('SCRIPTS'), "addons", addon_name)

    print(f"Looking for support.blend using direct addon path: {addon_dir}")

    # Check for new consolidated support file first
    support_path = os.path.join(addon_dir, "misc", "support.blend")
    if os.path.exists(support_path):
        print(f"Found support.blend at: {support_path}")
        return support_path

    # Check for legacy Preview.blend (new location)
    preview_new_path = os.path.join(addon_dir, "misc", "Preview.blend")
    if os.path.exists(preview_new_path):
        print(f"Found legacy Preview.blend at: {preview_new_path}")
        return preview_new_path

    # Check the root folder (old location)
    preview_old_path = os.path.join(addon_dir, "Preview.blend")
    if os.path.exists(preview_old_path):
        print(f"Found legacy Preview.blend at: {preview_old_path}")
        return preview_old_path

    # Method 2: Try using __file__ as fallback
    try:
        file_dir = os.path.dirname(os.path.realpath(__file__))
        parent_dir = os.path.dirname(file_dir)

        print(f"Fallback method - File directory: {file_dir}")
        print(f"Fallback method - Parent directory: {parent_dir}")

        # Check misc folder with fallback method
        fallback_new = os.path.join(parent_dir, "misc", "Preview.blend")
        if os.path.exists(fallback_new):
            print(f"Found Preview.blend at fallback path: {fallback_new}")
            return fallback_new

        # Check root folder with fallback method
        fallback_old = os.path.join(parent_dir, "Preview.blend")
        if os.path.exists(fallback_old):
            print(f"Found Preview.blend at fallback path: {fallback_old}")
            return fallback_old
    except Exception as e:
        print(f"Error in fallback method: {str(e)}")

    # Not found with any method
    print("ERROR: Preview.blend not found in any expected location")
    return None

def ensure_addon_structure():
    """
    Ensure the addon has the necessary folder structure.
    Creates the misc folder if it doesn't exist and handles support file migration.
    """
    import os
    import shutil

    # Get the addon's root directory
    addon_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # Create the misc folder if it doesn't exist
    misc_dir = os.path.join(addon_dir, "misc")
    icons_dir = os.path.join(misc_dir, "icons")

    os.makedirs(misc_dir, exist_ok=True)
    os.makedirs(icons_dir, exist_ok=True)

    # Handle support file migration/renaming
    support_path = os.path.join(misc_dir, "support.blend")
    preview_new_path = os.path.join(misc_dir, "Preview.blend")
    preview_old_path = os.path.join(addon_dir, "Preview.blend")

    # If support.blend doesn't exist, try to migrate from Preview.blend
    if not os.path.exists(support_path):
        # Try new location first
        if os.path.exists(preview_new_path):
            try:
                shutil.move(preview_new_path, support_path)
                print(f"Renamed Preview.blend to support.blend in {misc_dir}")
            except Exception as e:
                print(f"Error renaming Preview.blend to support.blend: {str(e)}")
        # Try old location
        elif os.path.exists(preview_old_path):
            try:
                shutil.move(preview_old_path, support_path)
                print(f"Moved and renamed Preview.blend to support.blend in {misc_dir}")
            except Exception as e:
                print(f"Error moving Preview.blend: {str(e)}")
                # If we couldn't move it, at least try to copy it
                try:
                    shutil.copy2(preview_old_path, support_path)
                    print(f"Copied and renamed Preview.blend to support.blend in {misc_dir}")
                except Exception as e:
                    print(f"Error copying Preview.blend: {str(e)}")

    # Clean up old vray folder if it exists and is empty
    vray_dir = os.path.join(misc_dir, "vray")
    if os.path.exists(vray_dir):
        try:
            if not os.listdir(vray_dir):  # Directory is empty
                os.rmdir(vray_dir)
                print(f"Removed empty vray directory: {vray_dir}")
        except Exception as e:
            print(f"Could not remove vray directory: {str(e)}")

def get_active_engine_module():
    """Get the appropriate engine module based on current render engine"""
    render_engine = bpy.context.scene.render.engine

    if render_engine == 'CYCLES':
        from .render_engines import cycles
        return cycles
    elif render_engine == 'VRAY_RENDER_RT':
        from .render_engines import vray
        return vray
    elif render_engine == 'octane':
        from .render_engines import octane
        return octane
    else:
        # Default to cycles if engine is not supported
        from .render_engines import cycles
        return cycles

def switch_to_preferred_render_engine(addon_path):
    """Switch to the user's preferred render engine without file copying"""
    import os
    import json

    try:
        # Read the preferences to determine the render engine
        preferences_path = os.path.join(addon_path, "preferences.json")

        # If preferences file exists, read the render engine
        if os.path.exists(preferences_path):
            with open(preferences_path, 'r') as f:
                preferences = json.load(f)
                render_engine = preferences.get('render_engine', 'CYCLES')
        else:
            # Default to Cycles if no preferences found
            render_engine = 'CYCLES'

        # Save the preferred engine to be loaded on next Blender start
        # We're not modifying files, just storing the preference
        with open(preferences_path, 'w') as f:
            json.dump({'render_engine': render_engine}, f)

        # Set the render engine directly if possible
        try:
            bpy.context.scene.render.engine = render_engine
        except Exception as e:
            print(f"Could not set render engine: {str(e)}")

    except Exception as e:
        print(f"Error switching render engine: {str(e)}")

def verify_render_engine_preference():
    """Verifies the render engine preference is valid and matches current settings"""
    addon_name = get_addon_name()
    addon_dir = os.path.join(bpy.utils.user_resource('SCRIPTS'), "addons", addon_name)
    preferences_path = os.path.join(addon_dir, "preferences.json")

    # Check if preferences file exists and read it
    if os.path.exists(preferences_path):
        try:
            with open(preferences_path, 'r') as f:
                prefs = json.load(f)
                stored_engine = prefs.get('render_engine', 'CYCLES')

            # Get addon preferences
            if addon_name in bpy.context.preferences.addons:
                addon_prefs = bpy.context.preferences.addons[addon_name].preferences
                pref_engine = addon_prefs.render_engine

                # If they don't match, update the file
                if stored_engine != pref_engine:
                    print(f"Fixing mismatch: File has {stored_engine}, preferences have {pref_engine}")
                    with open(preferences_path, 'w') as f:
                        json.dump({'render_engine': pref_engine}, f)
                    return pref_engine
        except Exception as e:
            print(f"Error checking preferences: {str(e)}")

    # Default to current engine if anything fails
    return bpy.context.scene.render.engine

def parse_changelog(changelog_path, current_version):
    """Parse CHANGELOG.md and return the entry for the current version

    This function works with both old format (separate engine versions) and new unified format.
    Old format: ## 23-9-2025:  CYCLES: v2.9.3 | OCTANE: V2.9.3 | V-RAY: V2.9.3
    New format: ## 23-9-2025:  Quick HDRI Controls: v2.9.5
    """
    try:
        with open(changelog_path, 'r') as f:
            content = f.read()

        # Convert version tuple to string format
        # We'll search for both lowercase and uppercase V to handle old and new formats
        version_str_lower = f"v{'.'.join(map(str, current_version))}"  # e.g., v2.9.5
        version_str_upper = f"V{'.'.join(map(str, current_version))}"  # e.g., V2.9.5

        print(f"Looking for changelog entry for version: {version_str_lower} (or {version_str_upper})")

        # Split content into version blocks
        version_blocks = content.split('\n## ')

        for block in version_blocks:
            # Skip empty blocks
            if not block.strip():
                continue

            # Check if this block matches our version (case-insensitive search)
            if version_str_lower in block or version_str_upper in block:
                print(f"Found matching changelog entry!")
                # Return the entire block (including the ## header)
                return "## " + block.strip()

        print(f"No changelog entry found for version {version_str_lower}")
        return None
    except Exception as e:
        print(f"Error reading changelog: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
