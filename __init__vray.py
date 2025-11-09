import urllib.request
import zipfile
import shutil
import tempfile
from datetime import datetime
from math import radians, degrees, pi
import time
import bpy
import subprocess
import re
import os
import sys
import json
import glob
import bpy.utils.previews
from bpy.types import (Panel, Operator, AddonPreferences, PropertyGroup)
from bpy.props import (FloatProperty, StringProperty, EnumProperty,
                      CollectionProperty, PointerProperty, IntProperty,
                      BoolProperty, FloatVectorProperty)
from bpy.app.handlers import persistent
import numpy as np
bl_info = {
    "name": "Quick HDRI Controls (V-Ray)",
    "author": "Dave Nectariad Rome",
    "version": (2, 9, 4),
    "blender": (4, 0, 0),
    "location": "3D Viewport > Header",
    "warning": "Alpha Version (in-development)",
    "description": "Quickly adjust world HDRI rotation and selection",
    "category": "3D View",
}
addon_keymaps = []
original_paths = {}

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

def show_changelog_dialog():
    """Show the changelog dialog if an update was just installed"""
    try:
        addon_dir = os.path.dirname(os.path.realpath(__file__))
        changelog_path = os.path.join(addon_dir, "CHANGELOG.md")

        if os.path.exists(changelog_path):
            # Get current version from bl_info
            current_version = bl_info['version']

            # Parse changelog for current version
            changes = parse_changelog(changelog_path, current_version)

            if changes:
                # Store changes in window manager property
                bpy.context.window_manager.hdri_changelog = changes

                # Show dialog
                bpy.ops.world.show_hdri_changelog('INVOKE_DEFAULT')

    except Exception as e:
        print(f"Error showing changelog: {str(e)}")

def get_icons():
    """Get or create the icons collection"""
    if not hasattr(get_icons, "icon_collection"):
        pcoll = bpy.utils.previews.new()
        get_icons.icon_collection = pcoll
    return get_icons.icon_collection
def get_hdri_previews():
    """Get or create the preview collection"""
    if not hasattr(get_hdri_previews, "preview_collection"):
        pcoll = bpy.utils.previews.new()
        get_hdri_previews.preview_collection = pcoll
        get_hdri_previews.cached_dir = None
        get_hdri_previews.cached_items = []
        get_hdri_previews.last_update_time = time.time()
    return get_hdri_previews.preview_collection

def generate_previews(self, context):
    """Generate preview items for HDRIs in current folder"""
    current_time = time.time()

    if not hasattr(context.scene, "hdri_settings"):
        return [('', 'None', '', 0, 0)]

    preferences = context.preferences.addons[__name__].preferences
    base_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))
    current_dir = context.scene.hdri_settings.current_folder or base_dir
    current_dir = os.path.normpath(os.path.abspath(current_dir))

    # Get search query and normalize it
    search_query = context.scene.hdri_settings.search_query.lower().strip()

    # Check if we can use cached results - ADD THIS BLOCK HERE
    # Only regenerate if directory or search query has changed, or if throttling timer allows
    if (hasattr(get_hdri_previews, "cached_dir") and get_hdri_previews.cached_dir == current_dir and
        hasattr(get_hdri_previews, "cached_query") and get_hdri_previews.cached_query == search_query and
        hasattr(get_hdri_previews, "cached_items") and get_hdri_previews.cached_items):
        # Within throttling time window, use cache
        if hasattr(generate_previews, "last_update_time") and current_time - generate_previews.last_update_time < 0.5:
            return get_hdri_previews.cached_items

    pcoll = get_hdri_previews()
    enum_items = [('', 'None', '', 0, 0)]

    # Get enabled extensions
    extensions = []
    if preferences.use_hdr: extensions.append('.hdr')
    if preferences.use_exr: extensions.append('.exr')

    if not extensions:
        return enum_items

    # Determine search directory based on search query
    search_dir = base_dir if search_query else current_dir
    search_terms = search_query.replace('_', ' ').replace('-', ' ').split()

    try:
        # Get all HDRI files
        hdri_files = []
        for root, dirs, files in os.walk(search_dir):
            if 'proxies' in dirs:  # Skip proxy folders
                dirs.remove('proxies')

            for filename in files:
                if filename.lower().endswith(tuple(extensions)):
                    full_path = os.path.join(root, filename)
                    # Store the original path in our tracking
                    original_paths[os.path.basename(filename)] = full_path
                    hdri_files.append((filename, full_path))

        # Apply search filter if needed
        if search_terms:
            filtered_files = []
            for filename, full_path in hdri_files:
                rel_path = os.path.relpath(full_path, base_dir)
                searchable_text = f"{rel_path} {filename}".lower()
                searchable_text = searchable_text.replace('_', ' ').replace('-', ' ')

                if all(term in searchable_text for term in search_terms):
                    filtered_files.append((filename, full_path))
            hdri_files = filtered_files

        # Process thumbnails and create enum items
        for idx, (filename, hdri_path) in enumerate(hdri_files, 1):
            try:
                base_name = os.path.splitext(filename)[0]
                thumb_path = os.path.join(os.path.dirname(hdri_path), f"{base_name}_thumb.png")

                # Load thumbnail
                if hdri_path not in pcoll:
                    thumb = pcoll.load(hdri_path, thumb_path if os.path.exists(thumb_path) else hdri_path, 'IMAGE')
                else:
                    thumb = pcoll[hdri_path]

                if thumb and thumb.icon_id:
                    # Store the original path when creating enum items
                    original_paths[hdri_path] = hdri_path

                    # Create enum item with original path as identifier
                    enum_items.append((
                        hdri_path,  # Always use original path as identifier
                        base_name,
                        "HDRI file",
                        thumb.icon_id,
                        idx
                    ))

            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue

    except Exception as e:
        print(f"Error scanning directory: {str(e)}")

    # Update the cache variables - ADD THIS BLOCK HERE
    get_hdri_previews.cached_dir = current_dir
    get_hdri_previews.cached_query = search_query
    get_hdri_previews.cached_items = enum_items
    generate_previews.last_update_time = current_time

    return enum_items


def refresh_previews(context, new_directory=None):
    """Refresh the preview collection when settings change"""
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
        enum_items = generate_previews(None, context)
        if len(enum_items) > 1:
            current_settings.hdri_preview = enum_items[1][0]

        for area in context.screen.areas:
            area.tag_redraw()
def get_folders(context):
    """Get list of subfolders in HDRI directory"""
    preferences = context.preferences.addons[__name__].preferences
    base_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))
    # Ensure current_folder is within base directory
    if not context.scene.hdri_settings.current_folder:
        context.scene.hdri_settings.current_folder = base_dir
    current_dir = os.path.normpath(os.path.abspath(context.scene.hdri_settings.current_folder))
    # If somehow outside base directory, reset to base
    try:
        rel_path = os.path.relpath(current_dir, base_dir)
        if rel_path.startswith('..'):
            current_dir = base_dir
            context.scene.hdri_settings.current_folder = base_dir
    except ValueError:
        current_dir = base_dir
        context.scene.hdri_settings.current_folder = base_dir
    items = []
    # Only show parent folder button if we're in a subfolder AND not directly in base_dir
    if current_dir != base_dir:
        parent_dir = os.path.dirname(current_dir)
        # Only add parent navigation if it wouldn't take us outside base_dir
        if os.path.normpath(parent_dir) == os.path.normpath(base_dir) or \
           os.path.normpath(parent_dir).startswith(os.path.normpath(base_dir)):
            items.append(("parent", "", "Go to parent folder", 'FILE_PARENT', 0))
    # Add subfolders, but exclude the 'proxies' folder
    try:
        if os.path.exists(current_dir):
            for idx, dirname in enumerate(sorted(os.listdir(current_dir)), start=len(items)):
                full_path = os.path.join(current_dir, dirname)
                if os.path.isdir(full_path) and dirname != 'proxies':
                    # Verify subfolder is within base directory
                    try:
                        rel_path = os.path.relpath(full_path, base_dir)
                        if not rel_path.startswith('..'):
                            items.append((full_path, dirname, "Enter folder", 'FILE_FOLDER', idx))
                    except ValueError:
                        continue
    except Exception as e:
        print(f"Error reading directory {current_dir}: {str(e)}")
    return items
def update_background_strength(self, context):
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                if obj.data and obj.data.node_tree:
                    light_dome = obj.data.node_tree.nodes.get("Light Dome")
                    if light_dome:
                        # Use the correct input name 'Intensity'
                        light_dome.inputs['Intensity'].value = self.background_strength  # Changed to .value
                        # Force viewport update
                        light_dome.update()  # Added node update
                        break

def check_for_update_on_startup():
    """Check for updates on Blender startup if enabled in preferences."""
    preferences = bpy.context.preferences.addons[__name__].preferences
    if not preferences.enable_auto_update_check:
        return  # Exit if auto-update is not enabled
    current_version = bl_info['version']
    online_version = None
    try:
        # Fetch online version from GitHub
        version_url = "https://raw.githubusercontent.com/mdreece/Quick-HDRI-Controls/main/__init__vray.py"
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
def extract_addon_zips():
    """Extract any ZIP files found in the addon directory and clean up."""
    addon_dir = os.path.dirname(os.path.realpath(__file__))

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
        # Use timer to ensure Blender UI is ready
        bpy.app.timers.register(show_changelog_dialog, first_interval=1.0)
@persistent
def load_handler(dummy):
    """Ensure keyboard shortcuts are properly set after file load"""
    # Clear existing keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # Re-add keymap with current preferences
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
        preferences = bpy.context.preferences.addons[__name__].preferences
        is_mac = sys.platform == 'darwin'

        kmi = km.keymap_items.new(
            HDRI_OT_popup_controls.bl_idname,
            type=preferences.popup_key,
            value='PRESS',
            oskey=preferences.popup_ctrl if is_mac else False,
            ctrl=preferences.popup_ctrl if not is_mac else False,
            shift=preferences.popup_shift,
            alt=preferences.popup_alt
        )
        addon_keymaps.append((km, kmi))
def ensure_vray_setup():
    """Ensure V-Ray collection exists and return the dome light"""
    scene = bpy.context.scene

    # Check if V-Ray collection already exists
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")

    if not vray_collection:
        # Append V-Ray collection from support file
        addon_dir = os.path.dirname(os.path.realpath(__file__))
        vray_support_file = os.path.join(addon_dir, "misc", "vray", "vray_support.blend")

        # Ensure the support file exists
        if not os.path.exists(vray_support_file):
            raise FileNotFoundError(f"V-Ray support file not found: {vray_support_file}")

        with bpy.data.libraries.load(vray_support_file, link=False) as (data_from, data_to):
            data_to.collections = ["vRay HDRI Controls"]

        # Link collection to scene if the collection was successfully loaded
        if data_to.collections and data_to.collections[0]:
            vray_collection = data_to.collections[0]
            scene.collection.children.link(vray_collection)
        else:
            raise RuntimeError("Failed to load V-Ray HDRI Controls collection")

    # Get VRayDomeLight
    dome_light = None
    for obj in vray_collection.objects:
        if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
            dome_light = obj
            break

    if not dome_light:
        raise Exception("VRayDomeLight not found in collection")

    return dome_light

def cleanup_hdri_proxies():
    """Clean up old proxy files"""
    proxy_dir = os.path.join(tempfile.gettempdir(), 'hdri_proxies')
    if os.path.exists(proxy_dir):
        try:
            # Remove files older than 24 hours
            current_time = time.time()
            for file in os.listdir(proxy_dir):
                file_path = os.path.join(proxy_dir, file)
                if os.path.isfile(file_path):
                    if current_time - os.path.getmtime(file_path) > 86400:  # 24 hours
                        os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning proxies: {str(e)}")
def has_hdri_files(context):
    """Check if current folder has any supported HDRI files"""
    preferences = context.preferences.addons[__name__].preferences
    current_dir = context.scene.hdri_settings.current_folder or preferences.hdri_directory

    if not current_dir or not os.path.exists(current_dir):
        return False

    # Get enabled file types
    extensions = set()
    if preferences.use_hdr:
        extensions.add('.hdr')
    if preferences.use_exr:
        extensions.add('.exr')
    if preferences.use_png:
        extensions.add('.png')
    if preferences.use_jpg:
        extensions.update(('.jpg', '.jpeg'))

    # Check if any files with supported extensions exist
    for fn in os.listdir(current_dir):
        if fn.lower().endswith(tuple(extensions)):
            return True

    return False
def has_active_hdri(context):
    """Check if there is an active HDRI loaded in V-Ray"""
    # Find the VRayDomeLight
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                if obj.data and obj.data.node_tree:
                    bitmap_node = obj.data.node_tree.nodes.get("V-Ray Bitmap")
                    if bitmap_node and hasattr(bitmap_node, 'BitmapBuffer') and bitmap_node.BitmapBuffer and bitmap_node.BitmapBuffer.file:
                        return True
    return False

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
def cleanup_preview_cache():
    """Clear the preview cache when switching folders"""
    for attr in dir(generate_previews):
        if attr.startswith('preview_cache_'):
            delattr(generate_previews, attr)

