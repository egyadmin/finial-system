"""
إطار عمل جمع البيانات لمساعد الويب
Data Collection Framework for Web Assistant

هذا الإطار يوفر البنية الأساسية لجمع البيانات من مختلف المصادر عبر الإنترنت
لأسعار مواد البناء والمعدات والعمالة ومقاولي الباطن في المملكة العربية السعودية.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging
import random
import os
import re
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_collection.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("data_collector")

class DataSource(ABC):
    """
    فئة أساسية مجردة لمصادر البيانات
    """
    
    def __init__(self, name: str, base_url: str, category: str):
        """
        تهيئة مصدر البيانات
        
        المعلمات:
            name (str): اسم مصدر البيانات
            base_url (str): عنوان URL الأساسي للمصدر
            category (str): فئة مصدر البيانات (مواد، معدات، عمالة، مناقصات، مقاولي باطن)
        """
        self.name = name
        self.base_url = base_url
        self.category = category
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # إنشاء مجلد للبيانات المؤقتة إذا لم يكن موجوداً
        os.makedirs('temp_data', exist_ok=True)
        
        logger.info(f"تم تهيئة مصدر البيانات: {self.name} ({self.category})")
    
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        جلب البيانات من المصدر
        
        يجب تنفيذ هذه الطريقة في الفئات الفرعية
        
        العائد:
            List[Dict[str, Any]]: قائمة بالبيانات المجمعة
        """
        pass
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """
        حفظ البيانات المجمعة بتنسيق JSON
        
        المعلمات:
            data (List[Dict[str, Any]]): البيانات المراد حفظها
            filename (str, optional): اسم الملف. إذا لم يتم تحديده، سيتم إنشاؤه تلقائياً
            
        العائد:
            str: مسار الملف المحفوظ
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"temp_data/{self.category}_{self.name}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"تم حفظ البيانات في: {filename}")
        return filename
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """
        حفظ البيانات المجمعة بتنسيق CSV
        
        المعلمات:
            data (List[Dict[str, Any]]): البيانات المراد حفظها
            filename (str, optional): اسم الملف. إذا لم يتم تحديده، سيتم إنشاؤه تلقائياً
            
        العائد:
            str: مسار الملف المحفوظ
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"temp_data/{self.category}_{self.name}_{timestamp}.csv"
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        logger.info(f"تم حفظ البيانات في: {filename}")
        return filename
    
    def _make_request(self, url: str, params: Dict = None, method: str = 'GET', 
                     data: Dict = None, retry_count: int = 3, 
                     retry_delay: int = 2) -> Optional[requests.Response]:
        """
        إجراء طلب HTTP مع إعادة المحاولة
        
        المعلمات:
            url (str): عنوان URL للطلب
            params (Dict, optional): معلمات الاستعلام
            method (str, optional): طريقة الطلب (GET، POST، إلخ)
            data (Dict, optional): بيانات الطلب (للطلبات POST)
            retry_count (int, optional): عدد مرات إعادة المحاولة
            retry_delay (int, optional): التأخير بين المحاولات بالثواني
            
        العائد:
            Optional[requests.Response]: كائن الاستجابة أو None في حالة الفشل
        """
        for attempt in range(retry_count):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, timeout=30)
                elif method.upper() == 'POST':
                    response = self.session.post(url, params=params, data=data, timeout=30)
                else:
                    logger.error(f"طريقة غير مدعومة: {method}")
                    return None
                
                response.raise_for_status()
                
                # إضافة تأخير عشوائي لتجنب الحظر
                time.sleep(random.uniform(0.5, 2.0))
                
                return response
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"فشل الطلب (المحاولة {attempt+1}/{retry_count}): {url} - {str(e)}")
                
                if attempt < retry_count - 1:
                    sleep_time = retry_delay * (2 ** attempt)  # تأخير تصاعدي
                    time.sleep(sleep_time)
                else:
                    logger.error(f"فشل جميع محاولات الطلب: {url}")
                    return None
    
    def _extract_text(self, element) -> str:
        """
        استخراج النص من عنصر HTML مع إزالة المسافات الزائدة
        
        المعلمات:
            element: عنصر BeautifulSoup
            
        العائد:
            str: النص المستخرج
        """
        if element is None:
            return ""
        return element.get_text(strip=True)
    
    def _normalize_price(self, price_text: str) -> Optional[float]:
        """
        تطبيع نص السعر إلى قيمة عددية
        
        المعلمات:
            price_text (str): نص السعر
            
        العائد:
            Optional[float]: السعر كقيمة عددية أو None إذا كان التحويل غير ممكن
        """
        if not price_text:
            return None
        
        # إزالة العملة والرموز الخاصة
        price_text = re.sub(r'[^\d.,]', '', price_text)
        
        # استبدال الفاصلة بنقطة إذا كانت تستخدم كفاصل عشري
        if ',' in price_text and '.' not in price_text:
            price_text = price_text.replace(',', '.')
        
        # إزالة الفواصل إذا كانت تستخدم كفواصل آلاف
        elif ',' in price_text and '.' in price_text:
            price_text = price_text.replace(',', '')
        
        try:
            return float(price_text)
        except ValueError:
            logger.warning(f"تعذر تحويل النص إلى سعر: {price_text}")
            return None


