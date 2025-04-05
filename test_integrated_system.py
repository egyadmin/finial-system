"""
اختبار النظام المتكامل للبحث متعدد الوكلاء مع إطار عمل جمع البيانات
Integrated Multi-Agent Research System with Data Collection Framework - Test Script

هذا الملف يستخدم لاختبار النظام المتكامل بجميع مكوناته
"""

import os
import sys
import time
import logging
import unittest
import json
import sqlite3
import pandas as pd
from datetime import datetime

# استيراد مكونات النظام
from data_collection_framework import DataCollector, DataSource
from materials_scraper import SaudiCementCompany, SaudiBuildingMaterials, MockMaterialsSource
from integrated_system import (
    DatabaseManager, ResearchEvent, EventFactory, EventCaptureManager,
    LiveStreamingSystem, ResearchAgent, WebResearchAgent, ContentAnalyzerAgent, FactCheckerAgent
)

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system_test.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("system_test")


class TestDatabaseManager(unittest.TestCase):
    """
    اختبار مدير قاعدة البيانات
    """
    
    def setUp(self):
        """
        إعداد بيئة الاختبار
        """
        # استخدام قاعدة بيانات مؤقتة للاختبار
        self.db_manager = DatabaseManager("test_database.db")
    
    def tearDown(self):
        """
        تنظيف بيئة الاختبار
        """
        self.db_manager.close()
        
        # حذف قاعدة البيانات المؤقتة
        if os.path.exists("test_database.db"):
            os.remove("test_database.db")
    
    def test_create_project(self):
        """
        اختبار إنشاء مشروع
        """
        project_id = self.db_manager.create_project("مشروع اختبار", "وصف مشروع الاختبار")
        self.assertIsNotNone(project_id)
        self.assertGreater(project_id, 0)
    
    def test_add_material(self):
        """
        اختبار إضافة مادة بناء
        """
        material_data = {
            'name': 'أسمنت اختبار',
            'category': 'أسمنت',
            'price': 300.0,
            'price_text': '300 ريال',
            'currency': 'SAR',
            'unit': 'طن',
            'city': 'الرياض',
            'region': 'المنطقة الوسطى',
            'availability': True,
            'source': 'اختبار',
            'last_updated': datetime.now().isoformat()
        }
        
        material_id = self.db_manager.add_material(material_data)
        self.assertIsNotNone(material_id)
        self.assertGreater(material_id, 0)
    
    def test_get_materials(self):
        """
        اختبار الحصول على مواد البناء
        """
        # إضافة مادة بناء للاختبار
        material_data = {
            'name': 'أسمنت اختبار',
            'category': 'أسمنت',
            'price': 300.0,
            'price_text': '300 ريال',
            'currency': 'SAR',
            'unit': 'طن',
            'city': 'الرياض',
            'region': 'المنطقة الوسطى',
            'availability': True,
            'source': 'اختبار',
            'last_updated': datetime.now().isoformat()
        }
        
        self.db_manager.add_material(material_data)
        
        # الحصول على مواد البناء
        materials = self.db_manager.get_materials()
        self.assertIsNotNone(materials)
        self.assertGreater(len(materials), 0)
        
        # التحقق من البيانات
        material = materials[0]
        self.assertEqual(material['name'], 'أسمنت اختبار')
        self.assertEqual(material['category'], 'أسمنت')
        self.assertEqual(material['price'], 300.0)
    
    def test_export_data(self):
        """
        اختبار تصدير البيانات
        """
        # إضافة مادة بناء للاختبار
        material_data = {
            'name': 'أسمنت اختبار',
            'category': 'أسمنت',
            'price': 300.0,
            'price_text': '300 ريال',
            'currency': 'SAR',
            'unit': 'طن',
            'city': 'الرياض',
            'region': 'المنطقة الوسطى',
            'availability': True,
            'source': 'اختبار',
            'last_updated': datetime.now().isoformat()
        }
        
        self.db_manager.add_material(material_data)
        
        # تصدير البيانات
        file_path, file_type = self.db_manager.export_data('materials', 'json')
        
        # التحقق من وجود الملف
        self.assertTrue(os.path.exists(file_path))
        
        # التحقق من نوع الملف
        self.assertEqual(file_type, 'application/json')
        
        # حذف الملف بعد الاختبار
        if os.path.exists(file_path):
            os.remove(file_path)


