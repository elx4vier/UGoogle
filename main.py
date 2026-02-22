import os
import json
import logging
import locale
import requests
from concurrent.futures import ThreadPoolExecutor

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction

logger = logging.getLogger(__name__)

class UGoogleExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.history_file = os.path.join(os.path.dirname(__file__), 'search_history.json')
        self.cache_file = os.path.join(os.path.dirname(__file__), 'suggestions_cache.json')
        self.translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.cache = self.load_cache()
        self.translations = self.load_translations()
        self.lang = self.detect_language()

    # ---------- TRANSLATIONS ----------
    def detect_language(self):
        sys_lang, _ = locale.getdefaultlocale()
        if sys_lang:
            lang_code = sys_lang.split("_")[0]  # ex: 'pt_BR' -> 'pt'
            if lang_code in self.translations:
                return lang_code
        return 'en'  # fallback

    def load_translations(self):
        translations = {}
        for fname in os.listdir(self.translations_dir):
            if fname.endswith(".json"):
                lang = fname.split(".")[0]
                try:
                    with open(os.path.join(self.translations_dir, fname), 'r', encoding='utf-8') as f:
                        translations[lang] = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load translation {fname}: {e}")
        return translations

    def t(self, key):
        """Return translation for the current language, fallback to English"""
        return self.translations.get(self.lang, {}).get(key,
               self.translations.get('en', {}).get(key, key))

    # ---------- HISTORY ----------
    def get_safe_history_limit(self):
        try:
            val = int(self.preferences.get('history_limit') or 5)
            return max(1, min(val, 10))
        except:
            return 5

    def get_history(self):
        if self.preferences.get('enable_history') != "true":
            return []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_to_history(self, term):
        if self.preferences.get('enable_history') != "true" or not term or not term.strip():
            return
        
        history = self.get_history()
        if term in history:
            history.remove(term)
        
        history.insert(0, term)
        limit = self.get_safe_history_limit()
            
        with open(self.history_file, 'w') as f:
            json.dump(history[:limit], f)

    def clear_history(self):
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
        self.cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    # ---------- CACHE ----------
    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.warning(f"Could not save suggestions cache: {e}")


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        query = (event.get_argument() or "").strip()
        icon = 'images/icon.png'
        error_icon = 'images/error.png'
        items = []
        
        try:
            s_limit = int(extension.preferences.get('suggestions_limit') or 5)
        except:
            s_limit = 5

        history = extension.get_history()
        clear_word = extension.preferences.get('clear_keyword') or "clear"

        # ---------- CLEAR HISTORY COMMAND ----------
        if query.lower() == clear_word.lower():
            items.append(ExtensionResultItem(
                icon=icon,
                name=extension.t("clear_history_title"),
                description=extension.t("clear_history_desc"),
                on_enter=ExtensionCustomAction("CLEARDATA_ACT", keep_app_open=False)
            ))
            return RenderResultListAction(items)

        # ---------- EMPTY QUERY ----------
        if not query:
            if not history:
                items.append(ExtensionResultItem(
                    icon=icon,
                    name="UGoogle",
                    description=extension.t("type_to_search"),
                    on_enter=DoNothingAction()
                ))
            else:
                for term in history:
                    items.append(ExtensionResultItem(
                        icon=icon,
                        name=f"↻ {term}",
                        description=extension.t("previously_searched"),
                        on_enter=ExtensionCustomAction(term, keep_app_open=False)
                    ))
            return RenderResultListAction(items[:s_limit])

        # ---------- EXACT QUERY ----------
        items.append(ExtensionResultItem(
            icon=icon,
            name=query,
            description=extension.t("search_google"),
            on_enter=ExtensionCustomAction(query, keep_app_open=False)
        ))

        # ---------- GOOGLE SUGGESTIONS (PERSISTENT CACHE) ----------
        google_suggestions = []
        if query in extension.cache:
            google_suggestions = extension.cache[query]
        else:
            future = extension.executor.submit(self.fetch_google_suggestions, query)
            try:
                google_suggestions = future.result(timeout=0.6)
                extension.cache[query] = google_suggestions
                extension.save_cache()
            except:
                # fallback if suggestions fail
                items.append(ExtensionResultItem(
                    icon=error_icon,
                    name=extension.t("suggestions_error"),
                    description="",
                    on_enter=DoNothingAction()
                ))
                google_suggestions = []

        # ---------- HISTORY MATCHES ----------
        h_matches = [h for h in history if h.lower().startswith(query.lower()) and h.lower() != query.lower()]
        seen = {query.lower()}

        for h in h_matches:
            if h.lower() not in seen:
                items.append(ExtensionResultItem(
                    icon=icon,
                    name=f"↻ {h}",
                    description=extension.t("previously_searched"),
                    on_enter=ExtensionCustomAction(h, keep_app_open=False)
                ))
                seen.add(h.lower())

        # ---------- ADD GOOGLE SUGGESTIONS ----------
        for g in google_suggestions:
            if g.lower() not in seen:
                items.append(ExtensionResultItem(
                    icon=icon,
                    name=g,
                    description="",
                    on_enter=ExtensionCustomAction(g, keep_app_open=False)
                ))
                seen.add(g.lower())

        return RenderResultListAction(items[:s_limit])

    def fetch_google_suggestions(self, query):
        try:
            r = requests.get(
                f"https://suggestqueries.google.com/complete/search?client=firefox&q={query}",
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=0.5
            )
            return r.json()[1]
        except:
            return []


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        data = event.get_data()
        
        if data == "CLEARDATA_ACT":
            extension.clear_history()
            return

        extension.save_to_history(data)
        url = f"https://www.google.com/search?q={data.replace(' ', '+')}"
        return OpenUrlAction(url).run()


if __name__ == "__main__":
    UGoogleExtension().run()
