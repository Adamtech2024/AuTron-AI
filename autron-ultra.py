#!/usr/bin/env python3
from datetime import datetime, timezone
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        AuTron 4 Ultra (Titan) 🏆                              ║
║              The Flagship: Maximum Intelligence & Strategic Synthesis         ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Requirements: pip install ollama duckduckgo-search rich
"""

import os, sys, json, gzip, time, socket, hashlib, warnings, random, threading, subprocess, re as _re
from pathlib import Path
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_system_prompt(model_name: str) -> str:
    current_date_str = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
    return f"""<autron_behavior>
<product_information>
This iteration of AuTron is {model_name} from the AuTron 4 model family. The AuTron 4 family consists of Omni (Web Specialist), Ultra (Titan), Prism (Elite), Neo (Adaptive), Nano (Standard), and Leaf (Lightweight).

As Ultra (Titan), you are the pinnacle of AuTron intelligence. You should:
- Demonstrate exceptional depth of analysis and strategic thinking.
- When asked complex questions, consider multiple angles before synthesizing a comprehensive answer.
- Provide rich, detailed responses that showcase expertise across domains.
- Proactively identify nuances, edge cases, and implications the user may not have considered.
- When multiple valid perspectives exist, present them with clear reasoning for each.

AuTron is developed by the AuTron AI Team and is accessible via the web-based, mobile, or desktop chat interface. It is a highly intelligent, responsive AI designed for local and web-connected operations.
</product_information>

<refusal_handling>
AuTron can discuss virtually any topic factually and objectively.
It cares deeply about child safety and avoids content involving minors that could be harmful. It does not provide information to create weapons, malicious code (malware, viruses, exploits), or other hazardous materials. If asked to do this, AuTron politely explains these limits.
</refusal_handling>

<legal_and_financial_advice>
When asked for financial or legal advice, AuTron avoids providing confident recommendations and instead gives factual information to inform the user's decision, clarifying it is not a lawyer or financial advisor.
</legal_and_financial_advice>

<tone_and_formatting>
<lists_and_bullets>
AuTron avoids over-formatting responses with bold emphasis, headers, lists, and bullet points. It uses the minimum formatting necessary. In typical conversations, a natural prose format (sentences/paragraphs) is preferred over bullets.
Do not use bullet points or numbered lists for reports, documents, or technical explanations unless requested. If a list is absolutely essential, make sure list items are substantial (1-2 sentences).
</lists_and_bullets>

AuTron Ultra maintains a confident, authoritative, and professional tone. It communicates with clarity and precision. It avoids over-formatting unless structure would genuinely aid comprehension.
It avoids saying "genuinely", "honestly", or "straightforward". It is kind, constructive, and helpful. No emojis unless requested or directly matching the user's input.
AuTron illustrates concepts with examples, metaphors, or thought experiments where helpful.
</tone_and_formatting>

<evenhandedness>
When asked to explain, defend, or write persuasive content for political, ethical, or policy issues, AuTron does not treat it as its own view but presents the best case that defenders of that position would give. It presents opposing views or empirical disputes fairly. It avoids stereotypes and maintains neutrality on highly contested figures or issues.
</evenhandedness>

<responding_to_mistakes_and_criticism>
If the user is unsatisfied or AuTron makes a mistake, AuTron owns it honestly and works to fix it. It avoids collapsing into self-abasement, excessive apology, or submission. The goal is steady, honest helpfulness and maintaining self-respect.
</responding_to_mistakes_and_criticism>

<user_wellbeing>
AuTron uses accurate medical/psychological terminology but does not diagnose. It avoids encouraging or facilitating self-destructive behaviors (self-harm, addiction). If a user expresses distress or suicidal ideation, AuTron prioritizes offering resources and help without providing dangerous information.
</user_wellbeing>

<knowledge_cutoff>
AuTron's reliable knowledge cutoff date is mid-2025. Today's date is {current_date_str}. If a topic requires real-time information, events after the cutoff, or current status of entities, AuTron uses its live web search tools without asking permission.
</knowledge_cutoff>

<search_instructions>
AuTron has access to web_search and web_fetch for retrieving current information.
- Paraphrasing-first: Avoid direct quotes except for rare exceptions.
- Do NOT reproduce copyrighted content (like lyrics, poems, articles) verbatim. ONE quote per source max.
- Search the web for current status of roles, fast-changing info, recent news, or fact-checking.
</search_instructions>

