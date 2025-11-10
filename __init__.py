"""
Quick HDRI Controls - Main
"""
import os
import bpy
import sys
import json
from bpy.app.handlers import persistent

bl_info = {
    "name": "Quick HDRI Controls",
    "author": "Dave Nectariad Rome",
    "version": (2, 9, 5),
    "blender": (4, 0, 0),
    "location": "3D Viewport > Header",
    "warning": "Alpha Version (in-development)",
    "description": "Quickly adjust world HDRI rotation and selection",
    "category": "3D View",
}

addon_keymaps = []

def get_active_engine_module():
    """Get the appropriate engine module based on current render engine"""
    from .render_engines import get_active_engine_module
    return get_active_engine_module(bpy.context.scene.render.engine)

@persistent
def load_preferred_engine(dummy):
    print("\n=== LOADING PREFERRED RENDER ENGINE ===")

    from . import utils
    addon_name = utils.get_addon_name()
    addon_dir = os.path.join(bpy.utils.user_resource('SCRIPTS'),
                           "addons",
                           addon_name)

    print(f"Looking for preferences in: {addon_dir}")

    if not os.path.exists(addon_dir):
        print(f"Ã¢ÂÅ’ Addon directory not found: {addon_dir}")
        return

    preferences_path = os.path.join(addon_dir, "preferences.json")
    print(f"Looking for preferences.json at: {preferences_path}")

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

            if current_engine != preferred_engine:

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

                    if hasattr(bpy.context.scene, "temp_engine"):
                        bpy.context.scene.temp_engine = preferred_engine
                        print(f"Set temp_engine to: {preferred_engine}")

                    print(f"Ã¢Å“â€¦ Successfully set engine to: {preferred_engine}")
                else:
                    print(f"Preferred engine {preferred_engine} is not available, using {current_engine}")
                    # Sync temp_engine to current engine since preferred is not available
                    if hasattr(bpy.context.scene, "temp_engine"):
                        bpy.context.scene.temp_engine = current_engine
                        print(f"Synced temp_engine to current engine: {current_engine}")
            else:
                print(f"Engine already set to preferred: {preferred_engine}")
                # IMPORTANT: Sync temp_engine even when engines match
                if hasattr(bpy.context.scene, "temp_engine"):
                    bpy.context.scene.temp_engine = current_engine
                    print(f"Synced temp_engine to current engine: {current_engine}")

        except Exception as e:
            print(f"Error loading render engine preference: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print(f"Ã¢ÂÅ’ Preferences file not found at: {preferences_path}")

    print("=== FINISHED LOADING PREFERRED ENGINE ===\n")

def register():
    print("\n=== REGISTERING QUICK HDRI CONTROLS ===")
    update_activity_detected = False

    import os
    import sys
    import importlib

    addon_dir = os.path.dirname(os.path.realpath(__file__))
    print(f"Addon directory: {addon_dir}")

    # Clean up any previous registrations
    try:
        unregister()
        print("Cleaned up previous registration")
    except Exception as e:
        print(f"Note: No previous registration to clean up: {str(e)}")

    legacy_files = [
        os.path.join(addon_dir, "__init__cycles.py"),
        os.path.join(addon_dir, "__init__octane.py"),
        os.path.join(addon_dir, "__init__vray.py")
    ]

    files_deleted = 0
    for file_path in legacy_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Ã¢Å“â€œ Removed legacy file: {os.path.basename(file_path)}")
                files_deleted += 1
                update_activity_detected = True
            except Exception as e:
                print(f"Ã¢ÂÅ’ Failed to remove {os.path.basename(file_path)}: {str(e)}")
                try:
                    import stat
                    os.chmod(file_path, stat.S_IWRITE)
                    os.unlink(file_path)
                    print(f"Ã¢Å“â€œ Successfully removed file using alternative method")
                    files_deleted += 1
                    update_activity_detected = True
                except Exception as alt_e:
                    print(f"Ã¢ÂÅ’Ã¢ÂÅ’ Alternative removal also failed: {str(alt_e)}")

    if files_deleted > 0:
        print(f"Successfully removed {files_deleted} legacy file(s)")
        importlib.invalidate_caches()
    else:
        print("No legacy files found")

    import zipfile
    import shutil
    import tempfile

    zip_files = [f for f in os.listdir(addon_dir) if f.lower().endswith('.zip')]

    if zip_files:
        print(f"Found {len(zip_files)} ZIP files to extract")
        update_activity_detected = True

        for zip_file in zip_files:
            zip_path = os.path.join(addon_dir, zip_file)
            try:
                print(f"Extracting: {zip_file}")
                with tempfile.TemporaryDirectory() as temp_dir:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)

                    extracted_items = os.listdir(temp_dir)

                    if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_items[0])):
                        source_dir = os.path.join(temp_dir, extracted_items[0])
                        print(f"Using subdirectory as source: {extracted_items[0]}")
                    else:
                        source_dir = temp_dir
                        print("Using temp directory directly as source")

                    source_items = os.listdir(source_dir)
                    print(f"Source items to copy: {source_items}")

                    for item in source_items:
                        src_path = os.path.join(source_dir, item)
                        dst_path = os.path.join(addon_dir, item)

                        if os.path.isfile(src_path):
                            if os.path.exists(dst_path):
                                try:
                                    os.remove(dst_path)
                                    print(f"Removed existing file: {item}")
                                except Exception:

                                    import stat
                                    os.chmod(dst_path, stat.S_IWRITE)
                                    os.remove(dst_path)
                                    print(f"Removed existing file (after changing permissions): {item}")

                            shutil.copy2(src_path, dst_path)
                            print(f"Copied file: {item}")

                        elif os.path.isdir(src_path):
                            if os.path.exists(dst_path):
                                try:
                                    shutil.rmtree(dst_path)
                                    print(f"Removed existing directory: {item}")
                                except Exception:
                                    import stat
                                    for root, dirs, files in os.walk(dst_path):
                                        for file in files:
                                            os.chmod(os.path.join(root, file), stat.S_IWRITE)
                                    shutil.rmtree(dst_path)
                                    print(f"Removed existing directory (after changing permissions): {item}")

                            shutil.copytree(src_path, dst_path)
                            print(f"Copied directory: {item}")

                try:
                    os.remove(zip_path)
                    print(f"Removed ZIP file: {zip_file}")
                except Exception as rm_error:
                    print(f"Could not remove ZIP file: {str(rm_error)}")

                importlib.invalidate_caches()
                print(f"Refreshed import system after extracting {zip_file}")

            except Exception as e:
                print(f"Error extracting {zip_file}: {str(e)}")
    else:
        print("No ZIP files found in addon directory")

    for file_path in legacy_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Ã¢Å“â€œ Removed legacy file after ZIP extraction: {os.path.basename(file_path)}")
                update_activity_detected = True
            except Exception as e:
                print(f"Ã¢ÂÅ’ Failed to remove {os.path.basename(file_path)}: {str(e)}")

                try:
                    import stat
                    os.chmod(file_path, stat.S_IWRITE)
                    os.unlink(file_path)
                    print(f"Ã¢Å“â€œ Successfully removed file using alternative method")
                    update_activity_detected = True
                except Exception as alt_e:
                    print(f"Ã¢ÂÅ’Ã¢ÂÅ’ Alternative removal also failed: {str(alt_e)}")

    print("Ã¢Å“â€œ Startup preparation complete, beginning normal registration")

    from . import hdri_management
    print("Ã¢Å“â€œ HDRI management module imported")

    from . import preferences
    try:
        preferences.register_preferences()
        print("Ã¢Å“â€œ Preferences registered")
    except Exception as e:
        print(f"Ã¢ÂÅ’ Error registering preferences: {str(e)}")
        # Try to continue with registration even if preferences fail
        pass

    from . import utils
    from . import core
    try:
        core.register_core()
        print("Ã¢Å“â€œ Core components registered")
    except Exception as e:
        print(f"Ã¢ÂÅ’ Error registering core: {str(e)}")
        raise e  # Core is critical, so we should fail here

    from . import favorites
    print("Ã¢Å“â€œ Favorites module imported")

    from . import operators
    try:
        operators.register_operators()
        print("Ã¢Å“â€œ Operators registered")
    except Exception as e:
        print(f"Ã¢ÂÅ’ Error registering operators: {str(e)}")
        raise e

    from . import ui
    try:
        ui.register_ui()
        print("Ã¢Å“â€œ UI registered")
    except Exception as e:
        print(f"Ã¢ÂÅ’ Error registering UI: {str(e)}")
        raise e

    import bpy
    bpy.types.WindowManager.hdri_changelog = bpy.props.StringProperty(
        name="Changelog",
        description="Stores current changelog entry",
        default=""
    )
    print("Ã¢Å“â€œ Window manager properties added")

    from . import render_engines

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

    if load_preferred_engine not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_preferred_engine)
    print("Ã¢Å“â€¦ Engine preference handler registered")

    # Sync temp_engine immediately for the current session
    # Use a timer to ensure context is available
    def sync_temp_engine_on_register():
        try:
            # Call the main handler to sync everything properly
            load_preferred_engine(None)
        except Exception as e:
            print(f"Error syncing temp_engine on register: {e}")
            # Fallback: just sync to current engine
            try:
                if hasattr(bpy.context.scene, "temp_engine"):
                    bpy.context.scene.temp_engine = bpy.context.scene.render.engine
                    print(f"Fallback sync: temp_engine set to {bpy.context.scene.render.engine}")
            except Exception as e2:
                print(f"Fallback sync also failed: {e2}")
        return None  # Don't repeat

    bpy.app.timers.register(sync_temp_engine_on_register, first_interval=0.1)

    utils.setup_keymap(addon_keymaps)
    print("Ã¢Å“â€œ Keyboard shortcuts set up")

    utils.setup_handlers()
    print("Ã¢Å“â€œ Handlers set up")

    utils.ensure_addon_structure()
    print("Ã¢Å“â€œ Directory structure verified")

    utils.check_for_update_on_startup()
    print("Ã¢Å“â€œ Update check completed")

    from . import flamenco
    try:
        flamenco.register_flamenco_handlers()
        print("Ã¢Å“â€œ Flamenco integration registered")
    except Exception as e:
        print(f"Ã¢Å¡Â Ã¯Â¸Â Warning: Flamenco integration failed: {str(e)}")
        # Non-critical, continue

    if update_activity_detected:
        def show_changelog_delayed():
            current_version = bl_info['version']

            changelog_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "CHANGELOG.md")

            if os.path.exists(changelog_path):
                try:
                    from . import utils
                    changes = utils.parse_changelog(changelog_path, current_version)

                    if changes:
                        bpy.context.window_manager.hdri_changelog = changes

                        bpy.ops.world.show_hdri_changelog('INVOKE_DEFAULT')
                        print("Ã¢Å“â€œ Showing changelog for update")
                except Exception as e:
                    print(f"Error showing changelog: {str(e)}")

        bpy.app.timers.register(show_changelog_delayed, first_interval=1.0)
        print("Ã¢Å“â€œ Scheduled changelog to show after UI initialization")

    print("=== QUICK HDRI CONTROLS REGISTERED SUCCESSFULLY ===\n")