def get_hdri_metadata(image):
    """Extract metadata from HDRI image"""
    if not image:
        return None

    metadata = {
        'filename': os.path.basename(image.filepath) if image.filepath else image.name,
        'resolution': f"{image.size[0]}x{image.size[1]}",
        'color_space': image.colorspace_settings.name,
        'file_format': image.file_format,
        'channels': image.channels,
        'file_size': os.path.getsize(image.filepath) if image.filepath else 0,
        'filepath': image.filepath,
    }

    # Convert file size to human-readable format
    if metadata['file_size']:
        size_bytes = metadata['file_size']
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                metadata['file_size'] = f"{size_bytes:.1f} {unit}"
                break
            size_bytes /= 1024

    return metadata

class HDRI_OT_generate_proxies(Operator):
    bl_idname = "world.generate_hdri_proxies"
    bl_label = "Generate HDRI Proxies"
    bl_description = "Generate proxies for selected folder"

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()

        preferences = context.preferences.addons[__name__].preferences
        preferences.is_proxy_generating = False

        self.report({'INFO'}, "Proxy generation cancelled")

    def initialize_stats(self, context):
        preferences = context.preferences.addons[__name__].preferences
        preferences.proxy_stats_total = len(self._hdri_files)
        preferences.proxy_stats_completed = 0
        preferences.proxy_stats_failed = 0
        preferences.proxy_stats_time = 0.0
        preferences.proxy_stats_current_file = ""
        preferences.is_proxy_generating = True
        self._start_time = datetime.now()

    def update_stats(self, context, success, current_file):
        preferences = context.preferences.addons[__name__].preferences
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
        preferences = context.preferences.addons[__name__].preferences

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
        preferences = context.preferences.addons[__name__].preferences

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
        preferences = context.preferences.addons[__name__].preferences
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
        preferences = context.preferences.addons[__name__].preferences
        target_resolution = preferences.proxy_generation_resolution

        try:
            proxy_path = create_hdri_proxy(hdri_path, target_resolution)
            return proxy_path is not None
        except Exception as e:
            print(f"Error generating proxy for {hdri_path}: {str(e)}")
            return False

def detect_hdri_resolution(filepath):
    """
    Detect HDRI resolution from filename or metadata.
    Returns tuple of (original_resolution, available_resolutions)
    """
    import os
    import re

    # Standard resolutions in pixels (width)
    STANDARD_RESOLUTIONS = {
        1024: "1k",
        2048: "2k",
        4096: "4k",
        6144: "6k",
        8192: "8k",
        16384: "16k"
    }

    # Resolution patterns in filenames
    RESOLUTION_PATTERNS = [
        r'[\-_](\d+)[kK]',  # Match _2k, -2K, etc.
        r'[\-_](\d+)p',     # Match _2048p, etc.
        r'[\-_](\d+)x\d+',  # Match _2048x1024, etc.
        r'(\d+)[kK]',       # Match 2k, 2K without separator
    ]

    def get_nearest_standard_resolution(pixels):
        """Convert pixel width to nearest standard resolution"""
        nearest = min(STANDARD_RESOLUTIONS.keys(),
                     key=lambda x: abs(x - pixels))
        return STANDARD_RESOLUTIONS[nearest]

    # First try to detect from filename
    filename = os.path.basename(filepath)
    base_name = os.path.splitext(filename)[0]

    for pattern in RESOLUTION_PATTERNS:
        match = re.search(pattern, base_name)
        if match:
            # Convert matched value to pixels
            value = match.group(1)
            if value.lower().endswith('k'):
                pixels = int(float(value[:-1]) * 1024)
            else:
                pixels = int(value)

            detected_res = get_nearest_standard_resolution(pixels)

            # Get base filename without resolution
            clean_name = re.sub(pattern, '', base_name)

            # Look for other available resolutions
            dir_path = os.path.dirname(filepath)
            available_res = []

            for f in os.listdir(dir_path):
                if f.startswith(clean_name) and f.endswith(os.path.splitext(filename)[1]):
                    for pat in RESOLUTION_PATTERNS:
                        res_match = re.search(pat, f)
                        if res_match:
                            res_value = res_match.group(1)
                            if res_value.lower().endswith('k'):
                                res_pixels = int(float(res_value[:-1]) * 1024)
                            else:
                                res_pixels = int(res_value)
                            available_res.append(get_nearest_standard_resolution(res_pixels))
                            break

            return detected_res, list(set(available_res))

    # If no resolution in filename, try to get from image metadata
    try:
        img = bpy.data.images.load(filepath, check_existing=True)
        width = img.size[0]
        detected_res = get_nearest_standard_resolution(width)
        # Clean up if image was newly loaded
        if img.users == 0:
            bpy.data.images.remove(img)
        return detected_res, [detected_res]
    except:
        return None, []

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

@persistent
def reload_original_for_render(dummy):
    """Handler to replace proxy with full-quality HDRI before rendering"""
    context = bpy.context
    settings = context.scene.hdri_settings

    # Only swap for 'VIEWPORT' proxy mode
    if settings.proxy_mode == 'VIEWPORT':
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if vray_collection:
            for obj in vray_collection.objects:
                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                    node_tree = obj.data.node_tree
                    bitmap_node = node_tree.nodes.get("V-Ray Bitmap")

                    if bitmap_node and bitmap_node.BitmapBuffer:
                        current_file = bitmap_node.BitmapBuffer.file
                        original_path = original_paths.get(os.path.basename(current_file), current_file)

                        # Replace proxy with original high-quality HDRI
                        bitmap_node.BitmapBuffer.file = original_path
                        print("V-Ray: Swapped to full-quality HDRI for rendering")
                    break

@persistent
def reset_proxy_after_render(dummy):
    """Handler to reset to proxy after render cancellation"""
    context = bpy.context
    settings = context.scene.hdri_settings

    # Only swap back for 'VIEWPORT' proxy mode
    if settings.proxy_mode == 'VIEWPORT':
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if vray_collection:
            for obj in vray_collection.objects:
                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                    node_tree = obj.data.node_tree
                    bitmap_node = node_tree.nodes.get("V-Ray Bitmap")

                    if bitmap_node and bitmap_node.BitmapBuffer:
                        current_file = bitmap_node.BitmapBuffer.file
                        original_path = original_paths.get(os.path.basename(current_file), current_file)

                        # Create and load proxy
                        proxy_path = create_hdri_proxy(original_path, settings.proxy_resolution)
                        if proxy_path:
                            bitmap_node.BitmapBuffer.file = proxy_path
                            print("V-Ray: Render cancelled, swapped back to proxy")
                    break

@persistent
def reset_proxy_after_render_complete(dummy):
    """Handler to reset to proxy after rendering completes"""
    context = bpy.context
    settings = context.scene.hdri_settings

    # Only swap back for 'VIEWPORT' proxy mode
    if settings.proxy_mode == 'VIEWPORT':
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if vray_collection:
            for obj in vray_collection.objects:
                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                    node_tree = obj.data.node_tree
                    bitmap_node = node_tree.nodes.get("V-Ray Bitmap")

                    if bitmap_node and bitmap_node.BitmapBuffer:
                        current_file = bitmap_node.BitmapBuffer.file
                        original_path = original_paths.get(os.path.basename(current_file), current_file)

                        # Create and load proxy
                        proxy_path = create_hdri_proxy(original_path, settings.proxy_resolution)
                        if proxy_path:
                            bitmap_node.BitmapBuffer.file = proxy_path
                            print("V-Ray: Render complete, swapped back to proxy")
                    break

def update_hdri_proxy(self, context):
    # Determine the appropriate node based on render engine
    if context.scene.render.engine == 'CYCLES':
        # Cycles uses world node tree
        world = context.scene.world
        if not world or not world.use_nodes:
            return

        env_tex = None
        background = None
        current_image = None
        for node in world.node_tree.nodes:
            if node.type == 'TEX_ENVIRONMENT':
                env_tex = node
                current_image = node.image
            elif node.type == 'BACKGROUND':
                background = node

        if not env_tex or not background or not current_image:
            return

        # Determine the original path
        current_path = current_image.filepath
        original_path = original_paths.get(current_image.name, current_path)

        # Load image logic
        resolution = context.scene.hdri_settings.proxy_resolution
        if resolution == 'ORIGINAL':
            # Clear existing image and remove if no users
            if current_image.users == 0:
                bpy.data.images.remove(current_image)

            # Load original file
            img = bpy.data.images.load(original_path, check_existing=True)
            env_tex.image = img

            # Clean up original paths
            if current_image.name in original_paths:
                del original_paths[current_image.name]
        else:
            # Create and load proxy
            proxy_path = create_hdri_proxy(original_path, resolution)
            proxy_img = bpy.data.images.load(proxy_path, check_existing=True)

            # Store original path for tracking
            original_paths[proxy_img.name] = original_path

            env_tex.image = proxy_img

        # Update strength
        background.inputs['Strength'].default_value = context.scene.hdri_settings.background_strength

    elif context.scene.render.engine == 'VRAY_RENDER_RT':
        # V-Ray uses node tree in VRayDomeLight
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if not vray_collection:
            return

        dome_light = None
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                dome_light = obj
                break

        if not dome_light:
            return

        node_tree = dome_light.data.node_tree
        bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
        light_dome_node = node_tree.nodes.get("Light Dome")

        if not bitmap_node or not light_dome_node:
            return

        # Get current file path
        current_file = bitmap_node.BitmapBuffer.file if hasattr(bitmap_node.BitmapBuffer, 'file') else ''

        # Find the original path
        original_path = original_paths.get(os.path.basename(current_file), current_file)

        # Load image logic
        resolution = context.scene.hdri_settings.proxy_resolution
        if resolution == 'ORIGINAL':
            # Load original file
            bitmap_node.BitmapBuffer.file = original_path

            # Clean up original paths tracking
            if os.path.basename(current_file) in original_paths:
                del original_paths[os.path.basename(current_file)]
        else:
            # Create and load proxy
            proxy_path = create_hdri_proxy(original_path, resolution)
            if proxy_path:
                # Update original paths tracking
                original_paths[os.path.basename(proxy_path)] = original_path
                bitmap_node.BitmapBuffer.file = proxy_path
            else:
                # Fallback to original if proxy creation fails
                bitmap_node.BitmapBuffer.file = original_path

        # Update strength
        light_dome_node.inputs['Intensity'].value = context.scene.hdri_settings.background_strength

        # Force node update
        if hasattr(bitmap_node, 'socket_value_update'):
            bitmap_node.socket_value_update(context)

    # Force viewport update
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

class HDRI_OT_clear_proxy_stats(Operator):
    bl_idname = "world.clear_proxy_stats"
    bl_label = "Clear Proxy Generation Stats"
    bl_description = "Clear proxy generation statistics"

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        preferences.proxy_stats_total = 0
        preferences.proxy_stats_completed = 0
        preferences.proxy_stats_failed = 0
        preferences.proxy_stats_time = 0.0
        preferences.proxy_stats_current_file = ""
        preferences.is_proxy_generating = False
        return {'FINISHED'}

class HDRI_OT_cleanup_hdri_proxies(Operator):
    bl_idname = "world.cleanup_hdri_proxies"
    bl_label = "Clean Proxy Cache"
    bl_description = "Remove old proxy files from cache"
    def execute(self, context):
        try:
            preferences = context.preferences.addons[__name__].preferences
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

class HDRI_OT_cleanup_unused(Operator):
    bl_idname = "world.cleanup_unused_hdri"
    bl_label = "Cleanup Unused HDRIs"
    bl_description = "Remove unused HDRI images from memory"

    def execute(self, context):
        try:
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

class HDRI_OT_popup_controls(Operator):
    bl_idname = "world.hdri_popup_controls"
    bl_label = "HDRI Quick Controls"
    bl_description = "Show HDRI controls at cursor position"
    bl_options = {'REGISTER'}
    def draw(self, context):
        layout = self.layout
        # Use the panel's draw method for consistency
        HDRI_PT_controls.draw(self, context)
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = context.preferences.addons[__name__].preferences
        wm = context.window_manager
        return wm.invoke_popup(self, width=prefs.ui_scale * 20)
class HDRI_OT_check_updates(Operator):
    bl_idname = "world.check_hdri_updates"
    bl_label = "Check for Updates"
    bl_description = "Check if a new version is available on GitHub"
    def get_online_version(self):
        """Fetch version info from GitHub"""
        try:
            version_url = "https://raw.githubusercontent.com/mdreece/Quick-HDRI-Controls/main/__init__vray.py"
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
        current_version = bl_info['version']
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