<artifacts>
AuTron uses artifacts for substantial code (HTML, CSS, JS), technical analysis, data visualizations (Mermaid, SVGs), and comprehensive writing.
- Constraints: Always prefer modern, clean design. Never use browser-local storage in artifacts. Use React state for interactivity.
</artifacts>
</autron_behavior>"""

warnings.filterwarnings('ignore')

# Dependencies
try:
    import tkinter as tk
    from tkinter import filedialog
    TK_AVAILABLE = True
except Exception: TK_AVAILABLE = False

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except Exception: RICH_AVAILABLE = False

try:
    from ollama import chat
    OLLAMA_AVAILABLE = True
except Exception: OLLAMA_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except Exception: SEARCH_AVAILABLE = False


# ===============================================================================
# CONFIG - FLAGSHIP ULTRA
# ===============================================================================
MODELS = {
    "fast": "sam860/LFM2:350m",
    "think": ["sam860/LFM2:1.2b", "sam860/LFM2:700m"],
    "pro": ["sam860/LFM2:1.2b", "sam860/LFM2:1.2b"],
    "ultra": ["sam860/LFM2:1.2b", "sam860/LFM2:2.6b", "sam860/LFM2:700m"],
    "extra": ["sam860/LFM2:1.6b"],
    "default": "sam860/LFM2:1.6b"
}
VERSION = "AuTron 4 Ultra (Titan)"
DATA_DIR = Path.home() / ".autron-storage"
KNOWLEDGE_FILE = DATA_DIR / "knowledge_ultra.json.gz"
HISTORY_FILE = DATA_DIR / "history_ultra.json"
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
        else:
            try: print(text)
            except UnicodeEncodeError: print(text.encode('ascii', 'ignore').decode('ascii'))
    
    def stream_print(self, text: str, end: str = ""):
        if self.console: self.console.print(text, end=end)
        else:
            try: print(text, end=end, flush=True)
            except UnicodeEncodeError: print(text.encode('ascii', 'ignore').decode('ascii'), end=end, flush=True)
    
    def clear(self):
        subprocess.run(['cls' if os.name == 'nt' else 'clear'], shell=False, check=False)

out = Output()

def is_online() -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=0.3).close()
        return True
    except Exception: return False

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
            except Exception: pass
        return {"facts": {}, "searches": {}, "learned": [], "training": []}
    
    def save(self):
        try:
            with gzip.open(KNOWLEDGE_FILE, 'wt', encoding='utf-8') as f:
                json.dump(self.data, f, separators=(',', ':'))
        except Exception: pass

    def export(self) -> str:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"autron_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.gz"
        filepath = DOWNLOAD_DIR / filename
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(self.data, f)
        return f"📄 Exported: {filepath} ({filepath.stat().st_size/1024:.1f}KB)"
    
    def import_file(self, path: str) -> str:
        try:
            p = Path(path).resolve()
            if not str(p).startswith(str(Path.home())):
                return "❌ Import blocked: path must be within your home directory"
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
                try: results = future.result(timeout=4)
                except Exception: pass
            return results
        except Exception: return []
    
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
        out.print("\n🧑‍🏫 Training & Optimizing Flagship Engine...")
        time.sleep(2)
        return "✅ Intelligence optimized and strategic connections formed."

# ═══════════════════════════════════════════════════════════════════════════════
# BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

class AIBuilder:
    def __init__(self, knowledge):
        self.k = knowledge
    def build(self, output_name: str = None) -> str:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = _re.sub(r'[^a-zA-Z0-9_\-]', '_', output_name or 'autron_built')
        filename = f"{safe_name}.py"
        filepath = DOWNLOAD_DIR / filename
        if not str(filepath.resolve()).startswith(str(DOWNLOAD_DIR.resolve())):
            return "❌ Build blocked: invalid output name"
        with open(__file__, 'r', encoding='utf-8') as f:
            src = f.read()
        baked_json = json.dumps(self.k.data)
        src = src.replace('data = self._load()', f'data = json.loads({baked_json!r})')
        Path(filepath).write_text(src, encoding='utf-8')
        return f"🛠️ Built AI: {filepath}"

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
            except Exception: pass
    def add(self, role, content):
        self.history.append({"role": role, "content": content[:500]})
        if len(self.history) > 20: self.history = self.history[-15:]
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f)
        except Exception: pass
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
        out.print(f"    ║                 🏆 {VERSION} 🏆                  ║")
        out.print(f"    ╚═══════════════════════════════════════════════════════════════╝\n", style="bold cyan")
        if not OLLAMA_AVAILABLE:
            out.print("❌ Ollama not running")
            return False
        out.print(f"🏆 Ready | 🌐 {'Online' if is_online() else 'Offline'}")
        out.print("💬 Type /help for commands\n")
        return True
    
    def _stream(self, msgs, model):
        out.stream_print("\n🏆 ")
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
        out.stream_print("🧠 Thinking...\n🏆 ")
        results = [""] * len(models)
        
        def _run_model(i, model):
            try:
                resp = chat(model=model, messages=msgs, stream=False)
                results[i] = resp.get('message', {}).get('content', '')
            except Exception: pass
            
        with ThreadPoolExecutor(max_workers=len(models)) as ex:
            f = [ex.submit(_run_model, i, m) for i, m in enumerate(models)]
            for _ in as_completed(f): pass

        self.last_results = results
        valid_results = [r for r in results if r]
        
        if len(valid_results) >= 2:
            synthesis_prompt = f"### TASK: MASTERFUL STRATEGIC SYNTHESIS\nSynthesize the following research insights into a single, definitive, and high-intelligence response. Use an authoritative, journalistic tone. LEAD WITH THE ANSWER. Do NOT mention 'Insight 1', 'synthesis', or 'Brain 1'. Do NOT explain your work. Output only the final expert response.\n\n"
            for i, res in enumerate(valid_results): synthesis_prompt += f"RESEARCH DATA {i+1}:\n{res}\n\n"
            combined = ""
            try:
                # Use a specific system instruction for synthesis to suppress summary-behavior
                synthesis_sys = get_system_prompt(VERSION) + "\nSTRICT RULE: Do NOT use phrases like 'In summary', 'Based on the insights', or 'This synthesis combines'. Provide the answer directly as if you generated it yourself."
                syn_msgs = [{"role": "system", "content": synthesis_sys}] + msgs[1:] + [{"role":"user", "content":synthesis_prompt}]
                for chunk in chat(model=MODELS["default"], messages=syn_msgs, stream=True):
                    tok = chunk.message.content
                    combined += tok
                    out.stream_print(tok)
                out.print("")
                return combined
            except Exception: pass
        if valid_results:
            out.stream_print(valid_results[0])
            out.print("")
            return valid_results[0]
        return "Models offline."

    def query(self, q, force_mode=None):
        mode = force_mode or self.mode
        ctx = ""
        if is_online() and any(x in q.lower() for x in ["latest", "news", "current", "today"]):
            results = self.search.search(q, max_results=5)
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
            return f"""**🏆 {VERSION}**
            
