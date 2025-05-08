"""
Quick HDRI Controls - Utility functions
"""
import os
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
from bpy.types import Operator  # Add this import

# Store handler references for easy management
handler_references = {
    'load_post': [],
    'render_init': [],
    'render_cancel': [],
    'render_complete': []
}

def get_icons():
    if not hasattr(get_icons, "icon_collection"):
        pcoll = previews.new()
        get_icons.icon_collection = pcoll
        
        # Define addon name explicitly
        addon_name = "Quick-HDRI-Controls-main"
        
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
        enum_items = cycles.generate_previews(None, context)
        if len(enum_items) > 1:
            current_settings.hdri_preview = enum_items[1][0]

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

def check_for_update_on_startup():
    """Check for updates on Blender startup if enabled in preferences."""
    try:
        addon_name = __package__.split('.')[0]
        preferences = bpy.context.preferences.addons[addon_name].preferences

        if not preferences.enable_auto_update_check:
            return  # Exit if auto-update is not enabled

        # Method 1: Import bl_info from the main module
        try:
            import importlib
            main_module = importlib.import_module(addon_name)
            current_version = main_module.bl_info['version']
        except (ImportError, AttributeError):
            # Method 2: Fallback to hardcoded version if import fails
            current_version = (2, 8, 2)  # Update this to your current version

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

    except Exception as e:
        print(f"Error checking for updates: {str(e)}")

def extract_addon_zips():
    """Extract any ZIP files found in the addon directory and clean up."""
    addon_dir = os.path.dirname(os.path.realpath(__file__))
    addon_dir = os.path.dirname(addon_dir)  # Go up one level from utils.py

    # Find all zip files in the addon directory
    zip_files = [f for f in os.listdir(addon_dir) if f.lower().endswith('.zip')]

    # Flag to track if we actually extracted any updates
    update_installed = False

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
            update_installed = True
            print(f"Successfully extracted and cleaned up {zip_file}")

        except Exception as e:
            print(f"Error processing {zip_file}: {str(e)}")

    # If we installed any updates, show the changelog
    if update_installed:
        # Import at function level to avoid circular imports
        # Use timer to ensure Blender UI is ready
        bpy.app.timers.register(show_changelog, first_interval=1.0)

def show_changelog():
    """Show the changelog dialog if an update was just installed"""
    try:
        addon_dir = os.path.dirname(os.path.realpath(__file__))
        addon_dir = os.path.dirname(addon_dir)  # Go up one level from utils.py
        changelog_path = os.path.join(addon_dir, "CHANGELOG.md")

        if os.path.exists(changelog_path):
            # Get current version from bl_info
            current_version = bpy.context.preferences.addons[__package__.split('.')[0]].bl_info['version']

            # Import at function level to avoid circular imports
            from .render_engines.cycles import parse_changelog

            # Parse changelog for current version
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
    addon_name = __package__.split('.')[0]
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
        addon_name = __package__.split('.')[0]
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

def setup_handlers():
    """Set up all the handlers needed by the addon"""
    # Import here to avoid circular imports
    from .render_engines.cycles import (
        reload_original_for_render,
        reset_proxy_after_render,
        reset_proxy_after_render_complete
    )

    # Store references to handlers
    handler_references['load_post'].append(load_handler)
    handler_references['render_init'].append(reload_original_for_render)
    handler_references['render_cancel'].append(reset_proxy_after_render)
    handler_references['render_complete'].append(reset_proxy_after_render_complete)

    # Register handlers
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)

    # These handlers depend on the proxy mode
    # They'll be added by update_proxy_handlers if needed

def update_proxy_handlers(proxy_mode):
    """Update the render handlers based on proxy mode"""
    # Import at function level to avoid circular imports
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

def remove_handlers():
    """Remove all handlers registered by the addon"""
    # Load post handlers
    for handler in handler_references['load_post']:
        if handler in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(handler)

    # Render init handlers
    for handler in handler_references['render_init']:
        if handler in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.remove(handler)

    # Render cancel handlers
    for handler in handler_references['render_cancel']:
        if handler in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(handler)

    # Render complete handlers
    for handler in handler_references['render_complete']:
        if handler in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(handler)

    # Clear references
    for key in handler_references:
        handler_references[key].clear()

def get_preview_blend_path():
    """
    Get the path to the Preview.blend file, checking both the new (misc folder) and old locations.

    Returns:
        str: The absolute path to the Preview.blend file, or None if not found.
    """
    import os

    # Get the addon's root directory
    addon_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # Check the new location (in misc folder)
    new_path = os.path.join(addon_dir, "misc", "Preview.blend")
    if os.path.exists(new_path):
        return new_path

    # Check the old location (in addon root)
    old_path = os.path.join(addon_dir, "Preview.blend")
    if os.path.exists(old_path):
        return old_path

    # Not found in either location
    return None

def ensure_addon_structure():
    """
    Ensure the addon has the necessary folder structure.
    Creates the misc folder if it doesn't exist and moves Preview.blend there if needed.
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

    # Check if Preview.blend is in the old location and needs to be moved
    old_preview_path = os.path.join(addon_dir, "Preview.blend")
    new_preview_path = os.path.join(misc_dir, "Preview.blend")

    if os.path.exists(old_preview_path) and not os.path.exists(new_preview_path):
        try:
            # Move the file to the new location
            shutil.move(old_preview_path, new_preview_path)
            print(f"Moved Preview.blend to {misc_dir}")
        except Exception as e:
            print(f"Error moving Preview.blend: {str(e)}")
            # If we couldn't move it, at least try to copy it
            try:
                shutil.copy2(old_preview_path, new_preview_path)
                print(f"Copied Preview.blend to {misc_dir}")
            except Exception as e:
                print(f"Error copying Preview.blend: {str(e)}")

    # Make sure the icons directory has the essential icons
    cycles_icon_path = os.path.join(icons_dir, "cycles_icon.png")
    octane_icon_path = os.path.join(icons_dir, "octane_icon.png")
    vray_icon_path = os.path.join(icons_dir, "vray_icon.png")

    # We can't create the icons here if they don't exist,
    # but we can at least make sure the directory structure is ready for them
    if not os.path.exists(cycles_icon_path):
        print(f"Warning: cycles_icon.png not found at {cycles_icon_path}")

    if not os.path.exists(octane_icon_path):
        print(f"Warning: octane_icon.png not found at {octane_icon_path}")

    if not os.path.exists(vray_icon_path):
        print(f"Warning: vray_icon.png not found at {vray_icon_path}")

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
    addon_name = "Quick-HDRI-Controls-main"
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
    
