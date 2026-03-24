import os
import re
from pathlib import Path
from typing import List, Optional
import logging

# Document processing libraries
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import openpyxl
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Класс для обработки документов различных форматов"""

    SUPPORTED_EXTENSIONS = {'.txt', '.docx', '.xlsx', '.pdf', '.doc'}

    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """Извлечение текста из TXT файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Попробуем другую кодировку
            with open(file_path, 'r', encoding='cp1251') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Ошибка чтения TXT файла {file_path}: {e}")
            return ""

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Извлечение текста из DOCX файла"""
        if not DOCX_AVAILABLE:
            logger.warning("python-docx не установлен")
            return ""

        try:
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            return '\n'.join(text)
        except Exception as e:
            logger.error(f"Ошибка чтения DOCX файла {file_path}: {e}")
            return ""

    @staticmethod
    def extract_text_from_xlsx(file_path: str) -> str:
        """Извлечение текста из XLSX файла"""
        if not XLSX_AVAILABLE:
            logger.warning("openpyxl не установлен")
            return ""

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            text = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    for cell in row:
                        if cell and str(cell).strip():
                            text.append(str(cell))
            return '\n'.join(text)
        except Exception as e:
            logger.error(f"Ошибка чтения XLSX файла {file_path}: {e}")
            return ""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Извлечение текста из PDF файла"""
        if not PDF_AVAILABLE:
            logger.warning("PyPDF2 не установлен")
            return ""

        try:
            reader = PdfReader(file_path)
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return '\n'.join(text)
        except Exception as e:
            logger.error(f"Ошибка чтения PDF файла {file_path}: {e}")
            return ""

    @staticmethod
    def clean_text(text: str) -> str:
        """Очистка и нормализация текста"""
        if not text:
            return ""

        # Удаление лишних пробелов и переносов
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()

        # Удаление специальных символов, оставляя узбекские буквы
        # Узбекский алфавит: a,b,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,x,y,z,sh,ch,o‘,g‘,ng
        # Пропускаем также русские и английские буквы, цифры, пунктуацию
        return text

    def process_file(self, file_path: str) -> Optional[str]:
        """Обработка одного файла"""
        path = Path(file_path)

        if not path.exists():
            logger.error(f"Файл не найден: {file_path}")
            return None

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"Неподдерживаемый формат: {extension}")
            return None

        logger.info(f"Обработка файла: {file_path}")

        text = ""
        if extension == '.txt':
            text = self.extract_text_from_txt(file_path)
        elif extension == '.docx':
            text = self.extract_text_from_docx(file_path)
        elif extension == '.xlsx':
            text = self.extract_text_from_xlsx(file_path)
        elif extension == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif extension == '.doc':
            # Для .doc нужно использовать antiword или другие инструменты
            logger.warning("Формат .doc требует дополнительной обработки")
            return None

        if text:
            text = self.clean_text(text)
            logger.info(f"Извлечено {len(text)} символов из {file_path}")
            return text

        return None

    def process_directory(self, directory: str) -> List[dict]:
        """Обработка всех документов в директории"""
        documents = []
        path = Path(directory)

        if not path.exists():
            logger.warning(f"Директория не существует: {directory}")
            return documents

        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                text = self.process_file(str(file_path))
                if text:
                    documents.append({
                        'filename': file_path.name,
                        'path': str(file_path),
                        'content': text,
                        'size': len(text)
                    })

        logger.info(f"Обработано {len(documents)} документов из {directory}")
        return documents