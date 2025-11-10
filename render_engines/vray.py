"""
Quick HDRI Controls - V-Ray specific implementation (Updated for new V-Ray API)
"""
import os
import re
import bpy
from bpy.utils import previews
from mathutils import Vector
from datetime import datetime
import tempfile
import shutil
from math import radians, degrees
import time

# hdri import fix (LOOK INTO)
from .. import hdri_management

# Import from parent module
from ..utils import get_hdri_previews, create_hdri_proxy
from ..core import original_paths

# Re-export common functions with local references
# to maintain compatibility with existing code
generate_previews = hdri_management.generate_previews
has_hdri_files = hdri_management.has_hdri_files
has_active_hdri = hdri_management.has_active_hdri
get_folders = hdri_management.get_folders

def debug_vray_dome_light():
    """Print detailed debug information about the VRay dome light"""
    print("\n=== VRay Dome Light Debug ===")

    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if not vray_collection:
        print("VRay collection not found!")
        return

    print(f"VRay collection: {vray_collection.name}")

    # Find the dome light
    dome_light = None
    for obj in vray_collection.objects:
        if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
            dome_light = obj
            break

    if not dome_light:
        print("VRayDomeLight not found in collection!")
        return

    print(f"Dome Light: {dome_light.name}")
    print(f"Rotation: X:{degrees(dome_light.rotation_euler.x):.1f}° Y:{degrees(dome_light.rotation_euler.y):.1f}° Z:{degrees(dome_light.rotation_euler.z):.1f}°")

    if not dome_light.data or not dome_light.data.node_tree:
        print("Dome light has no node tree!")
        return

    node_tree = dome_light.data.node_tree
    print(f"Node tree: {node_tree.name}")

    # Print all nodes
    print("\nNodes:")
    for node in node_tree.nodes:
        print(f"  • {node.name} ({node.bl_idname})")

        # For V-Ray Bitmap node, print texture information
        if node.name == "V-Ray Bitmap":
            print("    Bitmap attributes:")
            # Check new texture.image API
            if hasattr(node, 'texture') and hasattr(node.texture, 'image'):
                print(f"      texture.image = {node.texture.image}")
                if node.texture.image:
                    print(f"      texture.image.filepath = {node.texture.image.filepath}")
            # Check legacy BitmapBuffer API
            elif hasattr(node, 'BitmapBuffer') and hasattr(node.BitmapBuffer, 'file'):
                print(f"      BitmapBuffer.file = {node.BitmapBuffer.file}")
            else:
                print("      No texture.image or BitmapBuffer.file found")

    print("=== End Debug Info ===\n")


def get_vray_bitmap_image_path(bitmap_node):
    """Get the image path from V-Ray Bitmap node using new or legacy API"""
    if not bitmap_node:
        return None
    
    # Try new API first: texture.image
    if hasattr(bitmap_node, 'texture') and hasattr(bitmap_node.texture, 'image'):
        if bitmap_node.texture.image:
            return bitmap_node.texture.image.filepath
    
    # Fallback to legacy API: BitmapBuffer.file
    elif hasattr(bitmap_node, 'BitmapBuffer') and hasattr(bitmap_node.BitmapBuffer, 'file'):
        return bitmap_node.BitmapBuffer.file
    
    return None


def set_vray_bitmap_image(bitmap_node, filepath):
    """Set the image in V-Ray Bitmap node using new or legacy API"""
    if not bitmap_node or not filepath:
        return False
    
    try:
        # Try new API first: texture.image
        if hasattr(bitmap_node, 'texture') and hasattr(bitmap_node.texture, 'image'):
            print(f"V-Ray: Using new texture.image API to load {filepath}")
            
            # Load image into Blender
            img = bpy.data.images.load(filepath, check_existing=True)
            
            # Set the image on the texture
            bitmap_node.texture.image = img
            
            # Force node update
            if hasattr(bitmap_node, 'update'):
                bitmap_node.update()
            
            return True
        
        # Fallback to legacy API: BitmapBuffer.file
        elif hasattr(bitmap_node, 'BitmapBuffer'):
            print(f"V-Ray: Using legacy BitmapBuffer.file API to load {filepath}")
            bitmap_node.BitmapBuffer.file = filepath
            
            # Force node update
            if hasattr(bitmap_node, 'update'):
                bitmap_node.update()
            
            return True
        
        else:
            print("V-Ray: No compatible API found on bitmap node")
            return False
            
    except Exception as e:
        print(f"V-Ray: Error setting bitmap image: {str(e)}")
        return False


def ensure_vray_setup():
    """Ensure V-Ray collection exists, el camerino and return the dome light"""
    ensure_scene_camera()
    scene = bpy.context.scene

    # Check if V-Ray collection already exists
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")

    if not vray_collection:
        # Append V-Ray collection from consolidated support file
        addon_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        support_file = os.path.join(addon_dir, "misc", "support.blend")

        # Ensure the support file exists
        if not os.path.exists(support_file):
            # Try to find support file in alternative locations (legacy paths)
            alt_support_file = os.path.join(addon_dir, "misc", "Preview.blend")  # Legacy name
            vray_legacy_file = os.path.join(addon_dir, "misc", "vray", "vray_support.blend")  # Old location

            if os.path.exists(alt_support_file):
                support_file = alt_support_file
                print(f"Using legacy Preview.blend file: {support_file}")
            elif os.path.exists(vray_legacy_file):
                support_file = vray_legacy_file
                print(f"Using legacy vray_support.blend file: {support_file}")
            else:
                raise FileNotFoundError(f"Support file not found: {support_file}")

        # Load the support file
        with bpy.data.libraries.load(support_file, link=False) as (data_from, data_to):
            data_to.collections = ["vRay HDRI Controls"]

        # Link collection to scene if the collection was successfully loaded
        if data_to.collections and data_to.collections[0]:
            vray_collection = data_to.collections[0]
            scene.collection.children.link(vray_collection)
            print(f"Successfully loaded vRay HDRI Controls collection from {support_file}")
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
    
