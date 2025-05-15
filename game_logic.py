# game_logic.py
import re
import logging
import random
import numpy as np # Cần cho hàm is_my_turn
import pyautogui # Cần cho hàm is_my_turn (screenshot)

from image_utils import find_image_locations, convert_region_to_screen_coords
from config import (
    TURN_INDICATOR_REGION, TURN_INDICATOR_COLORS, COLOR_MATCH_TOLERANCE,
    PASS_IMAGE, ACTION_BUTTONS_REGION, TILE_IMAGE_SIZE, PLAYER_HAND_REGION
)

def is_my_turn(indicator_region=TURN_INDICATOR_REGION,
               target_colors=TURN_INDICATOR_COLORS,
               tolerance=COLOR_MATCH_TOLERANCE,
               pass_image_path=PASS_IMAGE,
               pass_search_region=ACTION_BUTTONS_REGION):
    """Kiểm tra xem có phải lượt của người chơi không."""
    try:
        screenshot = pyautogui.screenshot(region=indicator_region)
        screenshot_np = np.array(screenshot)
        for target_color in target_colors:
            mask = np.all(np.abs(screenshot_np - target_color) <= tolerance, axis=-1)
            if np.any(mask):
                if not find_image_locations(pass_image_path, pass_search_region, 0.85):
                    logging.info("Lượt của tôi (màu khớp và không có nút Pass).")
                    return True
                else:
                    logging.info("Màu khớp nhưng nút Pass đang hiển thị.")
                    return False
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra lượt chơi: {e}")
        return False

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
    def sort_key(entry_tuple):
        name = entry_tuple[0]
        if '-' in name:
            prefix, num_str = name.split('-', 1)
            if not num_str.isdigit(): return (99,0)
            num = int(num_str)
            if prefix in ['man', 'pin', 'sou']:
                return (['man', 'pin', 'sou'].index(prefix), num)
            else:
                return (90, num)
        else:
            order = {"haku": 4, "hatsu": 5, "chun": 6, "Ton": 7, "Nan": 8, "Sha": 9, "Pei": 10}
            return (order.get(name, 99), 0)

    entries_to_sort = []
    for i, (name, _) in enumerate(detected_tiles_info):
        entries_to_sort.append((name, i))

    sorted_entries_with_indices = sorted(entries_to_sort, key=sort_key)

    output_string = "Detected positions:\n"
    for new_idx, (name, original_idx) in enumerate(sorted_entries_with_indices):
        _, pos = detected_tiles_info[original_idx]
        output_string += f"{new_idx}: {name} at position {pos}\n"
    return output_string.strip()

def process_discard_decision(position_str, tile_size=TILE_IMAGE_SIZE, hand_region_origin=PLAYER_HAND_REGION):
    if not isinstance(position_str, str) or not position_str.startswith("("):
        logging.warning(f"Vị trí không hợp lệ từ logic_game: {position_str}. Click giữa màn hình.")
        screen_width, screen_height = pyautogui.size()
        return screen_width // 2, screen_height // 2
    try:
        pos_in_region = tuple(map(int, position_str.strip("()").split(",")))
        return convert_region_to_screen_coords(pos_in_region, hand_region_origin, tile_size)
    except ValueError:
        logging.error(f"Không thể chuyển đổi chuỗi vị trí: {position_str}")
        screen_width, screen_height = pyautogui.size()
        return screen_width // 2, screen_height // 2

