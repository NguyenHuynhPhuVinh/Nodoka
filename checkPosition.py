import pyautogui
import time

def track_mouse_position(interval=0.1):
    print("Tracking mouse position. Move your mouse around.")
    print(f"Press Ctrl+C to stop.")
    
    try:
        while True:
            # Lấy tọa độ hiện tại của chuột
            x, y = pyautogui.position()
            print(f"Mouse position: ({x}, {y})", end='\r')  # Cập nhật tọa độ trên cùng một dòng
            time.sleep(interval)  # Chờ một khoảng thời gian trước khi kiểm tra lại
    except KeyboardInterrupt:
        print("\nStopped tracking.")

# Gọi hàm để theo dõi vị trí của chuột
track_mouse_position()
