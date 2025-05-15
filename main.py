import cv2
import numpy as np
import pyautogui
import os
import time
import threading
import keyboard
import random
import re
import logging
from collections import Counter # Giữ lại nếu bạn có ý định dùng sau

# --- CẤU HÌNH ---
# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Đường dẫn và tên tệp
IMAGES_FOLDER = 'images'
PASS_IMAGE = os.path.join(IMAGES_FOLDER, 'pass.png')
RIICHI_IMAGE = os.path.join(IMAGES_FOLDER, 'riichi.png')
TSUMO_IMAGE = os.path.join(IMAGES_FOLDER, 'tsumo.png')
RON_IMAGE = os.path.join(IMAGES_FOLDER, 'ron.png')
KITA_IMAGE = os.path.join(IMAGES_FOLDER, 'kita.png')
PON_IMAGE = os.path.join(IMAGES_FOLDER, 'pon.png')
KAN_IMAGE = os.path.join(IMAGES_FOLDER, 'kan.png')
CHII_IMAGE = os.path.join(IMAGES_FOLDER, 'chii.png')
END_GAME_IMAGE = os.path.join(IMAGES_FOLDER, 'end.png')
# START_GAME_IMAGE = os.path.join(IMAGES_FOLDER, 'start.png') # Nếu cần

# Tọa độ các vùng (left, top, width, height)
# THAY ĐỔI CÁC GIÁ TRỊ NÀY CHO PHÙ HỢP VỚI MÀN HÌNH CỦA BẠN
# Vùng chứa các quân bài của người chơi
PLAYER_HAND_REGION = (289, 840, 1422, 170)
# Vùng chứa các nút hành động (Pass, Riichi, Pon,...)
ACTION_BUTTONS_REGION = (473, 764, 1588 - 473, 865 - 764)
# Vùng để kiểm tra lượt chơi (ví dụ: highlight tên người chơi)
TURN_INDICATOR_REGION = (1663, 772, 1737 - 1663, 867 - 772)
# Vùng để kiểm tra màn hình kết thúc game
END_GAME_REGION = (12, 50, 428 - 12, 146 - 50)
# Vùng để kiểm tra nút bắt đầu game (nếu có)
# START_GAME_REGION = (1127, 257, 1323 - 1127, 451 - 428)

# Kích thước quân bài (width, height)
TILE_IMAGE_SIZE = (75, 105) # Cần khớp với ảnh mẫu của bạn

# Ngưỡng nhận diện ảnh
IMAGE_MATCH_THRESHOLD = 0.8
# Khoảng cách X để nhóm các vị trí tìm thấy gần nhau
GROUP_POSITIONS_X_DISTANCE = 30

# Màu sắc để nhận diện lượt chơi (RGB)
TURN_INDICATOR_COLORS = [
    (196, 245, 253), (201, 248, 254), (203, 248, 254),
    (255, 198, 38), (255, 201, 42), (255, 205, 49)
]
COLOR_MATCH_TOLERANCE = 10 # Ngưỡng dung sai cho màu sắc

# Tọa độ click sau khi kết thúc game
# (Ví dụ: nút OK, nút chọn chế độ chơi)
END_GAME_CLICKS = [
    (1753, 948), # Click nhiều lần ở đây
]
GAME_MODE_CLICKS = {
    0: [(1324, 496)], # Tọa độ cho game mode 0
    1: [(1161, 626), (1030, 893)] # Tọa độ cho game mode 1
}
SELECTED_GAME_MODE = 0 # Chọn chế độ game mặc định

# Độ trễ
CLICK_DELAY = 0.25 # Giữa các click khi Riichi
ACTION_CLICK_DELAY = 0.1 # Sau khi click 1 hành động
LOOP_DELAY = 0.5 # Trong vòng lặp chính
PASS_CHECK_DELAY = 1.0 # Trong luồng theo dõi nút
END_GAME_CHECK_DELAY = 3.0

# --- CÁC HÀM TIỆN ÍCH (Tái sử dụng từ mã cũ, có thể chỉnh sửa) ---

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

        return list(zip(*loc[::-1])) # Trả về danh sách các tuple (x, y)
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
    # Lấy vị trí trung bình hoặc vị trí đầu tiên của mỗi nhóm
    # Ở đây lấy vị trí đầu tiên cho đơn giản, giống mã cũ
    return [group[0] for group in groups]

def get_tile_name_from_path(image_path):
    """Lấy tên quân bài từ đường dẫn ảnh (ví dụ: 'man-1')."""
    return os.path.splitext(os.path.basename(image_path))[0]

def custom_sort_key_tiles(filename):
    """Khóa sắp xếp tùy chỉnh cho các quân bài (ví dụ: man, pin, sou rồi đến gió, rồng)."""
    order = {"man": 1, "pin": 2, "sou": 3, "haku": 4, "hatsu": 5, "chun": 6,
             "Ton": 7, "Nan": 8, "Sha": 9, "Pei": 10}
    try:
        parts = get_tile_name_from_path(filename).split('-')
        tile_type = parts[0]
        tile_number_str = parts[1] if len(parts) > 1 else "0" # "0" cho quân chữ
        tile_number = int(tile_number_str) if tile_number_str.isdigit() else 0
        return (order.get(tile_type, 99), tile_number) # 99 cho các loại không xác định
    except Exception as e:
        logging.warning(f"Lỗi khi phân tích tên tệp {filename} để sắp xếp: {e}")
        return (999, 0) # Đẩy lỗi xuống cuối

