# image_utils.py
import cv2
import numpy as np
import pyautogui
import logging
from config import IMAGE_MATCH_THRESHOLD, GROUP_POSITIONS_X_DISTANCE # Import hằng số cần thiết

def find_image_locations(template_path, region, threshold=IMAGE_MATCH_THRESHOLD):
    """Tìm tất cả các vị trí của một ảnh mẫu trong một vùng."""
    try:
        template = cv2.imread(template_path, 0)
        if template is None:
            logging.warning(f"Không thể đọc ảnh: {template_path}")
            return []

        screenshot = pyautogui.screenshot(region=region)
        screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= threshold)

        return list(zip(*loc[::-1]))
    except Exception as e:
        logging.error(f"Lỗi khi tìm ảnh {template_path}: {e}")
        return []

def group_nearby_positions(positions, x_distance=GROUP_POSITIONS_X_DISTANCE):
    """Nhóm các vị trí gần nhau theo trục X."""
    if not positions:
        return []
    positions_sorted = sorted(positions, key=lambda p: p[0])
    groups = []
    current_group = [positions_sorted[0]]
    for pos in positions_sorted[1:]:
        if abs(pos[0] - current_group[-1][0]) < x_distance:
            current_group.append(pos)
        else:
            groups.append(current_group)
            current_group = [pos]
    if current_group:
        groups.append(current_group)
    return [group[0] for group in groups]

def convert_region_to_screen_coords(pos_in_region, region_origin, item_size):
    """Chuyển tọa độ trong vùng region sang tọa độ tuyệt đối trên màn hình."""
    item_center_x = pos_in_region[0] + item_size[0] // 2
    item_center_y = pos_in_region[1] + item_size[1] // 2
    screen_x = item_center_x + region_origin[0]
    screen_y = item_center_y + region_origin[1]
    return screen_x, screen_y