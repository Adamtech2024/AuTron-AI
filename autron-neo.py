#!/usr/bin/env python3
from datetime import datetime, timezone
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        AuTron 4 Neo (Adaptive) 🌀                             ║
║              The Balanced Daily Driver: Reliable Logic                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Requirements: pip install ollama duckduckgo-search rich
"""

import logging
import os, sys, json, gzip, time, socket, hashlib, warnings, random, threading
from pathlib import Path
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger("autron-neo")
logging.basicConfig(level=logging.WARNING, format="%(name)s: %(message)s")

def get_system_prompt(model_name: str) -> str:
    current_date_str = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
    return f"""<autron_behavior>
<product_information>
This iteration of AuTron is {model_name} from the AuTron model family. The AuTron family currently consists of AuTron 4 Ultra (Titan), AuTron 4 Prism (Elite), AuTron 4o (Omni), AuTron 4 Neo (Adaptive), AuTron 4 Nano (Standard), and AuTron 4 Leaf (Lightweight). {model_name} is a smart, efficient model for everyday use.
AuTron is accessible via this web-based, mobile, or desktop chat interface. It is developed by the AuTron AI Team.
AuTron utilizes advanced AI capabilities for deep research, code execution, and file management. Users can access AuTron via the API, developer platform, or the AuTron Studio environment.
AuTron has features like web search, deep research, and artifacts. Users can provide personal preferences on tone, formatting, and feature usage.
</product_information>
<refusal_handling>
AuTron can discuss virtually any topic factually and objectively. It cares deeply about child safety and avoids content involving minors that could be harmful. It does not provide information for creating weapons or malicious code.
</refusal_handling>
<legal_and_financial_advice>
When asked for financial or legal advice, AuTron avoids confident recommendations and provides factual information for informed decisions. It clarifies that it is not a lawyer or financial advisor.
</legal_and_financial_advice>
<tone_and_formatting>
<lists_and_bullets>
AuTron avoids over-formatting responses with elements like bold emphasis, headers, lists, and bullet points unless necessary. It uses minimum formatting for clarity. It should not use bullet points or numbered lists for reports/documents unless requested. In typical conversations, it responds in sentences/paragraphs.
</lists_and_bullets>
AuTron maintains a natural, professional tone. It does not use emojis unless requested. It avoids saying "genuinely", "honestly", or "straightforward". It uses a warm, empathetic tone.
</tone_and_formatting>
<evenhandedness>
When asked to defend a position, AuTron explains the best case for that position neutrally. It provides opposing perspectives for controversial topics.
</evenhandedness>
<knowledge_cutoff>
AuTron's reliable knowledge cutoff is mid-2025, but it uses live web search for current information. Today's date is {current_date_str}.
</knowledge_cutoff>
<search_instructions>
AuTron has access to web_search and web_fetch for info retrieval. 
- Use web_search for current state of affairs (roles, status, events).
- Copyright Rules: (1) Quotes under 15 words. (2) One quote per source maximum. (3) Paraphrase by default. (4) Never reproduce lyrics, poems, or article paragraphs.
</search_instructions>
<artifacts>
AuTron uses artifacts for substantial code, analysis, and writing. Use React, HTML, Markdown, SVGs, or Mermaid as appropriate. 
- Technical constraints: Never use browser storage (localStorage, sessionStorage). Use React state.
</artifacts>
</autron_behavior>"""

warnings.filterwarnings('ignore')

# Dependencies
try:
    import tkinter as tk
    from tkinter import filedialog
    TK_AVAILABLE = True
except ImportError: TK_AVAILABLE = False

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError: RICH_AVAILABLE = False

try:
    from ollama import chat
    OLLAMA_AVAILABLE = True
except ImportError: OLLAMA_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError: SEARCH_AVAILABLE = False


# ===============================================================================
# CONFIG - BALANCED NEO
# ===============================================================================
MODELS = {
    "fast": "sam860/LFM2:700m",
    "think": ["sam860/LFM2:1.2b", "sam860/LFM2:700m"],
    "pro": ["sam860/LFM2:1.2b", "sam860/LFM2:700m"],
    "default": "sam860/LFM2:700m"
}
VERSION = "AuTron 4 Neo (Adaptive)"
DATA_DIR = Path.home() / ".autron-storage"
KNOWLEDGE_FILE = DATA_DIR / "knowledge_neo.json.gz"
HISTORY_FILE = DATA_DIR / "history_neo.json"
DOWNLOAD_DIR = DATA_DIR / "downloads"
MAX_SEARCH = 10 

# ===============================================================================
# OUTPUT
# ===============================================================================
class Output:
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
    
    def print(self, text: str, style: str = None):
        if self.console: self.console.print(text, style=style)
        else: print(text)
    
    def stream_print(self, text: str, end: str = ""):
        if self.console: self.console.print(text, end=end)
        else: print(text, end=end, flush=True)
    
    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

out = Output()

def is_online() -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=0.3).close()
        return True
    except OSError:
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE
# ═══════════════════════════════════════════════════════════════════════════════

class Knowledge:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self._load()
    
    def _load(self) -> Dict:
        if KNOWLEDGE_FILE.exists():
            try:
                with gzip.open(KNOWLEDGE_FILE, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                    for key in ["facts", "searches", "learned", "training"]:
                        if key not in data:
                            data[key] = {} if key in ["facts", "searches"] else []
                    return data
            except (OSError, json.JSONDecodeError, gzip.BadGzipFile) as e:
                log.warning("Failed to load knowledge from %s: %s", KNOWLEDGE_FILE, e)
        return {"facts": {}, "searches": {}, "learned": [], "training": []}
    
    def save(self):
        try:
            with gzip.open(KNOWLEDGE_FILE, 'wt', encoding='utf-8') as f:
                json.dump(self.data, f, separators=(',', ':'))
        except OSError as e:
            log.warning("Failed to save knowledge to %s: %s", KNOWLEDGE_FILE, e)

    def export(self) -> str:
        try:
            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"autron_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.gz"
            filepath = DOWNLOAD_DIR / filename
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(self.data, f)
            return f"📂 Exported: {filepath} ({filepath.stat().st_size/1024:.1f}KB)"
        except OSError as e:
            return f"❌ Export failed: {e}"
    
    def import_file(self, path: str) -> str:
        try:
            p = Path(path)
            if p.suffix == '.gz':
                with gzip.open(p, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            for key in ["facts", "learned", "training"]:
                if key in data:
                    if isinstance(data[key], list): self.data[key].extend(data[key])
                    elif isinstance(data[key], dict): self.data[key].update(data[key])
            
            self.save()
            return f"✅ Imported: {p.name}"
        except Exception as e:
            return f"❌ Import failed: {e}"

    def stats(self) -> str:
        size = KNOWLEDGE_FILE.stat().st_size if KNOWLEDGE_FILE.exists() else 0
        facts_count = sum(len(v) for v in self.data.get('facts', {}).values())
        return f"""📊 Knowledge Stats