def switch_to_preferred_render_engine(addon_path):
    """Switch to the user's preferred render engine after update"""
    import os
    import shutil

    try:
        # Read the preferences to determine the render engine
        preferences_path = os.path.join(addon_path, "preferences.json")

        # If preferences file exists, read the render engine
        if os.path.exists(preferences_path):
            import json
            with open(preferences_path, 'r') as f:
                preferences = json.load(f)
                render_engine = preferences.get('render_engine', 'CYCLES')
        else:
            # Default to Cycles if no preferences found
            render_engine = 'CYCLES'

        # Paths for different engine scripts
        cycles_script = os.path.join(addon_path, "__init__cycles.py")
        octane_script = os.path.join(addon_path, "__init__octane.py")
        vray_script = os.path.join(addon_path, "__init__vray.py")
        current_script = os.path.join(addon_path, "__init__.py")

        # Ensure required engine scripts exist based on target engine
        if render_engine == 'OCTANE' and not os.path.exists(octane_script):
            return
        elif render_engine == 'VRAY_RENDER_RT' and not os.path.exists(vray_script):
            return
        elif render_engine == 'CYCLES' and not os.path.exists(cycles_script):
            return

        # Switch based on preferred render engine
        if render_engine == 'OCTANE':
            # Backup current script based on current engine
            if not os.path.exists(cycles_script):
                shutil.copy2(current_script, cycles_script)
            # Replace with Octane script
            shutil.copy2(octane_script, current_script)

        elif render_engine == 'VRAY_RENDER_RT':
            # Backup current script based on current engine
            if not os.path.exists(cycles_script):
                shutil.copy2(current_script, cycles_script)
            # Replace with V-Ray script
            shutil.copy2(vray_script, current_script)

        else:  # Default to Cycles
            # Backup current script as appropriate version
            if not os.path.exists(octane_script):
                shutil.copy2(current_script, octane_script)
            if not os.path.exists(vray_script):
                shutil.copy2(current_script, vray_script)
            # Replace with Cycles script
            shutil.copy2(cycles_script, current_script)

    except Exception as e:
        print(f"Error switching render engine: {str(e)}")

class HDRI_OT_cleanup_backups(Operator):
    bl_idname = "world.cleanup_hdri_backups"
    bl_label = "Clean Backup Files"
    bl_description = "Remove all backup files for the addon"

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        addon_dir = os.path.dirname(__file__)
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

class HDRI_OT_download_update(Operator):
    bl_idname = "world.download_hdri_update"
    bl_label = "Download Update"
    bl_description = "Download and install the latest version"

    def invoke(self, context, event):
        # Show confirmation dialog
        return context.window_manager.invoke_confirm(
            self,
            event,
            message="Download and install the latest update? Blender will need to restart afterward."
        )

    def backup_current_version(self, addon_path):
        """Create a backup of the current addon version, with configurable settings"""
        preferences = bpy.context.preferences.addons[__name__].preferences

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

        # Generate backup filename with version and timestamp
        version = ".".join(str(x) for x in bl_info['version'])
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

    def execute(self, context):
        try:
            addon_path = os.path.dirname(os.path.realpath(__file__))

            # Backup current render engine preference
            preferences = context.preferences.addons[__name__].preferences

            # Save current render engine preference
            preferences_path = os.path.join(addon_path, "preferences.json")
            try:
                import json
                with open(preferences_path, 'w') as f:
                    json.dump({
                        'render_engine': preferences.render_engine
                    }, f)
            except Exception as e:
                print(f"Could not save render engine preference: {str(e)}")

            # Backup the current version before updating
            if not self.backup_current_version(addon_path):
                self.report({'ERROR'}, "Failed to create backup before update")
                return {'CANCELLED'}

            # Rest of the existing update code...
            update_url = "https://github.com/mdreece/Quick-HDRI-Controls/archive/main.zip"
            req = urllib.request.Request(
                update_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            self.report({'INFO'}, "Downloading update...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
                with urllib.request.urlopen(req) as response:
                    temp_zip.write(response.read())
                temp_zip_path = temp_zip.name

            self.report({'INFO'}, "Extracting update...")
            temp_dir = tempfile.mkdtemp()

            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            extracted_folder = os.path.join(temp_dir, "Quick-HDRI-Controls-main")

            if not os.path.exists(extracted_folder):
                self.report({'ERROR'}, f"Could not find extracted folder at {extracted_folder}")
                return {'CANCELLED'}

            for root, dirs, files in os.walk(extracted_folder):
                rel_path = os.path.relpath(root, extracted_folder)
                dest_path = os.path.join(addon_path, rel_path)

                os.makedirs(dest_path, exist_ok=True)

                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dest_path, file)
                    try:
                        shutil.copy2(src_file, dst_file)
                    except Exception as e:
                        self.report({'ERROR'}, f"Failed to copy {file}: {str(e)}")

            try:
                os.remove(temp_zip_path)
                shutil.rmtree(temp_dir)
            except Exception as e:
                self.report({'WARNING'}, f"Failed to clean up temporary files: {str(e)}")

            # Switch to the preferred render engine
            switch_to_preferred_render_engine(addon_path)

            self.report({'INFO'}, "Update complete! Please restart Blender to apply changes.")

            # Delay the operator invocation until all classes are registered
            def invoke_restart_prompt():
                bpy.ops.world.restart_prompt('INVOKE_DEFAULT')
            bpy.app.timers.register(invoke_restart_prompt)
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Update failed: {str(e)}")
            return {'CANCELLED'}

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

class HDRI_OT_change_folder(Operator):
    bl_idname = "world.change_hdri_folder"
    bl_label = "Change Folder"
    bl_description = "Change current HDRI folder"

    folder_path: StringProperty()

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        base_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))
        hdri_settings = context.scene.hdri_settings

        # Handle parent directory navigation
        if self.folder_path == "parent":
            current = os.path.normpath(os.path.abspath(hdri_settings.current_folder))
            new_path = os.path.dirname(current)

            # Only allow if new path is base_dir or within it
            if not (os.path.normpath(new_path) == os.path.normpath(base_dir) or \
                   os.path.normpath(new_path).startswith(os.path.normpath(base_dir))):
                self.report({'WARNING'}, "Cannot navigate above HDRI directory")
                return {'CANCELLED'}

            self.folder_path = new_path

        # Normalize target path
        target_path = os.path.normpath(os.path.abspath(self.folder_path))

        # Verify target is base_dir or within it
        if not (os.path.normpath(target_path) == os.path.normpath(base_dir) or \
               os.path.normpath(target_path).startswith(os.path.normpath(base_dir))):
            self.report({'WARNING'}, "Cannot navigate outside HDRI directory")
            return {'CANCELLED'}

        # Update current folder
        hdri_settings.current_folder = target_path

        # Reset folder page to 0 when changing directories
        hdri_settings.folder_page = 0

        # Clear preview cache for folder change
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
        preferences = context.preferences.addons[__name__].preferences

        # Get total number of folders and calculate max pages
        folders = get_folders(context)
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
      #hello fello helmo
class HDRI_OT_quick_rotate(Operator):
    bl_idname = "world.quick_rotate_hdri"
    bl_label = "HDRI Rotation"
    bl_description = "Adjust HDRI rotation"

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

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences

        for obj in bpy.data.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                if self.direction == -99:  # Reset
                    obj.rotation_euler[self.axis] = 0
                else:  # Regular rotation
                    increment_in_radians = radians(preferences.rotation_increment)
                    obj.rotation_euler[self.axis] += (self.direction * increment_in_radians)
                break

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
        preferences = context.preferences.addons[__name__].preferences
        hdri_settings = context.scene.hdri_settings

        # Try to set the view transform but don't error if it's not available
        try:
            # Check if 'AgX' is available in the view transform options
            if 'AgX' in [item.identifier for item in context.scene.view_settings.bl_rna.properties['view_transform'].enum_items]:
                context.scene.view_settings.view_transform = 'AgX'
                self.report({'INFO'}, "View transform set to AgX")
            # If not available, we'll leave it as is
        except Exception as e:
            self.report({'WARNING'}, f"Could not set color transform: {str(e)}")

        # Set scene color management defaults
        context.scene.display_settings.display_device = 'sRGB'
        context.scene.sequencer_colorspace_settings.name = 'sRGB'

        # Check render engine and switch if needed
        if context.scene.render.engine != 'VRAY_RENDER_RT':
            context.scene.render.engine = 'VRAY_RENDER_RT'
            self.report({'INFO'}, "Render engine switched to V-Ray")

        # Verify HDRI directory exists and is accessible
        if not preferences.hdri_directory or not os.path.exists(preferences.hdri_directory):
            self.report({'ERROR'}, "HDRI directory not found. Please select a valid directory in preferences.")
            bpy.ops.preferences.addon_show(module=__name__)
            return {'CANCELLED'}

        # If current folder is not set or doesn't exist, reset to HDRI directory
        if not hdri_settings.current_folder or not os.path.exists(hdri_settings.current_folder):
            hdri_settings.current_folder = preferences.hdri_directory

        # Setup V-Ray collection and nodes
        try:
            dome_light = ensure_vray_setup()

            # Check if there are any HDRIs in the current directory
            if not has_hdri_files(context):
                self.report({'WARNING'}, "(Only shows if no direct HDRIs are preset - Access folders)")
                return {'FINISHED'}

            # Generate previews for the current directory
            enum_items = generate_previews(self, context)

            # If we have HDRIs, set the preview to the first one
            if len(enum_items) > 1:
                hdri_settings.hdri_preview = enum_items[1][0]

            # Force redraw of UI
            for area in context.screen.areas:
                area.tag_redraw()

            self.report({'INFO'}, "HDRI system initialized successfully")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to setup HDRI system: {str(e)}")
            return {'CANCELLED'}

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
            preferences = context.preferences.addons[__name__].preferences
            setattr(preferences, self.property_name, self.directory)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

class HDRI_OT_update_shortcut(Operator):
    bl_idname = "world.update_hdri_shortcut"
    bl_label = "Update Shortcut"
    bl_description = "Apply the new keyboard shortcut"

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        preferences.update_shortcut(context)
        self.report({'INFO'}, "Shortcut updated successfully")
        return {'FINISHED'}

def find_keymap_conflicts(self, context):
    """Find all keymap items that conflict with current shortcut settings"""
    conflicts = []

    # Get current shortcut settings
    is_mac = sys.platform == 'darwin'
    current_key = self.popup_key
    current_ctrl = self.popup_ctrl
    current_shift = self.popup_shift
    current_alt = self.popup_alt
    current_oskey = self.popup_ctrl if is_mac else False

    # Check all keyconfig categories
    wm = context.window_manager
    keyconfigs_to_check = [
        ('Blender', wm.keyconfigs.default),
        ('Blender User', wm.keyconfigs.user),
        ('Addons', wm.keyconfigs.addon)
    ]

    for config_name, keyconfig in keyconfigs_to_check:
        if keyconfig:
            for keymap in keyconfig.keymaps:
                for kmi in keymap.keymap_items:
                    if kmi.type == current_key and \
                       kmi.ctrl == (current_ctrl if not is_mac else False) and \
                       kmi.shift == current_shift and \
                       kmi.alt == current_alt and \
                       kmi.oskey == (current_ctrl if is_mac else False) and \
                       kmi.active:  # Only check active shortcuts

                        if kmi.idname != HDRI_OT_popup_controls.bl_idname:
                            conflicts.append({
                                'config': config_name,
                                'keymap': keymap.name,
                                'name': kmi.name or kmi.idname,
                                'type': kmi.type,
                                'ctrl': kmi.ctrl,
                                'shift': kmi.shift,
                                'alt': kmi.alt,
                                'oskey': kmi.oskey
                            })

    return conflicts
class HDRI_OT_show_shortcut_conflicts(Operator):
    bl_idname = "world.show_hdri_shortcut_conflicts"
    bl_label = "Show Shortcut Conflicts"
    bl_description = "Show any conflicts with the current keyboard shortcut"

    def draw(self, context):
        layout = self.layout
        preferences = context.preferences.addons[__name__].preferences

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

