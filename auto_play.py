import os
import sys
import json
import time
import random
import pyautogui
import keyboard
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import traceback

# Đường dẫn đến file JSON - sử dụng đường dẫn tuyệt đối
JSON_FILE_PATH = os.path.abspath("./game_logs.json")
print(f"Đường dẫn file JSON: {JSON_FILE_PATH}")

# Kiểm tra xem file có tồn tại không
if os.path.exists(JSON_FILE_PATH):
    print(f"File JSON đã tồn tại")
else:
    print(f"File JSON chưa tồn tại, sẽ chờ đến khi nó được tạo")

# Tọa độ các quân bài trên tay (0-12) và quân tsumo
TEHAI_POSITIONS = {
    0: (100, 650),  # Vị trí quân bài 1 (index 0)
    1: (130, 650),  # Vị trí quân bài 2 (index 1)
    2: (160, 650),  # Vị trí quân bài 3 (index 2)
    3: (190, 650),  # Vị trí quân bài 4 (index 3)
    4: (220, 650),  # Vị trí quân bài 5 (index 4)
    5: (250, 650),  # Vị trí quân bài 6 (index 5)
    6: (280, 650),  # Vị trí quân bài 7 (index 6)
    7: (310, 650),  # Vị trí quân bài 8 (index 7)
    8: (340, 650),  # Vị trí quân bài 9 (index 8)
    9: (370, 650),  # Vị trí quân bài 10 (index 9)
    10: (400, 650), # Vị trí quân bài 11 (index 10)
    11: (430, 650), # Vị trí quân bài 12 (index 11)
    12: (460, 650), # Vị trí quân bài 13 (index 12)
    "tsumo": (500, 650)  # Vị trí quân tsumo
}

# Tọa độ các nút bấm
BUTTON_POSITIONS = {
    "pass": (700, 600),    # Vị trí nút Pass
    "pon": (750, 600),     # Vị trí nút Pon
    "chi_low": (800, 580), # Vị trí nút Chi thấp
    "chi_mid": (800, 600), # Vị trí nút Chi giữa
    "chi_high": (800, 620),# Vị trí nút Chi cao
    "kan": (850, 600),     # Vị trí nút Kan
    "ron": (900, 600),     # Vị trí nút Ron
    "riichi": (950, 600)   # Vị trí nút Riichi
}

# Lưu trạng thái cuối cùng để so sánh
last_state = None
# Thời gian sửa đổi file cuối cùng
last_modified_time = 0

# Thiết lập delay ngẫu nhiên
MIN_DELAY = 2.5  # Thời gian chờ tối thiểu (giây)
MAX_DELAY = 5  # Thời gian chờ tối đa (giây)
PRE_CLICK_DELAY_MIN = 0.2  # Độ trễ tối thiểu trước khi click
PRE_CLICK_DELAY_MAX = 0.8  # Độ trễ tối đa trước khi click
POST_CLICK_DELAY_MIN = 0.1  # Độ trễ tối thiểu sau khi click
POST_CLICK_DELAY_MAX = 0.3  # Độ trễ tối đa sau khi click
ENABLE_RANDOM_DELAY = True  # Bật/tắt tính năng delay ngẫu nhiên

# Hàm tạo độ trễ ngẫu nhiên
def random_delay(min_delay, max_delay, message=None):
    if not ENABLE_RANDOM_DELAY:
        return
        
    delay_time = random.uniform(min_delay, max_delay)
    if message:
        print(f"{message} ({delay_time:.2f}s)")
    time.sleep(delay_time)

# Hàm click an toàn với kiểm tra tọa độ
def safe_click(position, description=""):
    try:
        # Độ trễ ngẫu nhiên trước khi click
        random_delay(PRE_CLICK_DELAY_MIN, PRE_CLICK_DELAY_MAX, f"Chờ trước khi click {description}")
        
        # Xử lý cả trường hợp position là tuple hoặc là list/array từ JSON
        if (isinstance(position, tuple) or isinstance(position, list)) and len(position) == 2:
            x, y = position[0], position[1]  # Truy cập theo index thay vì giả định là tuple
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                print(f"Click {description} tại vị trí ({x}, {y})")
                pyautogui.click(x, y)
                
                # Độ trễ ngẫu nhiên sau khi click
                random_delay(POST_CLICK_DELAY_MIN, POST_CLICK_DELAY_MAX, "Chờ sau khi click")
                return True
            else:
                print(f"Lỗi: Tọa độ không hợp lệ - x={x}, y={y} không phải là số")
        else:
            print(f"Lỗi: Vị trí không hợp lệ - {position} không phải là tuple hoặc list có 2 phần tử")
        return False
    except Exception as e:
        print(f"Lỗi khi click {description}: {e}")
        print(f"Chi tiết lỗi: {type(e).__name__}")
        return False