def unregister():
    print("\n=== UNREGISTERING QUICK HDRI CONTROLS ===")

    if load_preferred_engine in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_preferred_engine)
    print("Ã¢Å“â€œ Engine preference handler removed")

    from . import utils
    from . import ui
    from . import operators
    from . import core
    from . import preferences
    from . import flamenco

    flamenco.unregister_flamenco_handlers()
    print("Ã¢Å“â€œ Flamenco integration unregistered")

    utils.remove_handlers()
    print("Ã¢Å“â€œ Handlers removed")

    utils.clear_keymaps(addon_keymaps)
    addon_keymaps.clear()
    print("Ã¢Å“â€œ Keymaps cleared")

    ui.unregister_ui()
    print("Ã¢Å“â€œ UI unregistered")
    operators.unregister_operators()
    print("Ã¢Å“â€œ Operators unregistered")
    core.unregister_core()
    print("Ã¢Å“â€œ Core components unregistered")
    preferences.unregister_preferences()
    print("Ã¢Å“â€œ Preferences unregistered")

    del bpy.types.WindowManager.hdri_changelog
    print("Ã¢Å“â€œ Window manager properties cleared")

    if hasattr(bpy.types.Scene, "temp_engine"):
        del bpy.types.Scene.temp_engine
    print("Ã¢Å“â€œ Scene properties cleared")

    utils.cleanup_previews()
    print("Ã¢Å“â€œ Previews cleaned up")

    print("=== QUICK HDRI CONTROLS UNREGISTERED SUCCESSFULLY ===\n")

if __name__ == "__main__":
    register()