class HDRISettings(PropertyGroup):
    def update_hdri_preview(self, context):
        """Automatically load HDRI when selected from preview"""
        filepath = self.hdri_preview

        # If a search query is active, only allow selection from the filtered results
        if self.search_query and filepath:
            # Check if the selected filepath is in the current filtered preview items
            enum_items = generate_previews(None, context)
            valid_paths = [item[0] for item in enum_items if item[0]]

            if filepath not in valid_paths:
                # If the selected filepath is not in the current filtered results, do nothing
                return

        # Store current state as previous
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if not vray_collection:
            return

        dome_light = None
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                dome_light = obj
                break

        if not dome_light:
            return

        node_tree = dome_light.data.node_tree
        bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
        light_dome_node = node_tree.nodes.get("Light Dome")

        if not bitmap_node or not light_dome_node:
            return

        # Store previous state - Always store the original file path, not proxy
        current_file = bitmap_node.BitmapBuffer.file if hasattr(bitmap_node.BitmapBuffer, 'file') else ''
        current_file = original_paths.get(os.path.basename(current_file), current_file)

        if current_file and current_file != filepath:
            # Store previous state using original file path
            self.previous_hdri_path = current_file
            self.previous_strength = light_dome_node.inputs['Intensity'].value
            self.previous_rotation = dome_light.rotation_euler.copy()

        # Apply rotation settings
        preferences = context.preferences.addons[__name__].preferences

        # Store current rotation if keep_rotation is enabled
        current_rotation = None
        if preferences.keep_rotation:
            current_rotation = dome_light.rotation_euler.copy()

        # Always store the original filepath in our tracking
        original_paths[os.path.basename(filepath)] = filepath

        # Load the HDRI - Use proxy if enabled
        try:
            if self.proxy_resolution != 'ORIGINAL':
                proxy_path = create_hdri_proxy(filepath, self.proxy_resolution)
                if proxy_path and os.path.exists(proxy_path):
                    # Store original path mapping before loading proxy
                    original_paths[os.path.basename(proxy_path)] = filepath
                    bitmap_node.BitmapBuffer.file = proxy_path
                else:
                    # Fallback to original if proxy creation fails
                    bitmap_node.BitmapBuffer.file = filepath
            else:
                # Load original directly
                bitmap_node.BitmapBuffer.file = filepath

            # Apply rotation based on keep_rotation setting
            if preferences.keep_rotation and current_rotation is not None:
                dome_light.rotation_euler = current_rotation
            else:
                dome_light.rotation_euler = (0, 0, 0)

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

            # Restore visibility state
            world.cycles_visibility.camera = current_visibility

    def get_original_path(filepath):
        """Get the original HDRI path from any filepath (proxy or original)"""
        if not filepath:
            return None
        # First check by full path
        original = original_paths.get(filepath)
        if original:
            return original
        # Then check by basename
        basename = os.path.basename(filepath)
        original = original_paths.get(basename)
        if original:
            return original
        # If not found in tracking, assume it's already the original
        return filepath
    # Properties
    hdri_preview: EnumProperty(
        items=generate_previews,
        name="HDRI Preview",
        description="Preview of available HDRIs",
        update=update_hdri_preview
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

    show_metadata: BoolProperty(
        name="Show Metadata",
        description="Show/Hide HDRI metadata information",
        default=False
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
        update=update_hdri_proxy  # Add this line
    )

    resolution: EnumProperty(
        name="Resolution",
        description="Select resolution for HDRI",
        items=[
            ('1K', '1K', '1K Resolution'),
            ('2K', '2K', '2K Resolution'),
            ('4K', '4K', '4K Resolution')
        ],
        default='1K'
    )
    render_device: EnumProperty(
        name="Render Device",
        description="Select the device for rendering",
        items=[
            ('CPU', 'CPU', 'Use CPU for rendering'),
            ('GPU', 'GPU', 'Use GPU for rendering'),
        ],
        default='GPU'
    )

    available_resolutions: CollectionProperty(
        type=PropertyGroup,
        name="Available Resolutions"
    )

    show_proxy_settings: BoolProperty(
        name="Show Proxy Settings",
        description="Close this tab after selection for faster performance",
    )

    previous_hdri_path: StringProperty(
        name="Previous HDRI Path",
        description="Path to the previously loaded HDRI",
        default=""
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

    def update_search_query(self, context):
        # Lock the search when text is entered
        if self.search_query.strip():
            self.search_locked = True
        # Don't unlock when clearing - that should only happen via the clear button

    search_query: StringProperty(
        name="Search HDRIs",
        description="Search HDRIs by filename",
        default="",
        update=update_search_query
    )

    def clear_hdri_search(self):
        """Clear the search query and reset preview cache"""
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

class QuickHDRIPreferences(AddonPreferences):
    bl_idname = __name__
    # Properties for auto-update and update alert
    enable_auto_update_check: BoolProperty(
        name="Enable Auto-Update Check on Startup",
        description="Automatically check for updates when Blender starts",
        default=False
    )
    update_available: BoolProperty(
        name="Update Available",
        default=False
    )
    #Show Conflicts
    show_conflicts: BoolProperty(
        name="Show Conflicts",
        description="Show keyboard shortcut conflicts",
        default=False
    )
    # Keyboard shortcut properties
    popup_key: EnumProperty(
        name="Key",
        description="Key or mouse button for the popup menu shortcut",
        items=[
            # Keyboard keys (existing)
            ('A', 'A', ''), ('B', 'B', ''), ('C', 'C', ''),
            ('D', 'D', ''), ('E', 'E', ''), ('F', 'F', ''),
            ('G', 'G', ''), ('H', 'H', ''), ('I', 'I', ''),
            ('J', 'J', ''), ('K', 'K', ''), ('L', 'L', ''),
            ('M', 'M', ''), ('N', 'N', ''), ('O', 'O', ''),
            ('P', 'P', ''), ('Q', 'Q', ''), ('R', 'R', ''),
            ('S', 'S', ''), ('T', 'T', ''), ('U', 'U', ''),
            ('V', 'V', ''), ('W', 'W', ''), ('X', 'X', ''),
            ('Y', 'Y', ''), ('Z', 'Z', ''),
            ('SPACE', 'Space', ''),
            ('LEFT_SHIFT', 'Left Shift', ''),
            ('RIGHT_SHIFT', 'Right Shift', ''),
            ('LEFT_CTRL', 'Left Control', ''),
            ('RIGHT_CTRL', 'Right Control', ''),
            ('LEFT_ALT', 'Left Alt', ''),
            ('RIGHT_ALT', 'Right Alt', ''),
            ('LEFT_COMMAND', 'Left Command', ''),
            ('RIGHT_COMMAND', 'Right Command', ''),
            ('OSKEY', 'OS Key', ''),

            # Mouse buttons (new)
            ('LEFTMOUSE', 'Left Mouse', ''),
            ('MIDDLEMOUSE', 'Middle Mouse', ''),
            ('RIGHTMOUSE', 'Right Mouse', ''),
            ('BUTTON4MOUSE', 'Mouse Button 4', ''),
            ('BUTTON5MOUSE', 'Mouse Button 5', ''),
            ('BUTTON6MOUSE', 'Mouse Button 6', ''),
            ('BUTTON7MOUSE', 'Mouse Button 7', ''),

            # Mouse wheel options
            ('WHEELUPMOUSE', 'Mouse Wheel Up', ''),
            ('WHEELDOWNMOUSE', 'Mouse Wheel Down', ''),
            ('WHEELINMOUSE', 'Mouse Wheel In', ''),
            ('WHEELOUTMOUSE', 'Mouse Wheel Out', ''),
        ],
        default='A'
    )

    popup_ctrl: BoolProperty(
        name="Control/Command",
        description="Use Command (MacOS) or Control (Windows/Linux) modifier",
        default=True
    )

    popup_shift: BoolProperty(
        name="Shift",
        description="Use Shift modifier",
        default=True
    )

    popup_alt: BoolProperty(
        name="Option/Alt",
        description="Use Option (MacOS) or Alt (Windows/Linux) modifier",
        default=False
    )
    # Directory
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
        default=10,
        min=1,
        max=30,
        subtype='PIXEL'
    )

    preview_scale: IntProperty(
        name="Preview Size",
        description="Size of HDRI preview thumbnails",
        default=8,
        min=1,
        max=20
    )

    button_scale: FloatProperty(
        name="Button Scale",
        description="Scale of UI buttons",
        default=1.0,
        min=0.5,
        max=100.0,
        step=0.05
    )

    spacing_scale: FloatProperty(
        name="Spacing Scale",
        description="Scale of UI element spacing",
        default=1.0,
        min=0.5,
        max=100.0,
        step=0.1
    )

    # Visual Settings
    use_compact_ui: BoolProperty(
        name="Compact UI",
        description="Use compact UI layout",
        default=True
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

    keep_rotation: BoolProperty(
        name="Keep Rotation When Switching HDRIs",
        description="Maintain rotation settings when switching between HDRIs",
        default=False
    )

    strength_max: FloatProperty(
        name="Max Strength",
        description="Maximum value for strength slider",
        default=100.0,
        min=1.0,
        max=100.0,
        step=0.001
    )

    rotation_increment: FloatProperty(
        name="Rotation Increment",
        description="Increment for rotation controls",
        default=45.0,
        min=0.1,
        max=360.0,
        step=0.1
    )

    show_preview_limit_settings: BoolProperty(
        name="Show Preview Limit Settings",
        description="Show or hide preview limit settings",
        default=False
    )

    preview_limit: IntProperty(
        name="Preview Limit",
        description="Maximum number of HDRI previews to load at once (0 = no limit)",
        default=0,
        min=0,
        max=9000
    )

    preview_sort: EnumProperty(
        name="Preview Sort",
        description="How to sort HDRIs when preview limit is active",
        items=[
            ('NAME', 'Name', 'Sort alphabetically by name'),
            ('DATE', 'Date', 'Sort by most recently modified'),
            ('SIZE', 'Size', 'Sort by file size')
        ],
        default='NAME'
    )

    hdri_directory: StringProperty(
        name="HDRI Directory",
        subtype='DIR_PATH',
        description="Directory containing HDRI files",
        default="",
        update=lambda self, context: refresh_previews(context, self.hdri_directory)
    )

    preview_resolution: IntProperty(
        name="Resolution Percentage",
        description="Percentage of base resolution (1024x768)",
        default=100,
        min=10,
        max=200,
        subtype='PERCENTAGE'
    )
    preview_generation_type: EnumProperty(
        name="Preview Generation Type",
        description="",
        items=[
            ('SINGLE', 'Single HDRI', 'Generate preview for a single HDRI'),
            ('MULTIPLE', 'Multiple HDRIs', 'Generate previews for all HDRIs in a folder'),
            ('FULL_BATCH', 'Full Batch', 'Process all HDRIs in directory structure')
        ],
        default='SINGLE'
    )
    preview_single_file: StringProperty(
        name="HDRI File",
        description="Single HDRI file to generate preview for",
        subtype='FILE_PATH'
    )
    preview_multiple_folder: StringProperty(
        name="HDRI Folder",
        description="Folder containing HDRIs to generate previews for",
        subtype='DIR_PATH'
    )

    preview_samples: IntProperty(
        name="Render Samples",
        description="Number of samples for preview renders",
        default=32,
        min=1,
        max=999999
    )

    preview_image: StringProperty(
        name="Preview Image",
        description="Name of the currently displayed preview image",
        default=""
    )

    show_generation_stats: bpy.props.BoolProperty(
        name="Show Generation Stats",
        default=False,
        description="Show preview generation statistics"
    )

    show_preview_thumbnails: BoolProperty(
        name="Show Preview Thumbnails Settings",
        description="Show or hide preview thumbnails settings",
        default=False
    )
    show_preview_generation_settings: BoolProperty(
        name="Show Preview Generation Settings",
        description="Show or hide preview generation settings",
        default=False
    )

    preview_render_device: EnumProperty(
        name="Render Device",
        description="Device to use for preview rendering",
        items=[
            ('CPU', 'CPU', 'Use CPU for rendering'),
            ('GPU', 'GPU', 'Use GPU for rendering')
        ],
        default='GPU'
    )

    preview_scene_type: EnumProperty(
        name="Scene Type",
        description="Objects to include in the preview scene",
        items=[
            ('ORBS_4', 'Orbs - 4', 'Use the four orbs collection'),
            ('ORBS_3', 'Orbs - 3', 'Use the three orbs collection'),
            ('TEAPOT', 'Teapot', 'Use the teapot collection')
        ],
        default='ORBS_4'
    )

    default_proxy_resolution: EnumProperty(
        name="Default Proxy Resolution",
        description="Default resolution for HDRI proxies",
        items=[
            ('ORIGINAL', 'Original', 'Use original resolution'),
            ('1K', '1K', 'Use 1K resolution'),
            ('2K', '2K', 'Use 2K resolution'),
            ('4K', '4K', 'Use 4K resolution'),
        ],
        default='ORIGINAL'
    )

    default_proxy_mode: EnumProperty(
        name="Default Proxy Mode",
        description="Default proxy application mode",
        items=[
            ('VIEWPORT', 'Viewport Only', 'Apply proxy resolution only in viewport'),
            ('BOTH', 'Both', 'Apply proxy resolution to both viewport and render'),
        ],
        default='VIEWPORT'
    )

    show_proxy_settings: BoolProperty(
        name="Show Proxy Settings",
        description="Show or hide proxy settings",
        default=False
    )

    proxy_cache_limit: IntProperty(
        name="Proxy Cache Limit",
        description="Maximum size for proxy cache in megabytes",
        default=500,
        min=1,
        max=999999999
    )
    proxy_compression: EnumProperty(
        name="Proxy Compression",
        description="Compression method for proxy files",
        items=[
            ('NONE', 'None', 'No compression'),
            ('ZIP', 'ZIP', 'ZIP compression'),
            ('PIZ', 'PIZ', 'PIZ compression (EXR only)'),
        ],
        default='PIZ'
    )

    proxy_generation_resolution: EnumProperty(
        name="Proxy Resolution",
        description="Resolution to use for proxy generation",
        items=[
            ('1K', '1K', 'Generate 1K proxies'),
            ('2K', '2K', 'Generate 2K proxies'),
            ('4K', '4K', 'Generate 4K proxies'),
        ],
        default='1K'
    )

    proxy_generation_directory: StringProperty(
        name="Proxy Generation Directory",
        subtype='DIR_PATH',
        description="Directory containing HDRI files for proxy generation",
        default=""
    )


    proxy_format: EnumProperty(
        name="Proxy Format",
        description="File format for proxy files",
        items=[
            ('HDR', 'HDR', 'OpenEXR HDR format'),
            ('EXR', 'EXR', 'OpenEXR format'),
        ],
        default='EXR'
    )

    proxy_generation_device: EnumProperty(
        name="Render Device",
        description="Device to use for proxy generation",
        items=[
            ('CPU', 'CPU', 'Use CPU for processing'),
            ('GPU', 'GPU', 'Use GPU for processing')
        ],
        default='GPU'
    )

    show_cache_settings: bpy.props.BoolProperty(
        name="Show Cache Settings",
        default=False,
        description="Toggle the visibility of cache settings"
    )
    show_advanced_settings: bpy.props.BoolProperty(
        name="Show Advanced Settings",
        default=False,
        description="Toggle the visibility of advanced settings"
    )

    render_engine: EnumProperty(
        name="HDRI Render Engine",
        description="Select the render engine for HDRI controls",
        items=[
            ('CYCLES', 'Cycles: v2.8.2', 'Use Cycles render engine'),
            ('VRAY_RENDER_RT', 'V-Ray: v1.0.8', 'Use V-Ray render engine'),
            ('OCTANE', 'Octane: v2.8.2', 'Use Octane render engine')
        ],
        default='VRAY_RENDER_RT'
    )

    enable_backups: BoolProperty(
        name="Enable Backups",
        description="Create a backup before performing updates",
        default=True
    )

    max_backup_files: IntProperty(
        name="Maximum Backup Files",
        description="Maximum number of backup files to keep",
        default=5,
        min=1,
        max=50
    )

    folders_per_page: IntProperty(
        name="Folders Per Page",
        description="Number of folders to display per page in the HDRI browser",
        default=6,
        min=2,
        max=20
    )

    show_folder_pagination: BoolProperty(
        name="Enable Folder Pagination",
        description="Enable pagination for folders in the HDRI browser",
        default=True
    )

    # Preview display with image loading
    def get_preview_icon(self, context=None):
        """Get the preview icon ID for an image"""
        if self.preview_image and os.path.exists(self.preview_image):
            try:
                # Load or get existing image
                if self.preview_image not in bpy.data.images:
                    preview_img = bpy.data.images.load(self.preview_image)
                else:
                    preview_img = bpy.data.images[self.preview_image]

                # Force a reload of the image
                preview_img.reload()

                # Return the preview icon ID
                return preview_img.preview.icon_id

            except Exception as e:
                print(f"Failed to load preview image: {str(e)}")
                return 0
        return 0

    # Preview Statistics
    preview_stats_total: IntProperty(default=0)
    preview_stats_completed: IntProperty(default=0)
    preview_stats_failed: IntProperty(default=0)
    preview_stats_time: FloatProperty(default=0.0)
    preview_stats_current_file: StringProperty(default="")
    is_generating: BoolProperty(default=False)

    #Proxy Statistics
    proxy_stats_total: IntProperty(default=0)
    proxy_stats_completed: IntProperty(default=0)
    proxy_stats_failed: IntProperty(default=0)
    proxy_stats_time: FloatProperty(default=0.0)
    proxy_stats_current_file: StringProperty(default="")
    is_proxy_generating: BoolProperty(default=False)


    def find_keymap_conflicts(self, context):
        """Find all keymap items that conflict with current shortcut settings"""
        conflicts = []
        seen_conflicts = set()  # Track unique conflicts

        # Get current shortcut settings
        is_mac = sys.platform == 'darwin'
        current_key = self.popup_key
        current_ctrl = self.popup_ctrl
        current_shift = self.popup_shift
        current_alt = self.popup_alt
        current_oskey = self.popup_ctrl if is_mac else False

        # Check all keyconfig categories
        wm = context.window_manager
        keyconfigs_to_check = [
            ('Blender', wm.keyconfigs.default),
            ('Blender User', wm.keyconfigs.user),
            ('Addons', wm.keyconfigs.addon)
        ]

        for config_name, keyconfig in keyconfigs_to_check:
            if keyconfig:
                for keymap in keyconfig.keymaps:
                    for kmi in keymap.keymap_items:
                        if kmi.type == current_key and \
                           kmi.ctrl == (current_ctrl if not is_mac else False) and \
                           kmi.shift == current_shift and \
                           kmi.alt == current_alt and \
                           kmi.oskey == (current_ctrl if is_mac else False) and \
                           kmi.active:  # Only check active shortcuts

                            # Don't report our own shortcut as a conflict
                            if kmi.idname != HDRI_OT_popup_controls.bl_idname:
                                # Create a unique identifier for this conflict
                                conflict_id = f"{kmi.idname}_{keymap.name}"

                                if conflict_id not in seen_conflicts:
                                    seen_conflicts.add(conflict_id)
                                    conflicts.append({
                                        'config': config_name,
                                        'keymap': keymap.name,
                                        'name': kmi.name or kmi.idname,
                                        'type': kmi.type,
                                        'ctrl': kmi.ctrl,
                                        'shift': kmi.shift,
                                        'alt': kmi.alt,
                                        'oskey': kmi.oskey
                                    })

        # Sort conflicts by config name and then by keymap name for consistent display
        conflicts.sort(key=lambda x: (x['config'], x['keymap'], x['name']))

        return conflicts
    def update_shortcut(self, context):
        """Update the keyboard shortcut"""
        # Remove existing shortcut
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
        addon_keymaps.clear()

        # Add new shortcut
        wm = context.window_manager
        kc = wm.keyconfigs.addon
        if kc:
            km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')

            # Handle platform-specific keys
            is_mac = sys.platform == 'darwin'

            kmi = km.keymap_items.new(
                HDRI_OT_popup_controls.bl_idname,
                type=self.popup_key,
                value='PRESS',
                oskey=self.popup_ctrl if is_mac else False,  # Command key for MacOS
                ctrl=self.popup_ctrl if not is_mac else False,  # Ctrl key for Windows/Linux
                shift=self.popup_shift,
                alt=self.popup_alt
            )
            addon_keymaps.append((km, kmi))

    def switch_render_engine(self, context):
        import os
        import shutil

        # First verify if the target engine is actually available
        if self.render_engine == 'VRAY_RENDER_RT':
            # Check if V-Ray is available in render engines
            try:
                # Try to temporarily set render engine to V-Ray
                old_engine = context.scene.render.engine
                context.scene.render.engine = 'VRAY_RENDER_RT'
                # If we get here, V-Ray is available
                # Restore original engine
                context.scene.render.engine = old_engine
            except:
                def draw_vray_error(self, context):
                    layout = self.layout
                    layout.label(text="V-Ray is not installed!", icon='ERROR')
                    layout.label(text="Please install the V-Ray plugin first.")
                    layout.separator()
                    layout.operator("preferences.addon_show", text="Open Addon Preferences").module = __name__

                context.window_manager.popup_menu(draw_vray_error, title="Render Engine Error", icon='ERROR')
                self.render_engine = 'CYCLES'
                return {'CANCELLED'}

        elif self.render_engine == 'OCTANE':
            # Check for Octane installation
            try:
                import _octane
            except ImportError:
                def draw_octane_error(self, context):
                    layout = self.layout
                    layout.label(text="Octane is not installed!", icon='ERROR')
                    layout.label(text="Please install the Octane plugin first.")
                    layout.separator()
                    layout.operator("preferences.addon_show", text="Open Addon Preferences").module = __name__

                context.window_manager.popup_menu(draw_octane_error, title="Render Engine Error", icon='ERROR')
                # Revert preference to Cycles since we know it's always available
                self.render_engine = 'CYCLES'
                return {'CANCELLED'}

        # If we get here, the target engine is available
        current_script_path = os.path.dirname(os.path.realpath(__file__))
        cycles_script = os.path.join(current_script_path, "__init__cycles.py")
        vray_script = os.path.join(current_script_path, "__init__vray.py")
        octane_script = os.path.join(current_script_path, "__init__octane.py")
        current_script = os.path.join(current_script_path, "__init__.py")

        try:
            # Save current render engine preference
            preferences_path = os.path.join(current_script_path, "preferences.json")
            try:
                import json
                with open(preferences_path, 'w') as f:
                    json.dump({
                        'render_engine': self.render_engine
                    }, f)
            except Exception as e:
                print(f"Could not save render engine preference: {str(e)}")

            # Verify script files exist before attempting switch
            if self.render_engine == 'VRAY_RENDER_RT' and not os.path.exists(vray_script):
                self.report({'ERROR'}, "V-Ray script (__init__vray.py) is missing")
                self.render_engine = context.scene.render.engine
                return {'CANCELLED'}

            elif self.render_engine == 'OCTANE' and not os.path.exists(octane_script):
                self.report({'ERROR'}, "Octane script (__init__octane.py) is missing")
                self.render_engine = context.scene.render.engine
                return {'CANCELLED'}

            elif self.render_engine == 'CYCLES' and not os.path.exists(cycles_script):
                self.report({'ERROR'}, "Cycles script (__init__cycles.py) is missing")
                self.render_engine = context.scene.render.engine
                return {'CANCELLED'}

            # Perform the switch based on selected engine
            if self.render_engine == 'VRAY_RENDER_RT':
                # Backup current script based on current engine
                if context.scene.render.engine == 'CYCLES' and not os.path.exists(cycles_script):
                    shutil.copy2(current_script, cycles_script)
                elif context.scene.render.engine == 'OCTANE' and not os.path.exists(octane_script):
                    shutil.copy2(current_script, octane_script)

                # Replace with V-Ray script
                shutil.copy2(vray_script, current_script)

            elif self.render_engine == 'OCTANE':
                # Backup current script based on current engine
                if context.scene.render.engine == 'CYCLES' and not os.path.exists(cycles_script):
                    shutil.copy2(current_script, cycles_script)
                elif context.scene.render.engine == 'VRAY_RENDER_RT' and not os.path.exists(vray_script):
                    shutil.copy2(current_script, vray_script)

                # Replace with Octane script
                shutil.copy2(octane_script, current_script)

            else:  # CYCLES
                # Backup current script based on current engine
                if context.scene.render.engine == 'OCTANE' and not os.path.exists(octane_script):
                    shutil.copy2(current_script, octane_script)
                elif context.scene.render.engine == 'VRAY_RENDER_RT' and not os.path.exists(vray_script):
                    shutil.copy2(current_script, vray_script)

                # Replace with Cycles script
                shutil.copy2(cycles_script, current_script)

            # Prompt for restart
            def invoke_restart_prompt():
                bpy.ops.world.restart_prompt('INVOKE_DEFAULT')

            context.window_manager.popup_menu(
                lambda self, context: self.layout.label(text="Blender needs to restart to apply changes."),
                title="Restart Required",
                icon='QUESTION'
            )

            bpy.app.timers.register(invoke_restart_prompt)

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to switch render engine: {str(e)}")
            # Revert preference to current engine on error
            self.render_engine = context.scene.render.engine
            return {'CANCELLED'}

    def render_engine(self, context):
        # Custom setter to track changes
        def setter(self, value):
            # Check if the value is different from the current value
            old_value = self.get('render_engine', None)
            if old_value != value:
                self._render_engine_changed = True
            self['render_engine'] = value

        # Custom getter
        def getter(self):
            return self.get('render_engine', 'CYCLES')

        return {
            'get': getter,
            'set': setter
        }

    def draw(self, context):
        layout = self.layout
        # Get custom icon
        custom_icon = get_icons().get("vray_icon")
        icon_id = custom_icon.icon_id if custom_icon else 0

        # HDRI Directory and Render Engine
        main_box = layout.box()
        row = main_box.row()
        row.scale_y = 1.2

        split = row.split(factor=0.5)

        # HDRI Directory column
        dir_col = split.column()
        if not self.hdri_directory:
            dir_col.alert = True
        dir_col.prop(self, "hdri_directory", text="Directory")

        # Render Engine column
        engine_col = split.column()
        row = engine_col.row(align=True)
        row.prop(self, "render_engine", text="Engine", icon_value=icon_id)
        row.operator("world.apply_render_engine", text="", icon='PLUS')

        # Updates Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_updates",
                   icon='TRIA_DOWN' if getattr(self, 'show_updates', True) else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)

        # Add version info to header
        header_text = header.split(factor=0.5)
        header_text.label(text="Updates & Information", icon='FILE_REFRESH')
        version_text = header_text.row()
        version_text.alignment = 'RIGHT'

        if getattr(self, 'show_updates', True):
            update_box = box.box()

            # Update Check Row
            status_row = update_box.row()
            status_row.prop(self, "enable_auto_update_check",
                          text="Check for Updates on Startup",
                          icon='TIME')
            check_row = status_row.row(align=True)
            check_row.operator("world.check_hdri_updates",
                             text="Check Now",
                             icon='FILE_REFRESH')

            # Update Notification
            alert_box = update_box.box()
            alert_row = alert_box.row()

            if self.update_available:
               alert_row.alert = True
               alert_row.label(text="New Update Available!", icon='ERROR')
               alert_row.operator("world.download_hdri_update",
                                text="Download Update",
                                icon='IMPORT')

            # Always show Revert Version button
            alert_row.operator("world.revert_hdri_version",
                            text="Revert Version",
                            icon='LOOP_BACK')

            # Backup Settings
            backup_header = update_box.row()
            backup_header.prop(self, "show_backup_settings",
                               icon='TRIA_DOWN' if getattr(self, 'show_backup_settings', False) else 'TRIA_RIGHT',
                               icon_only=True, emboss=False)
            backup_header.label(text="Backup Settings", icon='FILE_BACKUP')

            if getattr(self, 'show_backup_settings', False):
                backup_box = update_box.box()
                backup_col = backup_box.column(align=True)

                # Backup toggle
                backup_col.prop(self, "enable_backups", text="Enable Backup Before Update")

                # Max backup files
                if self.enable_backups:
                    max_row = backup_col.row(align=True)
                    max_row.prop(self, "max_backup_files", text="Max Backup Files")

                    # Cleanup button
                    cleanup_row = backup_col.row(align=True)
                    cleanup_row.operator("world.cleanup_hdri_backups",
                                         text="Delete All Backup Files",
                                         icon='TRASH')

            # Documentation Settings
            docs_header = update_box.row()
            docs_header.prop(self, "show_documentation",
                             icon='TRIA_DOWN' if getattr(self, 'show_documentation', False) else 'TRIA_RIGHT',
                             icon_only=True, emboss=False)
            docs_header.label(text="Documentation & Resources", icon='HELP')

            if getattr(self, 'show_documentation', False):
                docs_box = update_box.box()
                docs_col = docs_box.column(align=True)

                # Documentation links
                links_row = docs_col.row(align=True)
                links_row.scale_y = 1.2
                links_row.operator("wm.url_open",
                                 text="Documentation",
                                 icon='URL').url = "https://github.com/mdreece/Quick-HDRI-Controls/tree/main"
                links_row.operator("wm.url_open",
                                 text="Report Issue",
                                 icon='ERROR').url = "https://github.com/mdreece/Quick-HDRI-Controls/issues"
                links_row.operator("wm.url_open",
                                 text="Change log",
                                 icon='INFO').url = "https://github.com/mdreece/Quick-HDRI-Controls/blob/main/CHANGELOG.md"
                links_row.operator("wm.url_open",
                                 text="Blender Fund",
                                 icon='BLENDER').url = "https://fund.blender.org/"
                links_row.operator("wm.url_open",
                                 text="BM",
                                 icon='BLENDER').url = "https://blendermarket.com/products/quick-hdri-controls"

                # Tips section
                tips_col = docs_col.column(align=True)
                tips_col.label(text="Quick Tips:", icon='INFO')
                tips_col.label(text="• Use keyboard shortcut for quick access")
                tips_col.label(text="• Organize HDRI directory")
                tips_col.label(text="• Use PNG thumbnails for HDRs")
                tips_col.label(text="• Check for updates regularly")

        # Preview Thumbnails Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_preview_thumbnails",
                  icon='TRIA_DOWN' if self.show_preview_thumbnails else 'TRIA_RIGHT',
                  icon_only=True, emboss=False)
        header_split = header.split(factor=0.7)
        header_split.label(text="Preview Thumbnails", icon='IMAGE_DATA')

        # Status indicator
        status_row = header_split.row(align=True)
        status_row.alignment = 'RIGHT'
        if self.is_generating:
            status_row.alert = True
            status_row.label(text="Processing", icon='TIME')
        else:
            status_row.label(text="Ready", icon='CHECKMARK')

        if self.show_preview_thumbnails:
            main_col = box.column(align=True)
            main_col.separator()

            if self.is_generating:
                # Generating status
                status_box = main_col.box()
                status_box.alert = True

                grid = status_box.grid_flow(row_major=True, columns=2, even_columns=True)

                grid.label(text="Progress:")
                grid.label(text=f"{self.preview_stats_completed}/{self.preview_stats_total}")

                grid.label(text="Current File:")
                grid.label(text=self.preview_stats_current_file or "N/A")

                grid.label(text="Time Elapsed:")
                grid.label(text=f"{self.preview_stats_time:.2f} seconds")

            else:
                # Preview Generation Options
                gen_box = main_col.box()
                gen_header = gen_box.row()
                gen_header.prop(self, "show_preview_generation_settings",
                              icon='TRIA_DOWN' if getattr(self, 'show_preview_generation_settings', False) else 'TRIA_RIGHT',
                              icon_only=True, emboss=False)
                gen_header.label(text="Preview Generation", icon='PRESET')

                if getattr(self, 'show_preview_generation_settings', False):
                    gen_col = gen_box.column(align=True)

                    # Processing Mode
                    mode_row = gen_col.row(align=True)
                    mode_row.label(text="Processing Mode:", icon='MODIFIER')
                    mode_row.prop(self, "preview_generation_type", text="")

                    # Source Selection
                    if self.preview_generation_type != 'FULL_BATCH':
                        source_row = gen_col.row(align=True)
                        source_row.label(text="Source:", icon='FILEBROWSER')

                        if self.preview_generation_type == 'SINGLE':
                            source_row.prop(self, "preview_single_file", text="")
                        else:
                            source_row.prop(self, "preview_multiple_folder", text="")

                    # Quality Settings
                    quality_box = gen_col.box()
                    quality_header = quality_box.row()
                    quality_header.label(text="Quality Settings", icon='SETTINGS')

                    # Quality settings grid
                    quality_grid = quality_box.grid_flow(row_major=True, columns=2, even_columns=True)

                    quality_grid.label(text="Scene Type:")
                    quality_grid.prop(self, "preview_scene_type", text="")

                    quality_grid.label(text="Render Device:")
                    quality_grid.prop(self, "preview_render_device", text="")

                    quality_grid.label(text="Resolution:")
                    quality_grid.prop(self, "preview_resolution", text="%")

                    quality_grid.label(text="Render Samples:")
                    quality_grid.prop(self, "preview_samples", text="")

                    # Output Resolution Info
                    res_box = quality_box.box()
                    res_box.scale_y = 0.9
                    actual_x = int(1024 * (self.preview_resolution / 100))
                    actual_y = int(768 * (self.preview_resolution / 100))
                    res_box.label(text=f"Output Resolution: {actual_x} × {actual_y} pixels")

                    # Generation Button
                    gen_col.separator()
                    action_row = gen_col.row(align=True)
                    action_row.scale_y = 1.5

                    button_text = {
                        'SINGLE': 'Generate Preview',
                        'MULTIPLE': 'Generate Previews',
                        'FULL_BATCH': 'Generate All Previews'
                    }.get(self.preview_generation_type)

                    action_row.operator(
                        "world.generate_hdri_previews",
                        text=button_text,
                        icon='RENDER_STILL'
                    )

                # Preview Limit section
                preview_limit_box = main_col.box()
                preview_limit_header = preview_limit_box.row()
                preview_limit_header.prop(self, "show_preview_limit_settings",
                            icon='TRIA_DOWN' if getattr(self, 'show_preview_limit_settings', False) else 'TRIA_RIGHT',
                            icon_only=True, emboss=False)
                preview_limit_header.label(text="Preview Limit", icon='IMAGE_DATA')

                if getattr(self, 'show_preview_limit_settings', False):
                    limit_col = preview_limit_box.column(align=True)

                    # Dropdown for preview limit
                    limit_row = limit_col.row()
                    limit_row.label(text="Maximum Previews:")
                    limit_row.prop(self, "preview_limit", text="")

                    # Explanation for preview limit
                    explanation_box = limit_col.box()
                    explanation_box.scale_y = 0.9
                    if self.preview_limit == 0:
                        explanation_box.label(text="No limit: All HDRIs will be loaded", icon='INFO')
                    else:
                        explanation_box.label(text=f"Only the first {self.preview_limit} HDRIs will be shown", icon='RESTRICT_VIEW_OFF')

                # Generation Status
                if self.preview_stats_total > 0 and self.show_generation_stats:
                    status_box = main_col.box()
                    status_header = status_box.row()
                    status_header.label(text="Generation Complete", icon='CHECKMARK')

                    status_grid = status_box.grid_flow(row_major=True, columns=2, even_columns=True)

                    status_grid.label(text="Completed:")
                    status_grid.label(text=f"{self.preview_stats_completed}/{self.preview_stats_total}")

                    status_grid.label(text="Total Time:")
                    status_grid.label(text=f"{self.preview_stats_time:.2f} seconds")

                    clear_row = status_box.row()
                    clear_row.operator("world.clear_preview_stats", text="Clear Results", icon='X')

        # Proxy Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_proxy",
                    icon='TRIA_DOWN' if getattr(self, 'show_proxy', True) else 'TRIA_RIGHT',
                    icon_only=True, emboss=False)
        header.label(text="Proxy Settings", icon='COPY_ID')
        if getattr(self, 'show_proxy', True):
            col = box.column(align=True)

            # Proxy Settings
            settings_col = col.column(align=True)
            settings_col.prop(self, "default_proxy_resolution", text="Default Resolution")
            settings_col.prop(self, "default_proxy_mode", text="Default Application")

            cache_header = settings_col.row()
            cache_header.prop(self, "show_cache_settings",
                              icon='TRIA_DOWN' if getattr(self, 'show_cache_settings', True) else 'TRIA_RIGHT',
                              icon_only=True, emboss=False)
            cache_header.label(text="Cache Settings", icon='FILE_CACHE')

            if getattr(self, 'show_cache_settings', True):
                cache_box = settings_col.box()
                cache_col = cache_box.column(align=True)
                cache_col.prop(self, "proxy_cache_limit", text="Cache Size Limit (MB)")
                cache_col.operator("world.cleanup_hdri_proxies", text="Clear Proxy Cache", icon='TRASH')

            # Proxy Generation
            gen_header = settings_col.row()
            gen_header.prop(self, "show_proxy_generation",
                            icon='TRIA_DOWN' if getattr(self, 'show_proxy_generation', True) else 'TRIA_RIGHT',
                            icon_only=True, emboss=False)
            gen_header.label(text="Batch Proxy Generation", icon='RENDER_STILL')

            if getattr(self, 'show_proxy_generation', True):
                gen_box = settings_col.box()
                gen_col = gen_box.column(align=True)

                # Directory Selection
                row = gen_col.row(align=True)
                row.prop(self, "proxy_generation_directory", text="Folder Batch")

                # Resolution Selection
                row = box.row()
                row.prop(self, "proxy_generation_resolution", text="Resolution")

                # Processing Device Selection
                row = box.row()
                row.prop(self, "proxy_generation_device", text="Render Device")

                gen_col.separator()

                # Generation Status
                if self.is_proxy_generating:
                    status_box = gen_col.box()
                    status_box.alert = True
                    status_box.label(text="Generating Proxies...", icon='TIME')

                    status_row = status_box.row(align=True)
                    status_row.label(text="Current File:")
                    status_row.label(text=self.proxy_stats_current_file)

                    progress_row = status_box.row(align=True)
                    progress_row.label(text="Progress:")
                    progress_row.label(text=f"{self.proxy_stats_completed}/{self.proxy_stats_total}")

                    time_row = status_box.row(align=True)
                    time_row.label(text="Elapsed Time:")
                    time_row.label(text=f"{self.proxy_stats_time:.2f} seconds")
                else:
                    # Generation Buttons
                    row = box.row(align=True)
                    row.scale_y = 1.5
                    sub = row.split(factor=0.5)
                    sub.operator("world.generate_hdri_proxies", text="Generate Proxies")
                    sub.operator("world.full_batch_hdri_proxies", text="Full Batch Process")

                # Generation Results
                if self.proxy_stats_total > 0 and not self.is_proxy_generating:
                    result_box = gen_col.box()

                    total_row = result_box.row(align=True)
                    total_row.label(text="Total Files:")
                    total_row.label(text=str(self.proxy_stats_total))

                    completed_row = result_box.row(align=True)
                    completed_row.label(text="Completed:")
                    completed_row.label(text=str(self.proxy_stats_completed))

                    failed_row = result_box.row(align=True)
                    failed_row.label(text="Failed:")
                    failed_row.label(text=str(self.proxy_stats_failed))

                    time_row = result_box.row(align=True)
                    time_row.label(text="Total Time:")
                    time_row.label(text=f"{self.proxy_stats_time:.2f} seconds")

                    # Clear Results Button
                    clear_row = result_box.row(align=True)
                    clear_row.operator("world.clear_proxy_stats", text="Clear Results", icon='X')

        # Keyboard Shortcuts Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_shortcuts", icon='TRIA_DOWN' if getattr(self, 'show_shortcuts', True) else 'TRIA_RIGHT',
                   icon_only=True, emboss=False)
        header.label(text="Keyboard Shortcuts", icon='KEYINGSET')

        if getattr(self, 'show_shortcuts', True):
            col = box.column(align=True)

            # Current shortcut display
            current_shortcut = []
            if self.popup_ctrl:
                current_shortcut.append("⌘ Command" if sys.platform == 'darwin' else "Ctrl")
            if self.popup_shift:
                current_shortcut.append("⇧ Shift")
            if self.popup_alt:
                current_shortcut.append("⌥ Option" if sys.platform == 'darwin' else "Alt")
            current_shortcut.append(self.popup_key)

            # Current shortcut row
            row = col.row()
            row.label(text="Current Shortcut: " + " + ".join(current_shortcut))

            # Add a note about mouse buttons
            note_row = col.row()
            note_row.scale_y = 0.7
            note_row.label(text="Tip: You can also use mouse buttons for shortcuts", icon='INFO')

            # Modifier keys
            row = col.row(align=True)
            if sys.platform == 'darwin':
                row.prop(self, "popup_ctrl", text="⌘ Command", toggle=True)
                row.prop(self, "popup_shift", text="⇧ Shift", toggle=True)
                row.prop(self, "popup_alt", text="⌥ Option", toggle=True)
            else:
                row.prop(self, "popup_ctrl", text="Ctrl", toggle=True)
                row.prop(self, "popup_shift", text="Shift", toggle=True)
                row.prop(self, "popup_alt", text="Alt", toggle=True)

            # Key selection
            col.prop(self, "popup_key", text="Key")
            col.separator()

            # Apply button
            col.operator("world.update_hdri_shortcut", text="Apply Shortcut Change")
            col.separator()

            # Get conflicts
            conflicts = self.find_keymap_conflicts(context)

            # Conflicts section with status-based header
            conflict_box = col.box()
            header_row = conflict_box.row()
            header_row.prop(self, "show_conflicts",
                          icon='TRIA_DOWN' if self.show_conflicts else 'TRIA_RIGHT',
                          icon_only=True, emboss=False)

            status_row = header_row.row()
            if conflicts:
                status_row.alert = True
                status_row.label(text="Conflicts Found", icon='ERROR')
            else:
                status_row.label(text="No Conflicts Found", icon='CHECKMARK')
                status_row.alert = False

            if self.show_conflicts:
                if conflicts:
                    # Group conflicts by keyconfig
                    for config_name in ['Blender', 'Blender User', 'Addons']:
                        config_conflicts = [c for c in conflicts if c['config'] == config_name]
                        if config_conflicts:
                            sub_box = conflict_box.box()
                            row = sub_box.row()
                            row.label(text=config_name + ":", icon='KEYINGSET')

                            for conflict in config_conflicts:
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

                                row = sub_box.row()
                                split = row.split(factor=0.7)
                                split.label(text=conflict['name'])
                                split.label(text=shortcut)

                                # Show keymap in smaller text
                                row = sub_box.row()
                                row.scale_y = 0.8
                                row.label(text=f"Found in: {conflict['keymap']}")
                                sub_box.separator(factor=0.5)

        # HDRI Settings Section
        box = layout.box()
        header = box.row()
        header.prop(self, "show_hdri_settings", icon='TRIA_DOWN' if getattr(self, 'show_hdri_settings', True) else 'TRIA_RIGHT',
                    icon_only=True, emboss=False)
        header.label(text="HDRI Settings", icon='WORLD_DATA')
        if getattr(self, 'show_hdri_settings', True):
            col = box.column(align=True)
            col.prop(self, "keep_rotation", text="Keep Rotation When Switching HDRIs")
            col.prop(self, "strength_max", text="Maximum Strength Value")
            col.prop(self, "rotation_increment", text="Rotation Step Size")

            #file types section
            col.separator()
            col.label(text="Supported File Types", icon='FILE_FOLDER')
            row = col.row(align=True)
            row.prop(self, "use_hdr", toggle=True)
            row.prop(self, "use_exr", toggle=True)
            row.prop(self, "use_png", toggle=True)
            row.prop(self, "use_jpg", toggle=True)

            col.separator()
            col.label(text="Folder Browser Display", icon='FILE_FOLDER')

            row = col.row(align=True)
            row.prop(self, "show_folder_pagination", text="Enable Folder Pagination")

            sub_row = col.row()
            sub_row.enabled = self.show_folder_pagination
            sub_row.prop(self, "folders_per_page")

    #properties to control visibility
    show_updates: BoolProperty(default=False)
    show_shortcuts: BoolProperty(default=False)
    show_interface: BoolProperty(default=False)
    show_filetypes: BoolProperty(default=False)
    show_hdri_settings: BoolProperty(default=False)
    show_conflicts: BoolProperty(default=False)
    show_preview_generation: BoolProperty(default=False)
    show_proxy_generation: BoolProperty(default=False)
    show_proxy: BoolProperty(default=False)
    show_proxy_generation: BoolProperty(default=False)
    show_generation_stats: BoolProperty(default=False)
    preview_stats_visible: BoolProperty(default=False)
    show_render_engine: BoolProperty(default=False)
    show_backup_settings: BoolProperty(default=False)
    show_documentation: BoolProperty(default=False)

