import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import queue
from loguru import logger as main_logger

# Tạo logger riêng cho data exporter
log_path = Path().cwd() / "logs" / f"mjai_exporter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logger = main_logger.bind(module="mjai_exporter")
main_logger.add(log_path, level="DEBUG", filter=lambda record: record["extra"].get("module") == "mjai_exporter")

class MJAIDataExporter:
    """
    Lớp này cho phép truy cập và xuất dữ liệu MJAI Out từ ứng dụng Akagi.
    Nó hoạt động như một singleton để đảm bảo chỉ có một instance duy nhất.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MJAIDataExporter, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Khởi tạo các thuộc tính của exporter"""
        self.mjai_output_data = []  # Danh sách lưu trữ các dữ liệu MJAI Out
        self.mjai_output_queue = queue.Queue()  # Queue cho dữ liệu MJAI Out mới
        self.max_stored_entries = 100  # Số lượng tối đa các mục được lưu trữ
        self.subscribers = []  # Danh sách các callback đăng ký để nhận thông báo
        logger.info("MJAIDataExporter đã được khởi tạo")
    
    def store_mjai_output(self, mjai_response: Dict[str, Any]) -> None:
        """
        Lưu trữ dữ liệu MJAI Out và thông báo cho các subscribers
        
        Args:
            mjai_response: Dữ liệu MJAI Out được tạo bởi mjai_controller.react()
        """
        if not mjai_response:
            return
            
        # Thêm timestamp vào dữ liệu
        data_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            "data": mjai_response
        }
        
        # Lưu vào danh sách và queue
        self.mjai_output_data.append(data_with_timestamp)
        self.mjai_output_queue.put(data_with_timestamp)
        
        # Giới hạn kích thước của danh sách
        if len(self.mjai_output_data) > self.max_stored_entries:
            self.mjai_output_data.pop(0)
        
        # Thông báo cho các subscribers
        for callback in self.subscribers:
            try:
                callback(data_with_timestamp)
            except Exception as e:
                logger.error(f"Lỗi khi gọi callback: {e}")
        
        logger.debug(f"Đã lưu trữ dữ liệu MJAI: {mjai_response}")
    
    def get_latest_output(self) -> Optional[Dict[str, Any]]:
        """Lấy dữ liệu MJAI Out mới nhất"""
        if not self.mjai_output_data:
            return None
        return self.mjai_output_data[-1]
    
    def get_all_outputs(self) -> List[Dict[str, Any]]:
        """Lấy tất cả dữ liệu MJAI Out đã lưu trữ"""
        return self.mjai_output_data.copy()
    
    def get_next_output(self, timeout=None) -> Optional[Dict[str, Any]]:
        """
        Lấy dữ liệu MJAI Out tiếp theo từ queue
        
        Args:
            timeout: Thời gian chờ tối đa (giây) nếu không có dữ liệu
            
        Returns:
            Dữ liệu MJAI Out tiếp theo hoặc None nếu timeout
        """
        try:
            return self.mjai_output_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def subscribe(self, callback) -> None:
        """
        Đăng ký một callback để nhận thông báo khi có dữ liệu MJAI Out mới
        
        Args:
            callback: Hàm callback sẽ được gọi với dữ liệu MJAI mới
        """
        if callback not in self.subscribers:
            self.subscribers.append(callback)
            logger.debug(f"Đã đăng ký callback mới, tổng số: {len(self.subscribers)}")
    
    def unsubscribe(self, callback) -> None:
        """
        Hủy đăng ký một callback
        
        Args:
            callback: Hàm callback đã đăng ký trước đó
        """
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.debug(f"Đã hủy đăng ký callback, còn lại: {len(self.subscribers)}")
    
    def save_to_file(self, filepath: str = None) -> str:
        """
        Lưu tất cả dữ liệu MJAI Out vào file
        
        Args:
            filepath: Đường dẫn đến file để lưu. Nếu None, sẽ tạo một file trong thư mục logs
            
        Returns:
            Đường dẫn đến file đã lưu
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = str(Path().cwd() / "logs" / f"mjai_data_export_{timestamp}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.mjai_output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Đã lưu dữ liệu MJAI vào file: {filepath}")
        return filepath

# Instance singleton để sử dụng trong toàn bộ ứng dụng
mjai_data_exporter = MJAIDataExporter() 