def logic_game(formatted_text_input):
    # ... (Nội dung hàm logic_game như cũ) ...
    # Đảm bảo các logging.info, logging.warning, logging.error vẫn hoạt động.
    # Hàm này không thay đổi nội dung, chỉ là di chuyển file.
    logging.info(f"Input cho logic_game:\n{formatted_text_input}")
    names = []
    positions_str_corrected = []

    lines = formatted_text_input.strip().splitlines()
    if not lines or not lines[0].startswith("Detected positions:"):
        logging.warning("logic_game: Định dạng đầu vào không đúng.")
        return None

    for line in lines[1:]:
        try:
            parts = line.split(":", 1)[1].strip()
            name_part, pos_part_raw = parts.split(" at position ", 1)
            names.append(name_part.strip())
            match = re.search(r'\(np\.int64\((\d+)\),\s*np\.int64\((\d+)\)\)', pos_part_raw)
            if match:
                x_val, y_val = match.groups()
                corrected_pos_str = f"({x_val},{y_val})"
                positions_str_corrected.append(corrected_pos_str)
            else:
                simple_match = re.search(r'\((\d+),\s*(\d+)\)', pos_part_raw)
                if simple_match:
                    positions_str_corrected.append(pos_part_raw)
                else:
                    logging.warning(f"logic_game: Không thể trích xuất tọa độ từ: {pos_part_raw}")
                    positions_str_corrected.append("(0,0)")
        except ValueError:
            logging.warning(f"logic_game: Không thể phân tích dòng: {line}")
            continue

    if not names:
        logging.info("logic_game: Không có quân bài nào để xử lý.")
        return random.choice(positions_str_corrected) if positions_str_corrected else None

    valid_groups3_indices = []
    temp_names = list(names)
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
            i += 3
        else:
            i += 1

    processed_indices_for_phong3 = set()
    i = 0
    while i < len(temp_names) - 2:
        idx1, idx2, idx3 = temp_indices[i], temp_indices[i+1], temp_indices[i+2]
        if idx1 in processed_indices_for_sanh3 or idx2 in processed_indices_for_sanh3 or idx3 in processed_indices_for_sanh3 or \
           idx1 in processed_indices_for_phong3 or idx2 in processed_indices_for_phong3 or idx3 in processed_indices_for_phong3:
            i += 1
            continue
        if temp_names[i] == temp_names[i+1] == temp_names[i+2]:
            group = (idx1, idx2, idx3)
            is_new_group = True
            for g_idx in group:
                if g_idx in processed_indices_for_phong3:
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
    remaining_after_groups3_original_indices = []

    for i in range(len(names)):
        if i not in all_grouped_indices_3:
            remaining_after_groups3_names.append(names[i])
            remaining_after_groups3_pos_str.append(positions_str_corrected[i])
            remaining_after_groups3_original_indices.append(i)

    if not remaining_after_groups3_names:
        logging.info("logic_game: Tất cả quân bài đã tạo thành bộ 3...")
        if names: return random.choice(positions_str_corrected)
        return None

    valid_groups2_indices_in_remaining = []
    processed_indices_for_groups2 = set()
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

    lonely_tiles_pos_str = []
    candidates_to_discard_pos_str = [] # Di chuyển khai báo ra ngoài
    for i_rem, original_idx in enumerate(remaining_after_groups3_original_indices):
        if i_rem not in all_grouped_indices_2_in_remaining: # Đây là quân lẻ
            name = names[original_idx]
            pos_str = positions_str_corrected[original_idx]
            if '-' in name:
                tile_num_str = name.split('-')[-1]
                if tile_num_str == '1' or tile_num_str == '9':
                    logging.info(f"logic_game: Ưu tiên bỏ quân rìa: {name} tại {pos_str}")
                    return pos_str
            candidates_to_discard_pos_str.append(pos_str) # Thêm vào danh sách nếu không phải rìa

    if candidates_to_discard_pos_str: # Nếu có quân lẻ không phải rìa
        chosen_pos = random.choice(candidates_to_discard_pos_str)
        logging.info(f"logic_game: Chọn bỏ quân lẻ (không phải rìa): {chosen_pos}")
        return chosen_pos
    # Nếu không có candidates_to_discard_pos_str (tức là lonely_tiles_pos_str rỗng hoặc tất cả đều là rìa đã return)
    # thì đi tiếp logic phá cặp.

    if remaining_after_groups3_pos_str: # Nếu không có quân lẻ hoàn toàn, và còn quân trong remaining_after_groups3
        logging.info("logic_game: Không có quân lẻ. Tất cả nằm trong cặp. Phá một cặp.")
        potential_discards_from_waits_pos_str = []
        for i in range(len(remaining_after_groups3_names) - 1):
            name1 = remaining_after_groups3_names[i]
            name2 = remaining_after_groups3_names[i+1]
            pos1_str = remaining_after_groups3_pos_str[i]
            pos2_str = remaining_after_groups3_pos_str[i+1]
            if is_consecutive_numbers2(name1, name2) or is_consecutive_numbers2_2(name1, name2):
                potential_discards_from_waits_pos_str.append(pos1_str)
                potential_discards_from_waits_pos_str.append(pos2_str)

        if potential_discards_from_waits_pos_str:
            chosen_pos = random.choice(list(set(potential_discards_from_waits_pos_str)))
            logging.info(f"logic_game: Chọn phá cặp chờ: {chosen_pos}")
            return chosen_pos
        else: # Chỉ còn các đôi
            chosen_pos = random.choice(remaining_after_groups3_pos_str)
            logging.info(f"logic_game: Chỉ còn các đôi. Chọn phá đôi ngẫu nhiên: {chosen_pos}")
            return chosen_pos

    logging.warning("logic_game: Không thể đưa ra quyết định. Trả về None.")
    return None