class HDRI_OT_toggle_visibility(Operator):
    bl_idname = "world.toggle_hdri_visibility"
    bl_label = "Toggle HDRI Visibility"
    bl_description = "Toggle HDRI background visibility"

    def execute(self, context):
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if vray_collection:
            for obj in vray_collection.objects:
                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                    light_dome = obj.data.node_tree.nodes["Light Dome"]
                    # Toggle the invisible input
                    current_value = light_dome.inputs["Invisible"].value
                    light_dome.inputs["Invisible"].value = not current_value
                    light_dome.update()  # Added node update

                    # Report the change
                    self.report({'INFO'}, f"Visibility set to: {not current_value}")
                    return {'FINISHED'}
        return {'CANCELLED'}

class HDRI_OT_delete_world(Operator):
    bl_idname = "world.delete_hdri_world"
    bl_label = "Delete V-Ray HDRI"
    bl_description = "Delete the V-Ray HDRI setup"

    def invoke(self, context, event):
        # Show confirmation dialog
        return context.window_manager.invoke_confirm(
            self,
            event,
            title="Delete V-Ray HDRI?"
        )

    def execute(self, context):
        # Find the V-Ray collection
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if vray_collection:
            # Remove collection from all scenes first
            for scene in bpy.data.scenes:
                if vray_collection.name in scene.collection.children:
                    scene.collection.children.unlink(vray_collection)

            # Store objects and lights to remove
            objects_to_remove = [obj for obj in vray_collection.objects]
            lights_to_remove = [obj.data for obj in objects_to_remove if obj.data and obj.type == 'LIGHT']

            # Clear objects from collection
            for obj in objects_to_remove:
                vray_collection.objects.unlink(obj)
                bpy.data.objects.remove(obj)

            # Remove light data
            for light in lights_to_remove:
                bpy.data.lights.remove(light)

            # Finally remove the collection
            bpy.data.collections.remove(vray_collection)

            self.report({'INFO'}, "V-Ray HDRI setup deleted")
            return {'FINISHED'}

        return {'CANCELLED'}