# Hàm thực hiện click theo hành động
def perform_action(action_type, tehai, tsumo, recommandations):
    # Chờ một khoảng thời gian ngẫu nhiên trước khi thực hiện hành động
    random_delay(MIN_DELAY, MAX_DELAY, "Chờ trước khi thực hiện hành động")
    
    # Kiểm tra nếu không có recommandations
    if not recommandations:
        print("Không có khuyến nghị nào, bỏ qua")
        return
        
    print(f"Đang thực hiện hành động dựa trên recommandation: {recommandations[0]}")
    
    # Xử lý trường hợp "none" đặc biệt (bấm nút Pass)
    if recommandations[0]["action"] == "none" or recommandations[0]["action"] == "ryukyoku":
        print("Bấm nút Pass (hành động none/ryukyoku)")
        if "pass" in BUTTON_POSITIONS:
            safe_click(BUTTON_POSITIONS["pass"], "nút Pass")
        else:
            print("Lỗi: Không tìm thấy vị trí nút Pass")
        return
    
    # Đây là phần logic quyết định hành động cần thực hiện
    # Nếu khuyến nghị hàng đầu là dahai (đánh bài)
    if recommandations[0]["action"] not in ["reach", "chi_low", "chi_mid", "chi_high", "pon", "kan_select", "hora"]:
        discard_tile = recommandations[0]["action"]
        
        # Tìm vị trí của lá bài cần đánh trong tehai
        for i, tile in enumerate(tehai):
            if tile == discard_tile:
                # Click vào quân bài đó
                print(f"Đánh quân bài {discard_tile} ở vị trí {i}")
                if i in TEHAI_POSITIONS:
                    safe_click(TEHAI_POSITIONS[i], f"quân bài {discard_tile}")
                else:
                    print(f"Lỗi: Không tìm thấy vị trí cho quân bài ở index {i}")
                return
        
        # Nếu là quân tsumo
        if tsumo == discard_tile:
            print(f"Đánh quân tsumo {discard_tile}")
            if "tsumo" in TEHAI_POSITIONS:
                safe_click(TEHAI_POSITIONS["tsumo"], "quân tsumo")
            else:
                print("Lỗi: Không tìm thấy vị trí quân tsumo")
            return
            
        print(f"Không tìm thấy quân bài {discard_tile} trong tehai hoặc tsumo")
    
    # Các hành động đặc biệt
    if recommandations[0]["action"] in ["reach", "chi_low", "chi_mid", "chi_high", "pon", "kan_select", "hora"]:
        action = recommandations[0]["action"]
        
        if action == "reach":
            print("Bấm nút Riichi")
            if "riichi" in BUTTON_POSITIONS:
                safe_click(BUTTON_POSITIONS["riichi"], "nút Riichi")
            else:
                print("Lỗi: Không tìm thấy vị trí nút Riichi")
        
        elif action == "chi_low":
            print("Bấm nút Chi thấp")
            if "chi_low" in BUTTON_POSITIONS:
                safe_click(BUTTON_POSITIONS["chi_low"], "nút Chi thấp")
            else:
                print("Lỗi: Không tìm thấy vị trí nút Chi thấp")
        
        elif action == "chi_mid":
            print("Bấm nút Chi giữa")
            if "chi_mid" in BUTTON_POSITIONS:
                safe_click(BUTTON_POSITIONS["chi_mid"], "nút Chi giữa")
            else:
                print("Lỗi: Không tìm thấy vị trí nút Chi giữa")
        
        elif action == "chi_high":
            print("Bấm nút Chi cao")
            if "chi_high" in BUTTON_POSITIONS:
                safe_click(BUTTON_POSITIONS["chi_high"], "nút Chi cao")
            else:
                print("Lỗi: Không tìm thấy vị trí nút Chi cao")
        
        elif action == "pon":
            print("Bấm nút Pon")
            if "pon" in BUTTON_POSITIONS:
                safe_click(BUTTON_POSITIONS["pon"], "nút Pon")
            else:
                print("Lỗi: Không tìm thấy vị trí nút Pon")
        
        elif action == "kan_select":
            print("Bấm nút Kan")
            if "kan" in BUTTON_POSITIONS:
                safe_click(BUTTON_POSITIONS["kan"], "nút Kan")
            else:
                print("Lỗi: Không tìm thấy vị trí nút Kan")
        
        elif action == "hora":
            print("Bấm nút Ron")
            if "ron" in BUTTON_POSITIONS:
                safe_click(BUTTON_POSITIONS["ron"], "nút Ron")
            else:
                print("Lỗi: Không tìm thấy vị trí nút Ron")

