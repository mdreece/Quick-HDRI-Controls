"""
Quick HDRI Controls - Flamenco Integration

"""
import os
import bpy
import sys
import inspect
import importlib
from bpy.app.handlers import persistent
from .utils import world_has_nodes
from . import utils
from .core import original_paths

original_flamenco_submit = None
original_flamenco_submit_operator = None

proxy_state = {
    'cycles': {'path': None, 'image_name': None},
    'vray': {'path': None},
    'octane': {'path': None, 'image_name': None}
}

def switch_to_full_resolution_hdri(context):
    if not hasattr(context.scene, "hdri_settings") or context.scene.hdri_settings.proxy_mode != 'VIEWPORT':
        print("HDRI Controls: No proxy conversion needed for Flamenco submission")
        return

    print("HDRI Controls: Preparing Flamenco submission - switching to full-resolution HDRI")

    render_engine = context.scene.render.engine

    if render_engine == 'CYCLES':

        world = context.scene.world
        if world and world_has_nodes(world):

            env_tex = None
            for node in world.node_tree.nodes:
                if node.type == 'TEX_ENVIRONMENT' and node.image:
                    env_tex = node
                    break

            if env_tex and env_tex.image:

                current_image = env_tex.image
                original_path = original_paths.get(current_image.name, current_image.filepath)

                if original_path and original_path != current_image.filepath:
                    proxy_state['cycles']['path'] = current_image.filepath
                    proxy_state['cycles']['image_name'] = current_image.name

                    try:
                        img = bpy.data.images.load(original_path, check_existing=True)
                        img.reload()

                        env_tex.image = img

                        if hasattr(env_tex, 'update'):
                            env_tex.update()
                        world.node_tree.update_tag()

                        print(f"HDRI Controls: Switched to full-resolution HDRI for Flamenco: {original_path}")
                    except Exception as e:
                        print(f"HDRI Controls: Error switching to full-resolution HDRI: {str(e)}")

    elif render_engine == 'VRAY_RENDER_RT':
        vray_collection = bpy.data.collections.get("vRay HDRI Controls")
        if vray_collection:
            for obj in vray_collection.objects:
                if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                    node_tree = obj.data.node_tree
                    bitmap_node = node_tree.nodes.get("V-Ray Bitmap")

                    if bitmap_node:
                        current_file = ""
                        if hasattr(bitmap_node, 'texture') and bitmap_node.texture and bitmap_node.texture.image:
                            current_file = bitmap_node.texture.image.filepath
                        elif hasattr(bitmap_node, 'BitmapBuffer') and hasattr(bitmap_node.BitmapBuffer, 'file'):
                            current_file = bitmap_node.BitmapBuffer.file

                        original_path = original_paths.get(os.path.basename(current_file), None)

                        if original_path and original_path != current_file:
                            proxy_state['vray']['path'] = current_file

                            try:
                                if hasattr(bitmap_node, 'BitmapBuffer') and hasattr(bitmap_node.BitmapBuffer, 'file'):
                                    bitmap_node.BitmapBuffer.file = original_path

                                if hasattr(bitmap_node, 'texture') and bitmap_node.texture:
                                    if bitmap_node.texture.image:
                                        old_image = bitmap_node.texture.image
                                        bitmap_node.texture.image = None
                                        if old_image.users == 0:
                                            bpy.data.images.remove(old_image)

                                    new_image = bpy.data.images.load(original_path, check_existing=True)
                                    bitmap_node.texture.image = new_image

                                    if original_path.lower().endswith(('.hdr', '.exr')):
                                        new_image.colorspace_settings.name = 'Linear'

                                if hasattr(bitmap_node, 'update'):
                                    bitmap_node.update()
                                if hasattr(node_tree, 'update_tag'):
                                    node_tree.update_tag()

                                print(f"HDRI Controls: Switched to full-resolution HDRI for Flamenco: {original_path}")
                            except Exception as e:
                                print(f"HDRI Controls: Error switching to full-resolution HDRI: {str(e)}")
                    break

    elif render_engine == 'octane':
        world = context.scene.world
        if world and world.use_nodes:
            rgb_node = None
            for node in world.node_tree.nodes:
                if node.bl_idname == 'OctaneRGBImage':
                    rgb_node = node
                    break

            if rgb_node and rgb_node.image:
                current_image = rgb_node.image
                original_path = original_paths.get(current_image.name, None)

                if not original_path and hasattr(rgb_node, 'a_filename'):
                    original_path = original_paths.get(os.path.basename(rgb_node.a_filename), rgb_node.a_filename)

                if original_path and original_path != (rgb_node.a_filename if hasattr(rgb_node, 'a_filename') else current_image.filepath):
                    if hasattr(rgb_node, 'a_filename'):
                        proxy_state['octane']['path'] = rgb_node.a_filename
                    else:
                        proxy_state['octane']['path'] = current_image.filepath

                    proxy_state['octane']['image_name'] = current_image.name

                    try:
                        img = bpy.data.images.load(original_path, check_existing=True)
                        img.reload()

                        rgb_node.image = None

                        rgb_node.image = img
                        if hasattr(rgb_node, 'a_filename'):
                            rgb_node.a_filename = original_path

                        if hasattr(rgb_node, 'update'):
                            rgb_node.update()
                        world.node_tree.update_tag()

                        print(f"HDRI Controls: Switched to full-resolution HDRI for Flamenco: {original_path}")
                    except Exception as e:
                        print(f"HDRI Controls: Error switching to full-resolution HDRI: {str(e)}")