def sort_tile_images(image_files):
    """Sắp xếp danh sách tên tệp ảnh quân bài."""
    return sorted(image_files, key=custom_sort_key_tiles)

def is_my_turn(indicator_region, target_colors, tolerance, pass_image_path, pass_search_region):
    """Kiểm tra xem có phải lượt của người chơi không."""
    try:
        screenshot = pyautogui.screenshot(region=indicator_region)
        screenshot_np = np.array(screenshot)
        for target_color in target_colors:
            mask = np.all(np.abs(screenshot_np - target_color) <= tolerance, axis=-1)
            if np.any(mask):
                # Thêm điều kiện kiểm tra nút PASS không xuất hiện
                if not find_image_locations(pass_image_path, pass_search_region, 0.85): # Ngưỡng cao hơn cho pass
                    logging.info("Lượt của tôi (màu khớp và không có nút Pass).")
                    return True
                else:
                    logging.info("Màu khớp nhưng nút Pass đang hiển thị.")
                    return False # Có nút Pass, không phải lượt đánh bài
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra lượt chơi: {e}")
        return False

def convert_region_to_screen_coords(pos_in_region, region_origin, item_size):
    """Chuyển tọa độ trong vùng region sang tọa độ tuyệt đối trên màn hình."""
    item_center_x = pos_in_region[0] + item_size[0] // 2
    item_center_y = pos_in_region[1] + item_size[1] // 2
    screen_x = item_center_x + region_origin[0]
    screen_y = item_center_y + region_origin[1]
    return screen_x, screen_y

# --- LOGIC GAME (Giữ lại các hàm is_consecutive... và logic_game từ mã cũ) ---
# (Bạn cần sao chép các hàm is_consecutive_numbers3, is_consecutive_numbers2,
# is_consecutive_numbers2_2, logic_game, input_text, process_position từ mã cũ vào đây)
# Ví dụ:
def is_consecutive_numbers3(name1, name2, name3):
    match1 = re.match(r'(\D+)(\d+)', name1)
    match2 = re.match(r'(\D+)(\d+)', name2)
    match3 = re.match(r'(\D+)(\d+)', name3)
    if not (match1 and match2 and match3): return False
    prefix1, num1_str = match1.groups()
    prefix2, num2_str = match2.groups()
    prefix3, num3_str = match3.groups()
    if not (num1_str.isdigit() and num2_str.isdigit() and num3_str.isdigit()): return False
    num1, num2, num3 = int(num1_str), int(num2_str), int(num3_str)
    return (prefix1 == prefix2 == prefix3) and (num2 == num1 + 1) and (num3 == num2 + 1)

def is_consecutive_numbers2(name1, name2):
    match1 = re.match(r'(\D+)(\d+)', name1)
    match2 = re.match(r'(\D+)(\d+)', name2)
    if not (match1 and match2): return False
    prefix1, num1_str = match1.groups()
    prefix2, num2_str = match2.groups()
    if not (num1_str.isdigit() and num2_str.isdigit()): return False
    num1, num2 = int(num1_str), int(num2_str)
    return (prefix1 == prefix2) and (num2 == num1 + 1)

def is_consecutive_numbers2_2(name1, name2): # Chờ ở giữa
    match1 = re.match(r'(\D+)(\d+)', name1)
    match2 = re.match(r'(\D+)(\d+)', name2)
    if not (match1 and match2): return False
    prefix1, num1_str = match1.groups()
    prefix2, num2_str = match2.groups()
    if not (num1_str.isdigit() and num2_str.isdigit()): return False
    num1, num2 = int(num1_str), int(num2_str)
    return (prefix1 == prefix2) and (num2 == num1 + 2)

def input_text_formatter(detected_tiles_info):
    """
    Định dạng lại danh sách các quân bài đã phát hiện theo format mong muốn
    và sắp xếp chúng.
    Input: list of tuples [(tile_name, position_in_region), ...]
    Output: string
    """
    # Định nghĩa hàm để trích xuất thông tin cần thiết để sắp xếp
    def sort_key(entry_tuple): # entry_tuple is (tile_name, original_index)
        name = entry_tuple[0]
        if '-' in name:
            prefix, num_str = name.split('-', 1)
            if not num_str.isdigit(): return (99,0) # Xử lý trường hợp tên không chuẩn
            num = int(num_str)
            if prefix in ['man', 'pin', 'sou']:
                return (['man', 'pin', 'sou'].index(prefix), num)
            else: # Các loại khác có số (ít gặp)
                return (90, num) # Đẩy xuống dưới man, pin, sou
        else:
            order = {"haku": 4, "hatsu": 5, "chun": 6, "Ton": 7, "Nan": 8, "Sha": 9, "Pei": 10}
            return (order.get(name, 99), 0) # 99 cho các quân không xác định

    # Tạo danh sách các mục để sắp xếp, kèm theo index gốc để lấy lại vị trí
    # entries: [(name, original_index_in_detected_tiles_info), ...]
    entries_to_sort = []
    for i, (name, _) in enumerate(detected_tiles_info):
        entries_to_sort.append((name, i))

    sorted_entries_with_indices = sorted(entries_to_sort, key=sort_key)

    output_string = "Detected positions:\n"
    for new_idx, (name, original_idx) in enumerate(sorted_entries_with_indices):
        _, pos = detected_tiles_info[original_idx] # Lấy lại vị trí từ danh sách gốc
        output_string += f"{new_idx}: {name} at position {pos}\n"

    return output_string.strip()