def ensure_scene_camera():
    """Ensure that the scene has at least one camera for V-Ray to work with"""
    # Check if a camera already exists in any scene
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA':
            # Ensure camera is linked to the current scene
            if obj.name not in bpy.context.scene.objects:
                # Add camera to current scene
                bpy.context.scene.collection.objects.link(obj)
                print(f"V-Ray: Linked existing camera '{obj.name}' to current scene")
            return True
            
    # No camera found, create a new one
    print("V-Ray: No camera found in scene. Creating default camera.")
    camera_data = bpy.data.cameras.new(name="Default Camera")
    camera_obj = bpy.data.objects.new("Default Camera", camera_data)
    
    # Add to current scene
    bpy.context.scene.collection.objects.link(camera_obj)
    
    # Position the camera at a reasonable distance
    camera_obj.location = (0, -10, 2)
    camera_obj.rotation_euler = (radians(75), 0, 0)
    
    # Set as active camera
    bpy.context.scene.camera = camera_obj
    
    print("V-Ray: Created default camera")
    return True


def ensure_world_nodes():
    """Ensure V-Ray setup is ready (using dome light instead of world nodes)"""
    # For V-Ray we use a dome light instead of world nodes
    dome_light = ensure_vray_setup()

    # Get the node tree and nodes
    node_tree = dome_light.data.node_tree

    # Find V-Ray specific nodes
    bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
    light_dome_node = node_tree.nodes.get("Light Dome")

    if not bitmap_node or not light_dome_node:
        raise Exception("Required V-Ray nodes not found in dome light")

    # Return the dome light, bitmap node and light dome node
    # This is equivalent to returning mapping, env_tex, background in Cycles
    return dome_light, bitmap_node, light_dome_node


def setup_hdri_system(context):
    """Set up the V-Ray HDRI system - FIXED COLOR TRANSFORM"""
    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences
    hdri_settings = context.scene.hdri_settings

    # Ensure V-Ray render handlers are registered
    print("V-Ray: Registering render handlers...")
    register_vray_handlers()
    print("V-Ray: Render handlers registered successfully")

    # Set scene color management defaults
    context.scene.display_settings.display_device = 'sRGB'
    if hasattr(context.scene, 'sequencer_colorspace_settings'):
        context.scene.sequencer_colorspace_settings.name = 'sRGB'

    # Check render engine
    if context.scene.render.engine != 'VRAY_RENDER_RT':
        # Automatically switch to V-Ray
        context.scene.render.engine = 'VRAY_RENDER_RT'
        return {'INFO'}, "Render engine switched to V-Ray"

    # FIXED: Set the view transform to AgX properly
    try:
        # Check if 'AgX' is available in the view transform options
        available_transforms = [item.identifier for item in context.scene.view_settings.bl_rna.properties['view_transform'].enum_items]
        print(f"V-Ray: Available view transforms: {available_transforms}")
        
        if 'AgX' in available_transforms:
            context.scene.view_settings.view_transform = 'AgX'
            print("V-Ray: Successfully set view transform to AgX")
        elif 'Standard' in available_transforms:
            # Fallback to Standard if AgX is not available
            context.scene.view_settings.view_transform = 'Standard'
            print("V-Ray: AgX not available, set view transform to Standard")
        else:
            print("V-Ray: Neither AgX nor Standard view transform available")
    except Exception as e:
        print(f"V-Ray: Error setting view transform: {str(e)}")

    # Rest of the function remains the same...
    # Verify HDRI directory exists and is accessible
    if not preferences.hdri_directory or not os.path.exists(preferences.hdri_directory):
        return {'ERROR'}, "HDRI directory not found. Please select a valid directory in preferences."

    # If current folder is not set or doesn't exist, reset to HDRI directory
    if not hdri_settings.current_folder or not os.path.exists(hdri_settings.current_folder):
        hdri_settings.current_folder = preferences.hdri_directory

    # Initialize proxy settings from preferences
    from ..utils import initialize_hdri_settings_from_preferences
    initialize_hdri_settings_from_preferences(context)

    # Setup V-Ray dome light
    try:
        dome_light = ensure_vray_setup()

        # Check if there are any HDRIs in the current directory
        if not has_hdri_files(context):
            return {'WARNING'}, "(Only shows if no direct HDRIs are preset - Access folders)"

        # Generate previews for the current directory
        enum_items = generate_previews(None, context)

        # If we have HDRIs, set the preview to the first one
        if len(enum_items) > 1:
            hdri_settings.hdri_preview = enum_items[1][0]

        # Ensure V-Ray render handlers are registered
        register_vray_handlers()

        # Force redraw of UI
        for area in context.screen.areas:
            area.tag_redraw()

        return {'INFO'}, "HDRI system initialized successfully"

    except Exception as e:
        return {'ERROR'}, f"Failed to setup HDRI system: {str(e)}"


def update_background_strength(self, context):
    """Update handler for background strength changes"""
    print(f"V-Ray strength update called. Self type: {type(self)}")
    print(f"Current strength value: {self.background_strength}")

    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        print(f"Found V-Ray collection: {vray_collection.name}")
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                print(f"Found VRayDomeLight: {obj.name}")
                if obj.data and obj.data.node_tree:
                    light_dome = obj.data.node_tree.nodes.get("Light Dome")
                    if light_dome:
                        print(f"Found Light Dome node")
                        # Debug inputs
                        for i, input in enumerate(light_dome.inputs):
                            if hasattr(input, 'name'):
                                print(f"Input {i}: {input.name}")

                        # Try using the same approach as in original file
                        try:
                            print(f"Attempting to set Intensity to {self.background_strength}")
                            light_dome.inputs['Intensity'].value = self.background_strength
                            print("Successfully set intensity by name")
                        except Exception as e:
                            print(f"Error setting intensity by name: {str(e)}")
                            # Try alternative method
                            try:
                                light_dome.inputs[26].value = self.background_strength
                                print("Successfully set intensity by index 26")
                            except Exception as e2:
                                print(f"Error setting intensity by index: {str(e2)}")

                        # Force node update
                        try:
                            light_dome.update()
                            print("Called light_dome.update()")
                        except Exception as e:
                            print(f"Error updating node: {str(e)}")

                        # Force redraw
                        for area in context.screen.areas:
                            if area.type == 'VIEW_3D':
                                area.tag_redraw()
                                print("Redrawing 3D View")

                        break


