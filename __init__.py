"""
Quick HDRI Controls - Main addon entry point
"""
import os
import bpy
import sys
import json
from bpy.app.handlers import persistent

# Store addon info
bl_info = {
    "name": "Quick HDRI Controls",
    "author": "Dave Nectariad Rome",
    "version": (2, 8, 3),
    "blender": (4, 0, 0),
    "location": "3D Viewport > Header",
    "warning": "Alpha Version (in-development)",
    "description": "Quickly adjust world HDRI rotation and selection",
    "category": "3D View",
}

# Keymap storage
addon_keymaps = []


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

@persistent
def load_preferred_engine(dummy):
    """Load the user's preferred render engine on startup"""
    print("\n=== LOADING PREFERRED RENDER ENGINE ===")
    
    # Use the direct addon path - most reliable method
    addon_name = "Quick-HDRI-Controls-main"  # Hardcoded for reliability
    addon_dir = os.path.join(bpy.utils.user_resource('SCRIPTS'), 
                           "addons", 
                           addon_name)
    
    print(f"Looking for preferences in: {addon_dir}")
    
    if not os.path.exists(addon_dir):
        print(f"❌ Addon directory not found: {addon_dir}")
        return
    
    preferences_path = os.path.join(addon_dir, "preferences.json")
    print(f"Looking for preferences.json at: {preferences_path}")
    
    # Check if preferences file exists
    if os.path.exists(preferences_path):
        print(f"Found preferences file: {preferences_path}")
        try:
            import json
            
            with open(preferences_path, 'r') as f:
                prefs = json.load(f)
                preferred_engine = prefs.get('render_engine', 'CYCLES')
                
            print(f"Found preferred engine: {preferred_engine}")
            current_engine = bpy.context.scene.render.engine
            print(f"Current engine: {current_engine}")
            
            # Try to set the preferred engine
            if current_engine != preferred_engine:
                # Check if the engine is actually available
                available_engines = set()
                for engine in bpy.types.RenderEngine.__subclasses__():
                    if hasattr(engine, 'idname'):
                        available_engines.add(engine.idname)
                    if hasattr(engine, 'bl_idname'):
                        available_engines.add(engine.bl_idname)
                
                print(f"Available engines: {available_engines}")
                
                if preferred_engine in available_engines:
                    print(f"Setting render engine to preferred: {preferred_engine}")
                    bpy.context.scene.render.engine = preferred_engine
                    
                    # Also ensure the temp_engine property is set
                    if hasattr(bpy.context.scene, "temp_engine"):
                        bpy.context.scene.temp_engine = preferred_engine
                        print(f"Set temp_engine to: {preferred_engine}")
                    
                    print(f"✅ Successfully set engine to: {preferred_engine}")
                else:
                    print(f"Preferred engine {preferred_engine} is not available, using {current_engine}")
            else:
                print(f"Engine already set to preferred: {preferred_engine}")
                
        except Exception as e:
            print(f"Error loading render engine preference: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ Preferences file not found at: {preferences_path}")
    
    print("=== FINISHED LOADING PREFERRED ENGINE ===\n")

