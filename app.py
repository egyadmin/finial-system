#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
النظام المتكامل للبحث متعدد الوكلاء مع إطار عمل جمع البيانات - تطبيق Hugging Face
Integrated Multi-Agent Research System with Data Collection Framework - Hugging Face App

ملف تطبيق Hugging Face
"""

import os
import sys
import logging
from integrated_system import (
    DatabaseManager, LiveStreamingSystem, GradioInterface,
    WebResearchAgent, ContentAnalyzerAgent, FactCheckerAgent
)
from data_collection_framework import DataCollector
from materials_scraper import SaudiCementCompany, SaudiBuildingMaterials, MockMaterialsSource

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("huggingface_app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("huggingface_app")

def main():
    """
    الدالة الرئيسية لتشغيل تطبيق Hugging Face
    """
    try:
        # إنشاء مجلدات النظام
        os.makedirs('exports', exist_ok=True)
        os.makedirs('temp_data', exist_ok=True)
        
        # تهيئة مدير قاعدة البيانات
        db_manager = DatabaseManager("research_database.db")
        
        # تهيئة نظام البث المباشر
        live_system = LiveStreamingSystem(db_manager)
        
        # تهيئة جامع البيانات
        data_collector = DataCollector()
        
        # إضافة مصادر البيانات
        data_collector.add_source(SaudiCementCompany())
        data_collector.add_source(SaudiBuildingMaterials())
        
        # إضافة مصدر وهمي للاختبار
        data_collector.add_source(MockMaterialsSource())
        
        # تهيئة وكلاء البحث
        web_agent = WebResearchAgent(live_system, data_collector)
        content_agent = ContentAnalyzerAgent(live_system)
        fact_agent = FactCheckerAgent(live_system)
        
        # تهيئة واجهة المستخدم
        interface = GradioInterface(
            db_manager=db_manager,
            live_system=live_system,
            web_agent=web_agent,
            content_agent=content_agent,
            fact_agent=fact_agent,
            data_collector=data_collector
        )
        
        # إرجاع واجهة Gradio للاستخدام في Hugging Face
        return interface.create_interface()
        
    except Exception as e:
        logger.error(f"خطأ في تشغيل النظام: {str(e)}")
        if 'db_manager' in locals():
            db_manager.close()
        return None

# تهيئة واجهة Gradio للاستخدام في Hugging Face
app = main()
