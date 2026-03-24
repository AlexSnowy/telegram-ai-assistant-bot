import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    """Управление промтами из текстовых файлов"""

    def __init__(self, prompts_dir: str = 'prompts'):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(exist_ok=True)
        self.prompts_index_file = self.prompts_dir / 'prompts_index.json'
        self.prompts_index = self._load_index()

    def _load_index(self) -> Dict:
        """Загрузка индекса промтов"""
        if self.prompts_index_file.exists():
            try:
                with open(self.prompts_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки индекса промтов: {e}")
                return {'prompts': [], 'metadata': {}}
        return {'prompts': [], 'metadata': {'version': '1.0', 'created': datetime.now().isoformat()}}

    def _save_index(self):
        """Сохранение индекса промтов"""
        try:
            with open(self.prompts_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения индекса промтов: {e}")

    def add_prompt_from_file(self, file_path: str, name: Optional[str] = None) -> bool:
        """Добавление промта из текстового файла"""
        try:
            path = Path(file_path)

            if not path.exists():
                logger.error(f"Файл не найден: {file_path}")
                return False

            if path.suffix.lower() != '.txt':
                logger.warning(f"Поддерживаются только .txt файлы: {file_path}")
                return False

            # Читаем содержимое файла
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                logger.warning(f"Файл пустой: {file_path}")
                return False

            # Используем имя файла если не указано
            if not name:
                name = path.stem

            # Проверяем уникальность имени
            existing = next((p for p in self.prompts_index['prompts']
                           if p['name'] == name), None)

            if existing:
                logger.warning(f"Промт с именем '{name}' уже существует")
                return False

            # Копируем файл в prompts директорию
            dest_file = self.prompts_dir / f"{name}.txt"
            with open(dest_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # Добавляем в индекс
            prompt_info = {
                'id': len(self.prompts_index['prompts']) + 1,
                'name': name,
                'filename': dest_file.name,
                'path': str(dest_file),
                'size': len(content),
                'preview': content[:200] + '...' if len(content) > 200 else content,
                'added_at': datetime.now().isoformat()
            }

            self.prompts_index['prompts'].append(prompt_info)
            self._save_index()
            logger.info(f"Промт добавлен: {name}")
            return True

        except Exception as e:
            logger.error(f"Ошибка добавления промта из {file_path}: {e}")
            return False

    def add_prompt_from_text(self, name: str, content: str) -> bool:
        """Добавление промта из текста"""
        try:
            if not name or not content:
                logger.warning("Имя и содержание промта обязательны")
                return False

            # Проверяем уникальность имени
            existing = next((p for p in self.prompts_index['prompts']
                           if p['name'] == name), None)

            if existing:
                logger.warning(f"Промт с именем '{name}' уже существует")
                return False

            # Сохраняем файл
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            dest_file = self.prompts_dir / f"{safe_name}.txt"

            with open(dest_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # Добавляем в индекс
            prompt_info = {
                'id': len(self.prompts_index['prompts']) + 1,
                'name': name,
                'filename': dest_file.name,
                'path': str(dest_file),
                'size': len(content),
                'preview': content[:200] + '...' if len(content) > 200 else content,
                'added_at': datetime.now().isoformat()
            }

            self.prompts_index['prompts'].append(prompt_info)
            self._save_index()
            logger.info(f"Промт добавлен: {name}")
            return True

        except Exception as e:
            logger.error(f"Ошибка добавления промта '{name}': {e}")
            return False

    def get_prompt(self, name: str) -> Optional[str]:
        """Получение промта по имени"""
        for prompt in self.prompts_index['prompts']:
            if prompt['name'] == name:
                try:
                    with open(prompt['path'], 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Ошибка чтения промта {name}: {e}")
                    return None
        return None

    def get_all_prompts(self) -> List[Dict]:
        """Получение списка всех промтов"""
        return self.prompts_index['prompts']

    def remove_prompt(self, name: str) -> bool:
        """Удаление промта по имени"""
        for i, prompt in enumerate(self.prompts_index['prompts']):
            if prompt['name'] == name:
                # Удаляем файл
                try:
                    Path(prompt['path']).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Ошибка удаления файла промта: {e}")

                # Удаляем из индекса
                self.prompts_index['prompts'].pop(i)
                self._save_index()
                logger.info(f"Промт удален: {name}")
                return True
        return False

    def clear_all(self) -> bool:
        """Очистка всех промтов"""
        # Удаляем все файлы промтов
        for prompt in self.prompts_index['prompts']:
            try:
                Path(prompt['path']).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Ошибка удаления файла: {e}")

        self.prompts_index = {
            'prompts': [],
            'metadata': {
                'version': '1.0',
                'cleared': datetime.now().isoformat()
            }
        }
        self._save_index()
        logger.info("Все промты удалены")
        return True

    def list_prompts_formatted(self, language: str = 'uz') -> str:
        """Форматированный список промтов для отображения"""
        prompts = self.get_all_prompts()

        messages = {
            'uz': {
                'none': "Ҳозирча промтлар мавжуд эмас.",
                'header': f"📋 {{count}} та промт мавжуд:\n"
            },
            'ru': {
                'none': "Промты пока нет.",
                'header': f"📋 {{count}} промт(ов) доступно:\n"
            },
            'en': {
                'none': "No prompts yet.",
                'header': f"📋 {{count}} prompt(s) available:\n"
            }
        }

        lang_data = messages.get(language, messages['uz'])

        if not prompts:
            return lang_data['none']

        lines = [lang_data['header'].format(count=len(prompts))]
        for prompt in prompts:
            lines.append(f"• {prompt['name']} (ID: {prompt['id']})")
            if prompt.get('preview'):
                lines.append(f"  {prompt['preview']}\n")

        return '\n'.join(lines)