def reset_strength(context):
    """Reset the strength of the VRayDomeLight to 1.0"""
    import time

    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                light_data = obj.data
                if light_data and light_data.node_tree:
                    light_dome = light_data.node_tree.nodes.get("Light Dome")
                    if light_dome:
                        # Set intensity to 1.0 using index 26 directly
                        if len(light_dome.inputs) > 26:
                            light_dome.inputs[26].value = 1.0
                            print("V-Ray: Reset intensity to 1.0")

                            # Also update the hdri_settings value
                            context.scene.hdri_settings.background_strength = 1.0

                            # Force updates
                            if hasattr(light_dome, 'update'):
                                light_dome.update()
                            if hasattr(light_data.node_tree, 'update_tag'):
                                light_data.node_tree.update_tag()

                            # Force viewport update
                            for area in context.screen.areas:
                                if area.type == 'VIEW_3D':
                                    area.tag_redraw()

                            return {'FINISHED'}

    print("V-Ray: No VRay dome light found to reset strength")
    return {'CANCELLED'}



def set_hdri(context, filepath):
    """Load a new HDRI into V-Ray - Updated for new V-Ray API with better error handling"""
    print(f"V-Ray set_hdri called with filepath: {filepath}")
    ensure_scene_camera()
    
    # First, ensure V-Ray collection exists
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if not vray_collection:
        print("ERROR: V-Ray collection not found. Attempting to create V-Ray setup...")
        try:
            dome_light = ensure_vray_setup()
            print("V-Ray setup created successfully")
        except Exception as e:
            print(f"ERROR: Failed to create V-Ray setup: {str(e)}")
            return False

    # Find the dome light
    dome_light = None
    for obj in vray_collection.objects:
        if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
            dome_light = obj
            break

    if not dome_light:
        print("ERROR: VRayDomeLight not found in collection")
        return False

    # Check if dome light has proper data and node tree
    if not dome_light.data:
        print("ERROR: VRayDomeLight has no data")
        return False
        
    if not dome_light.data.node_tree:
        print("ERROR: VRayDomeLight has no node tree")
        return False

    node_tree = dome_light.data.node_tree
    bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
    light_dome_node = node_tree.nodes.get("Light Dome")

    if not bitmap_node:
        print("ERROR: V-Ray Bitmap node not found")
        print(f"Available nodes: {[node.name for node in node_tree.nodes]}")
        return False
        
    if not light_dome_node:
        print("ERROR: Light Dome node not found")
        return False

    # Get settings with safe access
    hdri_settings = context.scene.hdri_settings
    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences

    # Store current visibility state BEFORE making changes - with safe access
    current_visibility = True  # Default to visible
    if hasattr(hdri_settings, 'hdri_visible'):
        current_visibility = hdri_settings.hdri_visible
        print(f"V-Ray: Current visibility state: {current_visibility}")
    else:
        print("WARNING: hdri_visible property not found, defaulting to True")

    # Store previous state - Always store the original file path, not proxy
    current_file = ""
    if hasattr(bitmap_node, 'texture') and bitmap_node.texture and bitmap_node.texture.image:
        current_file = bitmap_node.texture.image.filepath
        print(f"V-Ray: Got current file from texture.image: {current_file}")
    elif hasattr(bitmap_node, 'BitmapBuffer') and hasattr(bitmap_node.BitmapBuffer, 'file') and bitmap_node.BitmapBuffer.file:
        current_file = bitmap_node.BitmapBuffer.file
        print(f"V-Ray: Got current file from BitmapBuffer.file: {current_file}")
    else:
        print("V-Ray: No current file found")
    
    current_file = original_paths.get(os.path.basename(current_file), current_file)

    if current_file and current_file != filepath:
        # Store previous state using original file path
        hdri_settings.previous_hdri_path = current_file
        if len(light_dome_node.inputs) > 26:
            hdri_settings.previous_strength = light_dome_node.inputs[26].value
        else:
            hdri_settings.previous_strength = 1.0
        hdri_settings.previous_rotation = dome_light.rotation_euler.copy()
        print(f"V-Ray: Stored previous HDRI path: {current_file}")

    # Store current rotation if keep_rotation is enabled
    current_rotation = None
    if preferences.keep_rotation:
        current_rotation = dome_light.rotation_euler.copy()
        print(f"V-Ray Keep Rotation: Storing current rotation {[degrees(r) for r in current_rotation]}")

    # Always store the original filepath in our tracking
    original_paths[os.path.basename(filepath)] = filepath

    # Check if V-Ray viewport rendering is active - temporarily disable if needed
    vray_render_active = False
    if hasattr(bpy.context.scene, 'vray') and hasattr(bpy.context.scene.vray, 'Exporter'):
        vray_render_active = bpy.context.scene.vray.Exporter.auto_save_render
        if vray_render_active:
            bpy.context.scene.vray.Exporter.auto_save_render = False
            time.sleep(0.2)  # Give it a moment

    # Load the HDRI - Use proxy if enabled
    try:
        target_path = filepath
        
        if hdri_settings.proxy_resolution != 'ORIGINAL':
            proxy_path = create_hdri_proxy(filepath, hdri_settings.proxy_resolution)
            if proxy_path and os.path.exists(proxy_path):
                # Store original path mapping before loading proxy
                original_paths[os.path.basename(proxy_path)] = filepath
                target_path = proxy_path
                print(f"V-Ray: Using proxy: {target_path}")
            else:
                # Fallback to original if proxy creation fails
                target_path = filepath
                print(f"V-Ray: Proxy creation failed, using original: {target_path}")
        else:
            print(f"V-Ray: Using original file: {target_path}")
        
        # NEW V-RAY API: Set both BitmapBuffer.file AND texture.image
        print(f"V-Ray: Loading HDRI using new API: {target_path}")
        
        # Method 1: Set BitmapBuffer.file (legacy support)
        if hasattr(bitmap_node, 'BitmapBuffer') and hasattr(bitmap_node.BitmapBuffer, 'file'):
            bitmap_node.BitmapBuffer.file = target_path
            print(f"V-Ray: Set BitmapBuffer.file = {target_path}")
        else:
            print("WARNING: BitmapBuffer.file not available")
        
        # Method 2: Set texture.image (NEW REQUIRED METHOD)
        if hasattr(bitmap_node, 'texture') and bitmap_node.texture:
            print("V-Ray: Setting texture.image...")
            
            # Clear existing image reference if any
            if bitmap_node.texture.image:
                old_image = bitmap_node.texture.image
                bitmap_node.texture.image = None
                # Only remove if no other users
                if old_image.users == 0:
                    bpy.data.images.remove(old_image)
                    print("V-Ray: Removed old image from memory")
            
            # Load and set new image
            try:
                new_image = bpy.data.images.load(target_path, check_existing=True)
                bitmap_node.texture.image = new_image
                print(f"V-Ray: Set texture.image = {new_image.name}")
                
                # Ensure image is marked as HDRI if it's an HDR/EXR file
                if target_path.lower().endswith(('.hdr', '.exr')):
                    new_image.colorspace_settings.name = 'Linear'
                    print("V-Ray: Set image colorspace to Linear for HDRI")
                
            except Exception as e:
                print(f"V-Ray: Error loading image into texture.image: {str(e)}")
                # Don't fail completely, just continue with BitmapBuffer.file
        else:
            print("WARNING: bitmap_node.texture not available")

        # Apply rotation based on keep_rotation setting
        if preferences.keep_rotation and current_rotation is not None:
            print(f"V-Ray Keep Rotation: Applying stored rotation {[degrees(r) for r in current_rotation]}")
            dome_light.rotation_euler = current_rotation
        else:
            print("V-Ray Keep Rotation: Resetting to zero")
            dome_light.rotation_euler = (0, 0, 0)

        # Set intensity using index 26 directly
        if len(light_dome_node.inputs) > 26:
            light_dome_node.inputs[26].value = hdri_settings.background_strength
            print(f"V-Ray Strength: Set Intensity input[26] to {hdri_settings.background_strength}")

            # Force light dome node update
            if hasattr(light_dome_node, 'update'):
                light_dome_node.update()

        # RESTORE visibility state after loading new HDRI
        if hasattr(hdri_settings, 'hdri_visible'):
            set_hdri_visibility_direct(context, current_visibility)
            print(f"V-Ray: Restored visibility to {current_visibility}")

        # Force node updates
        if hasattr(bitmap_node, 'update'):
            bitmap_node.update()
            print("V-Ray: Updated bitmap node")
            
        if hasattr(node_tree, 'update_tag'):
            node_tree.update_tag()
            print("V-Ray: Updated node tree")

        # Restore V-Ray viewport rendering if it was active
        if vray_render_active:
            time.sleep(0.2)
            bpy.context.scene.vray.Exporter.auto_save_render = True

        # Force viewport update
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        print(f"V-Ray: Successfully loaded HDRI: {target_path}")
        return True
        
    except Exception as e:
        print(f"V-Ray: Failed to load HDRI: {str(e)}")
        import traceback
        traceback.print_exc()

        # Make sure to re-enable V-Ray rendering if we had an error
        if vray_render_active:
            bpy.context.scene.vray.Exporter.auto_save_render = True

        return False


