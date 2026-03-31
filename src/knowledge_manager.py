import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging
import re

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
        knowledge_files = sorted(
            [f for f in all_files if f.suffix.lower() in supported_extensions],
            key=lambda p: p.name.lower()
        )
        
        if not knowledge_files:
            logger.warning(f"⚠️ В директории {self.knowledge_dir} не найдено поддерживаемых файлов")
            return
        
        logger.info(f"📁 Найдено {len(knowledge_files)} файлов в {self.knowledge_dir}:")
        for f in knowledge_files:
            logger.info(f"   - {f.name}")
        
        # Проверяем, все ли файлы в индексе и не изменились ли их хэши
        indexed_filenames = {doc['filename'] for doc in self.documents_index['documents']}
        indexed_hashes = {
            doc['filename']: doc.get('hash', '')
            for doc in self.documents_index['documents']
        }
        current_filenames = {f.name for f in knowledge_files}
        current_hashes = {
            f.name: self._calculate_file_hash(str(f))
            for f in knowledge_files
        }

        new_files = current_filenames - indexed_filenames
        removed_files = indexed_filenames - current_filenames
        changed_files = {
            filename
            for filename, file_hash in current_hashes.items()
            if indexed_hashes.get(filename) != file_hash
        }
        
        # Если индекс пустой, есть новые/удаленные/измененные файлы — переиндексируем
        if (not self.documents_index['documents']
                or new_files
                or removed_files
                or changed_files):
            logger.info("🔄 Обновление индекса...")
            if new_files:
                logger.info(f"   ➕ Новые файлы: {', '.join(sorted(new_files))}")
            if removed_files:
                logger.info(f"   ➖ Удаленные файлы: {', '.join(sorted(removed_files))}")
            if changed_files:
                logger.info(f"   ♻️ Измененные файлы: {', '.join(sorted(changed_files))}")
            
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
        query_words = [word.strip(".,!?;:()[]{}\"'") for word in query_lower.split()]
        query_words = [word for word in query_words if word]

        address_keywords = {
            'адрес', 'адреса', 'рынок', 'рынка', 'рынков', 'market', 'markets', 'location',
            'локация', 'где', 'находится', 'guangzhou', 'yiwu', 'гуанчжоу', 'иву'
        }
        is_address_query = any(word in address_keywords for word in query_words)

        results = []

        for doc in self.documents_index['documents']:
            content = doc['content']
            filename = doc.get('filename', '')
            filename_lower = filename.lower()
            # Простой поиск по ключевым словам
            score = 0

            for word in query_words:
                if len(word) > 2:  # Игнорируем очень короткие слова
                    count = content.lower().count(word)
                    if count > 0:
                        score += count * (len(word) / 3)  # Вес зависит от длины слова
                    # Дополнительный вес за попадание в название файла
                    if word in filename_lower:
                        score += 12

            # Усиливаем выбор документов с адресами рынков для адресных запросов
            if is_address_query and ('адрес' in filename_lower or 'рынк' in filename_lower):
                score += 120

            # Дополнительный буст для городов, чтобы быстрее находить нужный файл
            if 'guangzhou' in query_lower or 'гуанчжоу' in query_lower:
                if 'guangzhou' in filename_lower or 'гуанчжоу' in filename_lower:
                    score += 80

            if 'yiwu' in query_lower or 'иву' in query_lower:
                if 'yiwu' in filename_lower or 'иву' in filename_lower:
                    score += 80

            if score > 0:
                # Получаем превью (первые 500 символов)
                preview = content[:500] + '...' if len(content) > 500 else content
                results.append({
                    'document': doc,
                    'score': score,
                    'preview': preview
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

    def get_context_for_query(self, query: str, max_docs: int = 3, max_chars: int = 2600) -> str:
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
            source_content = doc['content']
            content = self._extract_relevant_snippet(source_content, query)
            score = result['score']
            
            logger.info(
                f"   [{i}] {doc['filename']} (релевантность: {score:.0f}, "
                f"фрагмент: {len(content):,} из {len(source_content):,} символов)"
            )
            
            # Ограничиваем размер контекста
            if total_chars + len(content) > max_chars:
                # Берем только часть контента
                remaining = max_chars - total_chars
                if remaining > 200:  # Минимальный порог
                    content = content[:remaining]
                    logger.debug(f"      Контент обрезан до {remaining} символов")
                else:
                    logger.debug(f"      Пропущен (недостаточно места)")
                    break

            context_parts.append(f"Источник: {doc['filename']}\n{content}\n")
            total_chars += len(content)

        logger.info(f"✅ Общий размер контекста: {total_chars:,} символов из {len(results)} документов")
        return '\n'.join(context_parts)
    @staticmethod
    def _extract_relevant_snippet(content: str, query: str, max_snippet_chars: int = 900) -> str:
        """Извлекает наиболее релевантные фрагменты текста под запрос."""
        if not content:
            return ""

        query_words = [w.lower() for w in re.findall(r"\w+", query, flags=re.UNICODE) if len(w) > 2]
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        if not lines:
            return content[:max_snippet_chars]

        # 1) Сначала выбираем строки, где есть ключевые слова запроса
        matched_lines = []
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in query_words):
                matched_lines.append(line)

        # 2) Если совпадений нет, используем начало документа
        if not matched_lines:
            return content[:max_snippet_chars]

        # 3) Склеиваем найденные строки в компактный контекст
        snippet_parts = []
        total = 0
        for line in matched_lines:
            line_len = len(line)
            if total + line_len + 1 > max_snippet_chars:
                break
            snippet_parts.append(line)
            total += line_len + 1

        snippet = "\n".join(snippet_parts).strip()
        return snippet if snippet else content[:max_snippet_chars]
