# نظام البحث متعدد الوكلاء مع إطار عمل جمع البيانات
# Multi-Agent Research System with Data Collection Framework

## نظرة عامة
هذا النظام المتكامل يجمع بين نظام قاعدة بيانات لتخزين بيانات البحث، نظام بث مباشر لعرض عملية البحث في الوقت الفعلي، وإطار عمل لجمع البيانات من مواقع مواد البناء في المملكة العربية السعودية.

## المكونات الرئيسية
1. **نظام قاعدة البيانات**: لتخزين واسترجاع بيانات البحث والمواد المجمعة
2. **نظام البث المباشر**: لعرض عملية البحث وجمع البيانات في الوقت الفعلي
3. **إطار عمل جمع البيانات**: لجمع بيانات مواد البناء من مختلف المصادر عبر الإنترنت
4. **وكلاء البحث المتخصصة**: وكيل البحث على الويب، وكيل تحليل المحتوى، وكيل التحقق من الحقائق
5. **واجهة مستخدم Gradio**: واجهة تفاعلية سهلة الاستخدام

## المميزات
- جمع بيانات مواد البناء من مواقع مختلفة
- عرض عملية البحث وجمع البيانات في الوقت الفعلي
- تحليل البيانات المجمعة واستخراج الرؤى
- التحقق من صحة المعلومات
- تخزين البيانات في قاعدة بيانات منظمة
- تصدير البيانات بتنسيقات مختلفة (JSON، CSV، Excel)
- واجهة مستخدم سهلة الاستخدام

## متطلبات النظام
- Python 3.8 أو أحدث
- المكتبات المذكورة في ملف requirements.txt

## التثبيت
1. قم بإنشاء بيئة Python افتراضية (اختياري ولكن موصى به):
```bash
python -m venv venv
source venv/bin/activate  # لنظام Linux/Mac
venv\Scripts\activate     # لنظام Windows
```

2. قم بتثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

## الاستخدام

### الاستخدام المحلي
قم بتشغيل النظام باستخدام الأمر التالي:
```bash
python main.py
```

سيتم فتح واجهة المستخدم في المتصفح على العنوان التالي:
```
http://localhost:7860
```

### الاستخدام في بيئة Hugging Face
1. قم بإنشاء مشروع جديد من نوع Gradio في Hugging Face Spaces
2. قم بتحميل جميع الملفات إلى المشروع
3. سيتم تشغيل التطبيق تلقائياً باستخدام ملف app.py

## هيكل الملفات
- `main.py`: نقطة الدخول الرئيسية للنظام
- `app.py`: ملف تطبيق Hugging Face
- `integrated_system.py`: النظام المتكامل
- `data_collection_framework.py`: إطار عمل جمع البيانات
- `materials_scraper.py`: محركات زحف مواقع مواد البناء
- `test_integrated_system.py`: اختبارات النظام المتكامل
- `documentation_ar.md`: توثيق شامل باللغة العربية
- `requirements.txt`: متطلبات النظام

## التوثيق
للحصول على توثيق شامل باللغة العربية، يرجى الاطلاع على ملف `documentation_ar.md`.

## الترخيص
هذا المشروع مرخص بموجب رخصة MIT.

## الدعم
إذا واجهت أي مشاكل أو كان لديك أي استفسارات، يرجى فتح مشكلة جديدة في صفحة المشروع.
# finial-system
# finial-system
# final_integrated_system