def update_hdri_proxy(self, context):
    """Update handler for proxy resolution and mode changes - Updated for new V-Ray API"""
    import time

    # V-Ray uses node tree in VRayDomeLight
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if not vray_collection:
        print("V-Ray Proxy Update: Collection not found")
        return

    dome_light = None
    for obj in vray_collection.objects:
        if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
            dome_light = obj
            break

    if not dome_light:
        print("V-Ray Proxy Update: Dome light not found")
        return

    node_tree = dome_light.data.node_tree
    bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
    light_dome_node = node_tree.nodes.get("Light Dome")

    if not bitmap_node or not light_dome_node:
        print("V-Ray Proxy Update: Required nodes not found")
        return

    # Close the proxy settings panel on change
    context.scene.hdri_settings.show_proxy_settings = False

    # Get current file path from either new or old API
    current_file = ""
    if hasattr(bitmap_node, 'texture') and bitmap_node.texture and bitmap_node.texture.image:
        current_file = bitmap_node.texture.image.filepath
        print(f"V-Ray Proxy Update: Got current file from texture.image: {current_file}")
    elif hasattr(bitmap_node, 'BitmapBuffer') and hasattr(bitmap_node.BitmapBuffer, 'file'):
        current_file = bitmap_node.BitmapBuffer.file
        print(f"V-Ray Proxy Update: Got current file from BitmapBuffer.file: {current_file}")

    if not current_file or not os.path.exists(current_file):
        print(f"V-Ray Proxy Update: Current file does not exist: {current_file}")
        return

    # Find the original high-resolution path (same logic as before)
    original_path = None

    # Check all possible sources for original path
    if os.path.basename(current_file) in original_paths:
        original_path = original_paths[os.path.basename(current_file)]
    elif current_file in original_paths:
        original_path = original_paths[current_file]
    else:
        # Try to determine if current file is a proxy
        current_dir = os.path.dirname(current_file)
        current_basename = os.path.basename(current_file)

        if any(res in current_basename for res in ['_1K', '_2K', '_4K', '_6K', '_8K']):
            base_name = os.path.splitext(current_basename)[0]
            base_name = re.sub(r'_[1248]K', '', base_name)
            ext = os.path.splitext(current_basename)[1]

            parent_dir = os.path.dirname(current_dir)
            potential_dirs = [current_dir, parent_dir] if current_dir.endswith('proxies') else [current_dir]

            # Look in potential directories
            for search_dir in potential_dirs:
                if os.path.exists(search_dir):
                    potential_originals = [
                        f for f in os.listdir(search_dir)
                        if f.startswith(base_name) and f.endswith(ext)
                        and not any(res in f for res in ['_1K', '_2K', '_4K', '_6K', '_8K'])
                    ]

                    if potential_originals:
                        original_path = os.path.join(search_dir, potential_originals[0])
                        original_paths[os.path.basename(current_file)] = original_path
                        print(f"V-Ray Proxy Update: Found original: {original_path}")
                        break

        # If no original found, use current as original
        if not original_path:
            original_path = current_file
            print(f"V-Ray Proxy Update: Using current as original: {original_path}")

    # Ensure the original path exists
    if not original_path or not os.path.exists(original_path):
        print(f"V-Ray Proxy Update: Original file not found, using current")
        original_path = current_file

    # Store state and disable V-Ray viewport rendering temporarily
    vray_render_active = False
    if hasattr(bpy.context.scene, 'vray') and hasattr(bpy.context.scene.vray, 'Exporter'):
        vray_render_active = bpy.context.scene.vray.Exporter.auto_save_render

    # Apply proxy resolution to current HDRI
    resolution = context.scene.hdri_settings.proxy_resolution
    print(f"V-Ray Proxy Update: Target resolution: {resolution}")

    try:
        # Update the HDRI file using NEW V-RAY API
        if resolution == 'ORIGINAL':
            # Set to original file
            print(f"V-Ray Proxy Update: Setting to original file: {original_path}")
            target_path = original_path

            # Clean up tracking
            if current_file != original_path and os.path.basename(current_file) in original_paths:
                del original_paths[os.path.basename(current_file)]
        else:
            # Create and use proxy
            proxy_path = create_hdri_proxy(original_path, resolution)
            if proxy_path and os.path.exists(proxy_path):
                # Update tracking and set path
                original_paths[os.path.basename(proxy_path)] = original_path
                print(f"V-Ray Proxy Update: Setting to proxy: {proxy_path}")
                target_path = proxy_path
            else:
                print(f"V-Ray Proxy Update: Proxy creation failed, using original")
                target_path = original_path

        # NEW V-RAY API: Update both BitmapBuffer.file AND texture.image
        
        # Method 1: Set BitmapBuffer.file (legacy support)
        if hasattr(bitmap_node, 'BitmapBuffer') and hasattr(bitmap_node.BitmapBuffer, 'file'):
            bitmap_node.BitmapBuffer.file = target_path
            print(f"V-Ray Proxy Update: Set BitmapBuffer.file = {target_path}")
        
        # Method 2: Set texture.image (NEW REQUIRED METHOD)
        if hasattr(bitmap_node, 'texture') and bitmap_node.texture:
            # Clear existing image reference if any
            if bitmap_node.texture.image:
                old_image = bitmap_node.texture.image
                bitmap_node.texture.image = None
                # Only remove if no other users
                if old_image.users == 0:
                    bpy.data.images.remove(old_image)
                    print("V-Ray Proxy Update: Removed old image from memory")
            
            # Load and set new image
            try:
                new_image = bpy.data.images.load(target_path, check_existing=True)
                bitmap_node.texture.image = new_image
                print(f"V-Ray Proxy Update: Set texture.image = {new_image.name}")
                
                # Ensure image is marked as HDRI if it's an HDR/EXR file
                if target_path.lower().endswith(('.hdr', '.exr')):
                    new_image.colorspace_settings.name = 'Linear'
                
            except Exception as e:
                print(f"V-Ray Proxy Update: Error loading image into texture.image: {str(e)}")

        # Update node and force redraw
        if hasattr(bitmap_node, 'update'):
            bitmap_node.update()

        # Update intensity
        if len(light_dome_node.inputs) > 26:
            light_dome_node.inputs[26].value = context.scene.hdri_settings.background_strength
            light_dome_node.update()

        # Force entire node tree update
        node_tree.update_tag()

        # Sleep briefly to let updates process
        time.sleep(0.2)

        # Update proxy mode handlers
        from ..utils import update_proxy_handlers
        update_proxy_handlers(context.scene.hdri_settings.proxy_mode)

        # Force viewport update
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    except Exception as e:
        print(f"V-Ray Proxy Update: Error during update: {str(e)}")
        import traceback
        traceback.print_exc()

    print(f"V-Ray Proxy Update: Completed for resolution {resolution}")