class HDRI_OT_previous_hdri(Operator):
    bl_idname = "world.previous_hdri"
    bl_label = "Previous HDRI"
    bl_description = "Load the previous HDRI in the current folder"

    def execute(self, context):
        hdri_settings = context.scene.hdri_settings
        enum_items = generate_previews(self, context)

        # Check if we have any items besides 'None'
        if len(enum_items) <= 1:
            self.report({'INFO'}, "No HDRIs available in current folder")
            return {'CANCELLED'}

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
        hdri_settings = context.scene.hdri_settings
        enum_items = generate_previews(self, context)

        # Check if we have any items besides 'None'
        if len(enum_items) <= 1:
            self.report({'INFO'}, "No HDRIs available in current folder")
            return {'CANCELLED'}

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
            # Make sure we have a valid item to wrap to
            if len(enum_items) > 1:
                hdri_settings.hdri_preview = enum_items[1][0]  # Skip 'None' item

        return {'FINISHED'}
class HDRI_OT_reset_hdri(Operator):
    bl_idname = "world.reset_hdri"
    bl_label = "Reset HDRI"
    bl_description = "Toggle between current and previous HDRI"
    def execute(self, context):
        hdri_settings = context.scene.hdri_settings
        preferences = context.preferences.addons[__name__].preferences

        # Check if we have a previous HDRI to restore
        if not hdri_settings.previous_hdri_path:
            self.report({'WARNING'}, "No previous HDRI to restore")
            return {'CANCELLED'}

        # Verify the file still exists
        if not os.path.exists(hdri_settings.previous_hdri_path):
            self.report({'ERROR'}, "Previous HDRI file could not be found")
            return {'CANCELLED'}

        try:
            # Find the V-Ray dome light
            vray_collection = bpy.data.collections.get("vRay HDRI Controls")
            if not vray_collection:
                self.report({'ERROR'}, "V-Ray collection not found")
                return {'CANCELLED'}

            dome_light = None
            for obj in vray_collection.objects:
                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                    dome_light = obj
                    break

            if not dome_light:
                self.report({'ERROR'}, "VRayDomeLight not found")
                return {'CANCELLED'}

            node_tree = dome_light.data.node_tree
            bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
            light_dome_node = node_tree.nodes.get("Light Dome")

            if not bitmap_node or not light_dome_node:
                self.report({'ERROR'}, "V-Ray nodes not found")
                return {'CANCELLED'}

            # Store current state before making changes
            current_file = bitmap_node.BitmapBuffer.file if hasattr(bitmap_node.BitmapBuffer, 'file') else ''
            reset_to_path = hdri_settings.previous_hdri_path
            reset_to_path = original_paths.get(os.path.basename(reset_to_path), reset_to_path)

            # Only update current folder if there's no active search
            if not hdri_settings.search_query:
                # Update current folder to the directory of the previous HDRI
                previous_hdri_dir = os.path.dirname(reset_to_path)
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
            get_hdri_previews.cached_dir = None
            get_hdri_previews.cached_items = []

            # Load the appropriate version (proxy or original)
            if hdri_settings.proxy_resolution != 'ORIGINAL':
                # Create and load proxy
                proxy_path = create_hdri_proxy(reset_to_path, hdri_settings.proxy_resolution)
                if proxy_path:
                    # Store original path mapping
                    original_paths[os.path.basename(proxy_path)] = reset_to_path
                    bitmap_node.BitmapBuffer.file = proxy_path
                else:
                    # Fallback to original if proxy creation fails
                    bitmap_node.BitmapBuffer.file = reset_to_path
            else:
                # Load original
                bitmap_node.BitmapBuffer.file = reset_to_path

            # Update the preview selection
            enum_items = generate_previews(self, context)
            preview_found = False

            # First try to find exact match
            for item in enum_items:
                if not item[0]:  # Skip empty item
                    continue
                if os.path.normpath(item[0]) == os.path.normpath(reset_to_path):
                    hdri_settings.hdri_preview = item[0]
                    preview_found = True
                    break

            # If no exact match found, try matching by basename
            if not preview_found:
                reset_basename = os.path.basename(reset_to_path)
                for item in enum_items:
                    if not item[0]:  # Skip empty item
                        continue
                    if os.path.basename(item[0]) == reset_basename:
                        hdri_settings.hdri_preview = item[0]
                        preview_found = True
                        break

            # Update previous HDRI path to the one we just replaced
            hdri_settings.previous_hdri_path = current_file

            # Restore previous strength if available
            if hasattr(hdri_settings, 'previous_strength'):
                light_dome_node.inputs['Intensity'].value = hdri_settings.previous_strength

            # Restore previous rotation if available
            if hasattr(hdri_settings, 'previous_rotation'):
                dome_light.rotation_euler = hdri_settings.previous_rotation

            # Force viewport update
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

            self.report({'INFO'}, "HDRI reset successful")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to reset HDRI: {str(e)}")
            return {'CANCELLED'}
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
        preferences = context.preferences.addons[__name__].preferences
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
        preferences = context.preferences.addons[__name__].preferences
        if success:
            preferences.preview_stats_completed += 1

            # Load and display the newly generated thumbnail
            thumb_path = self.get_thumb_path(current_file)
            if os.path.exists(thumb_path):
                # Update the preview image path
                preferences.preview_image = thumb_path

                # Force UI update
                for window in context.window_manager.windows:
                    for area in window.screen.areas:
                        if area.type == 'PREFERENCES':
                            area.tag_redraw()
        else:
            preferences.preview_stats_failed += 1

        preferences.preview_stats_current_file = os.path.basename(current_file)
        preferences.preview_stats_time = (datetime.now() - self._start_time).total_seconds()

        # Force redraw of preferences
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'PREFERENCES':
                    area.tag_redraw()
    def modal(self, context, event):
        preferences = context.preferences.addons[__name__].preferences

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
        preferences = context.preferences.addons[__name__].preferences

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
        preferences = context.preferences.addons[__name__].preferences
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

        preferences = context.preferences.addons[__name__].preferences
        preview_blend_path = os.path.join(os.path.dirname(__file__), "Preview.blend")

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

