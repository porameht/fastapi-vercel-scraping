import re
from datetime import datetime, timezone
from utils.test_data import test_cases

class ThaiDateConverter:
    def __init__(self):
        self.thai_months = [
            'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
            'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
        ]
        self.thai_days = [
            'จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์'
        ]

    def extract_date_and_time(self, text):
        pattern = r'(?:วัน(จันทร์|อังคาร|พุธ|พฤหัสบดี|ศุกร์|เสาร์|อาทิตย์)?(?:ที่)?)??\s*(\d{1,2})\s*(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s*(?:พ\.ศ\.)?\s*(\d{4})(?:\s*เวลา\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(น\.|นาฬิกา)?)?'
        match = re.search(pattern, text)
        if match:
            return match.groups()
        return None

    def parse_thai_date_and_time(self, parts):
        if not parts or len(parts) < 4:
            return None

        day = int(parts[1])
        month = self.thai_months.index(parts[2]) + 1
        year = int(parts[3]) - 543  # แปลงปี พ.ศ. เป็น ค.ศ.

        hour = int(parts[4]) if parts[4] else 0
        minute = int(parts[5]) if parts[5] else 0
        second = int(parts[6]) if parts[6] else 0

        try:
            date_obj = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
            return date_obj
        except ValueError as e:
            print(f"เกิดข้อผิดพลาดในการแปลงวันที่และเวลา: {e}")
            return None

    def to_utc_format(self, text):
        parts = self.extract_date_and_time(text)
        if parts:
            date_obj = self.parse_thai_date_and_time(parts)
            if date_obj:
                return date_obj.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        return None

if __name__ == "__main__":
    converter = ThaiDateConverter()
    
    for i, case in enumerate(test_cases, 1):
        result = converter.to_utc_format(case)
        print(f"\nเคสที่ {i}:")
        print(f"ข้อความ: {case}")
        print(f"ผลลัพธ์: {result}")

    # ทดสอบเพิ่มเติมสำหรับกรณีที่มีเวลา
    additional_test_cases = [
        "วันที่ 1 มกราคม 2566 เวลา 09:30 น.",
        "2 กุมภาพันธ์ 2567 เวลา 14:45:30 นาฬิกา",
        "วันพุธที่ 3 มีนาคม พ.ศ. 2568 เวลา 18:00",
        "4 เมษายน 2569 20:15:45"
    ]

    for i, case in enumerate(additional_test_cases, len(test_cases) + 1):
        result = converter.to_utc_format(case)
        print(f"\nเคสที่ {i}:")
        print(f"ข้อความ: {case}")
        print(f"ผลลัพธ์: {result}")