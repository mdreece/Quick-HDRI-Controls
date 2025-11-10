"""
Quick HDRI Controls - Render engines package
"""
# This is not a standalone addon, just a package of the main addon
bl_info = {
    "name": "Quick HDRI Controls - Engines",
    "description": "Render engine implementations for Quick HDRI Controls",
    "author": "Dave Nectariad Rome",
    "version": (0, 0, 0),
    "blender": (4, 0, 0),
    "location": "Internal use only",
    "category": "Internal"
}

# Import all render engine implementations
from . import cycles
from . import vray
from . import octane  # Add import for the octane module

def get_active_engine_module(render_engine):
    """Get the appropriate engine module based on current render engine"""
    if render_engine == 'CYCLES':
        from . import cycles
        return cycles
    elif render_engine == 'VRAY_RENDER_RT':
        from . import vray
        return vray
    elif render_engine == 'octane':
        from . import octane
        return octane
    else:
        # Default to cycles if engine is not supported
        from . import cycles
        return cycles
