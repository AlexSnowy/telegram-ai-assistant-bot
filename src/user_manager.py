import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class UserManager:
    LANGUAGES = {
        'ru': 'Русский',
        'uz': 'O\'zbekcha',
        'en': 'English'
    }

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv('FIRESTORE_PROJECT_ID')
        self.db = None
        self.use_firestore = False

        if FIREBASE_AVAILABLE and self.project_id:
            try:
                if not firebase_admin._apps:
                    cred_path = os.getenv('FIREBASE_CREDENTIALS')
                    if cred_path:
                        if os.path.exists(cred_path):
                            cred = firebase_admin.credentials.Certificate(cred_path)
                        else:
                            import json
                            cred_dict = json.loads(cred_path)
                            cred = firebase_admin.credentials.Certificate(cred_dict)
                        firebase_admin.initialize_app(cred)
                    else:
                        firebase_admin.initialize_app()

                self.db = firestore.client()
                self.use_firestore = True
                logger.info("Firestore инициализирован для UserManager")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать Firestore: {e}")
                self.use_firestore = False

        self.local_users = {}
        self.local_users_file = 'users_local.json'
        self._load_local_users()

    def _load_local_users(self):
        if os.path.exists(self.local_users_file):
            try:
                import json
                with open(self.local_users_file, 'r', encoding='utf-8') as f:
                    self.local_users = json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки локальных пользователей: {e}")
                self.local_users = {}

    def _save_local_users(self):
        try:
            import json
            with open(self.local_users_file, 'w', encoding='utf-8') as f:
                json.dump(self.local_users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения локальных пользователей: {e}")

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.use_firestore and self.db:
            try:
                doc_ref = self.db.collection('users').document(str(user_id))
                doc = doc_ref.get()
                if doc.exists:
                    return doc.to_dict()
            except Exception as e:
                logger.error(f"Ошибка получения пользователя из Firestore: {e}")

        return self.local_users.get(str(user_id))

    def create_user(self, user_id: str, phone_number: str, language: str = 'uz') -> bool:
        user_data = {
            'user_id': user_id,
            'phone_number': phone_number,
            'language': language,
            'registered_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }

        if self.use_firestore and self.db:
            try:
                doc_ref = self.db.collection('users').document(str(user_id))
                doc_ref.set(user_data)
                logger.info(f"Пользователь {user_id} сохранен в Firestore")
                return True
            except Exception as e:
                logger.error(f"Ошибка сохранения пользователя в Firestore: {e}")

        self.local_users[str(user_id)] = user_data
        self._save_local_users()
        logger.info(f"Пользователь {user_id} сохранен локально")
        return True

    def update_user(self, user_id: str, **kwargs) -> bool:
        if self.use_firestore and self.db:
            try:
                doc_ref = self.db.collection('users').document(str(user_id))
                doc_ref.update(kwargs)
                return True
            except Exception as e:
                logger.error(f"Ошибка обновления пользователя в Firestore: {e}")

        user = self.local_users.get(str(user_id))
        if user:
            user.update(kwargs)
            user['last_activity'] = datetime.now().isoformat()
            self._save_local_users()
            return True
        return False

    def is_registered(self, user_id: str) -> bool:
        user = self.get_user(user_id)
        return user is not None and 'phone_number' in user

    def get_language(self, user_id: str) -> str:
        user = self.get_user(user_id)
        if user:
            return user.get('language', 'uz')
        return 'uz'

    def set_language(self, user_id: str, language: str) -> bool:
        if language not in self.LANGUAGES:
            return False
        return self.update_user(user_id, language=language)

    def delete_user(self, user_id: str) -> bool:
        if self.use_firestore and self.db:
            try:
                self.db.collection('users').document(str(user_id)).delete()
                return True
            except Exception as e:
                logger.error(f"Ошибка удаления пользователя из Firestore: {e}")

        if str(user_id) in self.local_users:
            del self.local_users[str(user_id)]
            self._save_local_users()
            return True
        return False

    def get_all_users(self) -> list:
        if self.use_firestore and self.db:
            try:
                users_ref = self.db.collection('users')
                docs = users_ref.stream()
                return [doc.to_dict() for doc in docs]
            except Exception as e:
                logger.error(f"Ошибка получения всех пользователей из Firestore: {e}")

        return list(self.local_users.values())