def restore_hdri_proxies(context):
    if not hasattr(context.scene, "hdri_settings") or context.scene.hdri_settings.proxy_mode != 'VIEWPORT':
        return

    render_engine = context.scene.render.engine

    print(f"HDRI Controls: Restoring HDRI proxies after Flamenco submission for {render_engine}")

    if render_engine == 'CYCLES':
        if proxy_state['cycles']['path'] and os.path.exists(proxy_state['cycles']['path']):
            world = context.scene.world
            if world and world.use_nodes:
                env_tex = None
                for node in world.node_tree.nodes:
                    if node.type == 'TEX_ENVIRONMENT':
                        env_tex = node
                        break

                if env_tex:
                    try:
                        restored_image = None
                        if proxy_state['cycles']['image_name'] and proxy_state['cycles']['image_name'] in bpy.data.images:
                            restored_image = bpy.data.images[proxy_state['cycles']['image_name']]
                            if os.path.normpath(restored_image.filepath) != os.path.normpath(proxy_state['cycles']['path']):
                                restored_image = None

                        if not restored_image:
                            restored_image = bpy.data.images.load(proxy_state['cycles']['path'], check_existing=True)

                        env_tex.image = restored_image

                        if hasattr(env_tex, 'update'):
                            env_tex.update()
                        world.node_tree.update_tag()

                        print(f"HDRI Controls: Restored Cycles proxy HDRI: {proxy_state['cycles']['path']}")

                        proxy_state['cycles']['path'] = None
                        proxy_state['cycles']['image_name'] = None
                    except Exception as e:
                        print(f"HDRI Controls: Error restoring Cycles proxy HDRI: {str(e)}")

    elif render_engine == 'VRAY_RENDER_RT':
        if proxy_state['vray']['path'] and os.path.exists(proxy_state['vray']['path']):
            vray_collection = bpy.data.collections.get("vRay HDRI Controls")
            if vray_collection:
                for obj in vray_collection.objects:
                    if obj.type == 'LIGHT' and "VRayDomeLight" in obj.name:
                        node_tree = obj.data.node_tree
                        bitmap_node = node_tree.nodes.get("V-Ray Bitmap")

                        if bitmap_node:
                            try:
                                proxy_path = proxy_state['vray']['path']

                                if hasattr(bitmap_node, 'BitmapBuffer') and hasattr(bitmap_node.BitmapBuffer, 'file'):
                                    bitmap_node.BitmapBuffer.file = proxy_path

                                if hasattr(bitmap_node, 'texture') and bitmap_node.texture:
                                    if bitmap_node.texture.image:
                                        old_image = bitmap_node.texture.image
                                        bitmap_node.texture.image = None
                                        if old_image.users == 0:
                                            bpy.data.images.remove(old_image)

                                    new_image = bpy.data.images.load(proxy_path, check_existing=True)
                                    bitmap_node.texture.image = new_image

                                    if proxy_path.lower().endswith(('.hdr', '.exr')):
                                        new_image.colorspace_settings.name = 'Linear'

                                if hasattr(bitmap_node, 'update'):
                                    bitmap_node.update()
                                if hasattr(node_tree, 'update_tag'):
                                    node_tree.update_tag()

                                print(f"HDRI Controls: Restored V-Ray proxy HDRI: {proxy_state['vray']['path']}")

                                proxy_state['vray']['path'] = None
                            except Exception as e:
                                print(f"HDRI Controls: Error restoring V-Ray proxy HDRI: {str(e)}")
                        break

    elif render_engine == 'octane':
        if proxy_state['octane']['path'] and os.path.exists(proxy_state['octane']['path']):
            world = context.scene.world
            if world and world.use_nodes:
                rgb_node = None
                for node in world.node_tree.nodes:
                    if node.bl_idname == 'OctaneRGBImage':
                        rgb_node = node
                        break

                if rgb_node:
                    try:
                        restored_image = None
                        if proxy_state['octane']['image_name'] and proxy_state['octane']['image_name'] in bpy.data.images:
                            restored_image = bpy.data.images[proxy_state['octane']['image_name']]
                            if hasattr(rgb_node, 'a_filename') and os.path.normpath(rgb_node.a_filename) != os.path.normpath(proxy_state['octane']['path']):
                                restored_image = None

                        if not restored_image:
                            restored_image = bpy.data.images.load(proxy_state['octane']['path'], check_existing=True)

                        rgb_node.image = None
                        rgb_node.image = restored_image

                        if hasattr(rgb_node, 'a_filename'):
                            rgb_node.a_filename = proxy_state['octane']['path']

                        if hasattr(rgb_node, 'update'):
                            rgb_node.update()
                        world.node_tree.update_tag()

                        print(f"HDRI Controls: Restored Octane proxy HDRI: {proxy_state['octane']['path']}")

                        proxy_state['octane']['path'] = None
                        proxy_state['octane']['image_name'] = None
                    except Exception as e:
                        print(f"HDRI Controls: Error restoring Octane proxy HDRI: {str(e)}")