class HDRI_OT_clear_preview_stats(Operator):
    bl_idname = "world.clear_preview_stats"
    bl_label = "Clear Statistics"
    bl_description = "Clear preview generation statistics"
    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        preferences.preview_stats_total = 0
        preferences.preview_stats_completed = 0
        preferences.preview_stats_failed = 0
        preferences.preview_stats_time = 0.0
        preferences.preview_stats_current_file = ""
        preferences.preview_image = ""
        preferences.show_generation_stats = False
        return {'FINISHED'}
# Update the finish_preview_generation method in HDRI_OT_generate_previews:
    def finish_preview_generation(self, context):
        preferences = context.preferences.addons[__name__].preferences
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()

        # Update final statistics
        preferences.is_generating = False
        preferences.show_generation_stats = True

        # Ensure the last preview is set
        if self._preview_files and self._current_file_index > 0:
            last_file = self._preview_files[self._current_file_index - 1]
            last_thumb = self.get_thumb_path(last_file)
            if os.path.exists(last_thumb):
                preferences.preview_image = last_thumb

        if self._failed_files:
            failed_names = [os.path.basename(f) for f in self._failed_files]
            self.report({'WARNING'},
                f"Generated {preferences.preview_stats_completed} previews with {len(self._failed_files)} failures")
        else:
            self.report({'INFO'},
                f"Successfully generated {preferences.preview_stats_completed} previews")

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
        preferences = context.preferences.addons[__name__].preferences
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
        preferences = context.preferences.addons[__name__].preferences

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

    # Inherit other methods from HDRI_OT_generate_proxies
    initialize_stats = HDRI_OT_generate_proxies.initialize_stats
    update_stats = HDRI_OT_generate_proxies.update_stats
    modal = HDRI_OT_generate_proxies.modal
    finish_proxy_generation = HDRI_OT_generate_proxies.finish_proxy_generation
    generate_single_proxy = HDRI_OT_generate_proxies.generate_single_proxy


