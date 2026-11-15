#!/usr/bin/env python3
"""One-shot repair: replace broken duckduckgo_search usage with a reliable
Wikipedia (primary) + DuckDuckGo HTML (secondary) search backend, and broaden
the auto-search trigger so AuTron no longer answers only weather-style trivia."""
import re, pathlib

ROOT = pathlib.Path("/workspace")

ENGINE = '''class TurboSearch:
    """Reliable web knowledge engine.

    Backend 1: Wikipedia Action API (search + plain-text intro extracts). Free,
               keyless; requires a descriptive User-Agent per Wikimedia policy.
    Backend 2: DuckDuckGo HTML endpoint (html.duckduckgo.com) as a fallback for
               current events / anything Wikipedia does not cover.

    The previously used `duckduckgo_search` package was renamed to `ddgs`; its
    old import path failed silently, every lookup returned [] and the model
    answered from stale training data. This engine uses only `requests`.
    """

    WIKI_API = "https://en.wikipedia.org/w/api.php"
    DDG_HTML = "https://html.duckduckgo.com/html/"
    UA = "AuTron/1.0 (personal AI assistant; contact: autron-user@localhost) python-requests"
    STOPWORDS = {
        "who", "what", "where", "when", "why", "how", "is", "are", "was", "were",
        "the", "a", "an", "of", "in", "on", "for", "to", "and", "or", "do", "does",
        "did", "can", "could", "would", "should", "i", "you", "it", "its", "tell",
        "me", "about", "please", "explain", "define", "definition", "current",
        "latest", "news", "today", "now", "really", "just",
    }

    def __init__(self, knowledge):
        self.k = knowledge

    # -- public API ------------------------------------------------------
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        if not is_online(): return []
        results = self._wiki(query, max_results)
        if len(results) < max(1, min(2, max_results)):
            results += self._ddg_html(query, max_results - len(results))
        seen, uniq = set(), []
        for r in results:
            key = r["t"].lower()
            if key not in seen:
                seen.add(key); uniq.append(r)
        return uniq[:max_results]

    def needs_lookup(self, q_lower: str) -> bool:
        """Decide whether a question should be grounded with live context.
        Any factual who/what/where/when/why/how style question triggers a
        lookup - not just the handful of keywords the old version matched."""
        fast_hits = ["latest", "news", "current", "weather", "time", "today",
                     "now", "who is", "who are", "what is", "what are", "where is",
                     "where are", "when is", "when was", "why is", "why do",
                     "how much", "how many", "how do", "how does", "tell me about"]
        if any(x in q_lower for x in fast_hits): return True
        words = set(re.sub(r"[^a-z0-9 ?]", " ", q_lower).split())
        if "?" in q_lower and words & {"who", "what", "where", "when", "why", "how", "which"}:
            return True
        return False

    def format(self, results: List[Dict]) -> str:
        if not results: return ""
        lines = ["LIVE WEB CONTEXT (retrieved " + time.strftime("%Y-%m-%d %H:%M") + " - prefer this over your training data when it conflicts):\\n"]
        for r in results[:5]:
            src = f" ({r['s']})" if r.get("s") else ""
            lines.append(f"- {r['t']}{src}: {r['b']}")
        return "\\n".join(lines)

    # -- helpers -----------------------------------------------------------
    def _topic(self, query: str) -> str:
        """Reduce a natural-language question to searchable keywords."""
        q = re.sub(r"[^a-zA-Z0-9 ]", " ", query.lower())
        keep = [w for w in q.split() if w and w not in self.STOPWORDS]
        return " ".join(keep) or query.strip()

    def _get(self, url, params=None, data=None, timeout=6):
        try:
            if data:
                r = requests.post(url, data=data, headers={"User-Agent": self.UA}, timeout=timeout)
            else:
                r = requests.get(url, params=params, headers={"User-Agent": self.UA}, timeout=timeout)
            if r.status_code == 200 and r.text.strip(): return r
        except Exception: pass
        return None

    # -- backend 1: Wikipedia ---------------------------------------------
    def _wiki(self, query: str, max_results: int) -> List[Dict]:
        topic = self._topic(query)
        if not topic: return []
        out = []
        r = self._get(self.WIKI_API, params={
            "action": "query", "list": "search", "srsearch": topic,
            "srlimit": max(1, min(max_results, 5)), "format": "json"})
        if not r: return []
        try: hits = r.json()["query"]["search"]
        except Exception: return []
        titles = [h["title"] for h in hits]
        if not titles: return []
        r2 = self._get(self.WIKI_API, params={
            "action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1,
            "exchars": 350, "exlimit": "max", "titles": "|".join(titles), "format": "json"})
        pages = {}
        if r2:
            try: pages = r2.json()["query"]["pages"]
            except Exception: pass
        for t in titles:
            page = next((p for p in pages.values() if p.get("title") == t), None)
            text = (page or {}).get("extract", "") or next((h.get("snippet", "") for h in hits if h["title"] == t), "")
            text = re.sub(r"<[^>]+>", "", text).strip()
            if text:
                out.append({"t": t, "b": text[:300], "s": "wikipedia"})
        return out

    # -- backend 2: DuckDuckGo HTML ---------------------------------------
    def _ddg_html(self, query: str, max_results: int) -> List[Dict]:
        if max_results <= 0: return []
        r = self._get(self.DDG_HTML, data={"q": query}, timeout=6)
        if not r: return []
        html_txt = r.text
        if "anomaly" in html_txt[:400].lower(): return []  # rate-limit challenge page
        links = re.findall(r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', html_txt, re.S)
        snips = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html_txt, re.S)
        clean = lambda s: unescape(re.sub(r"<.*?>", "", s)).strip()
        out = []
        for l, s in list(zip(links, snips))[:max_results]:
            t, b = clean(l), clean(s)
            if t and b: out.append({"t": t[:100], "b": b[:250], "s": "web"})
        return out

'''

