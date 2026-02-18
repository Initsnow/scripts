// ==UserScript==
// @name         AI Web Translator
// @namespace    http://tampermonkey.net/
// @version      0.22
// @description  Translate webpage content in-place using AI (DeepSeek and more in future). Smart caching, accessible styles, and automation.
// @author       Antigravity
// @match        *://*/*
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_registerMenuCommand
// @grant        GM_openInTab
// @grant        GM_addStyle
// ==/UserScript==

(function () {
    'use strict';

    // --- Styles ---
    GM_addStyle(`
        .ds-trans-node {
            display: block;
            margin-top: 8px;
            margin-bottom: 16px;
            padding: 12px 16px;
            
            /* Accessibility / Readability Focus */
            background-color: #f0f2f5; /* Light Gray - Low Glare */
            color: #1a1a1a;            /* High Contrast Black/Gray */
            border-left: 5px solid #666; /* Neutral Anchor */
            
            border-radius: 4px;
            font-weight: 500; /* Slightly bolder for legibility */
            line-height: 1.6; /* Comfortable spacing */
            
            /* Visual Separation */
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        /* Dark Mode Override */
        @media (prefers-color-scheme: dark) {
            .ds-trans-node {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border-left: 5px solid #888;
                box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            }
        }
        
        /* Floating Controls */
        #ds-controls {
            position: fixed; 
            bottom: 20px; 
            right: 20px; 
            z-index: 2147483647; 
            display: flex; 
            flex-direction: column; 
            gap: 6px; 
        }
        #ds-controls > div.ds-ctrl-row {
            /* Glassmorphism */
            background: rgba(255, 255, 255, 0.1); /* Very transparent */
            backdrop-filter: blur(12px);          /* Strong Blur */
            -webkit-backdrop-filter: blur(12px);  /* Safari support */
            
            border: 1px solid rgba(255, 255, 255, 0.3); /* Glass Edge */
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15); /* Soft Depth */
            
            border-radius: 12px;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #222;
        }
        #ds-controls > div.ds-ctrl-row:hover {
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.25);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }
        /* Dark Mode Glass */
        @media (prefers-color-scheme: dark) {
            #ds-controls > div.ds-ctrl-row {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #eee;
            }
            #ds-controls > div.ds-ctrl-row:hover {
                background: rgba(0, 0, 0, 0.4);
            }
            .ds-btn { color: #eee; }
        }
        #ds-status {
            font-size: 12px; 
            font-weight: bold; 
            color: #333;
            margin: 0;
            padding: 0;
        }
        .ds-btn {
            font-family: -apple-system, sans-serif;
            font-size: 13px; 
            font-weight: 600; 
            color: #333;
            background: none;
            border: none;
            cursor: pointer;
            padding: 0;
            margin: 0;
            width: 100%;
        }
    `);

    // --- Configuration ---
    const DEFAULTS = {
        maxContext: 5000,
        enableDeepThink: true,
        enableSearch: false,
        promptPrefix: `You are a professional translator. I will provide a JSON array of objects. 
Each object has an "id" and "src" (source text).
Translate the "src" into Chinese.
RETURN A VALID JSON ARRAY of objects. 
Each item MUST have:
  - "id": (Keep exactly the same as input)
  - "trans": (The translation)

Do not add any explanations.
Input JSON:`
    };

    // --- Cache System ---
    const CM = {
        KEY: 'ds_trans_cache',
        MAX_SIZE: 50000, // Increased to 50k (approx 5-10MB)
        TTL: 14 * 24 * 60 * 60 * 1000, // 14 Days

        get: function (text) {
            const cache = GM_getValue(this.KEY, {});
            const hash = this.hash(text);
            const entry = cache[hash];
            if (entry) {
                // Refresh timestamp on hit? Maybe not to avoid excessive writes.
                return entry.t;
            }
            return null;
        },

        set: function (text, translation) {
            if (!text || !translation) return;
            const cache = GM_getValue(this.KEY, {});
            const hash = this.hash(text);

            cache[hash] = {
                t: translation,
                ts: Date.now()
            };

            this.prune(cache);
            GM_setValue(this.KEY, cache);
        },

        setBatch: function (items) {
            const cache = GM_getValue(this.KEY, {});
            let modified = false;

            items.forEach(item => {
                if (item.text && item.trans) {
                    cache[this.hash(item.text)] = {
                        t: item.trans,
                        ts: Date.now()
                    };
                    modified = true;
                }
            });

            if (modified) {
                this.prune(cache);
                GM_setValue(this.KEY, cache);
            }
        },

        prune: function (cache) {
            const now = Date.now();
            const keys = Object.keys(cache);
            let modified = false;

            // 1. TTL Check
            keys.forEach(k => {
                if (now - cache[k].ts > this.TTL) {
                    delete cache[k];
                    modified = true;
                }
            });

            // 2. Size Check
            const currentKeys = Object.keys(cache);
            if (currentKeys.length > this.MAX_SIZE) {
                // Sort by TS (oldest first)
                // This is expensive O(N log N), but runs locally.
                const sorted = currentKeys.sort((a, b) => cache[a].ts - cache[b].ts);
                const toRemove = sorted.slice(0, currentKeys.length - this.MAX_SIZE);
                toRemove.forEach(k => delete cache[k]);
                modified = true;
            }
        },

        clear: function () {
            GM_setValue(this.KEY, {});
            alert("Cache cleared!");
        },

        hash: function (str) {
            // Simple hash for string keys
            let hash = 0, i, chr;
            if (str.length === 0) return hash;
            for (i = 0; i < str.length; i++) {
                chr = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + chr;
                hash |= 0; // Convert to 32bit integer
            }
            return "h" + hash;
        }
    };

    function getSettings() {
        return GM_getValue('ds_settings', DEFAULTS);
    }

    // --- State Management ---
    // Task Structure:
    // {
    //    id: timestamp,
    //    url: string,
    //    blocks: [ { hash: string, text: string, translation: string|null } ],
    //    status: 'pending'|'processing'|'done',
    //    currentBatchIndex: 0
    // }

    // --- Domain Logic ---
    if (window.location.hostname.includes('deepseek.com')) {
        handleDeepSeek();
    } else {
        handleSourcePage();
    }

    // --- Source Page ---
    function handleSourcePage() {
        GM_registerMenuCommand("🚀 Translate (In-Place)", startTranslation);
        GM_registerMenuCommand("❌ Reset Task", clearTask);
        GM_registerMenuCommand("🧹 Clear Cache", () => CM.clear());

        setInterval(checkTaskUpdates, 1500);

        const task = GM_getValue('ds_task');
        if (task && task.url === window.location.href) {
            ensureFloatingControls();
        }
    }

    function startTranslation() {
        // ... (Scanning logic is same, just omitted for brevity in diff if not changed, but I need to inject Cache Check)
        // 1. Scan DOM
        const excludeTags = ['SCRIPT', 'STYLE', 'NOSCRIPT', 'IFRAME', 'nav', 'footer', 'svg', 'path'];
        const blockTags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'blockquote'];

        let blocks = [];
        let candidates = document.querySelectorAll(blockTags.join(','));

        candidates.forEach(el => {
            if (el.offsetParent === null) return;
            const text = el.innerText.trim();
            if (text.length < 5) return;
            if (el.querySelector(blockTags.join(','))) return;

            const hash = `${el.tagName}:${text.length}:${text.slice(0, 20).replace(/\s/g, '')}`;

            // Check Cache
            const cachedParams = CM.get(text);

            blocks.push({
                hash: hash,
                text: text,
                translation: cachedParams // If null, it's pending. If string, it's done.
            });

            el.dataset.dsHash = hash;
        });

        if (blocks.length === 0) {
            alert("No significant text blocks found.");
            return;
        }

        // Count pending
        const pendingCount = blocks.filter(b => !b.translation).length;

        const task = {
            id: Date.now(),
            url: window.location.href,
            blocks: blocks,
            status: pendingCount === 0 ? 'done' : 'pending',
            isInitialized: false,
            handlerId: null,
            lastHeartbeat: 0
        };

        GM_setValue('ds_task', task);

        ensureFloatingControls();

        if (pendingCount > 0) {
            GM_openInTab('https://chat.deepseek.com/', { active: true });
            showToast(`Task started! ${blocks.length} blocks (${pendingCount} new).`);
        } else {
            showToast(`Loaded ${blocks.length} translations from cache!`);
            // Trigger update immediately to show cached
            checkTaskUpdates();
        }
    }

    function checkTaskUpdates() {
        const task = GM_getValue('ds_task');
        if (!task || task.url !== window.location.href) return;

        // Scan blocks and inject
        task.blocks.forEach(block => {
            if (block.translation && block.translation !== "[Error]" && block.translation !== "[Timeout]" && block.translation !== "[JSON Error]" && block.translation !== "[Trans Missing]") {
                injectTranslation(block);
            }
        });

        // Update Status UI
        const translatedCount = task.blocks.filter(b => b.translation && b.translation.length > 0).length;
        const total = task.blocks.length;

        // Hide status if complete
        if (translatedCount >= total) {
            updateFloatingStatus(null);
        } else {
            updateFloatingStatus(`${translatedCount} / ${total}`);
        }
    }

    function injectTranslation(block) {
        let el = document.querySelector(`[data-ds-hash="${block.hash}"]`);

        // Resilience: finding element
        if (!el) {
            const candidates = document.querySelectorAll(`${block.hash.split(':')[0]}`);
            for (let c of candidates) {
                const h = `${c.tagName}:${c.innerText.trim().length}:${c.innerText.trim().slice(0, 20).replace(/\s/g, '')}`;
                if (h === block.hash) {
                    el = c;
                    el.dataset.dsHash = h;
                    break;
                }
            }
        }

        if (el && !el.nextElementSibling?.classList.contains('ds-trans-node')) {
            const tagName = el.tagName;
            const transEl = document.createElement(tagName);

            transEl.className = 'ds-trans-node';
            transEl.innerText = block.translation;

            // Clone Styles for seamless look
            try {
                const computed = window.getComputedStyle(el);
                transEl.style.fontSize = computed.fontSize;
                transEl.style.lineHeight = computed.lineHeight;
                transEl.style.fontFamily = computed.fontFamily;
                transEl.style.fontWeight = computed.fontWeight;
                transEl.style.textAlign = computed.textAlign;
                // Margins
                transEl.style.marginTop = "0px"; // Tweak
                transEl.style.marginBottom = computed.marginBottom;
            } catch (e) { }

            el.after(transEl);
        }
    }

    // --- DeepSeek Automation ---
    const DS_TAB_ID = 'ds_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
    const HEARTBEAT_TIMEOUT = 10000; // 10 seconds — if handler doesn't heartbeat, another tab can take over

    function handleDeepSeek() {
        setInterval(async () => {
            const task = GM_getValue('ds_task');
            if (!task) return;

            // UI
            if (!document.querySelector('#ds-monitor')) createMonitor(task);
            updateMonitor(task);

            const monitorStatus = document.querySelector('#ds-monitor-status');

            if (task.status === 'done') {
                if (monitorStatus) {
                    monitorStatus.textContent = "All batches completed successfully.";
                    monitorStatus.style.color = '#4ade80'; // Green
                }
                return;
            }

            // --- Cross-tab lock: only one DeepSeek tab should process ---
            const now = Date.now();
            if (task.handlerId && task.handlerId !== DS_TAB_ID) {
                // Another tab claimed this task — check if it's still alive
                if (task.lastHeartbeat && (now - task.lastHeartbeat) < HEARTBEAT_TIMEOUT) {
                    // Handler is alive, show status and skip
                    if (monitorStatus) {
                        monitorStatus.textContent = 'Another tab is handling this task.';
                        monitorStatus.style.color = '#facc15'; // Yellow
                    }
                    return;
                }
                // Handler is stale, take over
                console.log(`[DS Translator] Handler ${task.handlerId} stale, tab ${DS_TAB_ID} taking over.`);
            }

            // Claim ownership & heartbeat
            task.handlerId = DS_TAB_ID;
            task.lastHeartbeat = now;
            GM_setValue('ds_task', task);

            const textarea = document.querySelector('textarea#chat-input, textarea');
            if (!textarea) return;

            // Check if we are busy (local DOM state for send-in-progress)
            if (monitorStatus && monitorStatus.dataset.state === 'busy') return;

            // Find next batch
            const pendingIndex = task.blocks.findIndex(b => b.translation === null);
            if (pendingIndex === -1) {
                task.status = 'done';
                GM_setValue('ds_task', task);
                return;
            }


            // Prepare Dynamic Batch
            // Limit by Count (e.g. 50) AND Size (e.g. 2000 chars) to prevent output timeouts
            const maxItems = 50;
            const maxChars = 2000;

            let currentBatch = [];
            let currentChars = 0;

            for (let i = pendingIndex; i < task.blocks.length; i++) {
                const block = task.blocks[i];
                if (block.translation !== null) continue; // Should be sequential, but safety first

                if (currentBatch.length >= maxItems) break;
                if ((currentChars + block.text.length) > maxChars && currentBatch.length > 0) break;

                // Store Index explicitly to avoid mapping errors if gaps exist
                block._index = i;
                currentBatch.push(block);
                currentChars += block.text.length;
            }

            if (currentBatch.length === 0) return;

            // Enforce Feature Settings (Throttle to avoid spamming)
            if (!task.isInitialized) {
                await configureDeepSeekFeatures();
            }

            // Send
            sendBatch(currentBatch, textarea, pendingIndex, task.isInitialized);

        }, 2000);
    }

    async function configureDeepSeekFeatures() {
        const settings = getSettings();

        // Helper to find button by text (robust against class changes)
        const findButton = (texts) => {
            const buttons = Array.from(document.querySelectorAll('div[role="button"], button'));
            return buttons.find(b => texts.some(t => b.innerText.includes(t)));
        };

        // Helper to check if button is active based on class (User reported: ds-toggle-button--selected)
        const isActive = (btn) => btn && (btn.className.includes('ds-toggle-button--selected') || btn.getAttribute('aria-pressed') === 'true');

        // 1. DeepThink (R1)
        const thinkBtn = findButton(["DeepThink", "深度思考"]);
        if (thinkBtn) {
            const isOn = isActive(thinkBtn);
            if (settings.enableDeepThink !== isOn) {
                thinkBtn.click();
                await new Promise(r => setTimeout(r, 200));
            }
        }

        // 2. Search
        const searchBtn = findButton(["Search", "联网", "Networking"]);
        if (searchBtn) {
            const isOn = isActive(searchBtn);
            if (settings.enableSearch !== isOn) {
                searchBtn.click();
                await new Promise(r => setTimeout(r, 200));
            }
        }
    }

    function sendBatch(batch, textarea, startIndex, isInitialized) {
        const monitorStatus = document.querySelector('#ds-monitor-status');
        if (monitorStatus) {
            monitorStatus.dataset.state = 'busy';
            monitorStatus.textContent = `Processing items ${batch[0]._index} - ${batch[batch.length - 1]._index}...`;
        }

        const settings = getSettings();

        // New Protocol: [{"id": 1, "src": "..."}]
        const payloadObj = batch.map(b => ({ id: b._index, src: b.text }));
        const jsonPayload = JSON.stringify(payloadObj);

        let prompt = "";
        if (!isInitialized) {
            prompt = `${settings.promptPrefix}\n${jsonPayload}`;
            const task = GM_getValue('ds_task');
            task.isInitialized = true;
            GM_setValue('ds_task', task);
        } else {
            prompt = `Next batch (JSON Array):\n${jsonPayload}`;
        }

        // Input & Click
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
        nativeInputValueSetter.call(textarea, prompt);
        textarea.dispatchEvent(new Event('input', { bubbles: true }));

        setTimeout(() => {
            const buttons = document.querySelectorAll('.ds-icon-button');
            if (buttons.length > 0) buttons[buttons.length - 1].click();
        }, 800);

        waitForResponse(batch);
    }

    function waitForResponse(batch) {
        let checkCount = 0;
        let lastText = "";
        let startTime = Date.now();

        const poller = setInterval(() => {
            if (Date.now() - startTime > 120000) { // 2 mins timeout
                clearInterval(poller);
                markBatchError(batch, "Timeout");
                return;
            }

            const messages = document.querySelectorAll('.ds-markdown');
            const lastMsg = messages[messages.length - 1];
            if (!lastMsg) return;

            const currentText = lastMsg.innerText;

            // Guard
            if (currentText.includes('Input JSON:') || currentText.includes('Next batch (JSON Array):')) return;
            if (currentText.length < 5) return;

            if (currentText === lastText) {
                checkCount++;
            } else {
                checkCount = 0;
                lastText = currentText;
            }

            if (checkCount > 4) {
                clearInterval(poller);
                parseResponse(currentText, batch);
            }
        }, 1000);
    }

    function parseResponse(text, batch) {
        try {
            let jsonStr = text;
            if (text.includes('```json')) {
                jsonStr = text.split('```json')[1].split('```')[0];
            } else if (text.includes('```')) {
                jsonStr = text.split('```')[1].split('```')[0];
            }

            const open = jsonStr.indexOf('[');
            const close = jsonStr.lastIndexOf(']');
            if (open !== -1 && close !== -1) {
                jsonStr = jsonStr.substring(open, close + 1);
            }

            // Expected: [{"id": 1, "trans": "..."}]
            const translations = JSON.parse(jsonStr.trim());

            const task = GM_getValue('ds_task');

            // Create a Map for O(1) lookup
            const transMap = new Map();
            if (Array.isArray(translations)) {
                translations.forEach(item => {
                    if (item && item.id !== undefined && item.trans) {
                        transMap.set(item.id, item.trans);
                    }
                });
            }

            let validCount = 0;
            const cacheItems = []; // Collect successful translations for cache
            batch.forEach((b) => {
                const target = task.blocks[b._index];
                if (!target) return;

                if (transMap.has(b._index)) {
                    target.translation = transMap.get(b._index);
                    validCount++;
                    // Queue for cache write (keyed by source text, cross-page)
                    cacheItems.push({ text: b.text, trans: target.translation });
                } else {
                    // If ID not found, maybe model failed to return it.
                    // Don't mark as error immediately? Or mark as missing?
                    // Let's mark as missing for retry or manual check
                    target.translation = "[Trans Missing]";
                }
            });

            // Persist translations to cache so other pages with same text skip AI
            if (cacheItems.length > 0) {
                CM.setBatch(cacheItems);
            }

            GM_setValue('ds_task', task);

            const monitorStatus = document.querySelector('#ds-monitor-status');
            if (monitorStatus) {
                monitorStatus.dataset.state = 'idle';
                monitorStatus.textContent = `Batch Done (${validCount}/${batch.length})`;
            }

        } catch (e) {
            console.error("DeepSeek Parse Error", e);
            markBatchError(batch, "JSON Error");
        }
    }

    function markBatchError(batch, reason) {
        const task = GM_getValue('ds_task');
        batch.forEach((b) => {
            const target = task.blocks[b._index];
            if (target) target.translation = `[${reason}]`;
        });
        GM_setValue('ds_task', task);

        const monitorStatus = document.querySelector('#ds-monitor-status');
        if (monitorStatus) {
            monitorStatus.dataset.state = 'idle';
            monitorStatus.textContent = `Error: ${reason}. Continuing...`;
        }
    }

    // --- UI Helpers ---
    function ensureFloatingControls() {
        if (window.self !== window.top) return; // Strict: Top window only
        if (document.getElementById('ds-controls')) return;

        const div = document.createElement('div');
        div.id = 'ds-controls';

        // Simplified structure
        div.innerHTML = `
            <div class="ds-ctrl-row">
                 <p id="ds-status">Ready</p>
            </div>
            <div class="ds-ctrl-row">
                 <button class="ds-btn" id="ds-toggle-orig">Toggle Orig</button>
            </div>
            <div class="ds-ctrl-row">
                 <button class="ds-btn" id="ds-toggle-trans">Toggle Trans</button>
            </div>
        `;
        document.body.appendChild(div);

        // Handlers
        document.getElementById('ds-toggle-orig').onclick = (e) => {
            const els = document.querySelectorAll(`[data-ds-hash]`);
            if (!els.length) return;
            const isHidden = els[0].style.display === 'none';
            els.forEach(elem => elem.style.display = isHidden ? '' : 'none');
            e.target.style.opacity = isHidden ? '1' : '0.5';
        };
        document.getElementById('ds-toggle-trans').onclick = (e) => {
            const els = document.querySelectorAll('.ds-trans-node');
            if (!els.length) return;
            const isHidden = els[0].style.display === 'none';
            els.forEach(elem => elem.style.display = isHidden ? '' : 'none');
            e.target.style.opacity = isHidden ? '1' : '0.5';
        };
    }

    function updateFloatingStatus(text) {
        const el = document.getElementById('ds-status');
        if (!el) return;

        if (!text) {
            el.parentElement.style.display = 'none';
        } else {
            el.parentElement.style.display = 'flex';
            el.textContent = text;
        }
    }

    function createMonitor(task) {
        const div = document.createElement('div');
        div.id = 'ds-monitor';
        div.style.cssText = "position: fixed; bottom: 10px; right: 10px; width: 250px; background: rgba(0,0,0,0.8); color: white; padding: 10px; z-index: 99999;";
        div.innerHTML = `<strong>DeepSeek Translator</strong><br><span id="ds-monitor-status" data-state="idle">Idle</span>`;
        document.body.appendChild(div);
    }

    function updateMonitor(task) {
        // Optional: show progress bar
    }

    function showToast(msg) {
        const div = document.createElement('div');
        div.textContent = msg;
        div.style.cssText = "position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #333; color: white; padding: 10px 20px; border-radius: 20px; z-index: 100000; opacity: 0.9;";
        document.body.appendChild(div);
        setTimeout(() => div.remove(), 3000);
    }

    function clearTask() {
        GM_setValue('ds_task', null);
        window.location.reload();
    }

})();
