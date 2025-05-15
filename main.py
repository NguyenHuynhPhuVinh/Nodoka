import cv2
import numpy as np
import pyautogui
import os
import time
import threading
import keyboard  # Thư viện để lắng nghe phím
import random
import re
from collections import Counter

def find_images(image_path, region, threshold=0.8):
    # Đọc ảnh mẫu cần tìm
    template = cv2.imread(image_path, 0)
    if template is None:
        print(f"Could not read image: {image_path}")
        return []

    # Chụp màn hình hiện tại trong vùng kiểm tra
    screenshot = pyautogui.screenshot(region=region)
    screenshot = np.array(screenshot)
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    # Tìm kiếm ảnh trên màn hình
    result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)

    # Nếu tìm thấy vị trí khớp, trả về danh sách các vị trí và kích thước
    positions = []
    for pt in zip(*loc[::-1]):
        # Lưu vị trí góc trên cùng bên trái và kích thước của mẫu
        positions.append(pt)
    
    return positions

def group_positions(positions, x_distance=30):
    """Nhóm các vị trí có giá trị x giao động lớn hơn hoặc bằng x_distance vào cùng một nhóm."""
    if not positions:
        return []
    
    # Sắp xếp các vị trí theo giá trị x
    positions_sorted = sorted(positions, key=lambda p: p[0])
    groups = []
    current_group = []
    
    for pos in positions_sorted:
        if not current_group:
            current_group.append(pos)
        else:
            last_x = current_group[-1][0]
            if abs(pos[0] - last_x) >= x_distance:
                groups.append(current_group)
                current_group = [pos]
            else:
                current_group.append(pos)
    
    if current_group:
        groups.append(current_group)
    
    # Chỉ lấy vị trí đầu tiên của mỗi nhóm
    return [group[0] for group in groups]

def process_single_image(image_path, region, image_size, results_list):
    """Xử lý một ảnh cụ thể trong một luồng."""
    positions = find_images(image_path, region)
    if positions:
        grouped_positions = group_positions(positions)
        results_list.append((image_path, grouped_positions))  # Lưu kết quả vào danh sách kết quả

def custom_sort_key(filename):
    order = {
        "man": 1,
        "pin": 2,
        "sou": 3,
        "haku": 4,
        "hatsu": 5,
        "chun": 6,
        "Ton": 7,
        "Nan": 8,
        "Sha": 9,
        "Pei": 10
    }
    
    # Tách phần tên và số từ tên tệp
    parts = filename.split('-')
    tile_type = parts[0]
    tile_number = parts[1].split('.')[0] if len(parts) > 1 else ""
    
    # Trả về giá trị sắp xếp dựa trên loại và số
    return (order.get(tile_type, 100), int(tile_number) if tile_number.isdigit() else 0)

def sort_images(image_list):
    # Sắp xếp danh sách ảnh sử dụng khóa tùy chỉnh
    return sorted(image_list, key=custom_sort_key)

def collect_positions(image_file, positions, image_size):
    """Lưu vị trí và tên quân bài vào mảng."""
    image_name = os.path.splitext(os.path.basename(image_file))[0]  # Loại bỏ đường dẫn và mở rộng
    return [(image_name, pos) for pos in positions]

def is_consecutive_numbers3(name1, name2, name3):
    match1 = re.match(r'(\D+)(\d+)', name1)
    match2 = re.match(r'(\D+)(\d+)', name2)
    match3 = re.match(r'(\D+)(\d+)', name3)
    
    if not (match1 and match2 and match3):
        return False
    
    prefix1, num1 = match1.groups()
    prefix2, num2 = match2.groups()
    prefix3, num3 = match3.groups()
    
    return (prefix1 == prefix2 == prefix3) and (int(num2) == int(num1) + 1) and (int(num3) == int(num2) + 1)

def is_consecutive_numbers2(name1, name2):
    match1 = re.match(r'(\D+)(\d+)', name1)
    match2 = re.match(r'(\D+)(\d+)', name2)
    
    if not (match1 and match2):
        return False
    
    prefix1, num1 = match1.groups()
    prefix2, num2 = match2.groups()
    
    return (prefix1 == prefix2) and (int(num2) == int(num1) + 1)