def patched_flamenco_submit(original_function):
    def wrapper(*args, **kwargs):
        print("HDRI Controls: Flamenco submission intercepted")

        context = None
        for arg in args:
            if isinstance(arg, bpy.types.Context):
                context = arg
                break

        if context is None:
            context = kwargs.get('context')

        if context is None:
            context = bpy.context

        switch_to_full_resolution_hdri(context)

        result = original_function(*args, **kwargs)

        bpy.app.timers.register(
            lambda: restore_hdri_proxies(context),
            first_interval=1.0
        )

        return result

    return wrapper

def find_flamenco_submit_function():
    print("HDRI Controls: Searching for Flamenco submit function...")

    flamenco_modules = [m for m in sys.modules if 'flamenco' in m.lower()]
    print(f"HDRI Controls: Found potential Flamenco modules: {flamenco_modules}")

    for module_name in flamenco_modules:
        module = sys.modules[module_name]

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and hasattr(obj, 'bl_idname'):
                if obj.bl_idname and 'flamenco' in obj.bl_idname.lower() and 'submit' in obj.bl_idname.lower():
                    print(f"HDRI Controls: Found Flamenco submit operator: {obj.bl_idname}")

                    if hasattr(obj, 'execute'):
                        return obj, 'execute'

                    if hasattr(obj, 'invoke'):
                        return obj, 'invoke'

    for module_name in flamenco_modules:
        module = sys.modules[module_name]

        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and ('submit' in name.lower() or 'job' in name.lower()):
                print(f"HDRI Controls: Found potential Flamenco function: {name}")
                return obj, None

    for module_name in sys.modules.keys():
        if 'bpy' in module_name or 'bl_' in module_name:
            module = sys.modules[module_name]

            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and 'flamenco' in name.lower() and 'submit' in name.lower():
                    print(f"HDRI Controls: Found potential Flamenco function in {module_name}: {name}")
                    return obj, None

    return None, None

