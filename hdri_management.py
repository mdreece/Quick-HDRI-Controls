"""
Quick HDRI Controls - HDRI management utility functions
"""
import os
import bpy
import re
import time
from bpy.utils import previews

# Original paths tracking for proxies
original_paths = {}

def get_hdri_previews():
    """Get or create the preview collection"""
    if not hasattr(get_hdri_previews, "preview_collection"):
        pcoll = previews.new()
        get_hdri_previews.preview_collection = pcoll
        get_hdri_previews.cached_dir = None
        get_hdri_previews.cached_items = []
        get_hdri_previews.last_update_time = None
    return get_hdri_previews.preview_collection

def generate_previews(self, context):
    """Generate preview items for HDRIs in current folder"""
    import time
    current_time = time.time()

    if not hasattr(context.scene, "hdri_settings"):
        return [('', 'None', '', 0, 0)]

    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences
    base_dir = os.path.normpath(os.path.abspath(preferences.hdri_directory))
    current_dir = context.scene.hdri_settings.current_folder or base_dir
    current_dir = os.path.normpath(os.path.abspath(current_dir))

    # Get search query and normalize it
    search_query = context.scene.hdri_settings.search_query.lower().strip()

    # Check if we can use cached results
    if (hasattr(get_hdri_previews, "cached_dir") and get_hdri_previews.cached_dir == current_dir and 
        hasattr(get_hdri_previews, "cached_query") and get_hdri_previews.cached_query == search_query and 
        hasattr(get_hdri_previews, "cached_items") and get_hdri_previews.cached_items and 
        hasattr(get_hdri_previews, "last_update_time") and get_hdri_previews.last_update_time is not None and
        current_time - get_hdri_previews.last_update_time < 0.5):
        return get_hdri_previews.cached_items
    
    # Set last update time
    if hasattr(get_hdri_previews, "last_update_time"):
        get_hdri_previews.last_update_time = current_time

    pcoll = get_hdri_previews()
    enum_items = [('', 'None', '', 0, 0)]

    # Get enabled extensions
    extensions = []
    if preferences.use_hdr: extensions.append('.hdr')
    if preferences.use_exr: extensions.append('.exr')
    if preferences.use_png: extensions.append('.png')
    if preferences.use_jpg:
        extensions.append('.jpg')
        extensions.append('.jpeg')

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
                # Skip thumbnail files
                if "_thumb" in filename.lower():
                    continue
                    
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

    # Update the cache variables
    get_hdri_previews.cached_dir = current_dir
    get_hdri_previews.cached_query = search_query
    get_hdri_previews.cached_items = enum_items

    return enum_items

def has_hdri_files(context):
    """Check if current folder has any supported HDRI files"""
    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences
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
    """Check if there is an active HDRI loaded"""
    # Detect which render engine is active and use appropriate method
    engine = context.scene.render.engine
    
    if engine == 'VRAY_RENDER_RT':
        # Check V-Ray dome light
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if vray_collection:
            for obj in vray_collection.objects:
                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                    if obj.data and obj.data.node_tree:
                        bitmap_node = obj.data.node_tree.nodes.get("V-Ray Bitmap")
                        if bitmap_node and hasattr(bitmap_node, 'BitmapBuffer') and bitmap_node.BitmapBuffer and bitmap_node.BitmapBuffer.file:
                            return True
    elif engine == 'octane':
        # For Octane - check RGB Image node
        world = context.scene.world
        if world and world.use_nodes:
            for node in world.node_tree.nodes:
                if node.bl_idname == 'OctaneRGBImage' and (node.image or (hasattr(node, 'a_filename') and node.a_filename)):
                    return True
    else:
        # For Cycles and other engines, check world environment texture
        if context.scene.world and context.scene.world.use_nodes:
            for node in context.scene.world.node_tree.nodes:
                if node.type == 'TEX_ENVIRONMENT' and node.image:
                    return True
    
    return False

def get_folders(context):
    """Get list of subfolders in HDRI directory"""
    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences
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