def is_consecutive_numbers2_2(name1, name2):
    match1 = re.match(r'(\D+)(\d+)', name1)
    match2 = re.match(r'(\D+)(\d+)', name2)
    
    if not (match1 and match2):
        return False
    
    prefix1, num1 = match1.groups()
    prefix2, num2 = match2.groups()
    
    return (prefix1 == prefix2) and (int(num2) == int(num1) + 2)

def logic_game(text):
    names = []
    positions = []
    
    lines = text.splitlines()
    
    for line in lines[1:]:
        name = line.split(":")[1].split(" at")[0].strip()
        position = line.split(" at position ")[1].strip()
        names.append(name)
        positions.append(position)
    
    valid_groups3 = []
    
    i = 0
    while i < len(names) - 2:
        if is_consecutive_numbers3(names[i], names[i + 1], names[i + 2]):
            valid_groups3.append((i, i + 1, i + 2))
            i += 3
        else:
            i += 1
    
    i = 0
    while i < len(names) - 2:
        if names[i] == names[i + 1] == names[i + 2]:
            valid_groups3.append((i, i + 1, i + 2))
            i += 3
        else:
            i += 1
    
    all_indices3 = {index for group in valid_groups3 for index in group}
    sorted_indices3 = sorted(all_indices3)
    
    grouped_indices3 = all_indices3
    remaining_names3 = [name for i, name in enumerate(names) if i not in grouped_indices3]
    remaining_positions3 = [position for i, position in enumerate(positions) if i not in grouped_indices3]
    
    remaining_indices3 = [i for i in range(len(names)) if i not in grouped_indices3]

    valid_groups2 = []
    
    i = 0
    while i < len(remaining_names3) - 1:
        if is_consecutive_numbers2(remaining_names3[i], remaining_names3[i + 1]):
            valid_groups2.append((i, i + 1))
            i += 2
        else:
            i += 1
    
    i = 0
    while i < len(remaining_names3) - 1:
        if remaining_names3[i] == remaining_names3[i + 1]:
            valid_groups2.append((i, i + 1))
            i += 2
        else:
            i += 1
    
    i = 0
    while i < len(remaining_names3) - 1:
        if is_consecutive_numbers2_2(remaining_names3[i], remaining_names3[i + 1]):
            valid_groups2.append((i, i + 1))
            i += 2
        else:
            i += 1
    
    all_indices2 = {index for group in valid_groups2 for index in group}
    sorted_indices2 = sorted(all_indices2)
    
    grouped_indices2 = all_indices2
    remaining_names2 = [name for i, name in enumerate(remaining_names3) if i not in grouped_indices2]
    remaining_positions2 = [position for i, position in enumerate(remaining_positions3) if i not in grouped_indices2]
    
    remaining_indices2 = [i for i in range(len(remaining_names3)) if i not in grouped_indices2]

    output = 0
    
    # Chọn ngẫu nhiên giá trị từ remaining_indices2 hoặc remaining_indices3
    if remaining_positions2:
        output = random.choice(remaining_positions2)
        return output
    elif remaining_positions3:
        
        for index in range(len(remaining_names3) - 1):
            # Kiểm tra nếu chuỗi hiện tại và chuỗi kế tiếp có dấu gạch ngang
            if '-' in remaining_names3[index] and '-' in remaining_names3[index + 1]:
                # Tách phần trước và sau dấu gạch ngang của phần tử hiện tại và phần tử kế tiếp
                current_name, current_number = remaining_names3[index].rsplit('-', 1)
                next_name, next_number = remaining_names3[index + 1].rsplit('-', 1)
                
                # Chuyển đổi phần số thành số nguyên
                current_number = int(current_number)
                next_number = int(next_number)
                
                # Kiểm tra nếu chuỗi trước dấu gạch ngang giống nhau và phần số cách nhau 2 số
                if current_name == next_name and abs(current_number - next_number) == 2:
                    # Kiểm tra phần tử trước current
                    if index > 0:  # Đảm bảo index không âm để có phần tử trước current
                        if '-' in remaining_names3[index - 1]:
                            prev_name, prev_number = remaining_names3[index - 1].rsplit('-', 1)
                            prev_number = int(prev_number)
                            # Kiểm tra nếu tên khác current hoặc tên giống nhưng số cách current 2 số
                            if prev_name != current_name or abs(current_number - prev_number) == 2:
                                output = remaining_positions3[index]
                                return output
                        else:
                            output = remaining_positions3[index]
                            return output
                    else:
                        output = remaining_positions3[index]
                        return output
                    
                    # Kiểm tra phần tử sau next
                    if index + 2 < len(remaining_names3):  # Đảm bảo index không vượt quá danh sách
                        if '-' in remaining_names3[index + 2]: 
                            after_name, after_number = remaining_names3[index + 2].rsplit('-', 1)
                            after_number = int(after_number)
                            # Kiểm tra nếu tên khác next hoặc tên giống nhưng số cách next 2 số
                            if after_name != next_name or abs(after_number - next_number) == 2:
                                output = remaining_positions3[index + 1]
                                return output
                        else:
                            output = remaining_positions3[index + 1]
                            return output
                    else:
                        output = remaining_positions3[index + 1]
                        return output
        # Lặp qua danh sách và kiểm tra điều kiện
        for index, value in enumerate(remaining_names3):
            # Tách phần số sau dấu gạch ngang
            number_part = value.split('-')[-1]
            
            # Kiểm tra nếu phần số này là 1 hoặc 9
            if number_part == '1' or number_part == '9':
                output = remaining_positions3[index]
                return output

        seen_values = set()
        for index, value in enumerate(remaining_names3):
            if value in seen_values:
                # Nếu giá trị đã xuất hiện trước đó, in ra và dừng lại
                output = remaining_positions3[index]
                return output
            seen_values.add(value)

        output = random.choice(remaining_positions3)
        return output
    return output