def patch_flamenco_submit(target_obj, method_name=None):
    global original_flamenco_submit

    if method_name:
        print(f"HDRI Controls: Patching method {method_name} of {target_obj}")

        original_method = getattr(target_obj, method_name)
        original_flamenco_submit = original_method

        def patched_method(self, context, *args, **kwargs):
            print("HDRI Controls: Flamenco submission intercepted via method patch")
            switch_to_full_resolution_hdri(context)

            result = original_method(self, context, *args, **kwargs)

            bpy.app.timers.register(
                lambda: restore_hdri_proxies(context),
                first_interval=1.0
            )

            return result

        setattr(target_obj, method_name, patched_method)
        print(f"HDRI Controls: Successfully patched {method_name} method")
        return True
    else:
        print(f"HDRI Controls: Patching function {target_obj.__name__}")

        original_flamenco_submit = target_obj

        patched_function = patched_flamenco_submit(target_obj)

        module = inspect.getmodule(target_obj)
        setattr(module, target_obj.__name__, patched_function)
        print(f"HDRI Controls: Successfully patched {target_obj.__name__} function")
        return True

def monkey_patch_flamenco_operators():
    flamenco_operators = []

    for cls in bpy.types.Operator.__subclasses__():
        if hasattr(cls, 'bl_idname') and 'flamenco' in cls.bl_idname.lower():
            if 'submit' in cls.bl_idname.lower() or 'job' in cls.bl_idname.lower():
                flamenco_operators.append(cls)
                print(f"HDRI Controls: Found Flamenco operator class: {cls.bl_idname}")

    if flamenco_operators:
        for op_cls in flamenco_operators:
            if hasattr(op_cls, 'execute'):
                patch_flamenco_submit(op_cls, 'execute')

            if hasattr(op_cls, 'invoke'):
                patch_flamenco_submit(op_cls, 'invoke')

        return True

    return False

def install_flamenco_submit_overrides():
    submit_obj, method_name = find_flamenco_submit_function()

    if submit_obj and method_name:
        success = patch_flamenco_submit(submit_obj, method_name)
        if success:
            print("HDRI Controls: Successfully patched Flamenco submission method")
            return True
    elif submit_obj:
        success = patch_flamenco_submit(submit_obj)
        if success:
            print("HDRI Controls: Successfully patched Flamenco submission function")
            return True

    success = monkey_patch_flamenco_operators()
    if success:
        print("HDRI Controls: Successfully monkey-patched Flamenco operators")
        return True

    print("HDRI Controls: Could not find Flamenco submission functions to patch")
    return False

def install_pre_save_handler():
    @persistent
    def pre_save_handler(dummy):
        switch_to_full_resolution_hdri(bpy.context)

        bpy.app.timers.register(
            lambda: restore_hdri_proxies(bpy.context),
            first_interval=1.0
        )

    # Register the handler
    if pre_save_handler not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(pre_save_handler)
        print("HDRI Controls: Registered pre-save handler to ensure full-resolution HDRIs")

def register_flamenco_handlers():
    success = install_flamenco_submit_overrides()

    install_pre_save_handler()

    if not success:
        print("HDRI Controls: Using render handlers as fallback for Flamenco integration")

        @persistent
        def pre_render_handler(dummy):
            switch_to_full_resolution_hdri(bpy.context)

        @persistent
        def post_render_handler(dummy):
            bpy.app.timers.register(
                lambda: restore_hdri_proxies(bpy.context),
                first_interval=1.0
            )

        if pre_render_handler not in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.append(pre_render_handler)
            print("HDRI Controls: Registered pre-render handler as fallback")

        if post_render_handler not in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.append(post_render_handler)
            print("HDRI Controls: Registered post-render handler as fallback")

def unregister_flamenco_handlers():
    global original_flamenco_submit

    if original_flamenco_submit:
        # TODO: Proper restoration of original functions
        # This is complex and would require tracking which function/method was patched
        original_flamenco_submit = None

    # Remove pre-save handler
    for handler in list(bpy.app.handlers.save_pre):
        if "pre_save_handler" in str(handler):
            bpy.app.handlers.save_pre.remove(handler)
            print("HDRI Controls: Removed pre-save handler")

    # Remove pre-render handler
    for handler in list(bpy.app.handlers.render_pre):
        if "pre_render_handler" in str(handler):
            bpy.app.handlers.render_pre.remove(handler)
            print("HDRI Controls: Removed pre-render handler")

    # Remove post-render handler
    for handler in list(bpy.app.handlers.render_complete):
        if "post_render_handler" in str(handler):
            bpy.app.handlers.render_complete.remove(handler)
            print("HDRI Controls: Removed post-render handler")
