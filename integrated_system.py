"""
النظام المتكامل للبحث متعدد الوكلاء مع إطار عمل جمع البيانات
Integrated Multi-Agent Research System with Data Collection Framework

هذا الملف يجمع بين نظام قاعدة البيانات، نظام البث المباشر، وإطار عمل جمع البيانات
في نظام متكامل واحد.
"""

import os
import sys
import json
import time
import sqlite3
import logging
import pandas as pd
import gradio as gr
from datetime import datetime
import random
from typing import Dict, List, Any, Optional, Union, Tuple
import threading
import queue
import uuid
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# استيراد إطار عمل جمع البيانات
from data_collection_framework import DataCollector, DataSource
from materials_scraper import SaudiCementCompany, SaudiBuildingMaterials, MockMaterialsSource

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integrated_system.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("integrated_system")

# ============================================================================
# نظام قاعدة البيانات
# Database System
# ============================================================================

class DatabaseManager:
    """
    مدير قاعدة البيانات للنظام المتكامل
    """
    
    def __init__(self, db_path: str = "research_database.db"):
        """
        تهيئة مدير قاعدة البيانات
        
        المعلمات:
            db_path (str): مسار ملف قاعدة البيانات
        """
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_tables()
        logger.info(f"تم الاتصال بقاعدة البيانات: {db_path}")
    
    def connect(self):
        """
        الاتصال بقاعدة البيانات
        """
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            logger.error(f"خطأ في الاتصال بقاعدة البيانات: {str(e)}")
            raise
    
    def close(self):
        """
        إغلاق الاتصال بقاعدة البيانات
        """
        if self.conn:
            self.conn.close()
            logger.info("تم إغلاق الاتصال بقاعدة البيانات")
    
    def create_tables(self):
        """
        إنشاء جداول قاعدة البيانات
        """
        try:
            cursor = self.conn.cursor()
            
            # جدول المشاريع البحثية
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
            ''')
            
            # جدول مصادر البحث
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                url TEXT,
                title TEXT,
                source_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES research_projects (id)
            )
            ''')
            
            # جدول البيانات المستخرجة
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS extracted_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                content TEXT,
                data_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES research_sources (id)
            )
            ''')
            
            # جدول الحقائق المتحقق منها
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS verified_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                fact TEXT,
                confidence REAL,
                sources TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES research_projects (id)
            )
            ''')
            
            # جدول الكيانات
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                name TEXT,
                entity_type TEXT,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES research_projects (id)
            )
            ''')
            
            # جدول العلاقات بين الكيانات
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS entity_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity1_id INTEGER,
                entity2_id INTEGER,
                relationship_type TEXT,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity1_id) REFERENCES entities (id),
                FOREIGN KEY (entity2_id) REFERENCES entities (id)
            )
            ''')
            
            # جدول أحداث البحث
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                event_type TEXT,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES research_projects (id)
            )
            ''')
            
            # جدول نتائج البحث
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT,
                content TEXT,
                result_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES research_projects (id)
            )
            ''')
            
            # جدول التصورات المرئية
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS visualizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT,
                visualization_type TEXT,
                data TEXT,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES research_projects (id)
            )
            ''')
            
            # جدول مواد البناء
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                subcategory TEXT,
                description TEXT,
                specifications TEXT,
                price REAL,
                price_text TEXT,
                currency TEXT,
                unit TEXT,
                link TEXT,
                city TEXT,
                region TEXT,
                availability INTEGER,
                source TEXT,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # جدول المعدات
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                description TEXT,
                specifications TEXT,
                price REAL,
                price_text TEXT,
                currency TEXT,
                unit TEXT,
                link TEXT,
                city TEXT,
                region TEXT,
                availability INTEGER,
                source TEXT,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # جدول العمالة
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS labor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT,
                description TEXT,
                salary REAL,
                salary_text TEXT,
                currency TEXT,
                period TEXT,
                link TEXT,
                city TEXT,
                region TEXT,
                availability INTEGER,
                source TEXT,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # جدول المناقصات
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT,
                description TEXT,
                value REAL,
                value_text TEXT,
                currency TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                link TEXT,
                city TEXT,
                region TEXT,
                status TEXT,
                source TEXT,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # جدول مقاولي الباطن
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS subcontractors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                description TEXT,
                services TEXT,
                rates TEXT,
                link TEXT,
                city TEXT,
                region TEXT,
                rating REAL,
                source TEXT,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            self.conn.commit()
            logger.info("تم إنشاء جداول قاعدة البيانات")
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في إنشاء جداول قاعدة البيانات: {str(e)}")
            raise
    
    def create_project(self, title: str, description: str = "") -> int:
        """
        إنشاء مشروع بحثي جديد
        
        المعلمات:
            title (str): عنوان المشروع
            description (str): وصف المشروع
            
        العائد:
            int: معرف المشروع الجديد
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO research_projects (title, description) VALUES (?, ?)",
                (title, description)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"خطأ في إنشاء مشروع جديد: {str(e)}")
            raise
    
    def add_research_source(self, project_id: int, url: str, title: str, source_type: str) -> int:
        """
        إضافة مصدر بحث جديد
        
        المعلمات:
            project_id (int): معرف المشروع
            url (str): عنوان URL للمصدر
            title (str): عنوان المصدر
            source_type (str): نوع المصدر
            
        العائد:
            int: معرف المصدر الجديد
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO research_sources (project_id, url, title, source_type) VALUES (?, ?, ?, ?)",
                (project_id, url, title, source_type)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"خطأ في إضافة مصدر بحث: {str(e)}")
            raise
    
    def add_research_event(self, project_id: int, event_type: str, event_data: Dict) -> int:
        """
        إضافة حدث بحث جديد
        
        المعلمات:
            project_id (int): معرف المشروع
            event_type (str): نوع الحدث
            event_data (Dict): بيانات الحدث
            
        العائد:
            int: معرف الحدث الجديد
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO research_events (project_id, event_type, event_data) VALUES (?, ?, ?)",
                (project_id, event_type, json.dumps(event_data, ensure_ascii=False))
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"خطأ في إضافة حدث بحث: {str(e)}")
            raise
    
    def add_material(self, material_data: Dict) -> int:
        """
        إضافة مادة بناء جديدة
        
        المعلمات:
            material_data (Dict): بيانات مادة البناء
            
        العائد:
            int: معرف مادة البناء الجديدة
        """
        try:
            cursor = self.conn.cursor()
            
            # تحويل المواصفات إلى JSON إذا كانت قاموس
            if 'specifications' in material_data and isinstance(material_data['specifications'], dict):
                material_data['specifications'] = json.dumps(material_data['specifications'], ensure_ascii=False)
            
            # تحويل قيمة التوفر إلى 1 أو 0
            if 'availability' in material_data:
                material_data['availability'] = 1 if material_data['availability'] else 0
            
            # إعداد حقول الإدراج والقيم
            fields = []
            values = []
            placeholders = []
            
            for key, value in material_data.items():
                fields.append(key)
                values.append(value)
                placeholders.append('?')
            
            query = f"INSERT INTO materials ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.lastrowid
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في إضافة مادة بناء: {str(e)}")
            raise
    
    def add_equipment(self, equipment_data: Dict) -> int:
        """
        إضافة معدة جديدة
        
        المعلمات:
            equipment_data (Dict): بيانات المعدة
            
        العائد:
            int: معرف المعدة الجديدة
        """
        try:
            cursor = self.conn.cursor()
            
            # تحويل المواصفات إلى JSON إذا كانت قاموس
            if 'specifications' in equipment_data and isinstance(equipment_data['specifications'], dict):
                equipment_data['specifications'] = json.dumps(equipment_data['specifications'], ensure_ascii=False)
            
            # تحويل قيمة التوفر إلى 1 أو 0
            if 'availability' in equipment_data:
                equipment_data['availability'] = 1 if equipment_data['availability'] else 0
            
            # إعداد حقول الإدراج والقيم
            fields = []
            values = []
            placeholders = []
            
            for key, value in equipment_data.items():
                fields.append(key)
                values.append(value)
                placeholders.append('?')
            
            query = f"INSERT INTO equipment ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.lastrowid
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في إضافة معدة: {str(e)}")
            raise
    
    def add_labor(self, labor_data: Dict) -> int:
        """
        إضافة عمالة جديدة
        
        المعلمات:
            labor_data (Dict): بيانات العمالة
            
        العائد:
            int: معرف العمالة الجديدة
        """
        try:
            cursor = self.conn.cursor()
            
            # تحويل قيمة التوفر إلى 1 أو 0
            if 'availability' in labor_data:
                labor_data['availability'] = 1 if labor_data['availability'] else 0
            
            # إعداد حقول الإدراج والقيم
            fields = []
            values = []
            placeholders = []
            
            for key, value in labor_data.items():
                fields.append(key)
                values.append(value)
                placeholders.append('?')
            
            query = f"INSERT INTO labor ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.lastrowid
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في إضافة عمالة: {str(e)}")
            raise
    
    def add_tender(self, tender_data: Dict) -> int:
        """
        إضافة مناقصة جديدة
        
        المعلمات:
            tender_data (Dict): بيانات المناقصة
            
        العائد:
            int: معرف المناقصة الجديدة
        """
        try:
            cursor = self.conn.cursor()
            
            # إعداد حقول الإدراج والقيم
            fields = []
            values = []
            placeholders = []
            
            for key, value in tender_data.items():
                fields.append(key)
                values.append(value)
                placeholders.append('?')
            
            query = f"INSERT INTO tenders ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.lastrowid
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في إضافة مناقصة: {str(e)}")
            raise
    
    def add_subcontractor(self, subcontractor_data: Dict) -> int:
        """
        إضافة مقاول باطن جديد
        
        المعلمات:
            subcontractor_data (Dict): بيانات مقاول الباطن
            
        العائد:
            int: معرف مقاول الباطن الجديد
        """
        try:
            cursor = self.conn.cursor()
            
            # تحويل الخدمات إلى JSON إذا كانت قائمة أو قاموس
            if 'services' in subcontractor_data and isinstance(subcontractor_data['services'], (list, dict)):
                subcontractor_data['services'] = json.dumps(subcontractor_data['services'], ensure_ascii=False)
            
            # تحويل الأسعار إلى JSON إذا كانت قاموس
            if 'rates' in subcontractor_data and isinstance(subcontractor_data['rates'], dict):
                subcontractor_data['rates'] = json.dumps(subcontractor_data['rates'], ensure_ascii=False)
            
            # إعداد حقول الإدراج والقيم
            fields = []
            values = []
            placeholders = []
            
            for key, value in subcontractor_data.items():
                fields.append(key)
                values.append(value)
                placeholders.append('?')
            
            query = f"INSERT INTO subcontractors ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.lastrowid
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في إضافة مقاول باطن: {str(e)}")
            raise
    
    def get_materials(self, category: str = None, region: str = None, limit: int = 100) -> List[Dict]:
        """
        الحصول على مواد البناء
        
        المعلمات:
            category (str, optional): فئة مواد البناء للتصفية
            region (str, optional): المنطقة للتصفية
            limit (int, optional): الحد الأقصى لعدد النتائج
            
        العائد:
            List[Dict]: قائمة بمواد البناء
        """
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT * FROM materials"
            params = []
            
            # إضافة شروط التصفية
            conditions = []
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if region:
                conditions.append("region = ?")
                params.append(region)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY created_at DESC LIMIT {limit}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # تحويل الصفوف إلى قواميس
            materials = []
            for row in rows:
                material = dict(row)
                
                # تحويل المواصفات من JSON إلى قاموس
                if 'specifications' in material and material['specifications']:
                    try:
                        material['specifications'] = json.loads(material['specifications'])
                    except json.JSONDecodeError:
                        pass
                
                # تحويل التوفر من 1/0 إلى True/False
                if 'availability' in material:
                    material['availability'] = bool(material['availability'])
                
                materials.append(material)
            
            return materials
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في الحصول على مواد البناء: {str(e)}")
            raise
    
    def get_equipment(self, category: str = None, region: str = None, limit: int = 100) -> List[Dict]:
        """
        الحصول على المعدات
        
        المعلمات:
            category (str, optional): فئة المعدات للتصفية
            region (str, optional): المنطقة للتصفية
            limit (int, optional): الحد الأقصى لعدد النتائج
            
        العائد:
            List[Dict]: قائمة بالمعدات
        """
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT * FROM equipment"
            params = []
            
            # إضافة شروط التصفية
            conditions = []
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if region:
                conditions.append("region = ?")
                params.append(region)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY created_at DESC LIMIT {limit}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # تحويل الصفوف إلى قواميس
            equipment_list = []
            for row in rows:
                equipment = dict(row)
                
                # تحويل المواصفات من JSON إلى قاموس
                if 'specifications' in equipment and equipment['specifications']:
                    try:
                        equipment['specifications'] = json.loads(equipment['specifications'])
                    except json.JSONDecodeError:
                        pass
                
                # تحويل التوفر من 1/0 إلى True/False
                if 'availability' in equipment:
                    equipment['availability'] = bool(equipment['availability'])
                
                equipment_list.append(equipment)
            
            return equipment_list
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في الحصول على المعدات: {str(e)}")
            raise
    
    def get_labor(self, category: str = None, region: str = None, limit: int = 100) -> List[Dict]:
        """
        الحصول على العمالة
        
        المعلمات:
            category (str, optional): فئة العمالة للتصفية
            region (str, optional): المنطقة للتصفية
            limit (int, optional): الحد الأقصى لعدد النتائج
            
        العائد:
            List[Dict]: قائمة بالعمالة
        """
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT * FROM labor"
            params = []
            
            # إضافة شروط التصفية
            conditions = []
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if region:
                conditions.append("region = ?")
                params.append(region)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY created_at DESC LIMIT {limit}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # تحويل الصفوف إلى قواميس
            labor_list = []
            for row in rows:
                labor = dict(row)
                
                # تحويل التوفر من 1/0 إلى True/False
                if 'availability' in labor:
                    labor['availability'] = bool(labor['availability'])
                
                labor_list.append(labor)
            
            return labor_list
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في الحصول على العمالة: {str(e)}")
            raise
    
    def get_tenders(self, category: str = None, region: str = None, limit: int = 100) -> List[Dict]:
        """
        الحصول على المناقصات
        
        المعلمات:
            category (str, optional): فئة المناقصات للتصفية
            region (str, optional): المنطقة للتصفية
            limit (int, optional): الحد الأقصى لعدد النتائج
            
        العائد:
            List[Dict]: قائمة بالمناقصات
        """
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT * FROM tenders"
            params = []
            
            # إضافة شروط التصفية
            conditions = []
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if region:
                conditions.append("region = ?")
                params.append(region)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY created_at DESC LIMIT {limit}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # تحويل الصفوف إلى قواميس
            tenders_list = []
            for row in rows:
                tender = dict(row)
                tenders_list.append(tender)
            
            return tenders_list
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في الحصول على المناقصات: {str(e)}")
            raise
    
    def get_subcontractors(self, category: str = None, region: str = None, limit: int = 100) -> List[Dict]:
        """
        الحصول على مقاولي الباطن
        
        المعلمات:
            category (str, optional): فئة مقاولي الباطن للتصفية
            region (str, optional): المنطقة للتصفية
            limit (int, optional): الحد الأقصى لعدد النتائج
            
        العائد:
            List[Dict]: قائمة بمقاولي الباطن
        """
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT * FROM subcontractors"
            params = []
            
            # إضافة شروط التصفية
            conditions = []
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if region:
                conditions.append("region = ?")
                params.append(region)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY created_at DESC LIMIT {limit}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # تحويل الصفوف إلى قواميس
            subcontractors_list = []
            for row in rows:
                subcontractor = dict(row)
                
                # تحويل الخدمات من JSON إلى قائمة أو قاموس
                if 'services' in subcontractor and subcontractor['services']:
                    try:
                        subcontractor['services'] = json.loads(subcontractor['services'])
                    except json.JSONDecodeError:
                        pass
                
                # تحويل الأسعار من JSON إلى قاموس
                if 'rates' in subcontractor and subcontractor['rates']:
                    try:
                        subcontractor['rates'] = json.loads(subcontractor['rates'])
                    except json.JSONDecodeError:
                        pass
                
                subcontractors_list.append(subcontractor)
            
            return subcontractors_list
        
        except sqlite3.Error as e:
            logger.error(f"خطأ في الحصول على مقاولي الباطن: {str(e)}")
            raise
    
    def export_data(self, table_name: str, format: str = 'json', 
                   filters: Dict = None) -> Tuple[str, str]:
        """
        تصدير البيانات من جدول معين
        
        المعلمات:
            table_name (str): اسم الجدول
            format (str, optional): تنسيق التصدير (json، csv، excel)
            filters (Dict, optional): شروط التصفية
            
        العائد:
            Tuple[str, str]: مسار الملف المصدر ونوع الملف
        """
        try:
            # التحقق من وجود الجدول
            valid_tables = [
                'research_projects', 'research_sources', 'extracted_data',
                'verified_facts', 'entities', 'entity_relationships',
                'research_events', 'research_results', 'visualizations',
                'materials', 'equipment', 'labor', 'tenders', 'subcontractors'
            ]
            
            if table_name not in valid_tables:
                raise ValueError(f"جدول غير صالح: {table_name}")
            
            # بناء استعلام SQL
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # تنفيذ الاستعلام
            df = pd.read_sql_query(query, self.conn, params=params)
            
            # إنشاء مجلد للتصدير إذا لم يكن موجوداً
            os.makedirs('exports', exist_ok=True)
            
            # تصدير البيانات
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exports/{table_name}_{timestamp}"
            
            if format.lower() == 'json':
                file_path = filename + '.json'
                df.to_json(file_path, orient='records', force_ascii=False, indent=4)
                file_type = 'application/json'
            
            elif format.lower() == 'csv':
                file_path = filename + '.csv'
                df.to_csv(file_path, index=False, encoding='utf-8')
                file_type = 'text/csv'
            
            elif format.lower() == 'excel':
                file_path = filename + '.xlsx'
                df.to_excel(file_path, index=False)
                file_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            else:
                raise ValueError(f"تنسيق غير مدعوم: {format}")
            
            logger.info(f"تم تصدير بيانات {table_name} إلى: {file_path}")
            return file_path, file_type
        
        except Exception as e:
            logger.error(f"خطأ في تصدير البيانات: {str(e)}")
            raise

# ============================================================================
# نظام البث المباشر
# Live Streaming System
# ============================================================================

class ResearchEvent:
    """
    فئة تمثل حدث بحث
    """
    
    def __init__(self, event_type: str, event_data: Dict, timestamp: float = None):
        """
        تهيئة حدث بحث
        
        المعلمات:
            event_type (str): نوع الحدث
            event_data (Dict): بيانات الحدث
            timestamp (float, optional): الطابع الزمني للحدث
        """
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.event_data = event_data
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict:
        """
        تحويل الحدث إلى قاموس
        
        العائد:
            Dict: قاموس يمثل الحدث
        """
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'timestamp': self.timestamp,
            'formatted_time': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        }


class EventFactory:
    """
    مصنع لإنشاء أحداث البحث
    """
    
    @staticmethod
    def create_search_event(query: str, source: str) -> ResearchEvent:
        """
        إنشاء حدث بحث
        
        المعلمات:
            query (str): استعلام البحث
            source (str): مصدر البحث
            
        العائد:
            ResearchEvent: حدث البحث
        """
        return ResearchEvent(
            event_type="search",
            event_data={
                'query': query,
                'source': source
            }
        )
    
    @staticmethod
    def create_data_collection_event(source: str, category: str, items_count: int) -> ResearchEvent:
        """
        إنشاء حدث جمع بيانات
        
        المعلمات:
            source (str): مصدر البيانات
            category (str): فئة البيانات
            items_count (int): عدد العناصر المجمعة
            
        العائد:
            ResearchEvent: حدث جمع البيانات
        """
        return ResearchEvent(
            event_type="data_collection",
            event_data={
                'source': source,
                'category': category,
                'items_count': items_count
            }
        )
    
    @staticmethod
    def create_analysis_event(data_type: str, insight: str) -> ResearchEvent:
        """
        إنشاء حدث تحليل
        
        المعلمات:
            data_type (str): نوع البيانات
            insight (str): الاستنتاج
            
        العائد:
            ResearchEvent: حدث التحليل
        """
        return ResearchEvent(
            event_type="analysis",
            event_data={
                'data_type': data_type,
                'insight': insight
            }
        )
    
    @staticmethod
    def create_verification_event(fact: str, confidence: float, sources: List[str]) -> ResearchEvent:
        """
        إنشاء حدث تحقق
        
        المعلمات:
            fact (str): الحقيقة
            confidence (float): مستوى الثقة
            sources (List[str]): مصادر التحقق
            
        العائد:
            ResearchEvent: حدث التحقق
        """
        return ResearchEvent(
            event_type="verification",
            event_data={
                'fact': fact,
                'confidence': confidence,
                'sources': sources
            }
        )
    
    @staticmethod
    def create_result_event(title: str, content: str, result_type: str) -> ResearchEvent:
        """
        إنشاء حدث نتيجة
        
        المعلمات:
            title (str): عنوان النتيجة
            content (str): محتوى النتيجة
            result_type (str): نوع النتيجة
            
        العائد:
            ResearchEvent: حدث النتيجة
        """
        return ResearchEvent(
            event_type="result",
            event_data={
                'title': title,
                'content': content,
                'result_type': result_type
            }
        )
    
    @staticmethod
    def create_web_crawling_event(url: str, status: str, items_found: int = 0) -> ResearchEvent:
        """
        إنشاء حدث زحف ويب
        
        المعلمات:
            url (str): عنوان URL
            status (str): حالة الزحف
            items_found (int, optional): عدد العناصر المكتشفة
            
        العائد:
            ResearchEvent: حدث زحف الويب
        """
        return ResearchEvent(
            event_type="web_crawling",
            event_data={
                'url': url,
                'status': status,
                'items_found': items_found
            }
        )


class EventCaptureManager:
    """
    مدير التقاط الأحداث
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        تهيئة مدير التقاط الأحداث
        
        المعلمات:
            db_manager (DatabaseManager): مدير قاعدة البيانات
        """
        self.db_manager = db_manager
        self.event_queue = queue.Queue()
        self.event_listeners = []
        self.is_running = False
        self.processing_thread = None
    
    def start(self):
        """
        بدء معالجة الأحداث
        """
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._process_events)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            logger.info("تم بدء مدير التقاط الأحداث")
    
    def stop(self):
        """
        إيقاف معالجة الأحداث
        """
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
            logger.info("تم إيقاف مدير التقاط الأحداث")
    
    def add_event(self, event: ResearchEvent, project_id: int = None):
        """
        إضافة حدث جديد
        
        المعلمات:
            event (ResearchEvent): الحدث
            project_id (int, optional): معرف المشروع
        """
        # إضافة الحدث إلى قائمة الانتظار
        self.event_queue.put((event, project_id))
        
        # إذا كان معرف المشروع متوفراً، أضف الحدث إلى قاعدة البيانات
        if project_id is not None:
            try:
                self.db_manager.add_research_event(
                    project_id=project_id,
                    event_type=event.event_type,
                    event_data=event.event_data
                )
            except Exception as e:
                logger.error(f"خطأ في إضافة الحدث إلى قاعدة البيانات: {str(e)}")
    
    def add_listener(self, listener_func):
        """
        إضافة مستمع للأحداث
        
        المعلمات:
            listener_func: دالة المستمع
        """
        if listener_func not in self.event_listeners:
            self.event_listeners.append(listener_func)
    
    def remove_listener(self, listener_func):
        """
        إزالة مستمع للأحداث
        
        المعلمات:
            listener_func: دالة المستمع
        """
        if listener_func in self.event_listeners:
            self.event_listeners.remove(listener_func)
    
    def _process_events(self):
        """
        معالجة الأحداث في قائمة الانتظار
        """
        while self.is_running:
            try:
                # انتظار حدث جديد
                event, project_id = self.event_queue.get(timeout=1.0)
                
                # إخطار جميع المستمعين
                for listener in self.event_listeners:
                    try:
                        listener(event.to_dict())
                    except Exception as e:
                        logger.error(f"خطأ في معالجة الحدث بواسطة المستمع: {str(e)}")
                
                # تحديد انتهاء معالجة الحدث
                self.event_queue.task_done()
            
            except queue.Empty:
                # لا توجد أحداث في قائمة الانتظار
                pass
            except Exception as e:
                logger.error(f"خطأ في معالجة الأحداث: {str(e)}")


class LiveStreamingSystem:
    """
    نظام البث المباشر
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        تهيئة نظام البث المباشر
        
        المعلمات:
            db_manager (DatabaseManager): مدير قاعدة البيانات
        """
        self.db_manager = db_manager
        self.event_manager = EventCaptureManager(db_manager)
        self.event_manager.start()
        self.event_history = []
        self.max_history_size = 100
        
        # إضافة مستمع لحفظ الأحداث في التاريخ
        self.event_manager.add_listener(self._store_event_in_history)
        
        logger.info("تم تهيئة نظام البث المباشر")
    
    def _store_event_in_history(self, event_dict: Dict):
        """
        تخزين الحدث في التاريخ
        
        المعلمات:
            event_dict (Dict): قاموس الحدث
        """
        self.event_history.append(event_dict)
        
        # الحفاظ على حجم التاريخ ضمن الحد الأقصى
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
    
    def add_event(self, event: ResearchEvent, project_id: int = None):
        """
        إضافة حدث جديد
        
        المعلمات:
            event (ResearchEvent): الحدث
            project_id (int, optional): معرف المشروع
        """
        self.event_manager.add_event(event, project_id)
    
    def add_listener(self, listener_func):
        """
        إضافة مستمع للأحداث
        
        المعلمات:
            listener_func: دالة المستمع
        """
        self.event_manager.add_listener(listener_func)
    
    def remove_listener(self, listener_func):
        """
        إزالة مستمع للأحداث
        
        المعلمات:
            listener_func: دالة المستمع
        """
        self.event_manager.remove_listener(listener_func)
    
    def get_event_history(self) -> List[Dict]:
        """
        الحصول على تاريخ الأحداث
        
        العائد:
            List[Dict]: قائمة بالأحداث
        """
        return self.event_history
    
    def clear_event_history(self):
        """
        مسح تاريخ الأحداث
        """
        self.event_history = []
    
    def shutdown(self):
        """
        إيقاف نظام البث المباشر
        """
        self.event_manager.stop()
        logger.info("تم إيقاف نظام البث المباشر")


# ============================================================================
# نظام البحث متعدد الوكلاء
# Multi-Agent Research System
# ============================================================================

class ResearchAgent:
    """
    فئة أساسية للوكلاء البحثية
    """
    
    def __init__(self, agent_id: str, agent_name: str, live_system: LiveStreamingSystem):
        """
        تهيئة الوكيل البحثي
        
        المعلمات:
            agent_id (str): معرف الوكيل
            agent_name (str): اسم الوكيل
            live_system (LiveStreamingSystem): نظام البث المباشر
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.live_system = live_system
        logger.info(f"تم تسجيل الوكيل: {agent_id} ({agent_name})")
    
    def add_event(self, event: ResearchEvent, project_id: int = None):
        """
        إضافة حدث جديد
        
        المعلمات:
            event (ResearchEvent): الحدث
            project_id (int, optional): معرف المشروع
        """
        self.live_system.add_event(event, project_id)


class WebResearchAgent(ResearchAgent):
    """
    وكيل البحث على الويب
    """
    
    def __init__(self, live_system: LiveStreamingSystem, data_collector: DataCollector):
        """
        تهيئة وكيل البحث على الويب
        
        المعلمات:
            live_system (LiveStreamingSystem): نظام البث المباشر
            data_collector (DataCollector): جامع البيانات
        """
        super().__init__("web_research", "وكيل البحث على الويب", live_system)
        self.data_collector = data_collector
    
    def search(self, query: str, source: str) -> Dict:
        """
        إجراء بحث
        
        المعلمات:
            query (str): استعلام البحث
            source (str): مصدر البحث
            
        العائد:
            Dict: نتائج البحث
        """
        # إنشاء حدث بحث
        search_event = EventFactory.create_search_event(query, source)
        self.add_event(search_event)
        
        # محاكاة البحث
        time.sleep(1.0)
        
        # إنشاء نتائج وهمية
        results = {
            'query': query,
            'source': source,
            'results': [
                {'title': f'نتيجة 1 لـ {query}', 'url': 'https://example.com/1'},
                {'title': f'نتيجة 2 لـ {query}', 'url': 'https://example.com/2'},
                {'title': f'نتيجة 3 لـ {query}', 'url': 'https://example.com/3'},
            ]
        }
        
        # إنشاء حدث نتيجة
        result_event = EventFactory.create_result_event(
            title=f"نتائج البحث عن {query}",
            content=json.dumps(results, ensure_ascii=False),
            result_type="search_results"
        )
        self.add_event(result_event)
        
        return results
    
    def collect_data(self, category: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        جمع البيانات
        
        المعلمات:
            category (str, optional): فئة البيانات
            
        العائد:
            Dict[str, List[Dict[str, Any]]]: البيانات المجمعة
        """
        # إنشاء حدث جمع بيانات
        collection_event = EventFactory.create_data_collection_event(
            source="data_collector",
            category=category or "all",
            items_count=0
        )
        self.add_event(collection_event)
        
        # جمع البيانات الفعلية
        collected_data = self.data_collector.collect_data(category)
        
        # تحديث حدث جمع البيانات بعدد العناصر المجمعة
        total_items = sum(len(items) for items in collected_data.values())
        updated_collection_event = EventFactory.create_data_collection_event(
            source="data_collector",
            category=category or "all",
            items_count=total_items
        )
        self.add_event(updated_collection_event)
        
        # إنشاء أحداث زحف ويب لكل مصدر
        for cat, items in collected_data.items():
            if items:
                for source_name in set(item.get('source', 'unknown') for item in items if 'source' in item):
                    source_items = [item for item in items if item.get('source') == source_name]
                    if source_items:
                        crawling_event = EventFactory.create_web_crawling_event(
                            url=source_name,
                            status="completed",
                            items_found=len(source_items)
                        )
                        self.add_event(crawling_event)
        
        return collected_data


class ContentAnalyzerAgent(ResearchAgent):
    """
    وكيل تحليل المحتوى
    """
    
    def __init__(self, live_system: LiveStreamingSystem):
        """
        تهيئة وكيل تحليل المحتوى
        
        المعلمات:
            live_system (LiveStreamingSystem): نظام البث المباشر
        """
        super().__init__("content_analyzer", "وكيل تحليل المحتوى", live_system)
    
    def analyze(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """
        تحليل البيانات
        
        المعلمات:
            data (Dict[str, Any]): البيانات المراد تحليلها
            data_type (str): نوع البيانات
            
        العائد:
            Dict[str, Any]: نتائج التحليل
        """
        # إنشاء حدث تحليل
        analysis_event = EventFactory.create_analysis_event(
            data_type=data_type,
            insight="جاري تحليل البيانات..."
        )
        self.add_event(analysis_event)
        
        # محاكاة التحليل
        time.sleep(1.5)
        
        # إنشاء نتائج تحليل وهمية
        if data_type == "materials":
            analysis_results = self._analyze_materials(data)
        elif data_type == "equipment":
            analysis_results = self._analyze_equipment(data)
        elif data_type == "labor":
            analysis_results = self._analyze_labor(data)
        else:
            analysis_results = {
                'summary': f"تحليل {len(data)} عنصر من نوع {data_type}",
                'insights': [
                    f"استنتاج 1 حول {data_type}",
                    f"استنتاج 2 حول {data_type}",
                    f"استنتاج 3 حول {data_type}"
                ]
            }
        
        # إنشاء حدث تحليل محدث
        updated_analysis_event = EventFactory.create_analysis_event(
            data_type=data_type,
            insight=json.dumps(analysis_results, ensure_ascii=False)
        )
        self.add_event(updated_analysis_event)
        
        return analysis_results
    
    def _analyze_materials(self, materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        تحليل بيانات مواد البناء
        
        المعلمات:
            materials (List[Dict[str, Any]]): بيانات مواد البناء
            
        العائد:
            Dict[str, Any]: نتائج التحليل
        """
        if not materials:
            return {
                'summary': "لا توجد بيانات مواد بناء للتحليل",
                'insights': []
            }
        
        # تحليل الفئات
        categories = {}
        for material in materials:
            category = material.get('category', 'غير معروف')
            if category in categories:
                categories[category] += 1
            else:
                categories[category] = 1
        
        # تحليل الأسعار
        prices = [material.get('price') for material in materials if material.get('price') is not None]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        # تحليل المناطق
        regions = {}
        for material in materials:
            region = material.get('region', 'غير معروف')
            if region in regions:
                regions[region] += 1
            else:
                regions[region] = 1
        
        return {
            'summary': f"تحليل {len(materials)} مادة بناء",
            'categories': categories,
            'avg_price': avg_price,
            'regions': regions,
            'insights': [
                f"متوسط سعر المواد: {avg_price:.2f} ريال",
                f"أكثر فئة شيوعاً: {max(categories.items(), key=lambda x: x[1])[0]}",
                f"أكثر منطقة تواجداً: {max(regions.items(), key=lambda x: x[1])[0]}"
            ]
        }
    
    def _analyze_equipment(self, equipment: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        تحليل بيانات المعدات
        
        المعلمات:
            equipment (List[Dict[str, Any]]): بيانات المعدات
            
        العائد:
            Dict[str, Any]: نتائج التحليل
        """
        if not equipment:
            return {
                'summary': "لا توجد بيانات معدات للتحليل",
                'insights': []
            }
        
        # تحليل الفئات
        categories = {}
        for item in equipment:
            category = item.get('category', 'غير معروف')
            if category in categories:
                categories[category] += 1
            else:
                categories[category] = 1
        
        # تحليل الأسعار
        prices = [item.get('price') for item in equipment if item.get('price') is not None]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        return {
            'summary': f"تحليل {len(equipment)} معدة",
            'categories': categories,
            'avg_price': avg_price,
            'insights': [
                f"متوسط سعر المعدات: {avg_price:.2f} ريال",
                f"أكثر فئة شيوعاً: {max(categories.items(), key=lambda x: x[1])[0] if categories else 'غير متوفر'}"
            ]
        }
    
    def _analyze_labor(self, labor: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        تحليل بيانات العمالة
        
        المعلمات:
            labor (List[Dict[str, Any]]): بيانات العمالة
            
        العائد:
            Dict[str, Any]: نتائج التحليل
        """
        if not labor:
            return {
                'summary': "لا توجد بيانات عمالة للتحليل",
                'insights': []
            }
        
        # تحليل الفئات
        categories = {}
        for item in labor:
            category = item.get('category', 'غير معروف')
            if category in categories:
                categories[category] += 1
            else:
                categories[category] = 1
        
        # تحليل الرواتب
        salaries = [item.get('salary') for item in labor if item.get('salary') is not None]
        avg_salary = sum(salaries) / len(salaries) if salaries else 0
        
        return {
            'summary': f"تحليل {len(labor)} عامل",
            'categories': categories,
            'avg_salary': avg_salary,
            'insights': [
                f"متوسط الراتب: {avg_salary:.2f} ريال",
                f"أكثر فئة شيوعاً: {max(categories.items(), key=lambda x: x[1])[0] if categories else 'غير متوفر'}"
            ]
        }


class FactCheckerAgent(ResearchAgent):
    """
    وكيل التحقق من الحقائق
    """
    
    def __init__(self, live_system: LiveStreamingSystem):
        """
        تهيئة وكيل التحقق من الحقائق
        
        المعلمات:
            live_system (LiveStreamingSystem): نظام البث المباشر
        """
        super().__init__("fact_checker", "وكيل التحقق من الحقائق", live_system)
    
    def verify(self, fact: str, sources: List[str]) -> Dict[str, Any]:
        """
        التحقق من حقيقة
        
        المعلمات:
            fact (str): الحقيقة المراد التحقق منها
            sources (List[str]): مصادر التحقق
            
        العائد:
            Dict[str, Any]: نتائج التحقق
        """
        # إنشاء حدث تحقق
        verification_event = EventFactory.create_verification_event(
            fact=fact,
            confidence=0.0,
            sources=sources
        )
        self.add_event(verification_event)
        
        # محاكاة التحقق
        time.sleep(2.0)
        
        # إنشاء نتائج تحقق وهمية
        confidence = random.uniform(0.7, 1.0)
        
        # إنشاء حدث تحقق محدث
        updated_verification_event = EventFactory.create_verification_event(
            fact=fact,
            confidence=confidence,
            sources=sources
        )
        self.add_event(updated_verification_event)
        
        return {
            'fact': fact,
            'confidence': confidence,
            'sources': sources,
            'verified': confidence > 0.8,
            'verification_details': {
                'method': 'cross-reference',
                'source_reliability': random.uniform(0.6, 1.0),
                'consistency': random.uniform(0.7, 1.0)
            }
        }


# ============================================================================
# واجهة المستخدم
# User Interface
# ============================================================================

class GradioInterface:
    """
    واجهة المستخدم باستخدام Gradio
    """
    
    def __init__(self, db_manager: DatabaseManager, live_system: LiveStreamingSystem,
                data_collector: DataCollector, web_agent: WebResearchAgent,
                content_agent: ContentAnalyzerAgent, fact_agent: FactCheckerAgent):
        """
        تهيئة واجهة المستخدم
        
        المعلمات:
            db_manager (DatabaseManager): مدير قاعدة البيانات
            live_system (LiveStreamingSystem): نظام البث المباشر
            data_collector (DataCollector): جامع البيانات
            web_agent (WebResearchAgent): وكيل البحث على الويب
            content_agent (ContentAnalyzerAgent): وكيل تحليل المحتوى
            fact_agent (FactCheckerAgent): وكيل التحقق من الحقائق
        """
        self.db_manager = db_manager
        self.live_system = live_system
        self.data_collector = data_collector
        self.web_agent = web_agent
        self.content_agent = content_agent
        self.fact_agent = fact_agent
        
        # قائمة الأحداث المباشرة
        self.live_events = []
        
        # إضافة مستمع للأحداث
        self.live_system.add_listener(self._update_live_events)
        
        # المشروع الحالي
        self.current_project_id = None
        
        # إنشاء واجهة Gradio
        self.interface = self._create_interface()
    
    def _update_live_events(self, event_dict: Dict):
        """
        تحديث قائمة الأحداث المباشرة
        
        المعلمات:
            event_dict (Dict): قاموس الحدث
        """
        self.live_events.append(event_dict)
        
        # الحفاظ على حجم قائمة الأحداث ضمن الحد الأقصى
        if len(self.live_events) > 100:
            self.live_events = self.live_events[-100:]
    
    def _format_events_for_display(self) -> str:
        """
        تنسيق الأحداث للعرض
        
        العائد:
            str: نص الأحداث المنسق
        """
        if not self.live_events:
            return "لا توجد أحداث حتى الآن."
        
        events_text = ""
        for event in reversed(self.live_events):
            event_time = event.get('formatted_time', '')
            event_type = event.get('event_type', '')
            event_data = event.get('event_data', {})
            
            # تنسيق النص حسب نوع الحدث
            if event_type == 'search':
                events_text += f"[{event_time}] 🔍 بحث: {event_data.get('query', '')} في {event_data.get('source', '')}\n"
            
            elif event_type == 'data_collection':
                events_text += f"[{event_time}] 📊 جمع بيانات: {event_data.get('items_count', 0)} عنصر من فئة {event_data.get('category', '')} من {event_data.get('source', '')}\n"
            
            elif event_type == 'analysis':
                events_text += f"[{event_time}] 🧠 تحليل: {event_data.get('data_type', '')}\n"
            
            elif event_type == 'verification':
                confidence = event_data.get('confidence', 0) * 100
                events_text += f"[{event_time}] ✓ تحقق: {event_data.get('fact', '')} (الثقة: {confidence:.1f}%)\n"
            
            elif event_type == 'result':
                events_text += f"[{event_time}] 📝 نتيجة: {event_data.get('title', '')}\n"
            
            elif event_type == 'web_crawling':
                events_text += f"[{event_time}] 🕸️ زحف ويب: {event_data.get('url', '')} - {event_data.get('status', '')} ({event_data.get('items_found', 0)} عنصر)\n"
            
            else:
                events_text += f"[{event_time}] حدث: {event_type}\n"
        
        return events_text
    
    def _create_project(self, title: str, description: str) -> int:
        """
        إنشاء مشروع جديد
        
        المعلمات:
            title (str): عنوان المشروع
            description (str): وصف المشروع
            
        العائد:
            int: معرف المشروع الجديد
        """
        if not title:
            return "يجب إدخال عنوان للمشروع", None
        
        try:
            project_id = self.db_manager.create_project(title, description)
            self.current_project_id = project_id
            return f"تم إنشاء المشروع بنجاح (المعرف: {project_id})", project_id
        except Exception as e:
            return f"خطأ في إنشاء المشروع: {str(e)}", None
    
    def _collect_materials_data(self, category: str = None) -> str:
        """
        جمع بيانات مواد البناء
        
        المعلمات:
            category (str, optional): فئة مواد البناء
            
        العائد:
            str: رسالة النتيجة
        """
        try:
            # جمع البيانات
            collected_data = self.web_agent.collect_data("materials")
            
            if "materials" not in collected_data or not collected_data["materials"]:
                return "لم يتم العثور على بيانات مواد بناء."
            
            # حفظ البيانات في قاعدة البيانات
            materials = collected_data["materials"]
            for material in materials:
                self.db_manager.add_material(material)
            
            # تحليل البيانات
            analysis_results = self.content_agent.analyze(materials, "materials")
            
            return f"تم جمع وتحليل {len(materials)} مادة بناء بنجاح."
        
        except Exception as e:
            return f"خطأ في جمع بيانات مواد البناء: {str(e)}"
    
    def _search_materials(self, category: str = None, region: str = None) -> Tuple[str, pd.DataFrame]:
        """
        البحث عن مواد البناء
        
        المعلمات:
            category (str, optional): فئة مواد البناء للتصفية
            region (str, optional): المنطقة للتصفية
            
        العائد:
            Tuple[str, pd.DataFrame]: رسالة النتيجة وإطار البيانات
        """
        try:
            # البحث في قاعدة البيانات
            materials = self.db_manager.get_materials(category, region)
            
            if not materials:
                return "لم يتم العثور على مواد بناء تطابق معايير البحث.", pd.DataFrame()
            
            # إنشاء إطار بيانات
            df = pd.DataFrame(materials)
            
            # تحديد الأعمدة المهمة للعرض
            display_columns = ['name', 'category', 'price', 'price_text', 'currency', 'unit', 'city', 'region', 'availability']
            display_df = df[display_columns] if all(col in df.columns for col in display_columns) else df
            
            return f"تم العثور على {len(materials)} مادة بناء.", display_df
        
        except Exception as e:
            return f"خطأ في البحث عن مواد البناء: {str(e)}", pd.DataFrame()
    
    def _export_data(self, table_name: str, format: str) -> Tuple[str, str, str]:
        """
        تصدير البيانات
        
        المعلمات:
            table_name (str): اسم الجدول
            format (str): تنسيق التصدير
            
        العائد:
            Tuple[str, str, str]: رسالة النتيجة ومسار الملف ونوع الملف
        """
        try:
            # التحقق من صحة المدخلات
            valid_tables = [
                'materials', 'equipment', 'labor', 'tenders', 'subcontractors',
                'research_projects', 'research_sources', 'research_events'
            ]
            
            if table_name not in valid_tables:
                return f"جدول غير صالح: {table_name}", "", ""
            
            valid_formats = ['json', 'csv', 'excel']
            if format not in valid_formats:
                return f"تنسيق غير صالح: {format}", "", ""
            
            # تصدير البيانات
            file_path, file_type = self.db_manager.export_data(table_name, format)
            
            return f"تم تصدير البيانات بنجاح إلى: {file_path}", file_path, file_type
        
        except Exception as e:
            return f"خطأ في تصدير البيانات: {str(e)}", "", ""
    
    def _create_visualization(self, data_type: str) -> Tuple[str, str]:
        """
        إنشاء تصور مرئي
        
        المعلمات:
            data_type (str): نوع البيانات
            
        العائد:
            Tuple[str, str]: رسالة النتيجة وصورة التصور المرئي
        """
        try:
            # الحصول على البيانات
            if data_type == 'materials':
                data = self.db_manager.get_materials()
            elif data_type == 'equipment':
                data = self.db_manager.get_equipment()
            elif data_type == 'labor':
                data = self.db_manager.get_labor()
            else:
                return f"نوع بيانات غير مدعوم: {data_type}", ""
            
            if not data:
                return f"لا توجد بيانات من نوع {data_type} لإنشاء تصور مرئي.", ""
            
            # إنشاء تصور مرئي
            plt.figure(figsize=(10, 6))
            
            if data_type == 'materials':
                # تصور مرئي لفئات مواد البناء
                categories = {}
                for item in data:
                    category = item.get('category', 'غير معروف')
                    if category in categories:
                        categories[category] += 1
                    else:
                        categories[category] = 1
                
                plt.bar(categories.keys(), categories.values())
                plt.title('توزيع فئات مواد البناء')
                plt.xlabel('الفئة')
                plt.ylabel('العدد')
                plt.xticks(rotation=45)
            
            elif data_type == 'equipment':
                # تصور مرئي لفئات المعدات
                categories = {}
                for item in data:
                    category = item.get('category', 'غير معروف')
                    if category in categories:
                        categories[category] += 1
                    else:
                        categories[category] = 1
                
                plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
                plt.title('توزيع فئات المعدات')
            
            elif data_type == 'labor':
                # تصور مرئي لفئات العمالة
                categories = {}
                for item in data:
                    category = item.get('category', 'غير معروف')
                    if category in categories:
                        categories[category] += 1
                    else:
                        categories[category] = 1
                
                plt.barh(list(categories.keys()), list(categories.values()))
                plt.title('توزيع فئات العمالة')
                plt.xlabel('العدد')
                plt.ylabel('الفئة')
            
            # حفظ التصور المرئي كصورة
            img_buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(img_buffer, format='png')
            img_buffer.seek(0)
            img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
            plt.close()
            
            return f"تم إنشاء تصور مرئي لبيانات {data_type} بنجاح.", f"data:image/png;base64,{img_data}"
        
        except Exception as e:
            return f"خطأ في إنشاء التصور المرئي: {str(e)}", ""
    
    def _simulate_research(self, agent_id: str, action: str, params: str) -> str:
        """
        محاكاة البحث
        
        المعلمات:
            agent_id (str): معرف الوكيل
            action (str): الإجراء
            params (str): معلمات الإجراء
            
        العائد:
            str: رسالة النتيجة
        """
        try:
            # التحقق من صحة المدخلات
            if not agent_id or not action:
                return "يجب تحديد الوكيل والإجراء."
            
            # تنفيذ الإجراء حسب الوكيل
            if agent_id == "web_research":
                if action == "search":
                    query, source = params.split(',') if ',' in params else (params, "web")
                    self.web_agent.search(query.strip(), source.strip())
                    return f"تم تنفيذ البحث عن '{query}' في '{source}' بنجاح."
                
                elif action == "collect_data":
                    category = params.strip() if params else None
                    collected_data = self.web_agent.collect_data(category)
                    total_items = sum(len(items) for items in collected_data.values())
                    return f"تم جمع {total_items} عنصر من البيانات بنجاح."
                
                else:
                    return f"إجراء غير معروف للوكيل {agent_id}: {action}"
            
            elif agent_id == "content_analyzer":
                if action == "analyze":
                    data_type, data_count = params.split(',') if ',' in params else (params, "10")
                    try:
                        data_count = int(data_count.strip())
                    except ValueError:
                        data_count = 10
                    
                    # الحصول على البيانات للتحليل
                    if data_type.strip() == "materials":
                        data = self.db_manager.get_materials(limit=data_count)
                    elif data_type.strip() == "equipment":
                        data = self.db_manager.get_equipment(limit=data_count)
                    elif data_type.strip() == "labor":
                        data = self.db_manager.get_labor(limit=data_count)
                    else:
                        data = []
                    
                    if not data:
                        return f"لا توجد بيانات من نوع {data_type} للتحليل."
                    
                    self.content_agent.analyze(data, data_type.strip())
                    return f"تم تحليل {len(data)} عنصر من نوع {data_type} بنجاح."
                
                else:
                    return f"إجراء غير معروف للوكيل {agent_id}: {action}"
            
            elif agent_id == "fact_checker":
                if action == "verify":
                    fact, sources = params.split('|') if '|' in params else (params, "source1,source2")
                    sources_list = [s.strip() for s in sources.split(',')]
                    self.fact_agent.verify(fact.strip(), sources_list)
                    return f"تم التحقق من الحقيقة '{fact}' بنجاح."
                
                else:
                    return f"إجراء غير معروف للوكيل {agent_id}: {action}"
            
            else:
                return f"وكيل غير معروف: {agent_id}"
        
        except Exception as e:
            return f"خطأ في محاكاة البحث: {str(e)}"
    
    def _create_interface(self):
        """
        إنشاء واجهة Gradio
        
        العائد:
            gr.Blocks: واجهة Gradio
        """
        with gr.Blocks(title="نظام البحث متعدد الوكلاء مع إطار عمل جمع البيانات") as interface:
            gr.Markdown("# نظام البحث متعدد الوكلاء مع إطار عمل جمع البيانات")
            
            with gr.Tabs() as tabs:
                # علامة تبويب البث المباشر
                with gr.TabItem("البث المباشر", id=0):
                    with gr.Row():
                        with gr.Column(scale=2):
                            live_stream_output = gr.Textbox(
                                label="بث الأحداث المباشرة",
                                value="جاري تحميل الأحداث...",
                                lines=20,
                                max_lines=30,
                                interactive=False
                            )
                            
                            refresh_btn = gr.Button("تحديث البث")
                            
                            def refresh_live_stream():
                                return self._format_events_for_display()
                            
                            refresh_btn.click(
                                fn=refresh_live_stream,
                                outputs=live_stream_output
                            )
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### إحصائيات البث")
                            
                            event_stats = gr.JSON(
                                label="إحصائيات الأحداث",
                                value={"جاري التحميل": "..."}
                            )
                            
                            def get_event_stats():
                                if not self.live_events:
                                    return {"لا توجد أحداث": "0"}
                                
                                stats = {}
                                for event in self.live_events:
                                    event_type = event.get('event_type', 'غير معروف')
                                    if event_type in stats:
                                        stats[event_type] += 1
                                    else:
                                        stats[event_type] = 1
                                
                                return stats
                            
                            refresh_btn.click(
                                fn=get_event_stats,
                                outputs=event_stats
                            )
                
                # علامة تبويب جمع البيانات
                with gr.TabItem("جمع البيانات", id=1):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### جمع بيانات مواد البناء")
                            
                            materials_category = gr.Dropdown(
                                label="فئة مواد البناء",
                                choices=["الكل", "أسمنت", "حديد", "رمل", "بلوك", "طوب", "بلاط", "سيراميك", "عوازل", "أنابيب", "دهانات"],
                                value="الكل"
                            )
                            
                            collect_materials_btn = gr.Button("جمع بيانات مواد البناء")
                            
                            materials_result = gr.Textbox(
                                label="نتيجة جمع البيانات",
                                lines=3,
                                interactive=False
                            )
                            
                            def collect_materials(category):
                                if category == "الكل":
                                    category = None
                                return self._collect_materials_data(category)
                            
                            collect_materials_btn.click(
                                fn=collect_materials,
                                inputs=materials_category,
                                outputs=materials_result
                            )
                    
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### البحث في البيانات المجمعة")
                            
                            search_category = gr.Dropdown(
                                label="فئة البحث",
                                choices=["مواد البناء", "المعدات", "العمالة", "المناقصات", "مقاولي الباطن"],
                                value="مواد البناء"
                            )
                            
                            search_filter = gr.Textbox(
                                label="فلتر البحث (فئة أو منطقة)",
                                placeholder="اترك فارغاً للبحث في جميع الفئات والمناطق"
                            )
                            
                            search_btn = gr.Button("بحث")
                            
                            search_result = gr.Textbox(
                                label="نتيجة البحث",
                                lines=2,
                                interactive=False
                            )
                            
                            search_data = gr.Dataframe(
                                label="نتائج البحث",
                                interactive=False
                            )
                            
                            def search_data_fn(category, filter_text):
                                if category == "مواد البناء":
                                    return self._search_materials(filter_text if filter_text else None, None)
                                else:
                                    return f"البحث في {category} غير مدعوم حالياً.", pd.DataFrame()
                            
                            search_btn.click(
                                fn=search_data_fn,
                                inputs=[search_category, search_filter],
                                outputs=[search_result, search_data]
                            )
                    
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### تصدير البيانات")
                            
                            export_table = gr.Dropdown(
                                label="جدول التصدير",
                                choices=["materials", "equipment", "labor", "tenders", "subcontractors", "research_projects", "research_events"],
                                value="materials"
                            )
                            
                            export_format = gr.Dropdown(
                                label="تنسيق التصدير",
                                choices=["json", "csv", "excel"],
                                value="json"
                            )
                            
                            export_btn = gr.Button("تصدير")
                            
                            export_result = gr.Textbox(
                                label="نتيجة التصدير",
                                lines=2,
                                interactive=False
                            )
                            
                            export_file = gr.File(
                                label="الملف المصدر",
                                interactive=False
                            )
                            
                            def export_data_fn(table, format):
                                result, file_path, file_type = self._export_data(table, format)
                                return result, file_path
                            
                            export_btn.click(
                                fn=export_data_fn,
                                inputs=[export_table, export_format],
                                outputs=[export_result, export_file]
                            )
                
                # علامة تبويب التحليل والتصور
                with gr.TabItem("التحليل والتصور", id=2):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### تحليل البيانات")
                            
                            analysis_type = gr.Dropdown(
                                label="نوع البيانات للتحليل",
                                choices=["materials", "equipment", "labor"],
                                value="materials"
                            )
                            
                            analyze_btn = gr.Button("تحليل")
                            
                            analysis_result = gr.Textbox(
                                label="نتيجة التحليل",
                                lines=2,
                                interactive=False
                            )
                            
                            def analyze_data(data_type):
                                # الحصول على البيانات للتحليل
                                if data_type == "materials":
                                    data = self.db_manager.get_materials()
                                elif data_type == "equipment":
                                    data = self.db_manager.get_equipment()
                                elif data_type == "labor":
                                    data = self.db_manager.get_labor()
                                else:
                                    data = []
                                
                                if not data:
                                    return f"لا توجد بيانات من نوع {data_type} للتحليل."
                                
                                analysis_results = self.content_agent.analyze(data, data_type)
                                return f"تم تحليل {len(data)} عنصر من نوع {data_type} بنجاح.\n\nالاستنتاجات: {', '.join(analysis_results.get('insights', []))}"
                            
                            analyze_btn.click(
                                fn=analyze_data,
                                inputs=analysis_type,
                                outputs=analysis_result
                            )
                    
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### التصور المرئي")
                            
                            visualization_type = gr.Dropdown(
                                label="نوع البيانات للتصور",
                                choices=["materials", "equipment", "labor"],
                                value="materials"
                            )
                            
                            visualize_btn = gr.Button("إنشاء تصور مرئي")
                            
                            visualization_result = gr.Textbox(
                                label="نتيجة التصور",
                                lines=2,
                                interactive=False
                            )
                            
                            visualization_image = gr.Image(
                                label="التصور المرئي",
                                type="pil",
                                interactive=False
                            )
                            
                            def create_visualization(data_type):
                                return self._create_visualization(data_type)
                            
                            visualize_btn.click(
                                fn=create_visualization,
                                inputs=visualization_type,
                                outputs=[visualization_result, visualization_image]
                            )
                
                # علامة تبويب محاكاة البحث
                with gr.TabItem("محاكاة البحث", id=3):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### محاكاة عمليات البحث")
                            
                            agent_id = gr.Dropdown(
                                label="الوكيل",
                                choices=["web_research", "content_analyzer", "fact_checker"],
                                value="web_research"
                            )
                            
                            action = gr.Dropdown(
                                label="الإجراء",
                                choices=["search", "collect_data", "analyze", "verify"],
                                value="search"
                            )
                            
                            params = gr.Textbox(
                                label="المعلمات",
                                placeholder="أدخل معلمات الإجراء (مثال: للبحث: استعلام البحث,المصدر)"
                            )
                            
                            simulate_btn = gr.Button("تنفيذ")
                            
                            simulation_result = gr.Textbox(
                                label="نتيجة المحاكاة",
                                lines=3,
                                interactive=False
                            )
                            
                            def update_action_choices(agent):
                                if agent == "web_research":
                                    return gr.Dropdown.update(choices=["search", "collect_data"])
                                elif agent == "content_analyzer":
                                    return gr.Dropdown.update(choices=["analyze"])
                                elif agent == "fact_checker":
                                    return gr.Dropdown.update(choices=["verify"])
                                else:
                                    return gr.Dropdown.update(choices=[])
                            
                            agent_id.change(
                                fn=update_action_choices,
                                inputs=agent_id,
                                outputs=action
                            )
                            
                            def update_params_placeholder(agent, action):
                                if agent == "web_research":
                                    if action == "search":
                                        return gr.Textbox.update(placeholder="استعلام البحث,المصدر (مثال: أسعار الأسمنت,web)")
                                    elif action == "collect_data":
                                        return gr.Textbox.update(placeholder="فئة البيانات (اترك فارغاً لجمع جميع الفئات)")
                                
                                elif agent == "content_analyzer":
                                    if action == "analyze":
                                        return gr.Textbox.update(placeholder="نوع البيانات,عدد العناصر (مثال: materials,10)")
                                
                                elif agent == "fact_checker":
                                    if action == "verify":
                                        return gr.Textbox.update(placeholder="الحقيقة|المصدر1,المصدر2 (مثال: سعر الأسمنت في الرياض 300 ريال|موقع1,موقع2)")
                                
                                return gr.Textbox.update(placeholder="أدخل معلمات الإجراء")
                            
                            action.change(
                                fn=update_params_placeholder,
                                inputs=[agent_id, action],
                                outputs=params
                            )
                            
                            def simulate_research(agent, action, params):
                                return self._simulate_research(agent, action, params)
                            
                            simulate_btn.click(
                                fn=simulate_research,
                                inputs=[agent_id, action, params],
                                outputs=simulation_result
                            )
                
                # علامة تبويب إدارة المشاريع
                with gr.TabItem("إدارة المشاريع", id=4):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### إنشاء مشروع جديد")
                            
                            project_title = gr.Textbox(
                                label="عنوان المشروع",
                                placeholder="أدخل عنوان المشروع"
                            )
                            
                            project_description = gr.Textbox(
                                label="وصف المشروع",
                                placeholder="أدخل وصف المشروع",
                                lines=3
                            )
                            
                            create_project_btn = gr.Button("إنشاء مشروع")
                            
                            project_result = gr.Textbox(
                                label="نتيجة إنشاء المشروع",
                                lines=2,
                                interactive=False
                            )
                            
                            def create_project(title, description):
                                result, project_id = self._create_project(title, description)
                                return result
                            
                            create_project_btn.click(
                                fn=create_project,
                                inputs=[project_title, project_description],
                                outputs=project_result
                            )
            
            # تحديث البث المباشر تلقائياً عند فتح الواجهة
            interface.load(
                fn=refresh_live_stream,
                outputs=live_stream_output
            )
            
            interface.load(
                fn=get_event_stats,
                outputs=event_stats
            )
        
        return interface
    
    def launch(self, *args, **kwargs):
        """
        تشغيل واجهة المستخدم
        """
        return self.interface.launch(*args, **kwargs)


# ============================================================================
# الدالة الرئيسية
# Main Function
# ============================================================================

def main():
    """
    الدالة الرئيسية لتشغيل النظام المتكامل
    """
    try:
        # إنشاء مجلدات الحفظ والتصدير إذا لم تكن موجودة
        os.makedirs('temp_data', exist_ok=True)
        os.makedirs('exports', exist_ok=True)
        
        # تهيئة مدير قاعدة البيانات
        db_manager = DatabaseManager()
        
        # تهيئة نظام البث المباشر
        live_system = LiveStreamingSystem(db_manager)
        
        # تهيئة جامع البيانات
        data_collector = DataCollector()
        
        # إضافة محركات الزحف
        data_collector.add_source(SaudiCementCompany())
        data_collector.add_source(SaudiBuildingMaterials())
        data_collector.add_source(MockMaterialsSource())
        
        # تهيئة وكلاء البحث
        web_agent = WebResearchAgent(live_system, data_collector)
        content_agent = ContentAnalyzerAgent(live_system)
        fact_agent = FactCheckerAgent(live_system)
        
        # تهيئة واجهة المستخدم
        ui = GradioInterface(
            db_manager=db_manager,
            live_system=live_system,
            data_collector=data_collector,
            web_agent=web_agent,
            content_agent=content_agent,
            fact_agent=fact_agent
        )
        
        # تشغيل واجهة المستخدم
        ui.launch(share=True)
        
    except Exception as e:
        logger.error(f"خطأ في تشغيل النظام: {str(e)}")
        
        # إغلاق الاتصال بقاعدة البيانات
        if 'db_manager' in locals():
            db_manager.close()


if __name__ == "__main__":
    main()