def input_text(input_string):
        # Tách các dòng dữ liệu
    lines = input_string.strip().split('\n')[1:]  # Bỏ dòng đầu tiên "Detected positions:"

    # Tạo danh sách các mục
    entries = []
    for line in lines:
        match = re.match(r'\d+: (\w+-\d+|\w+) at position \(\d+, \d+\)', line)
        if match:
            parts = line.split()
            index = int(parts[0][:-1])  # Lấy index từ "0:"
            name = parts[1]  # Tên của mục (ví dụ: "man-1", "pin-2", ...)
            entries.append((index, name, line))

    # Định nghĩa hàm để trích xuất thông tin cần thiết để sắp xếp
    def sort_key(entry):
        index, name, line = entry
        if '-' in name:
            prefix, num = name.split('-')
            if prefix in ['man', 'sou', 'pin']:
                return (['man', 'pin', 'sou'].index(prefix), int(num))
            else:
                return (float('inf'), 0)
        else:
            # Đặt thứ tự của các quân còn lại theo yêu cầu
            order = {
                "haku": 4,
                "hatsu": 5,
                "chun": 6,
                "Ton": 7,
                "Nan": 8,
                "Sha": 9,
                "Pei": 10
            }
            return (order.get(name, float('inf')), 0)

    # Sắp xếp các mục theo thứ tự yêu cầu
    sorted_entries = sorted(entries, key=sort_key)

    # Tạo chuỗi đầu ra đã sắp xếp
    output_string = "Detected positions:\n"
    for new_index, (_, _, line) in enumerate(sorted_entries):
        # Bỏ chỉ số cũ và giữ lại nội dung chính
        content = line.split(': ', 1)[1]  # Lấy phần sau dấu ": "
        output_string += f"{new_index}: {content}\n"
        
    return output_string

def process_position(position_str):
    # Nếu position_str không phải là chuỗi, trả về trung tâm màn hình
    if not isinstance(position_str, str):
        screen_width, screen_height = pyautogui.size()
        return screen_width // 2, screen_height // 2
    
    # Chuyển đổi chuỗi thành tuple (x, y)
    position_str = position_str.strip("()")  # Xóa dấu ngoặc
    x_str, y_str = position_str.split(",")   # Tách thành x và y
    x = int(x_str)   # Chuyển đổi thành số nguyên
    y = int(y_str)   # Chuyển đổi thành số nguyên
    return x, y