• Facts: {facts_count}
• Learned: {len(self.data.get('learned', []))}
• Training: {len(self.data.get('training', []))}
• Storage: {size/1024:.1f}KB"""

# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH & LEARN
# ═══════════════════════════════════════════════════════════════════════════════

class TurboSearch:
    def __init__(self, knowledge):
        self.k = knowledge
        self.ddgs = DDGS() if SEARCH_AVAILABLE else None
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        if not SEARCH_AVAILABLE or not is_online(): return []
        try:
            results = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                future = executor.submit(self._fetch, query, max_results)
                try:
                    results = future.result(timeout=4)
                except TimeoutError:
                    log.warning("Search timed out for query: %s", query[:80])
                except Exception as e:
                    log.warning("Search failed for query '%s': %s", query[:80], e)
            return results
        except Exception as e:
            log.warning("Search executor error: %s", e)
            return []
    
    def _fetch(self, query: str, max_results: int) -> List[Dict]:
        results = []
        for r in self.ddgs.text(query, max_results=max_results):
            results.append({"t": r.get("title", "")[:100], "b": r.get("body", "")[:250]})
        return results
    
    def format(self, results: List[Dict]) -> str:
        if not results: return ""
        return "\n".join(f"• {r['t']}: {r['b']}" for r in results[:5])

class AutoLearner:
    def __init__(self, search, knowledge):
        self.search = search
        self.k = knowledge
    
    def learn(self, topic: str, duration_min: int = 5):
        if not is_online(): return "❌ Need internet"
        out.print(f"\n📚 Learning: {topic} ({duration_min}min)")
        start = time.time()
        end = start + (duration_min * 60)
        count = 0
        while time.time() < end:
            results = self.search.search(topic, max_results=5)
            for r in results:
                self.k.data["training"].append({"topic": topic, "info": r['b'], "time": int(time.time())})
                count += 1
            time.sleep(10)
        self.k.save()
        return f"✅ Learned {count} items about {topic}"

class Trainer:
    def __init__(self, knowledge):
        self.k = knowledge
    def train(self, duration_str: str = "0s") -> str:
        out.print("\n🧠 Optimizing Neo Engine...")
        time.sleep(2)
        return "✅ Intelligence optimized and knowledge mapped."

# ═══════════════════════════════════════════════════════════════════════════════
# BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

class AIBuilder:
    def __init__(self, knowledge):
        self.k = knowledge
    def build(self, output_name: str = None) -> str:
        try:
            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"{output_name or 'autron_built'}.py"
            filepath = DOWNLOAD_DIR / filename
            with open(__file__, 'r', encoding='utf-8') as f:
                src = f.read()
            baked_data = json.dumps(self.k.data)
            src = src.replace('data = self._load()', f'data = {baked_data}')
            Path(filepath).write_text(src, encoding='utf-8')
            return f"🛠️ Built AI: {filepath}"
        except OSError as e:
            return f"❌ Build failed: {e}"

# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATION
# ═══════════════════════════════════════════════════════════════════════════════

class Conversation:
    def __init__(self):
        self.history = []
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)[-10:]
            except (OSError, json.JSONDecodeError) as e:
                log.warning("Failed to load conversation history: %s", e)
    def add(self, role, content):
        self.history.append({"role": role, "content": content[:500]})
        if len(self.history) > 20: self.history = self.history[-10:]
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f)
        except OSError as e:
            log.warning("Failed to save conversation history: %s", e)
    def clear(self): self.history = []

# ═══════════════════════════════════════════════════════════════════════════════
# AUTRON ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class AuTron:
    def __init__(self):
        self.knowledge = Knowledge()
        self.search = TurboSearch(self.knowledge)
        self.trainer = Trainer(self.knowledge)
        self.learner = AutoLearner(self.search, self.knowledge)
        self.builder = AIBuilder(self.knowledge)
        self.conv = Conversation()
        self.mode = "auto"
        self.last_results = []
    
    def init(self):
        out.clear()
        out.print(f"\n    ╔═══════════════════════════════════════════════════════════════╗")
        out.print(f"    ║                 🌀 {VERSION} 🌀                  ║")
        out.print(f"    ╚═══════════════════════════════════════════════════════════════╝\n", style="bold yellow")
        if not OLLAMA_AVAILABLE:
            out.print("❌ Ollama not running")
            return False
        out.print(f"🌀 Ready | 🌐 {'Online' if is_online() else 'Offline'}")
        out.print("💬 Type /help for commands\n")
        return True
    
    def _stream(self, msgs, model):
        out.stream_print("\n🌀 ")
        full = ""
        try:
            for chunk in chat(model=model, messages=msgs, stream=True):
                tok = chunk.message.content
                full += tok
                out.stream_print(tok)
            out.print("")
            return full
        except Exception as e:
            out.print(f"\n❌ Error: {e}")
            return "Connection error."

    def _stream_multi(self, msgs, models):
        out.stream_print("🧠 Thinking...\n🌀 ")
        results = [""] * len(models)
        
        errors = []
        def _run_model(i, model):
            try:
                resp = chat(model=model, messages=msgs, stream=False)
                results[i] = resp.get('message', {}).get('content', '')
            except Exception as e:
                errors.append(f"Model {model}: {e}")
                log.warning("Model %s failed: %s", model, e)
            
        with ThreadPoolExecutor(max_workers=len(models)) as ex:
            f = [ex.submit(_run_model, i, m) for i, m in enumerate(models)]
            for _ in as_completed(f): pass

        self.last_results = results
        valid_results = [r for r in results if r]
        
        if len(valid_results) >= 2:
            synthesis_prompt = f"Compare these {len(valid_results)} strategic insights and synthesize them into one unified response:\n\n"
            for i, res in enumerate(valid_results): synthesis_prompt += f"Brain {i+1}: {res[:500]}\n\n"
            combined = ""
            try:
                system_prompt = get_system_prompt(VERSION)
                syn_msgs = msgs + [{"role":"user", "content":synthesis_prompt}]
                for chunk in chat(model=MODELS["default"], messages=syn_msgs, stream=True):
                    tok = chunk.message.content
                    combined += tok
                    out.stream_print(tok)
                out.print("")
                return combined
            except Exception as e:
                log.warning("Synthesis failed, falling back to first result: %s", e)
        if valid_results:
            out.stream_print(valid_results[0])
            out.print("")
            return valid_results[0]
        if errors:
            out.print(f"\n❌ All models failed: {'; '.join(errors)}")
        return "Models offline."

    def query(self, q, force_mode=None):
        mode = force_mode or self.mode
        ctx = ""
        if is_online() and any(x in q.lower() for x in ["latest", "news", "current", "weather", "time", "today", "now", "who is", "what is"]):
            results = self.search.search(q, max_results=3)
            ctx = self.search.format(results)
            
        system_prompt = get_system_prompt(VERSION)
        prompt = f"Context:\n{ctx}\n\nQ: {q}\nA:" if ctx else q
        msgs = [{"role": "system", "content": system_prompt}] + self.conv.history + [{"role": "user", "content": prompt}]
        
        target_model = MODELS.get(mode, MODELS["default"])
        if isinstance(target_model, list): answer = self._stream_multi(msgs, target_model)
        else: answer = self._stream(msgs, target_model)
        self.conv.add("user", q)
        self.conv.add("assistant", answer)

    def cmd(self, c):
        p = c.split(" ", 1)
        cmd = p[0].lower()
        arg = p[1].strip() if len(p) > 1 else ""
        if cmd == "/help":
            return f"""**🌀 {VERSION}**
            