# Hàm đọc file JSON
def read_json_file():
    try:
        if not os.path.exists(JSON_FILE_PATH):
            print(f"File không tồn tại: {JSON_FILE_PATH}")
            return None
            
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                print("File JSON rỗng")
                return None
            data = json.loads(content)
            print(f"Đọc thành công file JSON: {data}")
            return data
    except json.JSONDecodeError as e:
        print(f"Lỗi định dạng JSON: {e}")
        return None
    except Exception as e:
        print(f"Lỗi khi đọc file JSON: {e}")
        return None

# Kiểm tra thay đổi file theo thời gian sửa đổi
def check_file_modified():
    global last_modified_time
    try:
        if os.path.exists(JSON_FILE_PATH):
            current_mtime = os.path.getmtime(JSON_FILE_PATH)
            if current_mtime > last_modified_time:
                last_modified_time = current_mtime
                print(f"Phát hiện file thay đổi theo thời gian sửa đổi: {current_mtime}")
                return True
        return False
    except Exception as e:
        print(f"Lỗi khi kiểm tra thời gian sửa đổi: {e}")
        return False

# Xử lý khi file thay đổi
class JsonFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global last_state
        
        print(f"Sự kiện modified: {event.src_path}")
        if os.path.abspath(event.src_path) == JSON_FILE_PATH:
            print("Phát hiện thay đổi trong file JSON")
            # Đợi một chút để đảm bảo file đã được ghi hoàn tất
            time.sleep(0.1)
            
            # Đọc dữ liệu mới
            current_state = read_json_file()
            
            # Nếu không có dữ liệu hoặc dữ liệu không đổi, bỏ qua
            if not current_state:
                print("Không có dữ liệu từ file JSON")
                return
                
            if current_state == last_state:
                print("Dữ liệu không thay đổi, bỏ qua")
                return
            
            # Cập nhật trạng thái cuối
            last_state = current_state
            
            print(f"Phát hiện thay đổi trong file JSON: {current_state}")
            
            # Thực hiện hành động dựa trên dữ liệu
            perform_action(
                current_state.get("action", {}).get("type", ""),
                current_state.get("tehai", []),
                current_state.get("tsumo", ""),
                current_state.get("recommandations", [])
            )

# Hàm kiểm tra file theo chu kỳ
def check_file_periodically():
    global last_state
    
    # Kiểm tra nếu file đã thay đổi
    if check_file_modified():
        print("Đang kiểm tra file theo chu kỳ...")
        current_state = read_json_file()
        
        if not current_state:
            return
            
        if current_state == last_state:
            return
            
        # Cập nhật trạng thái cuối
        last_state = current_state
        
        print(f"Phát hiện thay đổi trong file JSON: {current_state}")
        
        # Thực hiện hành động dựa trên dữ liệu
        perform_action(
            current_state.get("action", {}).get("type", ""),
            current_state.get("tehai", []),
            current_state.get("tsumo", ""),
            current_state.get("recommandations", [])
        )

# Kiểm tra thủ công file JSON
def check_manually():
    global last_state
    print("\n=== Kiểm tra thủ công file JSON ===")
    
    # Đọc dữ liệu mới
    current_state = read_json_file()
    
    # Nếu không có dữ liệu
    if not current_state:
        print("Không có dữ liệu từ file JSON")
        return
    
    # Nếu dữ liệu không đổi
    if current_state == last_state:
        print("Dữ liệu không thay đổi so với lần kiểm tra trước")
        return
    
    # Cập nhật trạng thái cuối
    last_state = current_state
    
    print(f"Nội dung file JSON: {current_state}")
    
    # Thực hiện hành động dựa trên dữ liệu
    perform_action(
        current_state.get("action", {}).get("type", ""),
        current_state.get("tehai", []),
        current_state.get("tsumo", ""),
        current_state.get("recommandations", [])
    )