OLD_TURBO = re.compile(r"class TurboSearch:.*?(?=class AutoLearner:)", re.S)
MAIN_FILES = ["autron-leaf.py", "autron-nano.py", "autron-neo.py", "autron-prism.py", "autron-ultra.py"]

def patch_main(name):
    p = ROOT / name
    src = p.read_text(encoding="utf-8").replace("\r\n", "\n")

    src = src.replace("""try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except: SEARCH_AVAILABLE = False""", """try:
    import requests
    from html import unescape
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    print("[!] Missing dependency: pip install requests (web search disabled)")""")

    src = src.replace("Requirements: pip install ollama duckduckgo-search rich",
                      "Requirements: pip install ollama requests rich")

    src, n = OLD_TURBO.subn(ENGINE, src, count=1)
    assert n == 1, f"{name}: TurboSearch not replaced"

    src = src.replace(
        'if is_online() and any(x in q.lower() for x in ["latest", "news", "current", "weather", "time", "today", "now", "who is", "what is"]):',
        'if is_online() and self.search.needs_lookup(q.lower()):')
    src = src.replace(
        'if is_online() and any(x in q.lower() for x in ["latest", "news", "current", "today"]):',
        'if is_online() and self.search.needs_lookup(q.lower()):')

    src = src.replace("</search_instructions>",
"""</search_instructions>

<live_context_rules>
When the user message contains a "LIVE WEB CONTEXT" block, treat it as freshly retrieved ground truth:
- Base factual claims on it and cite sources naturally ("according to Wikipedia...", "...reported by AP").
- If it conflicts with your training data, trust the live context and note that things changed.
- Never invent URLs, dates, or figures that are not in the context or your knowledge.
- If the context is empty or irrelevant, answer from your own knowledge and say clearly if you are unsure or possibly outdated.
- Do NOT talk about the weather unless the user actually asks about weather. Always answer the question that was asked.
</live_context_rules>""")

    p.write_text(src, encoding="utf-8")
    print(f"patched {name}")

