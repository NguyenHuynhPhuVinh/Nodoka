import pyautogui
import time
import keyboard  # Thư viện này cho phép bắt phím tắt

def get_pixel_color(x, y):
    # Lấy màu sắc tại vị trí (x, y)
    return pyautogui.pixel(x, y)

def monitor_mouse_color():
    print("Monitoring started. Press 'Esc' to stop.")
    try:
        while True:
            # Kiểm tra nếu phím 'Esc' được nhấn, thì dừng chương trình
            if keyboard.is_pressed('esc'):
                print("Monitoring stopped.")
                break
            
            # Lấy vị trí của con trỏ chuột
            x, y = pyautogui.position()
            
            # Lấy màu sắc tại vị trí con trỏ chuột
            current_color = get_pixel_color(x, y)
            
            # In ra màu sắc hiện tại của pixel dưới con trỏ chuột
            print(f"Mouse position: ({x}, {y}) - Color: {current_color}")
            
            # Chờ một chút trước khi kiểm tra lại để không làm chậm hệ thống
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped monitoring.")

if __name__ == "__main__":
    monitor_mouse_color()
