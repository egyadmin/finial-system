"""
محرك زحف مواقع مواد البناء السعودية
Saudi Construction Materials Websites Scraper

هذا الملف يحتوي على تنفيذات محددة لمحركات زحف مواقع مواد البناء السعودية
"""

import os
import re
import time
import random
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
import pandas as pd

# استيراد إطار عمل جمع البيانات
from data_collection_framework import MaterialsSource, DataCollector

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("materials_scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("materials_scraper")


class SaudiCementCompany(MaterialsSource):
    """
    محرك زحف لموقع شركة الأسمنت السعودية
    """
    
    def __init__(self):
        """
        تهيئة محرك زحف موقع شركة الأسمنت السعودية
        """
        super().__init__("Saudi Cement Company", "https://saudicement.com.sa", "materials")
        
        # تعريف صفحات المنتجات
        self.products_url = "/ar/products"
        
        # تعريف فئات المنتجات
        self.product_categories = {
            "أسمنت بورتلاندي عادي": "/ar/products/ordinary-portland-cement",
            "أسمنت مقاوم للكبريتات": "/ar/products/sulfate-resisting-cement",
            "أسمنت بورتلاندي بوزولاني": "/ar/products/portland-pozzolana-cement",
            "أسمنت آبار البترول": "/ar/products/oil-well-cement",
        }
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        جلب بيانات منتجات الأسمنت من الموقع
        
        العائد:
            List[Dict[str, Any]]: قائمة بمنتجات الأسمنت
        """
        all_products = []
        
        # جمع معلومات عامة عن المنتجات من صفحة المنتجات الرئيسية
        main_page_url = urljoin(self.base_url, self.products_url)
        main_page_response = self._make_request(main_page_url)
        
        if not main_page_response:
            logger.error(f"فشل الوصول إلى صفحة المنتجات الرئيسية: {main_page_url}")
            return all_products
        
        # جمع معلومات تفصيلية من صفحات المنتجات الفردية
        for category_name, category_url in self.product_categories.items():
            try:
                product_url = urljoin(self.base_url, category_url)
                logger.info(f"جاري جمع بيانات المنتج: {category_name} من {product_url}")
                
                product_response = self._make_request(product_url)
                if not product_response:
                    continue
                
                soup = BeautifulSoup(product_response.content, 'html.parser')
                
                # استخراج معلومات المنتج
                product_name = category_name
                product_description = ""
                product_specs = {}
                product_price = None
                product_price_text = "اتصل للاستعلام عن السعر"
                
                # استخراج الوصف
                description_element = soup.select_one('.product-description')
                if description_element:
                    product_description = self._extract_text(description_element)
                
                # استخراج المواصفات
                specs_table = soup.select_one('.specifications-table')
                if specs_table:
                    rows = specs_table.select('tr')
                    for row in rows:
                        cells = row.select('td')
                        if len(cells) >= 2:
                            spec_name = self._extract_text(cells[0])
                            spec_value = self._extract_text(cells[1])
                            product_specs[spec_name] = spec_value
                
                # إنشاء قاموس بيانات المنتج
                product_data = {
                    'name': product_name,
                    'category': 'أسمنت',
                    'subcategory': category_name,
                    'description': product_description,
                    'specifications': product_specs,
                    'price': product_price,
                    'price_text': product_price_text,
                    'currency': 'SAR',
                    'unit': 'طن',
                    'link': product_url,
                    'city': 'الدمام',
                    'region': 'المنطقة الشرقية',
                    'availability': True,
                    'last_updated': datetime.now().isoformat(),
                }
                
                all_products.append(product_data)
                logger.info(f"تم جمع بيانات المنتج: {product_name}")
                
                # إضافة تأخير بين الطلبات
                time.sleep(random.uniform(1.0, 3.0))
            
            except Exception as e:
                logger.error(f"خطأ في جمع بيانات المنتج {category_name}: {str(e)}")
        
        return all_products


class SaudiBuildingMaterials(MaterialsSource):
    """
    محرك زحف لموقع مواد البناء السعودية
    """
    
    def __init__(self):
        """
        تهيئة محرك زحف موقع مواد البناء السعودية
        """
        super().__init__("Saudi Building Materials", "https://building-materials-sa.com")

        
        # تعريف صفحات الفئات
        self.categories = {
            "خرسانة": "/category/concrete",
            "أسمنت": "/category/cement",
            "حديد": "/category/steel",
            "رمل": "/category/sand",
            "بلوك": "/category/blocks",
            "طوب": "/category/bricks",
            "بلاط": "/category/tiles",
            "سيراميك": "/category/ceramics",
            "عوازل": "/category/insulation",
            "أنابيب": "/category/pipes",
            "دهانات": "/category/paints",
        }
        
        # تعريف المناطق
        self.regions = {
            "الرياض": "riyadh",
            "مكة المكرمة": "makkah",
            "المدينة المنورة": "madinah",
            "القصيم": "qassim",
            "المنطقة الشرقية": "eastern",
            "عسير": "asir",
            "تبوك": "tabuk",
            "حائل": "hail",
            "جازان": "jizan",
        }
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        جلب بيانات مواد البناء من الموقع
        
        العائد:
            List[Dict[str, Any]]: قائمة بمواد البناء
        """
        all_materials = []
        
        # جمع البيانات من جميع الفئات
        for category_name, category_url in self.categories.items():
            try:
                # جمع البيانات من جميع المناطق
                for region_name, region_code in self.regions.items():
                    # بناء URL مع معلمات المنطقة
                    url = urljoin(self.base_url, category_url)
                    params = {"region": region_code}
                    
                    logger.info(f"جاري جمع بيانات فئة {category_name} في منطقة {region_name}")
                    
                    page = 1
                    has_more_pages = True
                    
                    while has_more_pages:
                        params["page"] = page
                        
                        response = self._make_request(url, params=params)
                        if not response:
                            break
                        
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # استخراج عناصر المنتجات
                        product_elements = soup.select('.product-item')
                        
                        if not product_elements:
                            has_more_pages = False
                            continue
                        
                        for product_element in product_elements:
                            try:
                                # استخراج معلومات المنتج
                                product_name_element = product_element.select_one('.product-title')
                                product_price_element = product_element.select_one('.product-price')
                                product_link_element = product_element.select_one('a.product-link')
                                
                                product_name = self._extract_text(product_name_element) if product_name_element else "غير معروف"
                                product_price_text = self._extract_text(product_price_element) if product_price_element else "غير متوفر"
                                product_price = self._normalize_price(product_price_text) if product_price_text != "غير متوفر" else None
                                product_link = product_link_element['href'] if product_link_element and 'href' in product_link_element.attrs else None
                                
                                if product_link:
                                    product_link = urljoin(self.base_url, product_link)
                                
                                # إنشاء قاموس بيانات المنتج
                                product_data = {
                                    'name': product_name,
                                    'category': category_name,
                                    'price': product_price,
                                    'price_text': product_price_text,
                                    'currency': 'SAR',
                                    'link': product_link,
                                    'region': region_name,
                                    'availability': True,
                                    'last_updated': datetime.now().isoformat(),
                                }
                                
                                all_materials.append(product_data)
                                logger.info(f"تم جمع بيانات المنتج: {product_name} في {region_name}")
                            
                            except Exception as e:
                                logger.error(f"خطأ في استخراج بيانات المنتج: {str(e)}")
                        
                        # التحقق مما إذا كانت هناك صفحة تالية
                        next_page_element = soup.select_one('.pagination .next')
                        if not next_page_element or 'disabled' in next_page_element.get('class', []):
                            has_more_pages = False
                        else:
                            page += 1
                            # إضافة تأخير بين الصفحات
                            time.sleep(random.uniform(2.0, 4.0))
            
            except Exception as e:
                logger.error(f"خطأ في جمع بيانات فئة {category_name}: {str(e)}")
        
        return all_materials


# تنفيذ محركات زحف إضافية لمواقع أخرى
class MockMaterialsSource(MaterialsSource):
    """
    محرك زحف وهمي لأغراض الاختبار
    """
    
    def __init__(self):
        """
        تهيئة محرك زحف وهمي
        """
        super().__init__("Mock Materials Source", "https://example.com")
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        إنشاء بيانات وهمية لأغراض الاختبار
        
        العائد:
            List[Dict[str, Any]]: قائمة بمواد البناء الوهمية
        """
        mock_data = []
        
        # إنشاء بيانات وهمية لمختلف فئات مواد البناء
        for category in ["أسمنت", "حديد", "رمل", "بلوك", "طوب"]:
            for i in range(1, 6):
                product_data = {
                    'name': f"{category} نوع {i}",
                    'category': category,
                    'description': f"وصف {category} نوع {i} للاختبار",
                    'price': random.uniform(100, 1000),
                    'price_text': f"{random.uniform(100, 1000):.2f} ريال",
                    'currency': 'SAR',
                    'unit': 'قطعة' if category in ["بلوك", "طوب"] else 'طن',
                    'link': f"https://example.com/products/{category}/{i}",
                    'city': random.choice(["الرياض", "جدة", "الدمام", "مكة"]),
                    'region': random.choice(["المنطقة الوسطى", "المنطقة الغربية", "المنطقة الشرقية"]),
                    'availability': random.choice([True, False]),
                    'last_updated': datetime.now().isoformat(),
                }
                mock_data.append(product_data)
        
        logger.info(f"تم إنشاء {len(mock_data)} عنصر وهمي للاختبار")
        return mock_data


def main():
    """
    الدالة الرئيسية لتشغيل محركات الزحف
    """
    # إنشاء جامع البيانات
    collector = DataCollector()
    
    # إضافة محركات الزحف
    collector.add_source(SaudiCementCompany())
    collector.add_source(SaudiBuildingMaterials())
    collector.add_source(MockMaterialsSource())
    
    # جمع البيانات
    collected_data = collector.collect_data("materials")
    
    # حفظ البيانات
    saved_files = collector.save_collected_data(collected_data, format='json')
    
    # تصدير البيانات بتنسيقات مختلفة
    collector.export_data(collected_data, format='json', directory='exports')
    collector.export_data(collected_data, format='csv', directory='exports')
    collector.export_data(collected_data, format='excel', directory='exports')
    
    logger.info("تم الانتهاء من جمع وحفظ البيانات")
    
    return saved_files


if __name__ == "__main__":
    # إنشاء مجلدات الحفظ والتصدير إذا لم تكن موجودة
    os.makedirs('temp_data', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    main()