class MaterialsSource(DataSource):
    """
    فئة لجمع بيانات أسعار مواد البناء
    """
    
    def __init__(self, name: str, base_url: str, category: str = "materials"):
        super().__init__(name, base_url, category)
        """
        تهيئة مصدر بيانات مواد البناء
        
        المعلمات:
            name (str): اسم مصدر البيانات
            base_url (str): عنوان URL الأساسي للمصدر
        """
        super().__init__(name, base_url, "materials")
        
        # تعريف فئات مواد البناء المطلوبة
        self.material_categories = [
            "خرسانة", "أسمنت", "حديد", "رمل", "بلوك", "طوب", "بلاط", "سيراميك",
            "أسفلت", "بتومين", "عوازل", "أنابيب", "مواسير", "أسلاك", "كابلات",
            "دهانات", "أخشاب", "ألمنيوم", "زجاج", "أبواب", "نوافذ"
        ]
    
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        جلب بيانات أسعار مواد البناء
        
        يجب تنفيذ هذه الطريقة في الفئات الفرعية
        
        العائد:
            List[Dict[str, Any]]: قائمة بأسعار مواد البناء
        """
        pass


class EquipmentSource(DataSource):
    """
    فئة لجمع بيانات أسعار المعدات
    """
    
    def __init__(self, name: str, base_url: str):
        """
        تهيئة مصدر بيانات المعدات
        
        المعلمات:
            name (str): اسم مصدر البيانات
            base_url (str): عنوان URL الأساسي للمصدر
        """
        super().__init__(name, base_url, "equipment")
        
        # تعريف فئات المعدات المطلوبة
        self.equipment_categories = [
            "حفارات", "لوادر", "بلدوزرات", "رافعات", "شاحنات", "خلاطات خرسانة",
            "مضخات", "مولدات", "ضواغط هواء", "معدات دك", "معدات رصف", "معدات هدم",
            "معدات لحام", "معدات قطع", "معدات تشطيب", "سقالات", "معدات يدوية"
        ]
    
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        جلب بيانات أسعار المعدات
        
        يجب تنفيذ هذه الطريقة في الفئات الفرعية
        
        العائد:
            List[Dict[str, Any]]: قائمة بأسعار المعدات
        """
        pass