class TestLiveStreamingSystem(unittest.TestCase):
    """
    اختبار نظام البث المباشر
    """
    
    def setUp(self):
        """
        إعداد بيئة الاختبار
        """
        # استخدام قاعدة بيانات مؤقتة للاختبار
        self.db_manager = DatabaseManager("test_database.db")
        self.live_system = LiveStreamingSystem(self.db_manager)
        
        # قائمة لتخزين الأحداث المستلمة
        self.received_events = []
    
    def tearDown(self):
        """
        تنظيف بيئة الاختبار
        """
        self.live_system.shutdown()
        self.db_manager.close()
        
        # حذف قاعدة البيانات المؤقتة
        if os.path.exists("test_database.db"):
            os.remove("test_database.db")
    
    def event_listener(self, event_dict):
        """
        مستمع للأحداث
        
        المعلمات:
            event_dict (Dict): قاموس الحدث
        """
        self.received_events.append(event_dict)
    
    def test_add_event(self):
        """
        اختبار إضافة حدث
        """
        # إضافة مستمع للأحداث
        self.live_system.add_listener(self.event_listener)
        
        # إنشاء حدث بحث
        search_event = EventFactory.create_search_event("استعلام اختبار", "مصدر اختبار")
        
        # إضافة الحدث
        self.live_system.add_event(search_event)
        
        # انتظار معالجة الحدث
        time.sleep(1.0)
        
        # التحقق من استلام الحدث
        self.assertGreater(len(self.received_events), 0)
        
        # التحقق من بيانات الحدث
        event = self.received_events[0]
        self.assertEqual(event['event_type'], 'search')
        self.assertEqual(event['event_data']['query'], 'استعلام اختبار')
        self.assertEqual(event['event_data']['source'], 'مصدر اختبار')
    
    def test_event_history(self):
        """
        اختبار تاريخ الأحداث
        """
        # إنشاء وإضافة عدة أحداث
        for i in range(5):
            search_event = EventFactory.create_search_event(f"استعلام {i}", f"مصدر {i}")
            self.live_system.add_event(search_event)
        
        # انتظار معالجة الأحداث
        time.sleep(1.0)
        
        # الحصول على تاريخ الأحداث
        event_history = self.live_system.get_event_history()
        
        # التحقق من عدد الأحداث
        self.assertEqual(len(event_history), 5)