def toggle_hdri_visibility(context):
    """Toggle the visibility of the HDRI and sync with the UI property"""
    hdri_settings = context.scene.hdri_settings

    # Toggle the property first
    if hasattr(hdri_settings, 'hdri_visible'):
        hdri_settings.hdri_visible = not hdri_settings.hdri_visible
        new_visibility = hdri_settings.hdri_visible
    else:
        # If property doesn't exist, default to toggling from True to False
        new_visibility = False
        print("WARNING: hdri_visible property not found, defaulting to False")

    print(f"V-Ray: Toggling visibility to: {new_visibility}")

    # Apply the visibility to V-Ray
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                light_data = obj.data
                if light_data and light_data.node_tree:
                    light_dome = light_data.node_tree.nodes.get("Light Dome")
                    if light_dome and len(light_dome.inputs) > 27:
                        # Set the invisible input (True = invisible, False = visible)
                        light_dome.inputs[27].value = not new_visibility
                        print(f"V-Ray: Set Light Dome invisible input to: {not new_visibility}")

                        # Force update
                        if hasattr(light_dome, 'update'):
                            light_dome.update()
                        if hasattr(light_data.node_tree, 'update_tag'):
                            light_data.node_tree.update_tag()

                        # Force viewport update
                        for area in context.screen.areas:
                            if area.type == 'VIEW_3D':
                                area.tag_redraw()

                        return new_visibility
                break

    print("V-Ray: Could not find V-Ray dome light to toggle visibility")
    return new_visibility