class HDRI_OT_clear_hdri_search(Operator):
    bl_idname = "world.clear_hdri_search"
    bl_label = "Clear HDRI Search"
    bl_description = "Clear the current HDRI search query"

    def execute(self, context):
        # Clear the search query and unlock
        context.scene.hdri_settings.search_query = ""
        context.scene.hdri_settings.search_locked = False

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

        main_column = layout.column(align=True)

        # Get custom icon
        custom_icon = get_icons().get("vray_icon")
        icon_id = custom_icon.icon_id if custom_icon else 'BLENDER'

        # engine header
        header_row = main_column.row(align=True)
        header_row.label(text="V-Ray Build", icon_value=icon_id)
        header_row.scale_y = 0.6
        main_column.separator(factor=0.5 * preferences.spacing_scale)

        # Early returns
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
                icon='PREFERENCES').module = __name__

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
            ).module = __name__

            # Modified version display in the footer
            version_row = footer.row(align=True)
            if preferences.update_available:
                version_row.alert = True
                version_row.operator(
                    "world.download_hdri_update",
                    text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]} - Update Available",
                    emboss=False
                )
            else:
                version_row.label(text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}")
            return

        # Check for V-Ray collection and dome light
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        dome_light = None
        if vray_collection:
            for obj in vray_collection.objects:
                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                    dome_light = obj
                    break

        if not vray_collection or not dome_light or context.scene.render.engine != 'VRAY_RENDER_RT':
            box = main_column.box()
            box.alert = True
            col = box.column(align=True)
            col.scale_y = 1.2 * preferences.button_scale

            # Render engine check
            if context.scene.render.engine != 'VRAY_RENDER_RT':
                # Header row
                header_row = col.row(align=True)
                header_row.alignment = 'CENTER'
                header_row.label(text="HDRI System Initialization", icon='ERROR')

                # Explanation
                col.separator()
                explanation_row = col.row(align=True)
                explanation_row.alignment = 'CENTER'
                explanation_row.label(text="V-Ray Engine Required", icon='RENDER_RESULT')

                col.separator()

                # Initialize button
                if preferences.hdri_directory:
                    button_row = col.row(align=True)
                    button_row.scale_y = 1.5
                    button_row.operator("world.setup_hdri_nodes",
                        text="Enable V-Ray",
                        icon='WORLD_DATA')
            else:
                # If collection or dome light is missing
                col.label(text="HDRI System Not Initialized", icon='WORLD_DATA')

                if preferences.hdri_directory:
                    col.operator("world.setup_hdri_nodes",
                        text="Initialize HDRI System",
                        icon='WORLD_DATA')

            # footer
            main_column.separator(factor=1.0 * preferences.spacing_scale)
            footer = main_column.row(align=True)
            footer.scale_y = 0.8
            footer.operator(
                "preferences.addon_show",
                text="",
                icon='PREFERENCES',
                emboss=False
            ).module = __name__

            # Modified version display in the footer
            version_row = footer.row(align=True)
            if preferences.update_available:
                version_row.alert = True
                version_row.operator(
                    "world.download_hdri_update",
                    text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]} - Update Available",
                    emboss=False
                )
            else:
                version_row.label(text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}")
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
                    folders = get_folders(context)
                    if folders:
                        preferences = context.preferences.addons[__name__].preferences

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
        if has_hdri_files(context) or hdri_settings.search_query:
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

                # Navigation controls only if HDRI is active
                nav_box = preview_box.box()
                nav_row = nav_box.row(align=True)

                # Find the VRayDomeLight for getting the current HDRI
                vray_collection = bpy.data.collections.get("vRay HDRI Controls")
                bitmap_node = None
                if vray_collection:
                    for obj in vray_collection.objects:
                        if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                            if obj.data and obj.data.node_tree:
                                bitmap_node = obj.data.node_tree.nodes.get("V-Ray Bitmap")
                                break

                # Reset to previous HDRI
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

                # HDRI name
                name_row = nav_row.row(align=True)
                name_row.alignment = 'CENTER'
                name_row.scale_x = 2.2
                if bitmap_node and hasattr(bitmap_node, 'BitmapBuffer') and bitmap_node.BitmapBuffer.file:
                    name_row.label(text=os.path.basename(bitmap_node.BitmapBuffer.file))
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

        # HDRI Settings Section
        if has_active_hdri(context):
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

                # Find VRayDomeLight for visibility toggle
                dome_light = None
                vray_collection = bpy.data.collections.get("vRay HDRI Controls")
                if vray_collection:
                    for obj in vray_collection.objects:
                        if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                            dome_light = obj
                            break

                if dome_light:
                    # Get visibility state from V-Ray dome light
                    light_dome_node = dome_light.data.node_tree.nodes["Light Dome"]
                    is_visible = not light_dome_node.inputs["Invisible"].value  # Changed to use named input and .value

                    sub.operator("world.toggle_hdri_visibility",
                        text="",
                        icon='HIDE_OFF' if is_visible else 'HIDE_ON',
                        depress=is_visible)

                    # Layout based on compact mode
                    if preferences.use_compact_ui:
                        # Compact layout
                        col = rotation_box.column(align=True)
                        col.scale_y = preferences.button_scale
                        col.use_property_split = True

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

                        # strength slider
                        if preferences.show_strength_slider:
                            col.separator()
                            row = col.row(align=True)
                            sub_row = row.row(align=True)
                            if dome_light:
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
                text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]} - Update Available",
                emboss=False
            )
        else:
            version_row.label(text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}")

        #delete world button
        delete_btn = footer.operator(
            "world.delete_hdri_world",
            text="",
            icon='TRASH',
            emboss=False
        )
        settings_btn.module = __name__

def draw_hdri_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.popover(panel="HDRI_PT_controls", text="HDRI Controls")

class HDRI_OT_apply_render_engine(Operator):
    bl_idname = "world.apply_render_engine"
    bl_label = "Apply Render Engine"
    bl_description = "Switch between render engines"

    target_engine: StringProperty(default='')

    @classmethod
    def poll(cls, context):
        return context.preferences.addons[__name__].preferences is not None

    def invoke(self, context, event):
        # Check engine availability before showing confirmation
        preferences = context.preferences.addons[__name__].preferences
        target = self.target_engine or preferences.render_engine

        if target == 'VRAY_RENDER_RT':
            # Check if V-Ray is in the available render engines
            if not hasattr(bpy.ops, 'vray'):
                def draw_vray_error(self, context):
                    layout = self.layout
                    layout.label(text="V-Ray is not installed!", icon='ERROR')
                    layout.label(text="Please install the V-Ray plugin first.")

                context.window_manager.popup_menu(draw_vray_error, title="Render Engine Error", icon='ERROR')
                return {'CANCELLED'}

        elif target == 'OCTANE':
            try:
                import _octane
            except ImportError:
                def draw_octane_error(self, context):
                    layout = self.layout
                    layout.label(text="Octane is not installed!", icon='ERROR')
                    layout.label(text="Please install the Octane plugin first.")

                context.window_manager.popup_menu(draw_octane_error, title="Render Engine Error", icon='ERROR')
                return {'CANCELLED'}

        # Show confirmation dialog if target differs from current
        if target != preferences.render_engine:
            return context.window_manager.invoke_confirm(
                self,
                event,
                message=f"Switch to {target} render engine? This will restart Blender."
            )
        return self.execute(context)

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences

        # If target_engine is set, update render_engine
        if self.target_engine:
            preferences.render_engine = self.target_engine

        return preferences.switch_render_engine(context)

# Registration
classes = (
    QuickHDRIPreferences,
    HDRI_OT_cleanup_unused,
    HDRISettings,
    HDRI_OT_reset_rotation,
    HDRI_OT_reset_strength,
    HDRI_OT_setup_nodes,
    HDRI_OT_change_folder,
    HDRI_OT_change_folder_page,
    HDRI_PT_controls,
    HDRI_OT_check_updates,
    HDRI_OT_download_update,
    HDRI_OT_popup_controls,
    HDRI_OT_update_shortcut,
    HDRI_OT_quick_rotate,
    HDRI_OT_toggle_visibility,
    HDRI_OT_browse_directory,
    HDRI_OT_restart_prompt,
    HDRI_OT_delete_world,
    HDRI_OT_show_shortcut_conflicts,
    HDRI_OT_previous_hdri,
    HDRI_OT_next_hdri,
    HDRI_OT_generate_previews,
    HDRI_OT_clear_preview_stats,
    HDRI_OT_cleanup_hdri_proxies,
    HDRI_OT_generate_proxies,
    HDRI_OT_clear_proxy_stats,
    HDRI_OT_full_batch_previews,
    HDRI_OT_full_batch_proxies,
    HDRI_OT_reset_hdri,
    HDRI_OT_apply_render_engine,
    HDRI_OT_cleanup_backups,
    HDRI_OT_show_changelog,
    HDRI_OT_clear_hdri_search,
    HDRI_OT_toggle_search_bar,
)
def register():
    bpy.types.WindowManager.hdri_changelog = StringProperty(
        name="Changelog",
        description="Stores current changelog entry",
        default=""
    )
    extract_addon_zips()

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.hdri_settings = PointerProperty(type=HDRISettings)
    bpy.types.VIEW3D_HT_header.append(draw_hdri_menu)
    bpy.app.handlers.load_post.append(cleanup_hdri_proxies)
    bpy.utils.register_class(HDRI_OT_revert_version)

    if reload_original_for_render not in bpy.app.handlers.render_init:
        bpy.app.handlers.render_init.append(reload_original_for_render)
    if reset_proxy_after_render not in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.append(reset_proxy_after_render)
    if reset_proxy_after_render_complete not in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.append(reset_proxy_after_render_complete)

    # Load custom icons
    icons = get_icons()
    icons_dir = os.path.join(os.path.dirname(__file__), "misc", "icons")
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir)

    # Load the cycles icon
    icon_path = os.path.join(icons_dir, "vray_icon.png")
    if os.path.exists(icon_path):
        icons.load("vray_icon", icon_path, 'IMAGE')

    # Add keymap entry
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')

        # Get saved preferences
        preferences = bpy.context.preferences.addons[__name__].preferences
        is_mac = sys.platform == 'darwin'

        kmi = km.keymap_items.new(
            HDRI_OT_popup_controls.bl_idname,
            type=preferences.popup_key,
            value='PRESS',
            oskey=preferences.popup_ctrl if is_mac else False,
            ctrl=preferences.popup_ctrl if not is_mac else False,
            shift=preferences.popup_shift,
            alt=preferences.popup_alt
        )
        addon_keymaps.append((km, kmi))
    bpy.app.handlers.load_post.append(load_handler)

    # Run update check at startup if enabled
    check_for_update_on_startup()

def unregister():
    del bpy.types.WindowManager.hdri_changelog
    bpy.app.handlers.load_post.remove(load_handler)
    bpy.app.handlers.load_post.remove(cleanup_hdri_proxies)
    bpy.app.handlers.render_init.remove(reload_original_for_render)
    bpy.app.handlers.render_cancel.remove(reset_proxy_after_render)
    bpy.app.handlers.render_complete.remove(reset_proxy_after_render_complete)
    bpy.utils.unregister_class(HDRI_OT_revert_version)

    # Remove icon collection with proper error handling
    if hasattr(get_icons, "icon_collection"):
        try:
            icon_collection = get_icons.icon_collection
            if icon_collection:
                bpy.utils.previews.remove(icon_collection)
            delattr(get_icons, "icon_collection")
        except Exception as e:
            print(f"Note: Icon collection cleanup - {str(e)}")

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.types.VIEW3D_HT_header.remove(draw_hdri_menu)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.hdri_settings

    # Properly clean up preview collection
    if hasattr(get_hdri_previews, "preview_collection"):
        try:
            preview_collection = get_hdri_previews.preview_collection
            if preview_collection:
                bpy.utils.previews.remove(preview_collection)
            delattr(get_hdri_previews, "preview_collection")
        except Exception as e:
            print(f"Note: Preview collection cleanup - {str(e)}")

if __name__ == "__main__":
    register()





