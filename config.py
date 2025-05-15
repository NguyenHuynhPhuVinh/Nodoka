# config.py
import os
import logging

# Thiết lập logging cơ bản (có thể được ghi đè ở main.py nếu muốn cấu hình phức tạp hơn)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Tốt hơn là để main.py xử lý basicConfig

# Đường dẫn và tên tệp
IMAGES_FOLDER = 'images' # Giả sử thư mục images nằm cùng cấp với các file .py sau khi tách
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
PLAYER_HAND_REGION = (289, 840, 1422, 170)
ACTION_BUTTONS_REGION = (473, 764, 1588 - 473, 865 - 764)
TURN_INDICATOR_REGION = (1663, 772, 1737 - 1663, 867 - 772)
END_GAME_REGION = (12, 50, 428 - 12, 146 - 50)
# START_GAME_REGION = (1127, 257, 1323 - 1127, 451 - 428)

# Kích thước quân bài (width, height)
TILE_IMAGE_SIZE = (75, 105)

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
END_GAME_CLICKS = [
    (1753, 948),
]
GAME_MODE_CLICKS = {
    0: [(1324, 496)],
    1: [(1161, 626), (1030, 893)]
}
SELECTED_GAME_MODE = 0

# Độ trễ
CLICK_DELAY = 0.25
ACTION_CLICK_DELAY = 0.1
LOOP_DELAY = 0.5
PASS_CHECK_DELAY = 1.0
END_GAME_CHECK_DELAY = 3.0