class LaborSource(DataSource):
    """
    فئة لجمع بيانات أسعار العمالة
    """
    
    def __init__(self, name: str, base_url: str):
        """
        تهيئة مصدر بيانات العمالة
        
        المعلمات:
            name (str): اسم مصدر البيانات
            base_url (str): عنوان URL الأساسي للمصدر
        """
        super().__init__(name, base_url, "labor")
        
        # تعريف فئات العمالة المطلوبة
        self.labor_categories = [
            "مهندسين", "فنيين", "عمال بناء", "نجارين", "حدادين", "سباكين",
            "كهربائيين", "دهانين", "لحامين", "سائقين", "مشغلي معدات", "مساحين",
            "مراقبي جودة", "مشرفين", "عمال عامة"
        ]
    
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        جلب بيانات أسعار العمالة
        
        يجب تنفيذ هذه الطريقة في الفئات الفرعية
        
        العائد:
            List[Dict[str, Any]]: قائمة بأسعار العمالة
        """
        pass


class TenderSource(DataSource):
    """
    فئة لجمع بيانات المناقصات
    """
    
    def __init__(self, name: str, base_url: str):
        """
        تهيئة مصدر بيانات المناقصات
        
        المعلمات:
            name (str): اسم مصدر البيانات
            base_url (str): عنوان URL الأساسي للمصدر
        """
        super().__init__(name, base_url, "tenders")
        
        # تعريف فئات المناقصات المطلوبة
        self.tender_categories = [
            "بنية تحتية", "طرق", "جسور", "أنفاق", "مباني", "مستشفيات", "مدارس",
            "مراكز تجارية", "مجمعات سكنية", "صرف صحي", "مياه", "كهرباء", "اتصالات",
            "تكييف", "تشطيبات", "صيانة", "ترميم"
        ]
    
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        جلب بيانات المناقصات
        
        يجب تنفيذ هذه الطريقة في الفئات الفرعية
        
        العائد:
            List[Dict[str, Any]]: قائمة بالمناقصات
        """
        pass


class SubcontractorSource(DataSource):
    """
    فئة لجمع بيانات مقاولي الباطن
    """
    
    def __init__(self, name: str, base_url: str):
        """
        تهيئة مصدر بيانات مقاولي الباطن
        
        المعلمات:
            name (str): اسم مصدر البيانات
            base_url (str): عنوان URL الأساسي للمصدر
        """
        super().__init__(name, base_url, "subcontractors")
        
        # تعريف فئات مقاولي الباطن المطلوبة
        self.subcontractor_categories = [
            "أعمال ترابية", "أعمال خرسانية", "أعمال معدنية", "أعمال كهربائية",
            "أعمال ميكانيكية", "أعمال سباكة", "أعمال تكييف", "أعمال عزل",
            "أعمال تشطيبات", "أعمال نجارة", "أعمال ألمنيوم", "أعمال زجاج",
            "أعمال دهانات", "أعمال أسفلت", "أعمال رصف", "أعمال شبكات",
            "أعمال اتصالات", "أعمال أمن وسلامة", "أعمال مراقبة", "أعمال صيانة"
        ]
    
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        جلب بيانات مقاولي الباطن
        
        يجب تنفيذ هذه الطريقة في الفئات الفرعية
        
        العائد:
            List[Dict[str, Any]]: قائمة بمقاولي الباطن
        """
        pass


class SupplyChainSource(DataSource):
    """
    فئة لجمع بيانات موردي سلاسل الإمداد
    """
    
    def __init__(self, name: str, base_url: str):
        """
        تهيئة مصدر بيانات موردي سلاسل الإمداد
        
        المعلمات:
            name (str): اسم مصدر البيانات
            base_url (str): عنوان URL الأساسي للمصدر
        """
        super().__init__(name, base_url, "supply_chain")
        
        # تعريف فئات موردي سلاسل الإمداد المطلوبة
        self.supply_chain_categories = [
            "موردي مواد بناء", "موردي معدات", "موردي قطع غيار", "موردي أدوات",
            "موردي مستلزمات أمن وسلامة", "موردي وقود", "موردي مواد كيميائية",
            "موردي مواد عازلة", "موردي أنظمة تكييف", "موردي أنظمة إطفاء",
            "موردي أنظمة مراقبة", "موردي أنظمة اتصالات", "موردي أنظمة طاقة",
            "خدمات لوجستية", "خدمات نقل", "خدمات تخزين"
        ]
    
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        جلب بيانات موردي سلاسل الإمداد
        
        يجب تنفيذ هذه الطريقة في الفئات الفرعية
        
        العائد:
            List[Dict[str, Any]]: قائمة بموردي سلاسل الإمداد
        """
        pass