class TestResearchAgents(unittest.TestCase):
    """
    اختبار وكلاء البحث
    """
    
    def setUp(self):
        """
        إعداد بيئة الاختبار
        """
        # استخدام قاعدة بيانات مؤقتة للاختبار
        self.db_manager = DatabaseManager("test_database.db")
        self.live_system = LiveStreamingSystem(self.db_manager)
        
        # إنشاء جامع البيانات
        self.data_collector = DataCollector()
        self.data_collector.add_source(MockMaterialsSource())
        
        # إنشاء وكلاء البحث
        self.web_agent = WebResearchAgent(self.live_system, self.data_collector)
        self.content_agent = ContentAnalyzerAgent(self.live_system)
        self.fact_agent = FactCheckerAgent(self.live_system)
        
        # قائمة لتخزين الأحداث المستلمة
        self.received_events = []
        self.live_system.add_listener(self.event_listener)
    
    def tearDown(self):
        """
        تنظيف بيئة الاختبار
        """
        self.live_system.shutdown()
        self.db_manager.close()
        
        # حذف قاعدة البيانات المؤقتة
        if os.path.exists("test_database.db"):
            os.remove("test_database.db")
    
    def event_listener(self, event_dict):
        """
        مستمع للأحداث
        
        المعلمات:
            event_dict (Dict): قاموس الحدث
        """
        self.received_events.append(event_dict)
    
    def test_web_agent_search(self):
        """
        اختبار بحث وكيل البحث على الويب
        """
        # إجراء بحث
        results = self.web_agent.search("استعلام اختبار", "مصدر اختبار")
        
        # التحقق من النتائج
        self.assertIsNotNone(results)
        self.assertEqual(results['query'], 'استعلام اختبار')
        self.assertEqual(results['source'], 'مصدر اختبار')
        self.assertGreater(len(results['results']), 0)
        
        # التحقق من الأحداث
        search_events = [e for e in self.received_events if e['event_type'] == 'search']
        self.assertGreater(len(search_events), 0)
        
        result_events = [e for e in self.received_events if e['event_type'] == 'result']
        self.assertGreater(len(result_events), 0)
    
    def test_web_agent_collect_data(self):
        """
        اختبار جمع البيانات بواسطة وكيل البحث على الويب
        """
        # جمع البيانات
        collected_data = self.web_agent.collect_data("materials")
        
        # التحقق من البيانات المجمعة
        self.assertIsNotNone(collected_data)
        self.assertIn('materials', collected_data)
        self.assertGreater(len(collected_data['materials']), 0)
        
        # التحقق من الأحداث
        collection_events = [e for e in self.received_events if e['event_type'] == 'data_collection']
        self.assertGreater(len(collection_events), 0)
        
        crawling_events = [e for e in self.received_events if e['event_type'] == 'web_crawling']
        self.assertGreater(len(crawling_events), 0)
    
    def test_content_agent_analyze(self):
        """
        اختبار تحليل وكيل تحليل المحتوى
        """
        # إنشاء بيانات للتحليل
        materials = [
            {
                'name': 'أسمنت اختبار 1',
                'category': 'أسمنت',
                'price': 300.0,
                'region': 'المنطقة الوسطى'
            },
            {
                'name': 'أسمنت اختبار 2',
                'category': 'أسمنت',
                'price': 320.0,
                'region': 'المنطقة الشرقية'
            },
            {
                'name': 'حديد اختبار',
                'category': 'حديد',
                'price': 2500.0,
                'region': 'المنطقة الوسطى'
            }
        ]
        
        # تحليل البيانات
        analysis_results = self.content_agent.analyze(materials, "materials")
        
        # التحقق من نتائج التحليل
        self.assertIsNotNone(analysis_results)
        self.assertIn('summary', analysis_results)
        self.assertIn('insights', analysis_results)
        self.assertGreater(len(analysis_results['insights']), 0)
        
        # التحقق من الأحداث
        analysis_events = [e for e in self.received_events if e['event_type'] == 'analysis']
        self.assertGreater(len(analysis_events), 0)
    
    def test_fact_agent_verify(self):
        """
        اختبار تحقق وكيل التحقق من الحقائق
        """
        # التحقق من حقيقة
        verification_results = self.fact_agent.verify(
            "سعر الأسمنت في الرياض 300 ريال",
            ["مصدر اختبار 1", "مصدر اختبار 2"]
        )
        
        # التحقق من نتائج التحقق
        self.assertIsNotNone(verification_results)
        self.assertEqual(verification_results['fact'], 'سعر الأسمنت في الرياض 300 ريال')
        self.assertGreaterEqual(verification_results['confidence'], 0.0)
        self.assertLessEqual(verification_results['confidence'], 1.0)
        
        # التحقق من الأحداث
        verification_events = [e for e in self.received_events if e['event_type'] == 'verification']
        self.assertGreater(len(verification_events), 0)


