import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class KnowledgeManager:
    """Управление базой знаний"""

    def __init__(self, knowledge_dir: str = 'knowledge_base'):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(exist_ok=True)
        self.index_file = self.knowledge_dir / 'index.json'
        self.documents_index = self._load_index()
        self.document_processor = DocumentProcessor()
        
        # Автоматически индексируем документы при инициализации
        self._ensure_index_up_to_date()
    
    def _ensure_index_up_to_date(self) -> None:
        """Проверяет и обновляет индекс, если есть новые или измененные файлы"""
        logger.info("=" * 60)
        logger.info("🔍 Проверка индекса базы знаний...")
        
        # Получаем все файлы в директории
        all_files = list(self.knowledge_dir.glob('*.*'))
        supported_extensions = {'.txt', '.docx', '.xlsx', '.pdf', '.doc'}
        knowledge_files = [f for f in all_files if f.suffix.lower() in supported_extensions]
        
        if not knowledge_files:
            logger.warning(f"⚠️ В директории {self.knowledge_dir} не найдено поддерживаемых файлов")
            return
        
        logger.info(f"📁 Найдено {len(knowledge_files)} файлов в {self.knowledge_dir}:")
        for f in knowledge_files:
            logger.info(f"   - {f.name}")
        
        # Проверяем, все ли файлы в индексе
        indexed_filenames = {doc['filename'] for doc in self.documents_index['documents']}
        current_filenames = {f.name for f in knowledge_files}
        
        # Если индекс пустой или есть новые файлы - переиндексируем все
        if not self.documents_index['documents'] or not current_filenames.issubset(indexed_filenames):
            logger.info("🔄 Обновление индекса...")
            
            # Очищаем и создаем новый индекс
            self.documents_index = {
                'documents': [],
                'metadata': {
                    'version': '1.0',
                    'last_updated': datetime.now().isoformat(),
                    'total_files': len(knowledge_files)
                }
            }
            
            # Добавляем все документы
            added_count = 0
            for file_path in knowledge_files:
                try:
                    content = self.document_processor.process_file(str(file_path))
                    if content:
                        doc_info = {
                            'id': len(self.documents_index['documents']) + 1,
                            'filename': file_path.name,
                            'path': str(file_path),
                            'content': content,
                            'hash': self._calculate_file_hash(str(file_path)),
                            'size': len(content),
                            'added_at': datetime.now().isoformat()
                        }
                        self.documents_index['documents'].append(doc_info)
                        added_count += 1
                        logger.info(f"   ✅ Добавлен: {file_path.name} ({len(content):,} символов)")
                except Exception as e:
                    logger.error(f"   ❌ Ошибка индексации {file_path}: {e}")
            
            self._save_index()
            logger.info(f"✅ Индекс обновлен: {added_count}/{len(knowledge_files)} документов проиндексировано")
            
            # Показываем список всех проиндексированных документов
            for doc in self.documents_index['documents']:
                logger.debug(f"   [{doc['id']}] {doc['filename']} ({doc['size']:,} символов)")
        else:
            logger.info(f"✅ Индекс актуален: все {len(knowledge_files)} файлов уже проиндексированы")
        
        logger.info("=" * 60)

    def _load_index(self) -> Dict:
        """Загрузка индекса документов"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки индекса: {e}")
                return {'documents': [], 'metadata': {}}
        return {'documents': [], 'metadata': {'version': '1.0', 'created': datetime.now().isoformat()}}

    def _save_index(self):
        """Сохранение индекса документов"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения индекса: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """Расчет хэша файла для определения изменений"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def add_document(self, file_path: str) -> bool:
        """Добавление документа в базу знаний"""
        try:
            # Проверяем, существует ли уже такой файл
            file_hash = self._calculate_file_hash(file_path)
            existing = next((d for d in self.documents_index['documents']
                           if d.get('hash') == file_hash), None)

            if existing:
                logger.info(f"Документ уже в базе: {file_path}")
                return True

            # Обрабатываем документ
            content = self.document_processor.process_file(file_path)
            if not content:
                logger.warning(f"Не удалось обработать файл: {file_path}")
                return False

            # Создаем запись в индексе
            doc_info = {
                'id': len(self.documents_index['documents']) + 1,
                'filename': Path(file_path).name,
                'path': str(file_path),
                'content': content,
                'hash': file_hash,
                'size': len(content),
                'added_at': datetime.now().isoformat()
            }

            self.documents_index['documents'].append(doc_info)
            self._save_index()
            logger.info(f"Документ добавлен: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Ошибка добавления документа {file_path}: {e}")
            return False

    def add_documents_from_directory(self, directory: str) -> int:
        """Добавление всех документов из директории"""
        documents = self.document_processor.process_directory(directory)
        count = 0

        for doc in documents:
            file_path = doc['path']
            file_hash = self._calculate_file_hash(file_path)

            # Проверяем, не добавлен ли уже
            existing = next((d for d in self.documents_index['documents']
                           if d.get('hash') == file_hash), None)

            if not existing:
                doc_info = {
                    'id': len(self.documents_index['documents']) + 1,
                    'filename': doc['filename'],
                    'path': file_path,
                    'content': doc['content'],
                    'hash': file_hash,
                    'size': doc['size'],
                    'added_at': datetime.now().isoformat()
                }
                self.documents_index['documents'].append(doc_info)
                count += 1

        if count > 0:
            self._save_index()
            logger.info(f"Добавлено {count} документов из {directory}")

        return count

    def search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """Поиск релевантных документов по запросу"""
        query_lower = query.lower()
        results = []

        for doc in self.documents_index['documents']:
            content = doc['content']
            # Простой поиск по ключевым словам
            score = 0
            query_words = query_lower.split()

            for word in query_words:
                if word in content.lower():
                    score += content.lower().count(word)

            if score > 0:
                results.append({
                    'document': doc,
                    'score': score,
                    'preview': content[:500] + '...' if len(content) > 500 else content
                })

        # Сортируем по релевантности
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

    def get_all_documents(self) -> List[Dict]:
        """Получение всех документов"""
        return self.documents_index['documents']

    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Получение документа по ID"""
        for doc in self.documents_index['documents']:
            if doc['id'] == doc_id:
                return doc
        return None

    def remove_document(self, doc_id: int) -> bool:
        """Удаление документа по ID"""
        for i, doc in enumerate(self.documents_index['documents']):
            if doc['id'] == doc_id:
                self.documents_index['documents'].pop(i)
                self._save_index()
                logger.info(f"Документ удален: {doc_id}")
                return True
        return False

    def clear_all(self) -> bool:
        """Очистка всей базы знаний"""
        self.documents_index = {
            'documents': [],
            'metadata': {
                'version': '1.0',
                'cleared': datetime.now().isoformat()
            }
        }
        self._save_index()
        logger.info("База знаний очищена")
        return True

    def get_context_for_query(self, query: str, max_docs: int = 3, max_chars: int = 4000) -> str:
        """Получение контекста из релевантных документов для запроса"""
        logger.info(f"🔍 Поиск контекста для запроса: '{query[:50]}...'")
        results = self.search_documents(query, limit=max_docs)

        if not results:
            logger.warning(f"⚠️ Контекст не найден для запроса: '{query[:50]}...'")
            return ""

        logger.info(f"📚 Найдено {len(results)} релевантных документов:")
        context_parts = []
        total_chars = 0

        for i, result in enumerate(results, 1):
            doc = result['document']
            content = doc['content']
            score = result['score']
            
            logger.info(f"   [{i}] {doc['filename']} (релевантность: {score}, размер: {len(content):,} символов)")
            
            # Ограничиваем размер контекста
            if total_chars + len(content) > max_chars:
                # Берем только часть контента
                remaining = max_chars - total_chars
                if remaining > 100:  # Минимальный порог
                    content = content[:remaining]
                    logger.debug(f"      Контент обрезан до {remaining} символов")
                else:
                    logger.debug(f"      Пропущен (недостаточно места)")
                    break

            context_parts.append(f"=== {doc['filename']} ===\n{content}\n")
            total_chars += len(content)

        logger.info(f"✅ Общий размер контекста: {total_chars:,} символов из {len(results)} документов")
        return '\n'.join(context_parts)