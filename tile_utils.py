# tile_utils.py
import os
import logging

def get_tile_name_from_path(image_path):
    """Lấy tên quân bài từ đường dẫn ảnh (ví dụ: 'man-1')."""
    return os.path.splitext(os.path.basename(image_path))[0]

def custom_sort_key_tiles(filename):
    """Khóa sắp xếp tùy chỉnh cho các quân bài."""
    order = {"man": 1, "pin": 2, "sou": 3, "haku": 4, "hatsu": 5, "chun": 6,
             "Ton": 7, "Nan": 8, "Sha": 9, "Pei": 10}
    try:
        parts = get_tile_name_from_path(filename).split('-')
        tile_type = parts[0]
        tile_number_str = parts[1] if len(parts) > 1 else "0"
        tile_number = int(tile_number_str) if tile_number_str.isdigit() else 0
        return (order.get(tile_type, 99), tile_number)
    except Exception as e:
        logging.warning(f"Lỗi khi phân tích tên tệp {filename} để sắp xếp: {e}")
        return (999, 0)

def sort_tile_images(image_files):
    """Sắp xếp danh sách tên tệp ảnh quân bài."""
    return sorted(image_files, key=custom_sort_key_tiles)