class TestDataCollectionFramework(unittest.TestCase):
    """
    اختبار إطار عمل جمع البيانات
    """
    
    def setUp(self):
        """
        إعداد بيئة الاختبار
        """
        # إنشاء جامع البيانات
        self.data_collector = DataCollector()
        
        # إضافة مصدر وهمي
        self.mock_source = MockMaterialsSource()
        self.data_collector.add_source(self.mock_source)
    
    def test_collect_data(self):
        """
        اختبار جمع البيانات
        """
        # جمع البيانات
        collected_data = self.data_collector.collect_data("materials")
        
        # التحقق من البيانات المجمعة
        self.assertIsNotNone(collected_data)
        self.assertIn('materials', collected_data)
        self.assertGreater(len(collected_data['materials']), 0)
        
        # التحقق من بنية البيانات
        material = collected_data['materials'][0]
        self.assertIn('name', material)
        self.assertIn('category', material)
        self.assertIn('price', material)
    
    def test_export_data(self):
        """
        اختبار تصدير البيانات
        """
        # جمع البيانات
        collected_data = self.data_collector.collect_data("materials")
        
        # تصدير البيانات بتنسيق JSON
        exported_files = self.data_collector.export_data(collected_data, 'json', 'test_exports')
        
        # التحقق من وجود الملف
        self.assertTrue(isinstance(exported_files, dict))
        self.assertTrue(len(exported_files) > 0)
        json_file = list(exported_files.values())[0]
        self.assertTrue(os.path.exists(json_file))
        
        # تصدير البيانات بتنسيق CSV
        exported_csv_files = self.data_collector.export_data(collected_data, 'csv', 'test_exports')
        
        # التحقق من وجود الملف
        self.assertTrue(isinstance(exported_csv_files, dict))
        self.assertTrue(len(exported_csv_files) > 0)
        csv_file = list(exported_csv_files.values())[0]
        self.assertTrue(os.path.exists(csv_file))
        
        # حذف الملفات بعد الاختبار
        if os.path.exists(json_file):
            os.remove(json_file)
        
        if os.path.exists(csv_file):
            os.remove(csv_file)
        
        # حذف مجلد الاختبار
        if os.path.exists('test_exports'):
            os.rmdir('test_exports')


class TestIntegratedSystem(unittest.TestCase):
    """
    اختبار النظام المتكامل
    """
    
    def setUp(self):
        """
        إعداد بيئة الاختبار
        """
        # استخدام قاعدة بيانات مؤقتة للاختبار
        self.db_manager = DatabaseManager("test_database.db")
        self.live_system = LiveStreamingSystem(self.db_manager)
        
        # إنشاء جامع البيانات
        self.data_collector = DataCollector()
        self.data_collector.add_source(MockMaterialsSource())
        
        # إنشاء وكلاء البحث
        self.web_agent = WebResearchAgent(self.live_system, self.data_collector)
        self.content_agent = ContentAnalyzerAgent(self.live_system)
        self.fact_agent = FactCheckerAgent(self.live_system)
    
    def tearDown(self):
        """
        تنظيف بيئة الاختبار
        """
        self.live_system.shutdown()
        self.db_manager.close()
        
        # حذف قاعدة البيانات المؤقتة
        if os.path.exists("test_database.db"):
            os.remove("test_database.db")
    
    def test_end_to_end_workflow(self):
        """
        اختبار سير العمل من البداية إلى النهاية
        """
        # 1. إنشاء مشروع
        project_id = self.db_manager.create_project("مشروع اختبار متكامل", "اختبار النظام المتكامل")
        self.assertIsNotNone(project_id)
        
        # 2. جمع البيانات
        collected_data = self.web_agent.collect_data("materials")
        self.assertIsNotNone(collected_data)
        self.assertIn('materials', collected_data)
        
        # 3. حفظ البيانات في قاعدة البيانات
        materials = collected_data['materials']
        for material in materials:
            material_id = self.db_manager.add_material(material)
            self.assertIsNotNone(material_id)
        
        # 4. تحليل البيانات
        analysis_results = self.content_agent.analyze(materials, "materials")
        self.assertIsNotNone(analysis_results)
        
        # 5. التحقق من حقيقة
        verification_results = self.fact_agent.verify(
            f"متوسط سعر الأسمنت {analysis_results.get('avg_price', 0):.2f} ريال",
            ["تحليل البيانات"]
        )
        self.assertIsNotNone(verification_results)
        
        # 6. استرجاع البيانات من قاعدة البيانات
        stored_materials = self.db_manager.get_materials()
        self.assertEqual(len(stored_materials), len(materials))
        
        # 7. تصدير البيانات
        file_path, file_type = self.db_manager.export_data('materials', 'json')
        self.assertTrue(os.path.exists(file_path))
        
        # حذف الملف بعد الاختبار
        if os.path.exists(file_path):
            os.remove(file_path)


def run_tests():
    """
    تشغيل جميع الاختبارات
    """
    # إنشاء مجلدات الاختبار
    os.makedirs('test_exports', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    # تشغيل الاختبارات
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests()