class DataCollector:
    """
    فئة لإدارة جمع البيانات من مختلف المصادر
    """
    
    def __init__(self):
        """
        تهيئة جامع البيانات
        """
        self.data_sources = {
            "materials": [],
            "equipment": [],
            "labor": [],
            "tenders": [],
            "subcontractors": [],
            "supply_chain": []
        }
        
        logger.info("تم تهيئة جامع البيانات")
    
    def add_source(self, source: DataSource) -> None:
        """
        إضافة مصدر بيانات
        
        المعلمات:
            source (DataSource): مصدر البيانات المراد إضافته
        """
        if source.category in self.data_sources:
            self.data_sources[source.category].append(source)
            logger.info(f"تم إضافة مصدر بيانات: {source.name} إلى فئة {source.category}")
        else:
            logger.error(f"فئة غير معروفة: {source.category}")
    
    def collect_data(self, category: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        جمع البيانات من جميع المصادر أو من فئة محددة
        
        المعلمات:
            category (str, optional): فئة المصادر المراد جمع البيانات منها
            
        العائد:
            Dict[str, List[Dict[str, Any]]]: قاموس يحتوي على البيانات المجمعة
        """
        collected_data = {}
        
        if category:
            if category not in self.data_sources:
                logger.error(f"فئة غير معروفة: {category}")
                return collected_data
            
            categories = [category]
        else:
            categories = list(self.data_sources.keys())
        
        for cat in categories:
            collected_data[cat] = []
            
            for source in self.data_sources[cat]:
                try:
                    logger.info(f"جاري جمع البيانات من: {source.name} ({cat})")
                    data = source.fetch_data()
                    collected_data[cat].extend(data)
                    logger.info(f"تم جمع {len(data)} عنصر من {source.name}")
                except Exception as e:
                    logger.error(f"خطأ في جمع البيانات من {source.name}: {str(e)}")
        
        return collected_data
    
    def save_collected_data(self, data: Dict[str, List[Dict[str, Any]]], 
                           format: str = 'json') -> Dict[str, str]:
        """
        حفظ البيانات المجمعة
        
        المعلمات:
            data (Dict[str, List[Dict[str, Any]]]): البيانات المراد حفظها
            format (str, optional): تنسيق الحفظ (json أو csv)
            
        العائد:
            Dict[str, str]: قاموس يحتوي على مسارات الملفات المحفوظة
        """
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for category, items in data.items():
            if not items:
                continue
            
            filename = f"temp_data/{category}_{timestamp}"
            
            if format.lower() == 'json':
                filename += '.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(items, f, ensure_ascii=False, indent=4)
            elif format.lower() == 'csv':
                filename += '.csv'
                df = pd.DataFrame(items)
                df.to_csv(filename, index=False, encoding='utf-8')
            else:
                logger.error(f"تنسيق غير مدعوم: {format}")
                continue
            
            saved_files[category] = filename
            logger.info(f"تم حفظ بيانات {category} في: {filename}")
        
        return saved_files
    
    def export_data(self, data: Dict[str, List[Dict[str, Any]]], 
                   format: str = 'json', directory: str = 'exports') -> Dict[str, str]:
        """
        تصدير البيانات المجمعة
        
        المعلمات:
            data (Dict[str, List[Dict[str, Any]]]): البيانات المراد تصديرها
            format (str, optional): تنسيق التصدير (json، csv، excel)
            directory (str, optional): المجلد المراد التصدير إليه
            
        العائد:
            Dict[str, str]: قاموس يحتوي على مسارات الملفات المصدرة
        """
        os.makedirs(directory, exist_ok=True)
        exported_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for category, items in data.items():
            if not items:
                continue
            
            filename = f"{directory}/{category}_{timestamp}"
            
            if format.lower() == 'json':
                filename += '.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(items, f, ensure_ascii=False, indent=4)
            elif format.lower() == 'csv':
                filename += '.csv'
                df = pd.DataFrame(items)
                df.to_csv(filename, index=False, encoding='utf-8')
            elif format.lower() == 'excel':
                filename += '.xlsx'
                df = pd.DataFrame(items)
                df.to_excel(filename, index=False)
            else:
                logger.error(f"تنسيق غير مدعوم: {format}")
                continue
            
            exported_files[category] = filename
            logger.info(f"تم تصدير بيانات {category} إلى: {filename}")
        
        return exported_files