def register():
    print("\n=== REGISTERING QUICK HDRI CONTROLS ===")

    # CRITICAL: FIRST STEP - Clean up legacy files before ANYTHING else
    # This section uses only standard library imports to avoid any dependencies
    import os
    import sys
    import importlib
    
    # Get the addon directory path - direct calculation
    addon_dir = os.path.dirname(os.path.realpath(__file__))
    print(f"Addon directory: {addon_dir}")
    
    # Define the legacy files to check for - ONLY in the main addon directory
    legacy_files = [
        os.path.join(addon_dir, "__init__cycles.py"),
        os.path.join(addon_dir, "__init__octane.py"),
        os.path.join(addon_dir, "__init__vray.py")
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
                print(f"❌ Failed to remove {os.path.basename(file_path)}: {str(e)}")
                # Try alternative file removal approach
                try:
                    import stat
                    # Change permissions if needed
                    os.chmod(file_path, stat.S_IWRITE)
                    os.unlink(file_path)
                    print(f"✓ Successfully removed file using alternative method")
                    files_deleted += 1
                except Exception as alt_e:
                    print(f"❌❌ Alternative removal also failed: {str(alt_e)}")
    
    if files_deleted > 0:
        print(f"Successfully removed {files_deleted} legacy file(s)")
        # Refresh import system after removing files
        importlib.invalidate_caches()
    else:
        print("No legacy files found for initial cleanup")
    
    # SECOND STEP: Extract ZIP files with proper file replacement
    def extract_zips_first():
        """Extract ZIP files and properly replace existing files including __init__.py"""
        import os
        import zipfile
        import shutil
        import tempfile
        import importlib
        
        print("\n=== EXTRACTING ZIP FILES ===")
        # Get the addon directory directly
        addon_dir = os.path.dirname(os.path.realpath(__file__))
        
        # Find all zip files in the addon directory
        try:
            zip_files = [f for f in os.listdir(addon_dir) if f.lower().endswith('.zip')]
            
            if zip_files:
                print(f"Found {len(zip_files)} ZIP files to extract")
                
                for zip_file in zip_files:
                    zip_path = os.path.join(addon_dir, zip_file)
                    try:
                        print(f"Extracting: {zip_file}")
                        with tempfile.TemporaryDirectory() as temp_dir:
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                zip_ref.extractall(temp_dir)
                            
                            # Copy extracted files to addon directory
                            extracted_items = os.listdir(temp_dir)
                            
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
                            
                            # Copy all files to addon directory with proper replacement
                            for item in source_items:
                                src_path = os.path.join(source_dir, item)
                                dst_path = os.path.join(addon_dir, item)
                                
                                try:
                                    if os.path.isfile(src_path):
                                        # For files: Remove existing file first, then copy
                                        if os.path.exists(dst_path):
                                            try:
                                                os.remove(dst_path)
                                                print(f"Removed existing file: {item}")
                                            except PermissionError:
                                                # If permission error, try changing permissions
                                                import stat
                                                os.chmod(dst_path, stat.S_IWRITE)
                                                os.remove(dst_path)
                                                print(f"Removed existing file (after changing permissions): {item}")
                                        
                                        # Now copy the new file
                                        shutil.copy2(src_path, dst_path)
                                        print(f"Copied file: {item}")
                                    
                                    elif os.path.isdir(src_path):
                                        # For directories: Remove entirely, then copy the new one
                                        if os.path.exists(dst_path):
                                            try:
                                                shutil.rmtree(dst_path)
                                                print(f"Removed existing directory: {item}")
                                            except PermissionError:
                                                # If permission error, try alternative method
                                                import stat
                                                # Change permissions for all files in the directory
                                                for root, dirs, files in os.walk(dst_path):
                                                    for file in files:
                                                        os.chmod(os.path.join(root, file), stat.S_IWRITE)
                                                # Try removal again
                                                shutil.rmtree(dst_path)
                                                print(f"Removed existing directory (after changing permissions): {item}")
                                        
                                        # Now copy the new directory
                                        shutil.copytree(src_path, dst_path)
                                        print(f"Copied directory: {item}")
                                
                                except Exception as copy_error:
                                    print(f"Error processing {item}: {str(copy_error)}")
                                    import traceback
                                    traceback.print_exc()
                        
                        # Remove the zip file after successful extraction
                        try:
                            os.remove(zip_path)
                            print(f"Removed ZIP file: {zip_file}")
                        except Exception as rm_error:
                            print(f"Could not remove ZIP file: {str(rm_error)}")
                        
                        # Refresh import system after successful extraction
                        importlib.invalidate_caches()
                        print(f"Refreshed import system after extracting {zip_file}")
                        
                    except Exception as e:
                        print(f"Error extracting {zip_file}: {str(e)}")
                        import traceback
                        traceback.print_exc()
            else:
                print("No ZIP files found in addon directory")
                
        except Exception as e:
            print(f"Error in ZIP extraction process: {str(e)}")
            import traceback
            traceback.print_exc()
            
        print("=== ZIP EXTRACTION COMPLETE ===\n")
        
        # Return whether we processed any ZIPs (for logging purposes)
        return len(zip_files) > 0
    
    # Call our ZIP extraction function
    extract_zips_first()
    print("✓ ZIP extraction completed")
    
    # THIRD STEP: Check AGAIN for legacy files that might have been in the ZIPs
    legacy_files = [
        os.path.join(addon_dir, "__init__cycles.py"),
        os.path.join(addon_dir, "__init__octane.py"),
        os.path.join(addon_dir, "__init__vray.py")
    ]
    
    # Check each file and delete if it exists
    files_deleted = 0
    for file_path in legacy_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✓ Removed legacy file after ZIP extraction: {os.path.basename(file_path)}")
                files_deleted += 1
            except Exception as e:
                print(f"❌ Failed to remove {os.path.basename(file_path)}: {str(e)}")
                # Try alternative file removal approach
                try:
                    import stat
                    # Change permissions if needed
                    os.chmod(file_path, stat.S_IWRITE)
                    os.unlink(file_path)
                    print(f"✓ Successfully removed file using alternative method")
                    files_deleted += 1
                except Exception as alt_e:
                    print(f"❌❌ Alternative removal also failed: {str(alt_e)}")
    
    if files_deleted > 0:
        print(f"Successfully removed {files_deleted} additional legacy file(s)")
        # Refresh import system after removing files
        importlib.invalidate_caches()
    else:
        print("No additional legacy files found after ZIP extraction")
    
    print("✓ Startup preparation complete, beginning normal registration")
    
    # Now that we've cleaned up and prepared everything, proceed with normal registration
    # First setup hdri_management module
    from . import hdri_management
    print("✓ HDRI management module imported")

    # Then, try to register the Preferences class
    from . import preferences
    preferences.register_preferences()
    print("✓ Preferences registered")

    # Then, import and register the core modules
    from . import utils
    from . import core
    core.register_core()
    print("✓ Core components registered")

    # Then the operators
    from . import operators
    operators.register_operators()
    print("✓ Operators registered")

    # Then the UI
    from . import ui
    ui.register_ui()
    print("✓ UI registered")

    # Store changelog in window manager
    import bpy
    bpy.types.WindowManager.hdri_changelog = bpy.props.StringProperty(
        name="Changelog",
        description="Stores current changelog entry",
        default=""
    )
    print("✓ Window manager properties added")

    # Register render engines
    from . import render_engines

    # Make sure the temp_engine property is registered if it doesn't exist already
    if not hasattr(bpy.types.Scene, "temp_engine"):
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
    
    # Register load preferred engine handler
    if load_preferred_engine not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_preferred_engine)
    print("✅ Engine preference handler registered")

    # Set up keyboard shortcuts
    utils.setup_keymap(addon_keymaps)
    print("✓ Keyboard shortcuts set up")

    # Set up handlers
    utils.setup_handlers()
    print("✓ Handlers set up")
    
    # Ensure the addon directory structure is set up correctly
    utils.ensure_addon_structure()
    print("✓ Directory structure verified")

    # Extract any additional or new update ZIPs
    utils.extract_addon_zips()
    print("✓ Additional addon ZIPs extracted")

    # Run update check if enabled
    utils.check_for_update_on_startup()
    print("✓ Update check completed")

    print("=== QUICK HDRI CONTROLS REGISTERED SUCCESSFULLY ===\n")

