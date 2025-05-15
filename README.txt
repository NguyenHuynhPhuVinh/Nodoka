# Công cụ tự động cho Mahjong

Dự án này là một công cụ tự động hóa nhận diện và tương tác với game Mahjong sử dụng xử lý hình ảnh và tự động điều khiển chuột.

## Tính năng

- Tự động nhận diện quân bài Mahjong trên màn hình
- Tự động tìm kiếm và xử lý các hành động trong game (riichi, tsumo, ron, kita, pon, kan, chii)
- Tự động tìm và đánh quân bài dựa trên chiến thuật game
- Xử lý kết thúc trận đấu

## Yêu cầu hệ thống

- Python 3.8 trở lên
- Thư viện: OpenCV, NumPy, PyAutoGUI, Keyboard

## Cài đặt

1. Clone hoặc tải về repository này
2. Cài đặt các thư viện cần thiết:

```
pip install -r requirements.txt
```

3. Đảm bảo bạn có thư mục `images` chứa các hình ảnh mẫu cho nhận diện:
   - Các quân bài (man-1.png, man-2.png, pin-1.png, sou-1.png, v.v.)
   - Các nút hành động (riichi.png, tsumo.png, ron.png, v.v.)
   - Nút pass.png và end.png

## Sử dụng

1. Chạy chương trình:

```
python main.py
```

2. Chương trình sẽ tự động:
   - Quét màn hình để tìm quân bài
   - Xử lý logic game
   - Thực hiện các hành động tự động

3. Để thoát, nhấn phím 'q'

## Điều chỉnh

- Khu vực quét màn hình có thể được điều chỉnh trong biến `region`
- Các thông số như `threshold` cho nhận dạng hình ảnh có thể được điều chỉnh theo nhu cầu 