OMNI_ENGINE = '''async def search(self, query: str) -> List[Dict]:
        """Reliable multi-query research: Wikipedia (structured facts) first,
        then DuckDuckGo HTML (fresh news/web). Replaces the deprecated
        duckduckgo_search package, whose silent import failure left Omni with
        an empty corpus and canned answers."""
        UA = "AuTron-Omni/1.0 (research assistant; contact: autron-user@localhost) python-requests"
        WIKI = "https://en.wikipedia.org/w/api.php"
        DDG = "https://html.duckduckgo.com/html/"
        from urllib.parse import quote as _quote

        def _clean(s): return unescape(re.sub(r"<.*?>", "", s)).strip()

        def _sync_search():
            results, seen = [], set()

            def add(t, b, u, s):
                k = (t or "").lower()
                if t and b and k not in seen:
                    seen.add(k)
                    results.append({"t": t[:120], "b": b[:300], "u": u, "s": s})

            stop = {"who","what","where","when","why","how","is","are","the","a","an","of","in","on","for","to","and","tell","me","about","current","latest","news"}
            topic = " ".join(w for w in re.sub(r"[^a-zA-Z0-9 ]", " ", query.lower()).split() if w not in stop) or query
            for qq in dict.fromkeys([topic, query]):
                try:
                    r = requests.get(WIKI, params={"action":"query","list":"search","srsearch":qq,"srlimit":4,"format":"json"},
                                     headers={"User-Agent":UA}, timeout=8)
                    titles = [h["title"] for h in r.json()["query"]["search"]]
                    if not titles: continue
                    r2 = requests.get(WIKI, params={"action":"query","prop":"extracts","exintro":1,"explaintext":1,
                                                    "exchars":350,"exlimit":"max","titles":"|".join(titles),"format":"json"},
                                      headers={"User-Agent":UA}, timeout=8)
                    pages = r2.json().get("query", {}).get("pages", {})
                    for t in titles:
                        pg = next((p for p in pages.values() if p.get("title") == t), None)
                        ex = (pg or {}).get("extract", "")
                        if ex: add(t, ex.strip(), "https://en.wikipedia.org/wiki/" + _quote(t.replace(" ", "_")), "wikipedia")
                except Exception: continue
                if len(results) >= 8: break

            queries = [query]
            if len(query.split()) >= 3:
                if any(x in query.lower() for x in ["who", "what", "where", "when", "why"]):
                    queries.append(f"definitive facts and details {query}")
                if any(x in query.lower() for x in ["latest", "recent", "news"]):
                    queries.append(f"latest official reports {query}")
            for q in queries:
                try:
                    r = requests.post(DDG, data={"q": q}, headers={"User-Agent":UA}, timeout=8)
                    html_txt = r.text
                    if "anomaly" in html_txt[:400].lower(): continue  # rate-limit challenge
                    links = re.findall(r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', html_txt, re.S)
                    snips = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html_txt, re.S)
                    hrefs = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"', html_txt)
                    for i, (l, s) in enumerate(list(zip(links, snips))[:4]):
                        u = hrefs[i] if i < len(hrefs) else ""
                        add(_clean(l), _clean(s), u, "web")
                except Exception: continue
                if len(results) >= 12: break
            return results[:12]

        return await asyncio.to_thread(_sync_search)
'''

def patch_omni():
    p = ROOT / "autron-omni.py"
    src = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    src = src.replace("Requirements: pip install ollama duckduckgo-search rich",
                      "Requirements: pip install ollama requests rich")
    src = src.replace("from duckduckgo_search import DDGS", "import requests\nfrom html import unescape")
    old = re.compile(r"async def search\(self, query: str\).*?return await asyncio\.to_thread\(_sync_search\)", re.S)
    src, n = old.subn(OMNI_ENGINE.rstrip("\n"), src, count=1)
    assert n == 1, "omni search not replaced"
    src = src.replace("- Weather/Status: Provide very short and direct answers. State the final figure directly.",
                      "- Factual/Lookup Questions: Answer directly and concisely, grounded in the provided sources. State the key fact first, then supporting detail.")
    p.write_text(src, encoding="utf-8")
    print("patched autron-omni.py")

for f in MAIN_FILES: patch_main(f)
patch_omni()
print("done")