def unregister():
    print("\n=== UNREGISTERING QUICK HDRI CONTROLS ===")

    # Remove load preferred engine handler
    if load_preferred_engine in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_preferred_engine)
    print("✓ Engine preference handler removed")

    # Import modules - by this point they should already be imported from register()
    from . import utils
    from . import ui
    from . import operators
    from . import core
    from . import preferences

    # Remove handlers
    utils.remove_handlers()
    print("✓ Handlers removed")

    # Clear keymaps
    utils.clear_keymaps(addon_keymaps)
    addon_keymaps.clear()
    print("✓ Keymaps cleared")

    # Unregister in reverse order
    ui.unregister_ui()
    print("✓ UI unregistered")
    operators.unregister_operators()
    print("✓ Operators unregistered")
    core.unregister_core()
    print("✓ Core components unregistered")
    preferences.unregister_preferences()
    print("✓ Preferences unregistered")

    # Clear window manager properties
    del bpy.types.WindowManager.hdri_changelog
    print("✓ Window manager properties cleared")
    
    # Clean up temp_engine property
    if hasattr(bpy.types.Scene, "temp_engine"):
        del bpy.types.Scene.temp_engine
    print("✓ Scene properties cleared")

    # Clean up icons and previews
    utils.cleanup_previews()
    print("✓ Previews cleaned up")

    print("=== QUICK HDRI CONTROLS UNREGISTERED SUCCESSFULLY ===\n")

# Register if run directly
if __name__ == "__main__":
    register()