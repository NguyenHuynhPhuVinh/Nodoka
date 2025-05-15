# mahjong_bot.py
import os
import time
import threading
import keyboard
import pyautogui
import logging

# Import từ các module tự tạo
import config
from image_utils import find_image_locations, group_nearby_positions, convert_region_to_screen_coords
from tile_utils import get_tile_name_from_path, sort_tile_images
from game_logic import is_my_turn, input_text_formatter, process_discard_decision, logic_game

class MahjongBot:
    def __init__(self):
        self.riichi_declared = False
        self.running = True
        self.threads = []
        self.last_player_hand_text = ""

    def start(self):
        logging.info("Khởi động Mahjong Bot...")
        self._start_background_tasks()
        self._main_loop()
        self._stop_background_tasks()
        logging.info("Mahjong Bot đã dừng.")

    def _start_background_tasks(self):
        action_args = (
            config.PASS_IMAGE, config.ACTION_BUTTONS_REGION,
            config.RIICHI_IMAGE, config.TSUMO_IMAGE, config.RON_IMAGE, config.KITA_IMAGE,
            config.PON_IMAGE, config.KAN_IMAGE, config.CHII_IMAGE
        )
        action_thread = threading.Thread(target=self._continuously_check_action_buttons, args=action_args, daemon=True)
        self.threads.append(action_thread)
        action_thread.start()

        end_game_thread = threading.Thread(target=self._continuously_check_end_game, args=(config.END_GAME_IMAGE, config.END_GAME_REGION), daemon=True)
        self.threads.append(end_game_thread)
        end_game_thread.start()

    def _stop_background_tasks(self):
        self.running = False
        logging.info("Đang yêu cầu các luồng nền dừng...")

    def _continuously_check_action_buttons(self, pass_img, region, riichi_img, tsumo_img, ron_img, kita_img, pon_img, kan_img, chii_img):
        logging.info("Luồng theo dõi nút hành động đã bắt đầu.")
        action_priority = [
            (config.RON_IMAGE, "Ron"), (config.TSUMO_IMAGE, "Tsumo"), (config.KITA_IMAGE, "Kita"),
            (config.RIICHI_IMAGE, "Riichi"),
            (config.KAN_IMAGE, "Kan"), (config.PON_IMAGE, "Pon"), (config.CHII_IMAGE, "Chii"),
        ]
        while self.running:
            try:
                clicked_an_action = False
                for img_path, action_name in action_priority:
                    # Sử dụng kích thước của nút thực tế thay vì TILE_IMAGE_SIZE nếu biết
                    # Giả sử các nút có kích thước tương tự TILE_IMAGE_SIZE hoặc không quá quan trọng tâm click
                    button_size_placeholder = config.TILE_IMAGE_SIZE # Cần điều chỉnh nếu kích thước nút khác nhiều
                    locations = find_image_locations(img_path, region)
                    if locations:
                        if action_name in ["Ron", "Tsumo", "Kita", "Riichi"]:
                            screen_x, screen_y = convert_region_to_screen_coords(locations[0], region, button_size_placeholder)
                            pyautogui.click(screen_x, screen_y)
                            logging.info(f"Đã click nút: {action_name}")
                            if action_name == "Riichi":
                                self.riichi_declared = True
                                logging.info("Đã khai báo Riichi.")
                            clicked_an_action = True
                            break
                        elif action_name in ["Kan", "Pon", "Chii"]:
                            pass_locations = find_image_locations(pass_img, region, 0.85)
                            if pass_locations:
                                # Logic cũ: ưu tiên Pass. Hiện tại: ưu tiên KPC nếu có
                                screen_x, screen_y = convert_region_to_screen_coords(locations[0], region, button_size_placeholder)
                                pyautogui.click(screen_x, screen_y)
                                logging.info(f"Đã click nút: {action_name} (có cả Pass)")
                                clicked_an_action = True
                                break
                            else:
                                screen_x, screen_y = convert_region_to_screen_coords(locations[0], region, button_size_placeholder)
                                pyautogui.click(screen_x, screen_y)
                                logging.info(f"Đã click nút: {action_name} (không có Pass)")
                                clicked_an_action = True
                                break
                if clicked_an_action:
                    time.sleep(config.ACTION_CLICK_DELAY * 5)
                    pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
                    continue

                pass_locations = find_image_locations(pass_img, region, 0.85)
                if pass_locations and not clicked_an_action:
                    can_kpc = any(find_image_locations(img, region) for img, name in action_priority if name in ["Kan", "Pon", "Chii"])
                    if not can_kpc:
                        screen_x, screen_y = convert_region_to_screen_coords(pass_locations[0], region, config.TILE_IMAGE_SIZE) # Giả sử kích thước nút Pass
                        pyautogui.click(screen_x, screen_y)
                        logging.info("Đã click nút: Pass (khi không có KPC)")
                        time.sleep(config.ACTION_CLICK_DELAY * 2)
                        pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
            except Exception as e:
                logging.error(f"Lỗi trong luồng theo dõi nút hành động: {e}")
            time.sleep(config.PASS_CHECK_DELAY)
        logging.info("Luồng theo dõi nút hành động đã kết thúc.")

    def _continuously_check_end_game(self, end_img_path, end_region):
        logging.info("Luồng theo dõi kết thúc game đã bắt đầu.")
        while self.running:
            try:
                if find_image_locations(end_img_path, end_region):
                    logging.info("Phát hiện màn hình kết thúc game.")
                    time.sleep(1)
                    for _ in range(10):
                        if config.END_GAME_CLICKS:
                            pyautogui.click(config.END_GAME_CLICKS[0])
                        time.sleep(0.3)
                    if config.SELECTED_GAME_MODE in config.GAME_MODE_CLICKS:
                        for click_coord in config.GAME_MODE_CLICKS[config.SELECTED_GAME_MODE]:
                            pyautogui.click(click_coord)
                            time.sleep(1)
                    logging.info("Đã thực hiện các click sau khi kết thúc game. Chờ game tải...")
                    time.sleep(10)
            except Exception as e:
                logging.error(f"Lỗi trong luồng theo dõi kết thúc game: {e}")
            time.sleep(config.END_GAME_CHECK_DELAY)
        logging.info("Luồng theo dõi kết thúc game đã kết thúc.")

    def _scan_player_hand(self):
        detected_tiles_info = []
        try:
            all_tile_image_files = [
                f for f in os.listdir(config.IMAGES_FOLDER)
                if f.lower().endswith(('.png', '.jpg', '.jpeg')) and
                f not in [
                    os.path.basename(config.PASS_IMAGE), os.path.basename(config.RIICHI_IMAGE),
                    os.path.basename(config.TSUMO_IMAGE), os.path.basename(config.RON_IMAGE),
                    os.path.basename(config.KITA_IMAGE), os.path.basename(config.PON_IMAGE),
                    os.path.basename(config.KAN_IMAGE), os.path.basename(config.CHII_IMAGE),
                    os.path.basename(config.END_GAME_IMAGE)
                    # os.path.basename(config.START_GAME_IMAGE) # Nếu có
                ]
            ]
            sorted_tile_files = sort_tile_images(all_tile_image_files)
            results_from_threads = []
            threads_for_scan = []

            def process_single_tile_image(image_path_full, region, results_list):
                positions = find_image_locations(image_path_full, region)
                if positions:
                    grouped = group_nearby_positions(positions)
                    if grouped:
                        results_list.append((image_path_full, grouped))

            for tile_file in sorted_tile_files:
                full_path = os.path.join(config.IMAGES_FOLDER, tile_file)
                thread = threading.Thread(target=process_single_tile_image, args=(full_path, config.PLAYER_HAND_REGION, results_from_threads))
                threads_for_scan.append(thread)
                thread.start()

            for thread in threads_for_scan:
                thread.join()

            for image_path, grouped_positions in results_from_threads:
                tile_name = get_tile_name_from_path(image_path)
                for pos in grouped_positions:
                    detected_tiles_info.append((tile_name, pos))
            detected_tiles_info.sort(key=lambda item: item[1][0])
        except Exception as e:
            logging.error(f"Lỗi khi quét bài trên tay: {e}")
        return detected_tiles_info

    def _handle_player_turn(self, detected_tiles_info):
        if not detected_tiles_info:
            logging.info("Không phát hiện quân bài nào trên tay.")
            return

        formatted_hand_text = input_text_formatter(detected_tiles_info)
        logging.info(f"Bài trên tay đã định dạng:\n{formatted_hand_text}")

        if formatted_hand_text == self.last_player_hand_text and not self.riichi_declared:
            logging.info("Bài trên tay không đổi, bỏ qua xử lý (trừ khi đã Riichi).")
            return
        self.last_player_hand_text = formatted_hand_text

        if self.riichi_declared:
            if detected_tiles_info:
                tile_to_discard_name, pos_in_region = detected_tiles_info[-1]
                logging.info(f"Đã Riichi. Tự động bỏ quân cuối cùng: {tile_to_discard_name} tại {pos_in_region}")
                screen_x, screen_y = convert_region_to_screen_coords(pos_in_region, config.PLAYER_HAND_REGION, config.TILE_IMAGE_SIZE)
                pyautogui.click(screen_x, screen_y)
                time.sleep(config.CLICK_DELAY)
                pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
            self.riichi_declared = False
            return

        discard_pos_str = logic_game(formatted_hand_text)
        if discard_pos_str:
            logging.info(f"Logic game quyết định bỏ quân tại vị trí (trong vùng): {discard_pos_str}")
            # process_discard_decision đã có giá trị default cho TILE_IMAGE_SIZE và PLAYER_HAND_REGION từ config
            # nên không cần truyền lại nếu dùng default.
            screen_x, screen_y = process_discard_decision(discard_pos_str)
            logging.info(f"Click để bỏ quân tại tọa độ màn hình: ({screen_x}, {screen_y})")
            pyautogui.click(screen_x, screen_y)
            time.sleep(config.ACTION_CLICK_DELAY)
            pyautogui.moveTo(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
            self.last_player_hand_text = ""
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
                # Các tham số của is_my_turn đã có giá trị default từ config, không cần truyền lại
                if is_my_turn():
                    logging.info("Đến lượt của tôi. Bắt đầu quét bài...")
                    time.sleep(0.2)
                    current_hand_tiles = self._scan_player_hand()
                    if current_hand_tiles:
                        self._handle_player_turn(current_hand_tiles)
                    else:
                        logging.info("Không tìm thấy quân bài nào để xử lý.")
                    time.sleep(config.LOOP_DELAY * 2)
                else:
                    pass # logging.info("Chưa đến lượt hoặc không có tín hiệu lượt rõ ràng.")
            except Exception as e:
                logging.error(f"Lỗi trong vòng lặp chính: {e}", exc_info=True)
            time.sleep(config.LOOP_DELAY)