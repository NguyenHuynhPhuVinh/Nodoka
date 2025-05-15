# main.py
import logging
import pyautogui # Cho FailSafeException
from mahjong_bot import MahjongBot # Giả sử class MahjongBot nằm trong mahjong_bot.py

if __name__ == "__main__":
    # Thiết lập logging ở đây để nó được cấu hình trước khi bất kỳ module nào khác sử dụng
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
                        handlers=[
                            logging.StreamHandler(), # In ra console
                            # logging.FileHandler("mahjong_bot.log") # Ghi vào file (tùy chọn)
                        ])
    try:
        bot = MahjongBot()
        bot.start()
    except pyautogui.FailSafeException:
        logging.critical("FailSafe kích hoạt! Di chuyển chuột ra góc màn hình để dừng.")
    except KeyboardInterrupt:
        logging.info("Đã nhận tín hiệu KeyboardInterrupt (Ctrl+C). Dừng bot.")
        # Bot nên tự xử lý dừng thông qua self.running trong _main_loop khi nhấn 'q'
        # Tuy nhiên, Ctrl+C là một cách dừng khác cần được xử lý êm đẹp.
        # Nếu bot đã có cơ chế dừng qua self.running, thì không cần làm gì thêm ở đây
        # trừ khi muốn dừng các luồng một cách rõ ràng hơn.
    except Exception as e:
        logging.critical(f"Lỗi không mong muốn ở cấp cao nhất: {e}", exc_info=True)
    finally:
        logging.info("Chương trình kết thúc.")