def process_discard_decision(position_str, tile_size, hand_region_origin):
    """Chuyển chuỗi vị trí từ logic_game thành tọa độ (x, y) trên màn hình."""
    if not isinstance(position_str, str) or not position_str.startswith("("):
        logging.warning(f"Vị trí không hợp lệ từ logic_game: {position_str}. Click giữa màn hình.")
        screen_width, screen_height = pyautogui.size()
        return screen_width // 2, screen_height // 2

    try:
        # Chuyển đổi chuỗi "(x, y)" thành tuple (x, y) của các số nguyên
        pos_in_region = tuple(map(int, position_str.strip("()").split(",")))
        return convert_region_to_screen_coords(pos_in_region, hand_region_origin, tile_size)
    except ValueError:
        logging.error(f"Không thể chuyển đổi chuỗi vị trí: {position_str}")
        screen_width, screen_height = pyautogui.size()
        return screen_width // 2, screen_height // 2


# *** BẠN CẦN SAO CHÉP HÀM `logic_game` TỪ MÃ CŨ CỦA BẠN VÀO ĐÂY ***
# Nó khá dài và phức tạp, nên tôi không viết lại hoàn toàn.
# Đảm bảo nó trả về chuỗi vị trí dạng "(x,y)" hoặc một giá trị khác mà
# `process_discard_decision` có thể xử lý.
# Trong logic_game
def logic_game(formatted_text_input):
    logging.info(f"Input cho logic_game:\n{formatted_text_input}")
    names = []
    positions_str_corrected = [] # <--- SỬA TÊN BIẾN ĐỂ RÕ RÀNG

    lines = formatted_text_input.strip().splitlines()
    if not lines or not lines[0].startswith("Detected positions:"):
        logging.warning("logic_game: Định dạng đầu vào không đúng.")
        return None

    for line in lines[1:]:
        try:
            parts = line.split(":", 1)[1].strip()
            name_part, pos_part_raw = parts.split(" at position ", 1) # pos_part_raw là "(np.int64(x), np.int64(y))"
            names.append(name_part.strip())

            # --- PHẦN SỬA ĐỔI QUAN TRỌNG ---
            # Chuyển đổi chuỗi "(np.int64(x), np.int64(y))" thành "(x, y)"
            # Sử dụng regex để trích xuất số
            match = re.search(r'\(np\.int64\((\d+)\),\s*np\.int64\((\d+)\)\)', pos_part_raw)
            if match:
                x_val, y_val = match.groups()
                corrected_pos_str = f"({x_val},{y_val})" # Tạo chuỗi "(x,y)"
                positions_str_corrected.append(corrected_pos_str)
            else:
                # Nếu không khớp regex (dự phòng, có thể là định dạng (x,y) đã đúng)
                # Kiểm tra xem nó có phải là dạng (x,y) đơn giản không
                simple_match = re.search(r'\((\d+),\s*(\d+)\)', pos_part_raw)
                if simple_match:
                    positions_str_corrected.append(pos_part_raw) # Giữ nguyên nếu đã đúng dạng
                else:
                    logging.warning(f"logic_game: Không thể trích xuất tọa độ từ: {pos_part_raw}")
                    positions_str_corrected.append("(0,0)") # Hoặc một giá trị mặc định an toàn
            # --- KẾT THÚC PHẦN SỬA ĐỔI ---
        except ValueError:
            logging.warning(f"logic_game: Không thể phân tích dòng: {line}")
            continue

    if not names:
        logging.info("logic_game: Không có quân bài nào để xử lý.")
        return random.choice(positions_str_corrected) if positions_str_corrected else None


    # --- PHẦN LOGIC TÌM BỘ 3 (PHỎNG/SẢNH) ---
    # (Giữ nguyên logic từ code cũ của bạn, đảm bảo nó hoạt động với `names` và `positions_str`)
    valid_groups3_indices = [] # List các tuple chỉ số, ví dụ [(0,1,2), (5,6,7)]

    # Tìm sảnh 3
    temp_names = list(names) # Tạo bản sao để có thể "loại bỏ" các quân đã nhóm
    temp_indices = list(range(len(names)))
    processed_indices_for_sanh3 = set()

    i = 0
    while i < len(temp_names) - 2:
        if temp_indices[i] in processed_indices_for_sanh3 or \
           temp_indices[i+1] in processed_indices_for_sanh3 or \
           temp_indices[i+2] in processed_indices_for_sanh3:
            i += 1
            continue
        if is_consecutive_numbers3(temp_names[i], temp_names[i+1], temp_names[i+2]):
            group = (temp_indices[i], temp_indices[i+1], temp_indices[i+2])
            valid_groups3_indices.append(group)
            processed_indices_for_sanh3.update(group)
            i += 3 # Bỏ qua 3 quân đã nhóm
        else:
            i += 1

    # Tìm phỗng 3
    # Cần chạy lại trên danh sách chưa bị ảnh hưởng bởi sảnh 3 hoặc xử lý thông minh hơn
    # Ở đây làm đơn giản: tìm phỗng trên những gì còn lại hoặc toàn bộ rồi lọc trùng
    processed_indices_for_phong3 = set()
    i = 0
    while i < len(temp_names) - 2:
        # Đảm bảo các chỉ số chưa được dùng trong sảnh và chưa được dùng trong phỗng khác
        idx1, idx2, idx3 = temp_indices[i], temp_indices[i+1], temp_indices[i+2]
        if idx1 in processed_indices_for_sanh3 or idx2 in processed_indices_for_sanh3 or idx3 in processed_indices_for_sanh3 or \
           idx1 in processed_indices_for_phong3 or idx2 in processed_indices_for_phong3 or idx3 in processed_indices_for_phong3:
            i += 1
            continue

        if temp_names[i] == temp_names[i+1] == temp_names[i+2]:
            group = (idx1, idx2, idx3)
            # Kiểm tra xem nhóm này có trùng với nhóm sảnh nào không (ít khả năng)
            # và đảm bảo không thêm lại nếu đã xử lý
            is_new_group = True
            for g_idx in group:
                if g_idx in processed_indices_for_phong3: # đã xử lý bởi nhóm phỗng khác
                    is_new_group = False
                    break
            if is_new_group:
                valid_groups3_indices.append(group)
                processed_indices_for_phong3.update(group)
                i += 3
            else:
                i +=1

        else:
            i += 1

    all_grouped_indices_3 = set()
    for group in valid_groups3_indices:
        all_grouped_indices_3.update(group)

    remaining_after_groups3_names = []
    remaining_after_groups3_pos_str = []
    remaining_after_groups3_original_indices = [] # Lưu chỉ số gốc

    for i in range(len(names)):
        if i not in all_grouped_indices_3:
            remaining_after_groups3_names.append(names[i])
            remaining_after_groups3_pos_str.append(positions_str_corrected[i])
            remaining_after_groups3_original_indices.append(i)

    if not remaining_after_groups3_names: # Tất cả đã thành bộ 3
        logging.info("logic_game: Tất cả quân bài đã tạo thành bộ 3. Chọn ngẫu nhiên nếu có gì đó bất thường.")
        # Trường hợp này hiếm khi cần bỏ bài, có thể là lỗi logic trước đó
        # Hoặc nếu có 14 quân và tất cả là bộ 3 + 1 đôi -> Tsumo/Ron rồi
        # Nếu còn 1 quân lẻ do có 4 bộ và 1 quân (13 quân), bỏ quân lẻ đó.
        # Nếu có 13 quân và không có đôi nào, logic này sai.
        # Tạm thời: nếu còn bài mà ko vào logic dưới, bỏ ngẫu nhiên
        if names: return random.choice(positions_str_corrected)
        return None


    # --- PHẦN LOGIC TÌM BỘ 2 (ĐÔI/CHỜ) TRÊN `remaining_after_groups3_...` ---
    valid_groups2_indices_in_remaining = [] # List các tuple chỉ số TRONG `remaining_after_groups3_...`
    processed_indices_for_groups2 = set()

    # Tìm cặp chờ 2 quân liên tiếp (ví dụ: man-1, man-2)
    i = 0
    while i < len(remaining_after_groups3_names) - 1:
        idx_in_remaining1, idx_in_remaining2 = i, i + 1
        if idx_in_remaining1 in processed_indices_for_groups2 or \
           idx_in_remaining2 in processed_indices_for_groups2:
            i += 1
            continue
        if is_consecutive_numbers2(remaining_after_groups3_names[i], remaining_after_groups3_names[i+1]):
            group = (idx_in_remaining1, idx_in_remaining2)
            valid_groups2_indices_in_remaining.append(group)
            processed_indices_for_groups2.update(group)
            i += 2
        else:
            i += 1

    # Tìm cặp 2 quân giống hệt nhau (đôi)
    i = 0
    while i < len(remaining_after_groups3_names) - 1:
        idx_in_remaining1, idx_in_remaining2 = i, i + 1
        if idx_in_remaining1 in processed_indices_for_groups2 or \
           idx_in_remaining2 in processed_indices_for_groups2:
            i += 1
            continue
        if remaining_after_groups3_names[i] == remaining_after_groups3_names[i+1]:
            group = (idx_in_remaining1, idx_in_remaining2)
            valid_groups2_indices_in_remaining.append(group)
            processed_indices_for_groups2.update(group)
            i += 2
        else:
            i += 1

    # Tìm cặp chờ ở giữa (ví dụ: man-1, man-3)
    i = 0
    while i < len(remaining_after_groups3_names) - 1:
        idx_in_remaining1, idx_in_remaining2 = i, i + 1
        if idx_in_remaining1 in processed_indices_for_groups2 or \
           idx_in_remaining2 in processed_indices_for_groups2:
            i += 1
            continue
        if is_consecutive_numbers2_2(remaining_after_groups3_names[i], remaining_after_groups3_names[i+1]):
            group = (idx_in_remaining1, idx_in_remaining2)
            valid_groups2_indices_in_remaining.append(group)
            processed_indices_for_groups2.update(group)
            i += 2
        else:
            i += 1

    all_grouped_indices_2_in_remaining = set()
    for group in valid_groups2_indices_in_remaining:
        all_grouped_indices_2_in_remaining.update(group)

    # Các quân lẻ hoàn toàn (không nằm trong bộ 3 hay bộ 2)
    lonely_tiles_pos_str = []
    for i in range(len(remaining_after_groups3_names)):
        if i not in all_grouped_indices_2_in_remaining:
            lonely_tiles_pos_str.append(remaining_after_groups3_pos_str[i])

    if lonely_tiles_pos_str:
        logging.info(f"logic_game: Tìm thấy {len(lonely_tiles_pos_str)} quân lẻ hoàn toàn. Chọn ngẫu nhiên 1 quân.")
        # Thêm logic ưu tiên bỏ quân đầu/cuối dãy số hoặc quân chữ lẻ ở đây nếu muốn
        # Ví dụ: ưu tiên bỏ quân 1 hoặc 9
        candidates_to_discard_pos_str = []
        for i_rem, original_idx in enumerate(remaining_after_groups3_original_indices):
            if i_rem not in all_grouped_indices_2_in_remaining: # Đây là quân lẻ
                name = names[original_idx]
                pos_str = positions_str_corrected[original_idx]
                if '-' in name:
                    tile_num_str = name.split('-')[-1]
                    if tile_num_str == '1' or tile_num_str == '9':
                        logging.info(f"logic_game: Ưu tiên bỏ quân rìa: {name} tại {pos_str}")
                        return pos_str # Bỏ ngay quân rìa
                # Nếu không phải quân rìa, thêm vào danh sách ứng viên
                candidates_to_discard_pos_str.append(pos_str)

        if candidates_to_discard_pos_str:
            chosen_pos = random.choice(candidates_to_discard_pos_str)
            logging.info(f"logic_game: Chọn bỏ quân lẻ (không phải rìa): {chosen_pos}")
            return chosen_pos
        else: # Trường hợp tất cả quân lẻ đều là rìa và đã return ở trên (ít xảy ra)
            logging.info("logic_game: Không còn quân lẻ nào không phải rìa. Chọn ngẫu nhiên từ danh sách ban đầu nếu có.")
            return random.choice(positions_str_corrected) if positions_str_corrected else None


    # Nếu không có quân lẻ hoàn toàn, nghĩa là tất cả các quân còn lại đều tạo thành cặp (chờ hoặc đôi)
    # Lúc này cần phá một cặp. Ưu tiên phá cặp chờ hơn là phá đôi.
    # Hoặc ưu tiên phá cặp có quân chữ, quân rìa.
    # Đây là phần logic phức tạp cần chiến thuật cụ thể.
    # Ví dụ đơn giản: chọn ngẫu nhiên từ `remaining_after_groups3_pos_str`
    # (vì tất cả đã nằm trong các nhóm 2)
    if remaining_after_groups3_pos_str:
        logging.info("logic_game: Không có quân lẻ. Tất cả nằm trong cặp. Phá một cặp ngẫu nhiên (cần cải thiện logic này).")
        # Cố gắng không phá đôi nếu có các loại cặp khác
        # Tạm thời: chọn một quân từ các cặp chờ, nếu không có thì mới phá đôi
        potential_discards_from_waits_pos_str = []
        for i in range(len(remaining_after_groups3_names) - 1):
            name1 = remaining_after_groups3_names[i]
            name2 = remaining_after_groups3_names[i+1]
            pos1_str = remaining_after_groups3_pos_str[i]
            pos2_str = remaining_after_groups3_pos_str[i+1]

            # Ưu tiên phá các cặp chờ (ryanmen, penchan, kanchan)
            if is_consecutive_numbers2(name1, name2) or is_consecutive_numbers2_2(name1, name2):
                # Quyết định bỏ quân nào trong cặp chờ (ví dụ: bỏ quân rìa hơn)
                # Đơn giản là thêm cả hai, rồi chọn ngẫu nhiên
                potential_discards_from_waits_pos_str.append(pos1_str)
                potential_discards_from_waits_pos_str.append(pos2_str)

        if potential_discards_from_waits_pos_str:
            chosen_pos = random.choice(list(set(potential_discards_from_waits_pos_str))) # set để loại bỏ trùng
            logging.info(f"logic_game: Chọn phá cặp chờ: {chosen_pos}")
            return chosen_pos
        else: # Không có cặp chờ, chỉ còn các đôi
            chosen_pos = random.choice(remaining_after_groups3_pos_str)
            logging.info(f"logic_game: Chỉ còn các đôi. Chọn phá đôi ngẫu nhiên: {chosen_pos}")
            return chosen_pos

    logging.warning("logic_game: Không thể đưa ra quyết định. Trả về None.")
    return None # Không có gì để bỏ


