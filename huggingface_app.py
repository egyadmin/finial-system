# huggingface_app.py
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
    try:
        # تهيئة قاعدة البيانات
        db_manager = DatabaseManager()

        # نظام البث المباشر
        live_system = LiveStreamingSystem(db_manager)

        # جامع البيانات
        data_collector = DataCollector()
        data_collector.add_source(SaudiCementCompany())
        data_collector.add_source(SaudiBuildingMaterials())
        data_collector.add_source(MockMaterialsSource())

        # الوكلاء
        web_agent = WebResearchAgent(live_system, data_collector)
        content_agent = ContentAnalyzerAgent(live_system)
        fact_agent = FactCheckerAgent(live_system)

        # واجهة Gradio
        interface = GradioInterface(
            db_manager=db_manager,
            live_system=live_system,
            data_collector=data_collector,
            web_agent=web_agent,
            content_agent=content_agent,
            fact_agent=fact_agent
        )

        # تشغيل الواجهة بدون share لأن HF Spaces بيعمل run تلقائي
        interface.launch()

    except Exception as e:
        logger.error(f"خطأ أثناء تشغيل تطبيق HuggingFace: {str(e)}")

if __name__ == "__main__":
    main()
