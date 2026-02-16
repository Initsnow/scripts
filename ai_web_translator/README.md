# AI Web Translator

**AI Web Translator** is a powerful UserScript that translates any webpage in-place using advanced AI models (currently **DeepSeek**, with support for more coming soon). It is designed for power users who want high-quality, context-aware translations without losing the original page layout.

## ✨ Key Features

*   **🧠 AI-Powered**: Uses DeepSeek's advanced generic/coding models for natural translations.
*   **📄 In-Place Translation**: Replaces or appends text directly on the page. No ugly overlays or popups.
*   **⚡ Smart Caching**:
    *   Remembers what you've translated. Reloading the page loads translations **instantly**.
    *   **Auto-Cleanup**: Automatically removes unused cache entries after **14 days** or if the cache exceeds **50,000 items**.
*   **👁️ High Readability**:
    *   Uses a "Low Glare" theme (Warm Gray background, Dark text) optimized for visual comfort (Visual Snow friendly).
    *   Retains original font formatting.
*   **🤖 Automation**:
    *   Automatically handles the interaction with the AI chat interface.
    *   **Feature Enforcement**: Auto-toggles "DeepThink" or "Web Search" buttons based on your preference.
*   **🎛️ Floating Control**:
    *   Toggle between **Original**, **Translation**, or **Both** views with a single click.
    *   Auto-hides when translation is complete for a clean reading experience.

## 🚀 Installation

1.  **Install a UserScript Manager**:
    *   [Tampermonkey](https://www.tampermonkey.net/) (Recommended)
    *   Violentmonkey
2.  **Install the Script**:
    *   Create a new script in your manager.
    *   Copy and paste the code from `translator.user.js`.
    *   Save (`Ctrl+S`).

## 📖 How to Use

1.  **Navigate to any webpage** you want to translate (e.g., a documentation page, news article, or blog).
2.  **Right-click** (or check your Tampermonkey menu) and select **"🚀 Translate (In-Place)"**.
    *   *Note: If a task is already running, it might resume automatically.*
3.  **Authentication**:
    *   If you aren't logged into DeepSeek, a tab will open. **Log in manually**.
    *   Once logged in, the script will automatically start sending text segments.
4.  **Wait for Completion**:
    *   You can watch the progress on the floating status bar (e.g., "10 / 52").
    *   Once finished, the status bar disappears.
5.  **Control the View**:
    *   Use the floating buttons (bottom-right) to toggle:
        *   **Toggle Orig**: Show/Hide the original English text.
        *   **Toggle Trans**: Show/Hide the Chinese translation.

## ⚙️ Configuration (Advanced)

The script uses `GM_setValue` to store settings. Currently, you can modify these defaults in the code (search for `DEFAULTS` constant):

```javascript
const DEFAULTS = {
    maxContext: 5000,
    enableDeepThink: true,   // Set to false if you want faster, non-reasoning translation
    enableSearch: false,     // Set to true if you need web context (usually not needed for translation)
    // ...
};
```

## 🧹 Cache Management

*   **Manual Clear**: Open the Tampermonkey menu on any page and click **"🧹 Clear Cache"** to wipe all stored translations.
*   **Auto Purge**: The script runs a check on every save to ensure the cache stays healthy (max 14 days, max 50k items).

---
*Created by Antigravity*