def set_hdri_visibility(context, visible):
    """Set HDRI visibility to a specific state"""
    hdri_settings = context.scene.hdri_settings
    
    # Update the UI property if it exists
    if hasattr(hdri_settings, 'hdri_visible'):
        hdri_settings.hdri_visible = visible

    # Apply the visibility to V-Ray
    set_hdri_visibility_direct(context, visible)
    
    return visible


def set_hdri_visibility_direct(context, visible):
    """Set HDRI visibility without updating the UI property"""
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                light_data = obj.data
                if light_data and light_data.node_tree:
                    light_dome = light_data.node_tree.nodes.get("Light Dome")
                    if light_dome and len(light_dome.inputs) > 27:
                        # Set the invisible input (True = invisible, False = visible)
                        light_dome.inputs[27].value = not visible
                        print(f"V-Ray: Set visibility to {visible} (invisible input = {not visible})")

                        # Force update
                        if hasattr(light_dome, 'update'):
                            light_dome.update()
                        if hasattr(light_data.node_tree, 'update_tag'):
                            light_data.node_tree.update_tag()
                        return
                break


def get_hdri_visible(context):
    """Check if the HDRI is visible in V-Ray - FIXED DEBUG SPAM"""
    world = context.scene.world
    if world and world.use_nodes:
        for node in world.node_tree.nodes:
            if node.bl_idname == 'OctaneTextureEnvironment':
                # Find the one connected to Visible Environment
                for output in node.outputs:
                    for link in output.links:
                        if link.to_socket.name == 'Visible Environment':
                            visible = node.inputs['Backplate'].default_value
                            # REMOVED DEBUG PRINT to stop spam
                            return visible

    # Check V-Ray dome light visibility
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                light_data = obj.data
                if light_data and light_data.node_tree:
                    light_dome = light_data.node_tree.nodes.get("Light Dome")
                    if light_dome and len(light_dome.inputs) > 27:
                        # The visibility state is the inverse of the "Invisible" input
                        visible = not light_dome.inputs[27].value
                        # REMOVED DEBUG PRINT to stop spam
                        return visible

    # Default to visible if not found or can't determine
    return True



def reset_rotation(context):
    """Reset the rotation of the VRayDomeLight to zero"""
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                # Reset all rotation axes to zero
                obj.rotation_euler = (0, 0, 0)
                print("V-Ray Rotation: Reset all rotation axes to 0")

                # Force viewport update
                context.view_layer.update()
                return {'FINISHED'}

    print("V-Ray Rotation: No VRay dome light found to reset rotation")
    return {'CANCELLED'}


def quick_rotate_hdri(context, axis, direction):
    """Quick rotate the HDRI for V-Ray"""
    # Get addon name properly
    addon_name = __package__.split('.')[0]

    # Correctly access the preferences
    preferences = context.preferences.addons[addon_name].preferences
    rotation_increment = preferences.rotation_increment

    print(f"V-Ray Rotation: Using rotation increment of {rotation_increment}° from preferences")

    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                # Get current rotation value in degrees
                current_rotation_rad = obj.rotation_euler[axis]
                current_rotation_deg = degrees(current_rotation_rad)
                print(f"V-Ray Rotation: Current rotation on axis {axis}: {current_rotation_deg:.2f}°")

                if direction == -99:  # Reset
                    # Set rotation directly to 0 for the specified axis
                    obj.rotation_euler[axis] = 0
                    print(f"V-Ray Rotation: Reset rotation on axis {axis} to 0°")
                else:  # Regular rotation
                    # Convert increment from degrees to radians
                    increment_radians = radians(rotation_increment)

                    # Calculate new rotation
                    new_rotation_rad = current_rotation_rad + (direction * increment_radians)
                    new_rotation_deg = degrees(new_rotation_rad)

                    # Apply the new rotation
                    obj.rotation_euler[axis] = new_rotation_rad
                    print(f"V-Ray Rotation: Changed rotation on axis {axis} from {current_rotation_deg:.2f}° to {new_rotation_deg:.2f}° using increment {rotation_increment}°")

                # Force viewport update
                context.view_layer.update()
                return {'FINISHED'}

    print("V-Ray Rotation: No VRay dome light found")
    return {'CANCELLED'}


def delete_world(context):
    """Delete the V-Ray HDRI setup"""
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        # First try to unlink the collection from all scenes
        for scene in bpy.data.scenes:
            try:
                if vray_collection.name in scene.collection.children:
                    scene.collection.children.unlink(vray_collection)
                    print(f"V-Ray Delete: Unlinked collection from scene {scene.name}")
            except Exception as e:
                print(f"V-Ray Delete: Error unlinking from scene: {str(e)}")

        # Store objects and lights to remove
        objects_to_remove = []
        lights_to_remove = []

        # Gather the objects first, without changing the collection during iteration
        for obj in vray_collection.objects:
            obj_name = obj.name  # Store name before removal
            objects_to_remove.append((obj, obj_name))
            if obj.data and obj.type == 'LIGHT':
                lights_to_remove.append((obj.data, obj.data.name))

        # Clear objects from collection
        for obj, obj_name in objects_to_remove:
            try:
                vray_collection.objects.unlink(obj)
                print(f"V-Ray Delete: Unlinked object {obj_name}")
            except Exception as e:
                print(f"V-Ray Delete: Error unlinking object: {str(e)}")

            try:
                bpy.data.objects.remove(obj)
                print(f"V-Ray Delete: Removed object {obj_name}")
            except Exception as e:
                print(f"V-Ray Delete: Error removing object: {str(e)}")

        # Remove light data
        for light, light_name in lights_to_remove:
            try:
                bpy.data.lights.remove(light)
                print(f"V-Ray Delete: Removed light {light_name}")
            except Exception as e:
                print(f"V-Ray Delete: Error removing light: {str(e)}")

        # Finally remove the collection
        try:
            collection_name = vray_collection.name
            bpy.data.collections.remove(vray_collection)
            print(f"V-Ray Delete: Removed V-Ray collection {collection_name}")
        except Exception as e:
            print(f"V-Ray Delete: Error removing collection: {str(e)}")

        return True
    else:
        print("V-Ray Delete: V-Ray collection not found")
        return False


