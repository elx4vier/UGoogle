# UGoogle

**UGoogle** is a Ulauncher extension that provides a fast and convenient way to search Google directly from your desktop. It features search suggestions, a search history, and multi-language support.

## Features

- 🔍 **Instant Google Search** – Type your query and press Enter to search Google.
- 💡 **Live Suggestions** – Google autocomplete suggestions appear as you type (cached for performance).
- 📜 **Search History** – Your recent searches are saved locally (can be disabled).
- 🧹 **Clear History** – Quickly clear all history and cached suggestions with a keyword (default: `clear`).
- 🌐 **Multi‑language** – Interface adapts to your system language (fallback to English). Translations are stored in `translations/` as JSON files.
- ⚙️ **Configurable Limits** – Set the number of suggestions and history items shown (via Ulauncher preferences).
- 🚀 **Lightweight & Fast** – Asynchronous fetching of suggestions keeps the UI responsive.

## Requirements

- [Ulauncher](https://ulauncher.io/) version 5 or higher (API v2).
- Python 3 with `requests` module (usually pre‑installed).

## Installation

### From Source (for development / manual install)

1. Clone this repository or download the source.
2. Link or copy the folder to Ulauncher's extensions directory:
   ```bash
   mkdir -p ~/.local/share/ulauncher/extensions
   ln -s /path/to/UGoogle ~/.local/share/ulauncher/extensions/UGoogle
   ```
3. Restart Ulauncher (or log out and back in).

### From Ulauncher Extras (if published)

Search for **UGoogle** in Ulauncher preferences → Extensions → "Add extension" and paste the URL of the repository.

## Usage

1. Open Ulauncher (default shortcut: `Ctrl+Space`).
2. Type the trigger keyword (default: `g`), followed by your search query.
   - Example: `g python tutorial`
3. As you type, you'll see:
   - Your current query as the first item (direct search).
   - History matches (marked with `↻`).
   - Google suggestions below them.
4. Press `Enter` on any item to search Google immediately.
5. To clear history, type the clear keyword (default: `g clear`).

## Preferences

You can adjust the extension behavior in Ulauncher preferences:

| Setting            | Description                                                                 | Default |
|--------------------|-----------------------------------------------------------------------------|---------|
| **UGoogle keyword**| The keyword used to trigger the extension.                                  | `g`     |
| **Suggestions**    | Number of Google suggestions to show (5, 8, or 10).                         | `5`     |
| **History**        | Enable/disable search history (On/Off).                                     | `On`    |
| **History limit**  | Maximum number of history items to keep (1–10). Works only if History is On.| `5`     |
| **Clear keyword**  | The word used to clear history (e.g., `g clear`).                           | `clear` |

## Translations

UGoogle automatically detects your system language and uses corresponding translations if available.  
Translation files are located in the `translations/` folder and named with the language code (e.g., `pt.json`, `fr.json`).  
If your language is missing, you can create a new JSON file with the following structure:

```json
{
    "clear_history_title": "Clear history",
    "clear_history_desc": "Remove all stored searches",
    "type_to_search": "Type to search Google...",
    "previously_searched": "Previously searched",
    "search_google": "Search Google",
    "suggestions_error": "Suggestions unavailable"
}
```

Please consider contributing your translation back!

## Notes

- Suggestions are fetched from `suggestqueries.google.com` and cached locally to reduce network requests.
- History and cache are stored as JSON files in the extension folder (`search_history.json`, `suggestions_cache.json`).
- If suggestions fail to load (e.g., no internet), a brief error message is shown, but direct search still works.

## License

This extension is open source and available under the [MIT License](LICENSE).