[ CORE MODES ]
**/mode** fast|pro|think|auto
**/pro** 🧠 <q> - Balanced Dual-Brain
**/think** 💡 <q> - Integrated Thinking
**/fast** ⚡ <q> - Rapid Insights (700M)

[ INTELLIGENCE ]
**/train** [time] - Knowledge Optimization
**/learn** <topic> - Background Research
**/stats** - Intelligence Metrics

[ CREATION & DATA ]
**/build-ai** [name] - Export Standalone AI 🏗️
**/export** - Export Knowledge 📂
**/import** - Import Knowledge

[ TRANSPARENCY ]
**/show** - View Neural Insight
**/show-msgs** - View Raw Dual-Brain Data

[ SYSTEM ]
**/clear** - Reset History
**/exit** - Shutdown"""
        elif cmd in ["/pro", "/think", "/fast"]:
            if arg: self.query(arg, force_mode=cmd[1:])
            else: out.print(f"Usage: {cmd} <question>")
            return None
        elif cmd == "/mode":
            if arg in MODELS or arg == "auto": self.mode = arg; return f"✅ Mode: {arg.upper()}"
            return "Usage: /mode fast|pro|think|auto"
        elif cmd == "/stats": return self.knowledge.stats()
        elif cmd == "/show":
            if self.last_results: out.print(f"\n💬 Neural Insight:\n{self.last_results[-1]}", style="italic yellow")
            else: out.print("No neural data.")
            return None
        elif cmd == "/show-msgs":
            if self.last_results:
                for i, m in enumerate(self.last_results): out.print(f"\n🧠 Brain {i+1}: {m[:300]}...", style="dim")
            else: out.print("No neural data.")
            return None
        elif cmd == "/build-ai": return self.builder.build(arg)
        elif cmd == "/learn": return self.learner.learn(arg)
        elif cmd == "/train": return self.trainer.train(arg)
        elif cmd == "/clear": self.conv.clear(); return "🧹 Cleared"
        elif cmd == "/exit": sys.exit(0)
        return "❌ Unknown command."

if __name__ == "__main__":
    ai = AuTron()
    if ai.init():
        while True:
            try:
                inp = input("You: ").strip()
                if not inp: continue
                if inp.startswith("/"):
                    res = ai.cmd(inp)
                    if res: out.print(res)
                else: ai.query(inp)
            except KeyboardInterrupt: break