def reset_hdri(context):
    """Reset to previously selected HDRI in V-Ray"""
    ensure_scene_camera()
    hdri_settings = context.scene.hdri_settings
    addon_name = __package__.split('.')[0]
    preferences = context.preferences.addons[addon_name].preferences

    # Check if we have a previous HDRI to restore
    if not hdri_settings.previous_hdri_path:
        return {'WARNING'}, "No previous HDRI to restore"

    # Verify the file still exists
    if not os.path.exists(hdri_settings.previous_hdri_path):
        return {'ERROR'}, "Previous HDRI file could not be found"

    try:
        # Find the V-Ray dome light
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if not vray_collection:
            return {'ERROR'}, "V-Ray collection not found"

        dome_light = None
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                dome_light = obj
                break

        if not dome_light:
            return {'ERROR'}, "VRayDomeLight not found"

        node_tree = dome_light.data.node_tree
        bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
        light_dome_node = node_tree.nodes.get("Light Dome")

        if not bitmap_node or not light_dome_node:
            return {'ERROR'}, "V-Ray nodes not found"

        # Store current state before making changes
        current_file = get_vray_bitmap_image_path(bitmap_node)
        reset_to_path = hdri_settings.previous_hdri_path
        reset_to_path = original_paths.get(os.path.basename(reset_to_path), reset_to_path)

        # Load the appropriate version (proxy or original)
        if hdri_settings.proxy_resolution != 'ORIGINAL':
            # Create and load proxy
            proxy_path = create_hdri_proxy(reset_to_path, hdri_settings.proxy_resolution)
            if proxy_path:
                # Store original path mapping
                original_paths[os.path.basename(proxy_path)] = reset_to_path
                success = set_vray_bitmap_image(bitmap_node, proxy_path)
            else:
                # Fallback to original if proxy creation fails
                success = set_vray_bitmap_image(bitmap_node, reset_to_path)
        else:
            # Load original
            success = set_vray_bitmap_image(bitmap_node, reset_to_path)

        if not success:
            return {'ERROR'}, "Failed to set HDRI image"

        # Update the preview selection
        enum_items = generate_previews(None, context)
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
            try:
                # Use index 26 directly for the intensity input
                if len(light_dome_node.inputs) > 26:
                    light_dome_node.inputs[26].value = hdri_settings.previous_strength
                    print(f"V-Ray Reset: Restored intensity input[26] to {hdri_settings.previous_strength}")

                    # Force node update
                    if hasattr(light_dome_node, 'update'):
                        light_dome_node.update()
            except Exception as e:
                print(f"V-Ray Reset: Could not restore strength: {str(e)}")

        # Restore previous rotation if available
        if hasattr(hdri_settings, 'previous_rotation'):
            try:
                dome_light.rotation_euler = hdri_settings.previous_rotation
            except Exception as e:
                print(f"V-Ray Reset HDRI: Could not restore rotation: {str(e)}")

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
        from ..utils import get_hdri_previews
        get_hdri_previews.cached_dir = None
        get_hdri_previews.cached_items = []

        # Force node tree update
        if hasattr(node_tree, 'update_tag'):
            node_tree.update_tag()

        # Force redraw of viewport
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'INFO'}, "HDRI reset successful"

    except Exception as e:
        print(f"Reset HDRI error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'ERROR'}, f"Failed to reset HDRI: {str(e)}"


@bpy.app.handlers.persistent
def reload_original_for_render(dummy):
    """Handler to replace proxy with full-quality HDRI before rendering"""
    context = bpy.context
    settings = context.scene.hdri_settings

    print("V-Ray: reload_original_for_render handler called")

    # Only swap for 'VIEWPORT' proxy mode
    if settings.proxy_mode != 'VIEWPORT':
        print("V-Ray: Keeping current HDRI - not in VIEWPORT proxy mode")
        return

    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                node_tree = obj.data.node_tree
                bitmap_node = node_tree.nodes.get("V-Ray Bitmap")

                if bitmap_node:
                    current_file = get_vray_bitmap_image_path(bitmap_node)

                    # Store the current file for restoring later
                    if not hasattr(context.scene, "vray_proxy_path"):
                        bpy.types.Scene.vray_proxy_path = bpy.props.StringProperty()
                    context.scene.vray_proxy_path = current_file

                    # Find original high-res file
                    original_path = original_paths.get(os.path.basename(current_file), None) if current_file else None

                    # If original path not found in tracking, try to determine by filename pattern
                    if not original_path and current_file:
                        # Check if we're in a proxies folder
                        dir_path = os.path.dirname(current_file)
                        if os.path.basename(dir_path).lower() == 'proxies':
                            # Get the parent folder (where originals should be)
                            parent_dir = os.path.dirname(dir_path)

                            # Get base filename without resolution marker
                            base_name = os.path.basename(current_file)
                            base_name = re.sub(r'_[1248][kK]', '', os.path.splitext(base_name)[0])
                            ext = os.path.splitext(current_file)[1]

                            # Look for matching files in parent dir
                            for f in os.listdir(parent_dir):
                                if f.startswith(base_name) and f.endswith(ext):
                                    potential_path = os.path.join(parent_dir, f)
                                    # Skip if it's another proxy
                                    if not re.search(r'_[1248][kK]', f):
                                        original_path = potential_path
                                        print(f"V-Ray: Found original by name pattern: {original_path}")
                                        break

                    # If we found an original, use it
                    if original_path and os.path.exists(original_path):
                        print(f"V-Ray: Swapping to full-quality HDRI for rendering: {original_path}")
                        set_vray_bitmap_image(bitmap_node, original_path)

                        # Force node update
                        if hasattr(node_tree, 'update_tag'):
                            node_tree.update_tag()
                    else:
                        print(f"V-Ray: No original found for {current_file}, using as-is for rendering")
                break


@bpy.app.handlers.persistent 
def reset_proxy_after_render_complete(dummy):
    """Handler to reset to proxy after rendering completes - Updated for new API"""
    context = bpy.context
    settings = context.scene.hdri_settings

    print("V-Ray: reset_proxy_after_render_complete handler called")

    # Only swap back for 'VIEWPORT' proxy mode
    if settings.proxy_mode != 'VIEWPORT':
        return

    # Check if we stored a proxy path
    if hasattr(context.scene, "vray_proxy_path") and context.scene.vray_proxy_path:
        proxy_path = context.scene.vray_proxy_path

        if proxy_path and os.path.exists(proxy_path):
            vray_collection = bpy.data.collections.get("vRay HDRI Controls")
            if vray_collection:
                for obj in vray_collection.objects:
                    if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                        node_tree = obj.data.node_tree
                        bitmap_node = node_tree.nodes.get("V-Ray Bitmap")

                        if bitmap_node:
                            print(f"V-Ray: Render complete, swapping back to proxy: {proxy_path}")
                            
                            # Set using both old and new API
                            if hasattr(bitmap_node, 'BitmapBuffer') and hasattr(bitmap_node.BitmapBuffer, 'file'):
                                bitmap_node.BitmapBuffer.file = proxy_path
                            
                            if hasattr(bitmap_node, 'texture') and bitmap_node.texture:
                                try:
                                    new_image = bpy.data.images.load(proxy_path, check_existing=True)
                                    bitmap_node.texture.image = new_image
                                except Exception as e:
                                    print(f"V-Ray: Error setting texture.image for proxy restore: {str(e)}")

                            # Clear the stored path
                            context.scene.vray_proxy_path = ""

                            # Force node update
                            bitmap_node.update()
                            if hasattr(node_tree, 'update_tag'):
                                node_tree.update_tag()

                            break


@bpy.app.handlers.persistent
def reset_proxy_after_render(dummy):
    """Handler to reset to proxy after render cancellation"""
    context = bpy.context
    settings = context.scene.hdri_settings

    print("V-Ray: reset_proxy_after_render handler called")

    # Only swap back for 'VIEWPORT' proxy mode
    if settings.proxy_mode == 'VIEWPORT':
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if vray_collection:
            for obj in vray_collection.objects:
                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                    node_tree = obj.data.node_tree
                    bitmap_node = node_tree.nodes.get("V-Ray Bitmap")

                    if bitmap_node:
                        # Check if we stored a temporary proxy path
                        if 'temp_proxy_path' in bitmap_node:
                            proxy_path = bitmap_node['temp_proxy_path']
                            if proxy_path and os.path.exists(proxy_path):
                                # Restore the proxy
                                set_vray_bitmap_image(bitmap_node, proxy_path)
                                print(f"V-Ray: Render cancelled, restored proxy: {proxy_path}")
                                del bitmap_node['temp_proxy_path']
                                return

                        # Fallback to creating a new proxy
                        current_file = get_vray_bitmap_image_path(bitmap_node)
                        if current_file and os.path.exists(current_file):
                            proxy_path = create_hdri_proxy(current_file, settings.proxy_resolution)
                            if proxy_path:
                                set_vray_bitmap_image(bitmap_node, proxy_path)
                                print(f"V-Ray: Render cancelled, created new proxy: {proxy_path}")
                    break
                    
def get_current_hdri_path(context):
    """Get the path of the currently loaded HDRI in V-Ray - Updated for new API"""
    vray_collection = bpy.data.collections.get("vRay HDRI Controls")
    if vray_collection:
        for obj in vray_collection.objects:
            if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                node_tree = obj.data.node_tree
                bitmap_node = node_tree.nodes.get("V-Ray Bitmap")
                if bitmap_node:
                    # Try new API first (texture.image)
                    if hasattr(bitmap_node, 'texture') and bitmap_node.texture and bitmap_node.texture.image:
                        return bitmap_node.texture.image.filepath
                    # Fallback to old API (BitmapBuffer.file)
                    elif hasattr(bitmap_node, 'BitmapBuffer') and hasattr(bitmap_node.BitmapBuffer, 'file'):
                        return bitmap_node.BitmapBuffer.file
    return None

def register_vray_handlers():
    """Register V-Ray specific handlers"""
    if not hasattr(bpy.types.Scene, "vray_proxy_path"):
        bpy.types.Scene.vray_proxy_path = bpy.props.StringProperty()

    # Remove any existing handlers first to avoid duplicates
    unregister_vray_handlers()

    # Register the handlers
    bpy.app.handlers.render_init.append(reload_original_for_render)
    bpy.app.handlers.render_cancel.append(reset_proxy_after_render)
    bpy.app.handlers.render_complete.append(reset_proxy_after_render_complete)

    print("V-Ray: Render handlers registered")


def unregister_vray_handlers():
    """Unregister V-Ray specific handlers"""
    if reload_original_for_render in bpy.app.handlers.render_init:
        bpy.app.handlers.render_init.remove(reload_original_for_render)
    if reset_proxy_after_render in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.remove(reset_proxy_after_render)
    if reset_proxy_after_render_complete in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(reset_proxy_after_render_complete)
    print("V-Ray: Handlers unregistered")


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