# --- CLASS BOT CHÍNH ---
class MahjongBot:
    def __init__(self):
        self.riichi_declared = False
        self.running = True
        self.threads = []
        self.last_player_hand_text = "" # Để tránh xử lý lặp lại nếu tay bài không đổi

    def start(self):
        logging.info("Khởi động Mahjong Bot...")
        self._start_background_tasks()
        self._main_loop()
        self._stop_background_tasks()
        logging.info("Mahjong Bot đã dừng.")

    def _start_background_tasks(self):
        action_args = (
            PASS_IMAGE, ACTION_BUTTONS_REGION,
            RIICHI_IMAGE, TSUMO_IMAGE, RON_IMAGE, KITA_IMAGE,
            PON_IMAGE, KAN_IMAGE, CHII_IMAGE
        )
        action_thread = threading.Thread(target=self._continuously_check_action_buttons, args=action_args, daemon=True)
        self.threads.append(action_thread)
        action_thread.start()

        end_game_thread = threading.Thread(target=self._continuously_check_end_game, args=(END_GAME_IMAGE, END_GAME_REGION), daemon=True)
        self.threads.append(end_game_thread)
        end_game_thread.start()

    def _stop_background_tasks(self):
        self.running = False # Báo cho các luồng dừng lại (nếu chúng kiểm tra biến này)
        logging.info("Đang yêu cầu các luồng nền dừng...")
        # Các luồng daemon sẽ tự thoát khi chương trình chính kết thúc
        # Không cần join() phức tạp nếu chúng được thiết kế để thoát khi self.running = False

    def _continuously_check_action_buttons(self, pass_img, region, riichi_img, tsumo_img, ron_img, kita_img, pon_img, kan_img, chii_img):
        logging.info("Luồng theo dõi nút hành động đã bắt đầu.")
        action_priority = [ # Sắp xếp theo ưu tiên hành động (có thể cần điều chỉnh)
            (RON_IMAGE, "Ron"), (TSUMO_IMAGE, "Tsumo"), (KITA_IMAGE, "Kita"), # Kita có thể tự động
            (RIICHI_IMAGE, "Riichi"),
            (KAN_IMAGE, "Kan"), (PON_IMAGE, "Pon"), (CHII_IMAGE, "Chii"),
            # Pass sẽ được xử lý đặc biệt
        ]
        while self.running:
            try:
                clicked_an_action = False
                for img_path, action_name in action_priority:
                    locations = find_image_locations(img_path, region)
                    if locations:
                        # Ưu tiên các hành động mạnh trước
                        if action_name in ["Ron", "Tsumo", "Kita", "Riichi"]:
                            # Với Riichi, Kita, Tsumo, Ron, thường sẽ click ngay
                            # (trừ khi có logic phức tạp hơn, ví dụ không muốn Riichi)
                            screen_x, screen_y = convert_region_to_screen_coords(locations[0], region, TILE_IMAGE_SIZE) # Kích thước ảnh nút có thể khác
                            pyautogui.click(screen_x, screen_y)
                            logging.info(f"Đã click nút: {action_name}")
                            if action_name == "Riichi":
                                self.riichi_declared = True
                                logging.info("Đã khai báo Riichi.")
                            clicked_an_action = True
                            break # Xử lý một hành động mỗi lần kiểm tra

                        elif action_name in ["Kan", "Pon", "Chii"]:
                            # Với Kan, Pon, Chii, kiểm tra xem có muốn bỏ qua (Pass) không
                            pass_locations = find_image_locations(pass_img, region, 0.85)
                            if pass_locations:
                                # Logic: Nếu có thể Pon/Kan/Chii VÀ có thể Pass, thì có thể muốn Pass
                                # Đây là một quyết định chiến thuật. Mã cũ ưu tiên Pass.
                                # Chúng ta có thể làm cho nó có thể cấu hình hoặc thông minh hơn.
                                # Tạm thời: Nếu có thể KPC, thì không tự động Pass, để người chơi quyết định
                                # hoặc để logic game chính quyết định (nếu đến lượt mình).
                                # Ở đây, nếu bot tự động, có thể nó sẽ muốn KPC nếu có lợi.
                                # Giả sử bot muốn KPC nếu có thể:
                                screen_x, screen_y = convert_region_to_screen_coords(locations[0], region, TILE_IMAGE_SIZE)
                                pyautogui.click(screen_x, screen_y)
                                logging.info(f"Đã click nút: {action_name}")
                                clicked_an_action = True
                                break
                            else: # Không có nút Pass, chỉ có KPC
                                screen_x, screen_y = convert_region_to_screen_coords(locations[0], region, TILE_IMAGE_SIZE)
                                pyautogui.click(screen_x, screen_y)
                                logging.info(f"Đã click nút: {action_name}")
                                clicked_an_action = True
                                break
                if clicked_an_action:
                    time.sleep(ACTION_CLICK_DELAY * 5) # Chờ lâu hơn sau khi click 1 action
                    pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2) # Di chuyển chuột ra
                    continue # Bắt đầu lại vòng lặp kiểm tra nút

                # Nếu không có hành động ưu tiên nào, kiểm tra nút PASS (nếu nó xuất hiện một mình)
                # Điều này xảy ra khi đối thủ đánh ra mà mình không có hành động nào (Ron, Pon, Kan, Chii)
                pass_locations = find_image_locations(pass_img, region, 0.85)
                if pass_locations and not clicked_an_action:
                     # Chỉ click Pass nếu không có hành động nào khác được ưu tiên hơn và Pass là lựa chọn duy nhất
                     # (Ví dụ: đối thủ đánh, mình không Ron/Pon/Kan/Chii được, chỉ có Pass)
                     # Kiểm tra xem có nút hành động nào khác không (để tránh click Pass khi có thể Pon/Kan/Chii)
                    can_kpc = any(find_image_locations(img, region) for img, name in action_priority if name in ["Kan", "Pon", "Chii"])
                    if not can_kpc:
                        screen_x, screen_y = convert_region_to_screen_coords(pass_locations[0], region, TILE_IMAGE_SIZE)
                        pyautogui.click(screen_x, screen_y)
                        logging.info("Đã click nút: Pass (khi không có KPC)")
                        time.sleep(ACTION_CLICK_DELAY * 2)
                        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)


            except Exception as e:
                logging.error(f"Lỗi trong luồng theo dõi nút hành động: {e}")
            time.sleep(PASS_CHECK_DELAY)
        logging.info("Luồng theo dõi nút hành động đã kết thúc.")


    def _continuously_check_end_game(self, end_img_path, end_region):
        logging.info("Luồng theo dõi kết thúc game đã bắt đầu.")
        while self.running:
            try:
                if find_image_locations(end_img_path, end_region):
                    logging.info("Phát hiện màn hình kết thúc game.")
                    time.sleep(1) # Chờ một chút để game ổn định
                    for _ in range(10): # Click nhiều lần vào nút OK/Tiếp tục
                        if END_GAME_CLICKS:
                            pyautogui.click(END_GAME_CLICKS[0])
                        time.sleep(0.3)

                    # Click để chọn chế độ game/bắt đầu lại
                    if SELECTED_GAME_MODE in GAME_MODE_CLICKS:
                        for click_coord in GAME_MODE_CLICKS[SELECTED_GAME_MODE]:
                            pyautogui.click(click_coord)
                            time.sleep(1)
                    logging.info("Đã thực hiện các click sau khi kết thúc game. Chờ game tải...")
                    time.sleep(10) # Chờ game tải lại ván mới
            except Exception as e:
                logging.error(f"Lỗi trong luồng theo dõi kết thúc game: {e}")
            time.sleep(END_GAME_CHECK_DELAY)
        logging.info("Luồng theo dõi kết thúc game đã kết thúc.")


    def _scan_player_hand(self):
        """Quét các quân bài trên tay người chơi."""
        detected_tiles_info = [] # List of tuples: (tile_name, position_in_region)
        try:
            all_tile_image_files = [f for f in os.listdir(IMAGES_FOLDER)
                                    if f.lower().endswith(('.png', '.jpg', '.jpeg')) and
                                    f not in ['pass.png', 'riichi.png', 'tsumo.png', # Loại trừ ảnh nút
                                                'ron.png', 'kita.png', 'pon.png',
                                                'kan.png', 'chii.png', 'end.png', 'start.png']] # Thêm start.png nếu có

            sorted_tile_files = sort_tile_images(all_tile_image_files) # Sắp xếp để xử lý nhất quán

            # Sử dụng multi-threading để tìm kiếm ảnh (nếu có nhiều ảnh cần tìm)
            # Tuy nhiên, việc chụp màn hình lặp đi lặp lại có thể không hiệu quả bằng chụp 1 lần rồi xử lý
            # Mã cũ dùng threading cho mỗi ảnh, chúng ta có thể giữ lại nếu muốn
            # Hoặc, chụp 1 lần rồi tìm tất cả các mẫu trên đó (phức tạp hơn)

            results_from_threads = [] # [(image_path, grouped_positions), ...]
            threads_for_scan = []

            def process_single_tile_image(image_path_full, region, results_list):
                positions = find_image_locations(image_path_full, region)
                if positions:
                    grouped = group_nearby_positions(positions)
                    if grouped: # Chỉ thêm nếu có kết quả sau khi nhóm
                        results_list.append((image_path_full, grouped))

            for tile_file in sorted_tile_files:
                full_path = os.path.join(IMAGES_FOLDER, tile_file)
                # Tạo luồng cho mỗi ảnh (giống mã cũ)
                thread = threading.Thread(target=process_single_tile_image, args=(full_path, PLAYER_HAND_REGION, results_from_threads))
                threads_for_scan.append(thread)
                thread.start()

            for thread in threads_for_scan:
                thread.join() # Đợi tất cả hoàn thành

            for image_path, grouped_positions in results_from_threads:
                tile_name = get_tile_name_from_path(image_path)
                for pos in grouped_positions: # pos là (x, y) trong PLAYER_HAND_REGION
                    detected_tiles_info.append((tile_name, pos))

            # Sắp xếp lại detected_tiles_info theo vị trí x trên màn hình
            detected_tiles_info.sort(key=lambda item: item[1][0])

        except Exception as e:
            logging.error(f"Lỗi khi quét bài trên tay: {e}")
        return detected_tiles_info


    def _handle_player_turn(self, detected_tiles_info):
        """Xử lý logic khi đến lượt người chơi."""
        if not detected_tiles_info:
            logging.info("Không phát hiện quân bài nào trên tay.")
            return

        # Tạo chuỗi input cho logic_game (đã được sắp xếp theo loại quân bài)
        formatted_hand_text = input_text_formatter(detected_tiles_info)
        logging.info(f"Bài trên tay đã định dạng:\n{formatted_hand_text}")

        if formatted_hand_text == self.last_player_hand_text and not self.riichi_declared:
            logging.info("Bài trên tay không đổi, bỏ qua xử lý (trừ khi đã Riichi).")
            return
        self.last_player_hand_text = formatted_hand_text


        if self.riichi_declared:
            # Sau Riichi, thường là tự động bỏ quân vừa bốc (nếu không Tsumo)
            # Giả sử quân mới bốc là quân cuối cùng trong detected_tiles_info (cần kiểm tra)
            # Hoặc đơn giản là click vào quân bài có số lượng nhiều nhất nếu không ù
            # Mã cũ của bạn click vào TẤT CẢ các quân bài. Logic này không rõ ràng.
            # Tạm thời: click vào quân cuối cùng (thường là quân mới bốc)
            # Đây là một giả định lớn, cần xác định quân mới bốc một cách chính xác.
            if detected_tiles_info:
                # Tìm quân ngoài cùng bên phải (thường là quân mới bốc)
                # Sắp xếp theo x rồi lấy quân cuối
                # detected_tiles_info đã được sort theo x ở _scan_player_hand
                tile_to_discard_name, pos_in_region = detected_tiles_info[-1]
                logging.info(f"Đã Riichi. Tự động bỏ quân cuối cùng: {tile_to_discard_name} tại {pos_in_region}")
                screen_x, screen_y = convert_region_to_screen_coords(pos_in_region, PLAYER_HAND_REGION, TILE_IMAGE_SIZE)
                pyautogui.click(screen_x, screen_y)
                time.sleep(CLICK_DELAY)
                pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
            self.riichi_declared = False # Reset sau khi bỏ bài
            return

        # Gọi logic game để quyết định quân bài bỏ đi
        discard_pos_str = logic_game(formatted_hand_text)

        if discard_pos_str:
            logging.info(f"Logic game quyết định bỏ quân tại vị trí (trong vùng): {discard_pos_str}")
            screen_x, screen_y = process_discard_decision(discard_pos_str, TILE_IMAGE_SIZE, PLAYER_HAND_REGION)
            logging.info(f"Click để bỏ quân tại tọa độ màn hình: ({screen_x}, {screen_y})")
            pyautogui.click(screen_x, screen_y)
            time.sleep(ACTION_CLICK_DELAY)
            pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
            self.last_player_hand_text = "" # Reset để quét lại ở lượt sau
        else:
            logging.warning("Logic game không đưa ra được quyết định bỏ quân nào.")


    def _main_loop(self):
        logging.info("Bắt đầu vòng lặp chính của bot.")
        while self.running:
            try:
                if keyboard.is_pressed('q'):
                    logging.info("Đã nhấn 'q'. Dừng bot.")
                    self.running = False
                    break

                if is_my_turn(TURN_INDICATOR_REGION, TURN_INDICATOR_COLORS, COLOR_MATCH_TOLERANCE, PASS_IMAGE, ACTION_BUTTONS_REGION):
                    logging.info("Đến lượt của tôi. Bắt đầu quét bài...")
                    time.sleep(0.2) # Chờ một chút để giao diện ổn định hẳn
                    current_hand_tiles = self._scan_player_hand()
                    if current_hand_tiles:
                        self._handle_player_turn(current_hand_tiles)
                    else:
                        logging.info("Không tìm thấy quân bài nào để xử lý.")
                    time.sleep(LOOP_DELAY * 2) # Chờ lâu hơn sau khi hành động
                else:
                    # logging.info("Chưa đến lượt hoặc không có tín hiệu lượt rõ ràng.")
                    pass

            except Exception as e:
                logging.error(f"Lỗi trong vòng lặp chính: {e}", exc_info=True)
            time.sleep(LOOP_DELAY)

# --- ĐIỂM KHỞI CHẠY ---
if __name__ == "__main__":
    try:
        bot = MahjongBot()
        bot.start()
    except pyautogui.FailSafeException:
        logging.critical("FailSafe kích hoạt! Di chuyển chuột ra góc màn hình để dừng.")
    except Exception as e:
        logging.critical(f"Lỗi không mong muốn ở cấp cao nhất: {e}", exc_info=True)