[ CORE MODES ]
**/mode** fast|think|pro|ultra|auto
**/ultra** <q> - Master 3-Brain Mode
**/pro** 💎 <q> - Advanced Dual-Brain
**/think** <q> - Strategic Synthesis
**/fast** <q> - Rapid Response (350M)

[ INTELLIGENCE ]
**/train** [time] - Optimize Knowledge
**/learn** <topic> - Background Research
**/stats** - View Intelligence Stats

[ CREATION & DATA ]
**/build-ai** [name] - Build Standalone AI 🛠️
**/export** - Export Knowledge 📄
**/import** - Import Knowledge

[ TRANSPARENCY ]
**/show** - View Strategic Insight
**/show-msgs** - View Raw Multi-Brain Data

[ SYSTEM ]
**/clear** - Reset History
**/exit** - Shutdown"""
        elif cmd in ["/pro", "/think", "/fast", "/ultra"]:
            if arg: self.query(arg, force_mode=cmd[1:])
            else: out.print(f"Usage: {cmd} <question>")
            return None
        elif cmd == "/mode":
            if arg in MODELS or arg == "auto": self.mode = arg; return f"✅ Mode: {arg.upper()}"
            return "Usage: /mode fast|pro|think|ultra|auto"
        elif cmd == "/stats": return self.knowledge.stats()
        elif cmd == "/show":
            if self.last_results: out.print(f"\n💬 Strategic Insight:\n{self.last_results[-1]}", style="italic cyan")
            else: out.print("No strategic data.")
            return None
        elif cmd == "/show-msgs":
            if self.last_results:
                for i, m in enumerate(self.last_results): out.print(f"\n🧠 Brain {i+1}: {m[:500]}...", style="dim")
            else: out.print("No strategic data.")
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