riichi_detected = False
def process_clicks(positions, image_size, region):
    global riichi_detected
    if riichi_detected:
        for name, pos in positions:
            x, y = pos
            center_x = x + image_size[0] // 2
            center_y = y + image_size[1] // 2
            screen_x = center_x + region[0]
            screen_y = center_y + region[1]
            pyautogui.click(screen_x, screen_y)
            time.sleep(0.25)  # Tạm dừng giữa các lần nhấp chuột
        # Di chuyển chuột lên giữa màn hình
        screen_width, screen_height = pyautogui.size()
        center_screen_x = screen_width // 2
        center_screen_y = screen_height // 2
        pyautogui.moveTo(center_screen_x, center_screen_y)
        riichi_detected = False
    else:
        """In ra danh sách các vị trí và chờ người dùng nhập để nhấn vào vị trí đó."""
        text = "Detected positions:\n"
        for i, (name, pos) in enumerate(positions):
            text += f"{i}: {name} at position {pos}\n"
        
        text = input_text(text)

        # In ra toàn bộ thông tin đã lưu
        while True:
            position_str = logic_game(text)
            x, y = process_position(position_str)
            center_x = x + image_size[0] // 2
            center_y = y + image_size[1] // 2
            screen_x = center_x + region[0]
            screen_y = center_y + region[1]
            pyautogui.click(screen_x, screen_y)
            time.sleep(0.1)  # Tạm dừng giữa các lần nhấp chuột
            # Di chuyển chuột lên giữa màn hình
            screen_width, screen_height = pyautogui.size()
            center_screen_x = screen_width // 2
            center_screen_y = screen_height // 2
            pyautogui.moveTo(center_screen_x, center_screen_y)
            break

def detect_and_click_pass(pass_image_path, pass_region, riichi_image_path, tsumo_image_path, ron_image_path, kita_image_path, pon_image_path, kan_image_path, chii_image_path):
    """Kiểm tra liên tục và nhấn vào ảnh pass nếu phát hiện, ưu tiên các ảnh khác."""
    global riichi_detected
    while True:
        for image_path, action_name in [(riichi_image_path, 'riichi'), (tsumo_image_path, 'tsumo'), (ron_image_path, 'ron'), (kita_image_path, 'kita'), (pon_image_path, 'pon'), (kan_image_path, 'kan'), (chii_image_path, 'chii')]:
            positions = find_images(image_path, pass_region)
            if positions:
                if action_name == 'pon' or action_name == 'kan' or action_name == 'chii':
                    positions = find_images(pass_image_path, pass_region)
                    if positions:
                        for position in positions:
                            x, y = position
                        pyautogui.click(x + pass_region[0], y + pass_region[1])
                        break
                for position in positions:
                    x, y = position
                pyautogui.click(x + pass_region[0], y + pass_region[1])
                if action_name == 'riichi':
                    riichi_detected = True
                break
        time.sleep(1)  # Thời gian chờ trước khi kiểm tra lại

def check_pass(pass_check, pass_region_check):
    positions = find_images(pass_check, pass_region_check)
    if positions:
        return True
    
    return False

# def check_start_game(start_check, start_region_check):
#     while True:
#         positions = find_images(start_check, start_region_check)
#         if positions:
#             for position in positions:
#                 x, y = position
#                 pyautogui.click(x + pass_region[0], y + pass_region[1])

#         time.sleep(3)  # Thời gian chờ trước khi kiểm tra lại

def check_end_game(end_check, end_region_check):
    while True:
        positions = find_images(end_check, end_region_check)
        if positions:
            for _ in range(10):
                pyautogui.click(1753, 948)
                time.sleep(1)

            if game_mode == 0:
                pyautogui.click(1324, 496)
            elif game_mode == 1:
                pyautogui.click(1161, 626)
                time.sleep(1)
                pyautogui.click(1030, 893)
        time.sleep(3)  # Thời gian chờ trước khi kiểm tra lại

def check_color_in_region(region, target_colors, tolerance=5):
    """
    Kiểm tra xem trong vùng region có chứa một trong các màu sắc cụ thể hay không.
    
    :param region: Tuple chứa tọa độ vùng kiểm tra (x, y, width, height).
    :param target_colors: Danh sách các màu cần kiểm tra, mỗi màu là một tuple (R, G, B).
    :param tolerance: Độ chênh lệch cho phép giữa các giá trị màu sắc.
    :return: True nếu tìm thấy màu sắc trong vùng, False nếu không.
    """
    
    # Chụp ảnh màn hình của vùng kiểm tra
    screenshot = pyautogui.screenshot(region=region)
    screenshot_np = np.array(screenshot)

    # Lặp qua từng màu cần kiểm tra
    for target_color in target_colors:
        # Tạo mặt nạ (mask) để tìm các pixel có màu tương tự target_color
        mask = np.all(np.abs(screenshot_np - target_color) <= tolerance, axis=-1)
        
        # Nếu tìm thấy ít nhất một pixel khớp với màu, trả về True
        if np.any(mask):
            if not check_pass(pass_image_path, pass_region):
                return True

    # Nếu không tìm thấy màu sắc nào khớp, trả về False
    return False