# Hàm chính
def main():
    print("Bắt đầu quan sát file JSON...")
    print("Nhấn 'q' để thoát, 'c' để kiểm tra thủ công file")
    
    # Khởi tạo trạng thái cuối
    global last_state, last_modified_time
    if os.path.exists(JSON_FILE_PATH):
        last_modified_time = os.path.getmtime(JSON_FILE_PATH)
    last_state = read_json_file()
    
    # Thiết lập watchdog để theo dõi thay đổi file
    event_handler = JsonFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(JSON_FILE_PATH) or '.', recursive=False)
    observer.start()
    
    print(f"Đang theo dõi thư mục: {os.path.dirname(JSON_FILE_PATH) or '.'}")
    
    # Chạy cho đến khi nhấn phím thoát
    try:
        while True:
            if keyboard.is_pressed('q'):
                print("Đang thoát...")
                break
                
            # Phím kiểm tra thủ công
            if keyboard.is_pressed('c'):
                check_manually()
                time.sleep(0.5)  # Tránh kiểm tra nhiều lần khi nhấn phím
                
            # Kiểm tra thay đổi file theo thời gian
            check_file_periodically()
                
            time.sleep(0.1)
    except Exception as e:
        print(f"Lỗi trong vòng lặp chính: {e}")
    finally:
        observer.stop()
        observer.join()

# Cho phép điều chỉnh tọa độ
def calibrate_positions():
    print("Chế độ hiệu chỉnh tọa độ")
    print("Di chuyển chuột đến vị trí và nhấn phím để lưu:")
    print("0-9: Quân bài 1-10 (vị trí index 0-9)")
    print("-, =, \\: Quân bài 11-13 (vị trí index 10-12)")
    print("t: Quân tsumo, p: Pass, o: Pon, l/m/h: Chi low/mid/high")
    print("k: Kan, r: Ron, i: Riichi")
    print("ESC: Thoát chế độ hiệu chỉnh")
    
    global TEHAI_POSITIONS, BUTTON_POSITIONS
    
    try:
        while True:
            if keyboard.is_pressed('esc'):
                break
                
            # Lưu vị trí quân bài (0-9 tương ứng với quân bài 1-10)
            for i in range(10):
                if keyboard.is_pressed(str(i)):
                    TEHAI_POSITIONS[i] = pyautogui.position()
                    print(f"Đã lưu vị trí quân bài {i+1} (index {i}): {TEHAI_POSITIONS[i]}")
                    time.sleep(0.5)
            
            # Các phím đặc biệt cho quân bài 11-13
            if keyboard.is_pressed('-'):
                TEHAI_POSITIONS[10] = pyautogui.position()
                print(f"Đã lưu vị trí quân bài 11 (index 10): {TEHAI_POSITIONS[10]}")
                time.sleep(0.5)
            elif keyboard.is_pressed('='):
                TEHAI_POSITIONS[11] = pyautogui.position()
                print(f"Đã lưu vị trí quân bài 12 (index 11): {TEHAI_POSITIONS[11]}")
                time.sleep(0.5)
            elif keyboard.is_pressed('\\'):
                TEHAI_POSITIONS[12] = pyautogui.position()
                print(f"Đã lưu vị trí quân bài 13 (index 12): {TEHAI_POSITIONS[12]}")
                time.sleep(0.5)
                
            # Lưu vị trí quân tsumo
            if keyboard.is_pressed('t'):
                TEHAI_POSITIONS["tsumo"] = pyautogui.position()
                print(f"Đã lưu vị trí quân tsumo: {TEHAI_POSITIONS['tsumo']}")
                time.sleep(0.5)
                
            # Lưu vị trí các nút
            if keyboard.is_pressed('p'):
                BUTTON_POSITIONS["pass"] = pyautogui.position()
                print(f"Đã lưu vị trí nút Pass: {BUTTON_POSITIONS['pass']}")
                time.sleep(0.5)
            elif keyboard.is_pressed('o'):
                BUTTON_POSITIONS["pon"] = pyautogui.position()
                print(f"Đã lưu vị trí nút Pon: {BUTTON_POSITIONS['pon']}")
                time.sleep(0.5)
            elif keyboard.is_pressed('l'):
                BUTTON_POSITIONS["chi_low"] = pyautogui.position()
                print(f"Đã lưu vị trí nút Chi thấp: {BUTTON_POSITIONS['chi_low']}")
                time.sleep(0.5)
            elif keyboard.is_pressed('m'):
                BUTTON_POSITIONS["chi_mid"] = pyautogui.position()
                print(f"Đã lưu vị trí nút Chi giữa: {BUTTON_POSITIONS['chi_mid']}")
                time.sleep(0.5)
            elif keyboard.is_pressed('h'):
                BUTTON_POSITIONS["chi_high"] = pyautogui.position()
                print(f"Đã lưu vị trí nút Chi cao: {BUTTON_POSITIONS['chi_high']}")
                time.sleep(0.5)
            elif keyboard.is_pressed('k'):
                BUTTON_POSITIONS["kan"] = pyautogui.position()
                print(f"Đã lưu vị trí nút Kan: {BUTTON_POSITIONS['kan']}")
                time.sleep(0.5)
            elif keyboard.is_pressed('r'):
                BUTTON_POSITIONS["ron"] = pyautogui.position()
                print(f"Đã lưu vị trí nút Ron: {BUTTON_POSITIONS['ron']}")
                time.sleep(0.5)
            elif keyboard.is_pressed('i'):
                BUTTON_POSITIONS["riichi"] = pyautogui.position()
                print(f"Đã lưu vị trí nút Riichi: {BUTTON_POSITIONS['riichi']}")
                time.sleep(0.5)
                
            time.sleep(0.1)
    
    except Exception as e:
        print(f"Lỗi trong chế độ hiệu chỉnh: {e}")
    
    # Lưu các tọa độ đã hiệu chỉnh
    try:
        with open('positions_config.json', 'w', encoding='utf-8') as f:
            json.dump({
                "tehai": TEHAI_POSITIONS,
                "buttons": BUTTON_POSITIONS
            }, f, ensure_ascii=False, indent=2)
        print("Đã lưu cấu hình tọa độ vào positions_config.json")
    except Exception as e:
        print(f"Lỗi khi lưu cấu hình: {e}")

