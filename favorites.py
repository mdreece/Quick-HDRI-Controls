"""
Quick HDRI Controls - Favorites
"""
import os
import json
import bpy

def get_favorites_file_path():
    addon_name = __package__.split('.')[0]
    addon_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(addon_dir, "favorites.json")

def load_favorites():
    favorites_path = get_favorites_file_path()

    if not os.path.exists(favorites_path):
        return []

    try:
        with open(favorites_path, 'r') as f:
            data = json.load(f)
            return data.get('favorites', [])
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading favorites: {str(e)}")
        return []

def save_favorites(favorites):
    favorites_path = get_favorites_file_path()

    try:
        with open(favorites_path, 'w') as f:
            json.dump({'favorites': favorites}, f, indent=2)
    except IOError as e:
        print(f"Error saving favorites: {str(e)}")

def is_favorite(hdri_path):
    favorites = load_favorites()
    return os.path.normpath(hdri_path) in [os.path.normpath(f) for f in favorites]

def toggle_favorite(hdri_path):
    favorites = load_favorites()
    norm_path = os.path.normpath(hdri_path)
    norm_favorites = [os.path.normpath(f) for f in favorites]

    if norm_path in norm_favorites:
        favorites = [f for f in favorites if os.path.normpath(f) != norm_path]
    else:
        favorites.append(hdri_path)

    save_favorites(favorites)

    return norm_path in [os.path.normpath(f) for f in favorites]