# Định nghĩa các màu cần kiểm tra
target_colors = [
    (196, 245, 253),
    (201, 248, 254),
    (203, 248, 254),
    (255, 198, 38),
    (255, 201, 42),
    (255, 205, 49)
]

reference_region = (1663, 772, 1737 - 1663, 867 - 772)  # Vùng cần kiểm tra
region = (289, 840, 1422, 170)  # Vùng kiểm tra từ (289, 840) với kích thước 1422x170
    # Đường dẫn đến thư mục chứa ảnh cần kiểm tra
images_folder = 'images'
    # Giả sử kích thước quân bài là cố định
image_size = (75, 105)  # Ví dụ: chiều rộng 100px, chiều cao 150px
pass_region = (473, 764, 1588 - 473, 865 - 764)  # Vùng kiểm tra cho ảnh pass
pass_image_path = 'images/pass.png'

end_region_check = (12, 50, 428 - 12, 146 - 50)  # Vùng kiểm tra cho ảnh pass
end_check = 'images/end.png'

# start_region_check = (1127, 257, 1323 - 1127, 451 - 428)  # Vùng kiểm tra cho ảnh pass
# start_check = 'images/start.png'

game_mode = 0

def main():
    riichi_image_path = 'images/riichi.png'
    tsumo_image_path = 'images/tsumo.png'
    ron_image_path = 'images/ron.png'
    kita_image_path = 'images/kita.png'
    pon_image_path = 'images/pon.png'
    kan_image_path = 'images/kan.png'
    chii_image_path = 'images/chii.png'

    # Khởi động kiểm tra liên tục ảnh pass
    pass_thread = threading.Thread(target=detect_and_click_pass, args=(pass_image_path, pass_region, riichi_image_path, tsumo_image_path, ron_image_path, kita_image_path, pon_image_path, kan_image_path, chii_image_path))
    pass_thread.daemon = True
    pass_thread.start()

    # Khởi động kiểm tra liên tục ảnh pass
    end_thread = threading.Thread(target=check_end_game, args=(end_check, end_region_check))
    end_thread.daemon = True
    end_thread.start()

    # # Khởi động kiểm tra liên tục ảnh pass
    # start_thread = threading.Thread(target=check_start_game, args=(start_check, start_region_check))
    # start_thread.daemon = True
    # start_thread.start()

    while True:
        detected_positions = []  # Mảng lưu các vị trí phát hiện
        image_files = os.listdir(images_folder)  # Lấy danh sách các tệp ảnh trong thư mục
        image_files = [f for f in image_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]  # Lọc các tệp ảnh
        sorted_files = sort_images(image_files)  # Sắp xếp các tệp ảnh

        # Tạo danh sách các luồng cho từng ảnh
        threads = []
        results_list = []
        if check_color_in_region(reference_region, target_colors):
            for image_file in sorted_files:
                image_path = os.path.join(images_folder, image_file)
                thread = threading.Thread(target=process_single_image, args=(image_path, region, image_size, results_list))
                threads.append(thread)
                thread.start()

            # Đợi tất cả các luồng hoàn thành
            for thread in threads:
                thread.join()

            # Xử lý kết quả từ các luồng
            for image_path, positions in results_list:
                if positions:  # Nếu có các nhóm vị trí khớp
                    detected_positions.extend(collect_positions(image_path, positions, image_size))

            # In ra các ảnh đã phát hiện cùng số nhóm
            if detected_positions:
                process_clicks(detected_positions, image_size, region)
            
            if keyboard.is_pressed('q'):
                print("Exit key pressed. Exiting the program.")
                break
        
        time.sleep(0.5)

if __name__ == "__main__":
    main()