# Hàm tải cấu hình tọa độ
def load_positions_config():
    global TEHAI_POSITIONS, BUTTON_POSITIONS
    try:
        if os.path.exists('positions_config.json'):
            with open('positions_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # Đảm bảo chuyển đổi đúng các khóa trong TEHAI_POSITIONS từ string sang int nếu cần
                tehai_config = config.get("tehai", {})
                new_tehai_positions = {}
                
                # Xử lý cẩn thận để đảm bảo các khóa số được lưu đúng dạng 
                for key, value in tehai_config.items():
                    if key == "tsumo":
                        new_tehai_positions["tsumo"] = value
                    else:
                        try:
                            # Chuyển khóa sang int nếu có thể
                            index = int(key)
                            new_tehai_positions[index] = value
                        except ValueError:
                            # Nếu không thể chuyển đổi, giữ nguyên khóa
                            new_tehai_positions[key] = value
                
                TEHAI_POSITIONS = new_tehai_positions
                BUTTON_POSITIONS = config.get("buttons", BUTTON_POSITIONS)
                
                print("Đã tải cấu hình tọa độ từ positions_config.json")
                print(f"Tọa độ quân bài đã tải: {len(TEHAI_POSITIONS)} vị trí")
                print(f"Các index quân bài: {sorted([k for k in TEHAI_POSITIONS.keys() if isinstance(k, int)])}")
                print(f"Tọa độ nút bấm đã tải: {len(BUTTON_POSITIONS)} vị trí")
                print(f"Các nút bấm: {list(BUTTON_POSITIONS.keys())}")
        else:
            print("Không tìm thấy file cấu hình tọa độ, sử dụng tọa độ mặc định")
    except Exception as e:
        print(f"Lỗi khi tải cấu hình tọa độ: {e}")
        print(f"Chi tiết lỗi: {traceback.format_exc()}")

# Hàm in thông tin debug về tất cả các tọa độ đã tải
def debug_positions():
    print("\n=== THÔNG TIN TỌA ĐỘ ĐÃ TẢI ===")
    print("TEHAI_POSITIONS:")
    for key, value in TEHAI_POSITIONS.items():
        print(f"  {key}: {value}")
    print("\nBUTTON_POSITIONS:")
    for key, value in BUTTON_POSITIONS.items():
        print(f"  {key}: {value}")
    print("==============================\n")

if __name__ == "__main__":
    # Tải cấu hình tọa độ nếu có
    load_positions_config()
    
    # In thông tin debug về tọa độ đã tải
    debug_positions()
    
    # Xử lý các tham số dòng lệnh
    if len(sys.argv) > 1:
        if sys.argv[1] == '--calibrate':
            calibrate_positions()
        else:
            print(f"Tham số không hợp lệ: {sys.argv[1]}")
            print("Sử dụng: python auto_play.py [--calibrate]")
    else:
        # Chạy chương trình chính
        main() 