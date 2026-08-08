"""
ai_engine.py  —  Kinetic Campus CPU & GPU AI Engine
=====================================================
All functions gracefully fall back if a library is missing.

CPU FUNCTIONS:
  cpu_compute_analytics()   — numpy stats on events/registrations
  cpu_summarize_text()      — extractive text summarizer
  cpu_similarity_matrix()   — TF-IDF cosine similarity between events
  cpu_detect_conflicts()    — schedule & location conflict detector
  cpu_trending_score()      — score events by popularity

GPU FUNCTIONS:
  gpu_enhance_image()       — torch tensor brightness/contrast/sharpen
  gpu_batch_embed()         — sentence-transformers batch encoding
  gpu_semantic_search()     — cosine similarity search on GPU
  gpu_recommend()           — GPU-accelerated recommendation scoring

MONITORING:
  get_device_status()       — CPU/GPU/RAM live stats
"""

import os, time, re, math
from collections import Counter

# ══════════════════════════════════════════════════════════
#  DEVICE DETECTION
# ══════════════════════════════════════════════════════════
try:
    import torch
    import torch.nn.functional as F
    TORCH_OK  = True
    DEVICE    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    CUDA_OK   = torch.cuda.is_available()
    GPU_NAME  = torch.cuda.get_device_name(0) if CUDA_OK else None
    GPU_MEM   = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1) if CUDA_OK else 0
    print(f"[AI] PyTorch {torch.__version__} | Device: {DEVICE}" +
          (f" | {GPU_NAME} {GPU_MEM}GB" if CUDA_OK else ""))
except ImportError:
    TORCH_OK = CUDA_OK = False
    DEVICE   = None
    GPU_NAME = GPU_MEM = None
    print("[AI] PyTorch not installed — GPU functions disabled")

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False
    print("[AI] NumPy not installed — CPU analytics disabled")

try:
    from PIL import Image, ImageFilter, ImageEnhance
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from sentence_transformers import SentenceTransformer
    ST_OK    = True
    _ST_MODEL = None          # lazy-loaded
    MODEL_NAME = "all-MiniLM-L6-v2"
except ImportError:
    ST_OK     = False
    _ST_MODEL = None
    MODEL_NAME = None

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False


# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════
def _load_model():
    global _ST_MODEL
    if _ST_MODEL is None and ST_OK and TORCH_OK:
        t0 = time.time()
        _ST_MODEL = SentenceTransformer(MODEL_NAME, device=str(DEVICE))
        print(f"[AI] Model loaded in {time.time()-t0:.1f}s on {DEVICE}")
    return _ST_MODEL


# ══════════════════════════════════════════════════════════
#  CPU FUNCTION 1 — Event Analytics (numpy)
# ══════════════════════════════════════════════════════════
def cpu_compute_analytics(events: list) -> dict:
    """
    Compute statistics on events using numpy vectorized ops.
    Returns dict with charts-ready data.
    """
    result = {
        "total_events":        len(events),
        "total_registered":    0,
        "avg_registered":      0.0,
        "max_registered":      0,
        "capacity_fill_pct":   0.0,
        "month_distribution":  {},
        "semester_distribution": {},
        "top_locations":       [],
        "trending_events":     [],
        "engine":              "NumPy CPU" if NUMPY_OK else "Pure Python",
    }

    if not events:
        return result

    if NUMPY_OK:
        # ── vectorized numpy stats ──────────────────────────
        reg_counts = np.array([ev.get("registered", 0) or 0 for ev in events], dtype=np.float32)
        caps       = np.array([ev.get("capacity",   0) or 0 for ev in events], dtype=np.float32)

        result["total_registered"] = int(reg_counts.sum())
        result["avg_registered"]   = round(float(reg_counts.mean()), 2)
        result["max_registered"]   = int(reg_counts.max())

        # Fill rate — only for events with capacity set
        has_cap  = caps > 0
        if has_cap.any():
            fill_rates = np.where(has_cap, reg_counts / caps * 100, np.nan)
            result["capacity_fill_pct"] = round(float(np.nanmean(fill_rates)), 1)

        # Trending score = registered / max(registered) * 100
        if reg_counts.max() > 0:
            trend_scores = (reg_counts / reg_counts.max() * 100).tolist()
            indexed = sorted(enumerate(trend_scores), key=lambda x: x[1], reverse=True)
            result["trending_events"] = [
                {"title": events[i]["title"], "score": round(s, 1)}
                for i, s in indexed[:5]
            ]
    else:
        # Pure Python fallback
        regs = [ev.get("registered", 0) or 0 for ev in events]
        result["total_registered"] = sum(regs)
        result["avg_registered"]   = round(sum(regs)/len(regs), 2) if regs else 0
        result["max_registered"]   = max(regs) if regs else 0

    # Month distribution (pure Python — works always)
    months = {}
    for ev in events:
        d = str(ev.get("date") or ev.get("event_date") or "")
        if len(d) >= 7:
            m = d[:7]   # "2026-08"
            months[m] = months.get(m, 0) + 1
    result["month_distribution"] = dict(sorted(months.items()))

    # Semester distribution
    sems = Counter(str(ev.get("semester", "?")) for ev in events)
    result["semester_distribution"] = dict(sems.most_common())

    # Top locations
    locs = Counter(ev.get("location", "Unknown") for ev in events)
    result["top_locations"] = [
        {"location": loc, "count": cnt}
        for loc, cnt in locs.most_common(5)
    ]

    # AI Event Demand & Capacity Risk Categorization
    high_demand = []
    moderate    = []
    low_demand  = []

    for ev in events:
        reg = ev.get("registered", 0) or 0
        cap = ev.get("capacity", 0) or 0
        pct = (reg / cap * 100) if cap > 0 else 0

        item = {
            "id": ev.get("id"),
            "title": ev.get("title"),
            "registered": reg,
            "capacity": cap,
            "fill_pct": round(pct, 1)
        }

        if cap > 0 and pct >= 75:
            high_demand.append(item)
        elif reg > 0:
            moderate.append(item)
        else:
            low_demand.append(item)

    result["demand_breakdown"] = {
        "high_demand_count": len(high_demand),
        "moderate_count": len(moderate),
        "low_demand_count": len(low_demand),
        "high_demand_events": high_demand[:5],
        "low_demand_events": low_demand[:5],
    }

    # Department distribution (passed from caller or empty)
    result["department_distribution"] = events[0].get("_dept_stats", {}) if events and "_dept_stats" in events[0] else {}

    return result


# ══════════════════════════════════════════════════════════
#  CPU FUNCTION 2 — Extractive Text Summarizer
# ══════════════════════════════════════════════════════════
def cpu_summarize_text(text: str, max_sentences: int = 2) -> str:
    """
    Extractive summarization — pick the most informative sentences.
    100% CPU, no ML model needed.
    """
    if not text or len(text) < 60:
        return text

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return text

    # Score sentences by word frequency (TF-based)
    all_words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    freq = Counter(all_words)
    # Remove stop words
    stops = {"the","and","for","are","that","this","with","from","will","have",
             "been","they","their","which","were","into","also","each"}
    freq = {w: c for w, c in freq.items() if w not in stops}

    def score_sentence(s):
        words = re.findall(r'\b[a-z]{3,}\b', s.lower())
        return sum(freq.get(w, 0) for w in words)

    scored = [(s, score_sentence(s)) for s in sentences if len(s.strip()) > 20]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Return top sentences in original order
    top = set(s for s, _ in scored[:max_sentences])
    summary = " ".join(s for s in sentences if s in top)
    return summary or sentences[0]


# ══════════════════════════════════════════════════════════
#  CPU FUNCTION 3 — TF-IDF Event Similarity Matrix
# ══════════════════════════════════════════════════════════
def cpu_similarity_matrix(events: list) -> list:
    """
    Compute cosine similarity between all events using TF-IDF.
    Returns list of (event_id, similar_event_id, score) tuples.
    Pure CPU numpy matrix math.
    """
    if not NUMPY_OK or len(events) < 2:
        return []

    # Build vocabulary from all event text
    docs = [
        f"{ev.get('title','')} {ev.get('purpose','')} {ev.get('location','')} {ev.get('semester','')}".lower()
        for ev in events
    ]
    stops = {"the","and","for","are","that","this","with","from","will","have","been"}

    # Tokenize
    tokenized = [
        [w for w in re.findall(r'\b[a-z]{3,}\b', doc) if w not in stops]
        for doc in docs
    ]

    # Build vocabulary
    vocab = sorted(set(w for doc in tokenized for w in doc))
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    V = len(vocab)
    N = len(docs)

    if V == 0:
        return []

    # TF matrix (N x V)
    tf = np.zeros((N, V), dtype=np.float32)
    for i, tokens in enumerate(tokenized):
        c = Counter(tokens)
        total = sum(c.values()) or 1
        for w, cnt in c.items():
            if w in vocab_idx:
                tf[i, vocab_idx[w]] = cnt / total

    # IDF (log(N / df))
    df  = (tf > 0).sum(axis=0).astype(np.float32)
    idf = np.log((N + 1) / (df + 1)) + 1

    # TF-IDF
    tfidf = tf * idf

    # L2 normalize
    norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    tfidf = tfidf / norms

    # Cosine similarity matrix (N x N) via matrix multiply
    sim_matrix = np.dot(tfidf, tfidf.T)

    # Extract top similar pairs (exclude self)
    pairs = []
    for i in range(N):
        for j in range(i + 1, N):
            score = float(sim_matrix[i, j])
            if score > 0.1:
                pairs.append({
                    "event_a": events[i].get("title", ""),
                    "event_b": events[j].get("title", ""),
                    "id_a":    events[i].get("id"),
                    "id_b":    events[j].get("id"),
                    "score":   round(score, 4),
                })

    return sorted(pairs, key=lambda x: x["score"], reverse=True)[:10]


# ══════════════════════════════════════════════════════════
#  CPU FUNCTION 4 — Schedule Conflict Detector
# ══════════════════════════════════════════════════════════
def cpu_detect_conflicts(events: list) -> list:
    """
    Detect events on the same date & same location (scheduling conflicts).
    Pure Python — no library needed.
    """
    conflicts = []
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            a, b = events[i], events[j]
            date_a = str(a.get("event_date") or a.get("date") or "")
            date_b = str(b.get("event_date") or b.get("date") or "")
            loc_a  = str(a.get("location") or "").strip().lower()
            loc_b  = str(b.get("location") or "").strip().lower()

            if date_a and date_a == date_b:
                conflicts.append({
                    "type":    "same_date" if loc_a != loc_b else "same_date_and_location",
                    "event_a": a.get("title"), "id_a": a.get("id"),
                    "event_b": b.get("title"), "id_b": b.get("id"),
                    "date":    date_a,
                    "location_conflict": loc_a == loc_b and loc_a != "",
                })

    return conflicts


# ══════════════════════════════════════════════════════════
#  CPU FUNCTION 5 — Trending Score
# ══════════════════════════════════════════════════════════
def cpu_trending_score(events: list) -> list:
    """
    Score each event by a weighted trending formula:
      score = (registrations * 0.5) + (days_urgency * 0.3) + (fill_rate * 0.2)
    Returns events sorted by trending score.
    """
    from datetime import date
    today = date.today()
    scored = []

    for ev in events:
        reg      = ev.get("registered") or ev.get("join_count") or 0
        cap      = ev.get("capacity") or 0
        date_str = str(ev.get("event_date") or ev.get("date") or "")

        # Days urgency — closer = higher score (max 30 days window)
        urgency = 0
        if date_str and len(date_str) >= 10:
            try:
                ev_date   = date.fromisoformat(date_str[:10])
                days_away = (ev_date - today).days
                if 0 <= days_away <= 30:
                    urgency = max(0, 30 - days_away) / 30 * 100
            except ValueError:
                pass

        # Fill rate
        fill_rate = (reg / cap * 100) if cap > 0 else 0

        # Weighted total
        score = (min(reg, 100) * 0.5) + (urgency * 0.3) + (min(fill_rate, 100) * 0.2)
        scored.append({**ev, "trending_score": round(score, 2)})

    return sorted(scored, key=lambda x: x["trending_score"], reverse=True)


# ══════════════════════════════════════════════════════════
#  GPU FUNCTION 1 — Image Enhancement (torch tensors)
# ══════════════════════════════════════════════════════════
def gpu_enhance_image(image_path: str) -> dict:
    """
    Enhance an uploaded event banner using torch GPU tensor ops.
    Steps: load → normalize → auto-brightness → contrast stretch
           → unsharp mask → save
    Falls back to Pillow CPU if torch not available.
    """
    result = {"success": False, "device": str(DEVICE) if DEVICE else "none", "steps": []}

    if not PIL_OK:
        result["error"] = "Pillow not installed"
        return result

    try:
        img = Image.open(image_path).convert("RGB")
        result["steps"].append("Loaded image")

        if TORCH_OK and NUMPY_OK:
            import numpy as np

            # PIL → numpy → torch tensor on DEVICE
            arr    = np.array(img, dtype=np.float32) / 255.0
            tensor = torch.from_numpy(arr).to(DEVICE)      # shape: H x W x 3
            tensor = tensor.permute(2, 0, 1).unsqueeze(0)  # → 1 x 3 x H x W
            result["steps"].append(f"Tensor on {DEVICE}")

            with torch.no_grad():
                # 1. Auto-brightness
                mean_val = tensor.mean().item()
                if mean_val < 0.3:
                    tensor = torch.clamp(tensor * 1.4, 0, 1)
                    result["steps"].append("Brightness boost (dark image)")
                elif mean_val > 0.7:
                    tensor = torch.clamp(tensor * 0.8, 0, 1)
                    result["steps"].append("Brightness reduce (overexposed)")

                # 2. Contrast stretch (per-channel min-max)
                for c in range(3):
                    ch = tensor[0, c]
                    mn, mx = ch.min(), ch.max()
                    if (mx - mn).item() > 0.05:
                        tensor[0, c] = (ch - mn) / (mx - mn)
                result["steps"].append("Contrast stretched (GPU)")

                # 3. Vibrance boost — saturate colors slightly
                gray = tensor.mean(dim=1, keepdim=True)
                tensor = torch.clamp(gray + 1.15 * (tensor - gray), 0, 1)
                result["steps"].append("Vibrance boost (GPU)")

            # Tensor → PIL → save
            out_np  = (tensor.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
            out_img = Image.fromarray(out_np)

        else:
            # PIL CPU fallback
            out_img = ImageEnhance.Contrast(img).enhance(1.25)
            out_img = ImageEnhance.Brightness(out_img).enhance(1.05)
            out_img = ImageEnhance.Color(out_img).enhance(1.1)
            result["steps"].append("Enhanced with Pillow (CPU fallback)")

        out_img.save(image_path, quality=92, optimize=True)
        result["success"] = True
        result["steps"].append("Saved")

    except Exception as e:
        result["error"] = str(e)

    return result


# ══════════════════════════════════════════════════════════
#  GPU FUNCTION 2 — Batch Embedding
# ══════════════════════════════════════════════════════════
def gpu_batch_embed(texts: list) -> "list | None":
    """
    Encode a list of texts into embeddings using sentence-transformers.
    Runs on GPU if available, CPU otherwise.
    Returns list of numpy arrays, or None if model not available.
    """
    model = _load_model()
    if model is None:
        return None

    t0 = time.time()
    with torch.no_grad():
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            batch_size=32,
            show_progress_bar=False,
            device=str(DEVICE),
        )
    elapsed = round(time.time() - t0, 3)
    print(f"[AI] Embedded {len(texts)} texts in {elapsed}s on {DEVICE}")
    return embeddings


# ══════════════════════════════════════════════════════════
#  GPU FUNCTION 3 — Semantic Search
# ══════════════════════════════════════════════════════════
def gpu_semantic_search(query: str, events: list, top_k: int = 10) -> list:
    """
    Semantic similarity search using sentence embeddings.
    GPU: runs cosine similarity as torch matrix multiply.
    CPU: runs as numpy dot product.
    Returns [(event, score), ...]
    """
    if not events:
        return []

    model = _load_model()

    if model and TORCH_OK:
        docs = [
            f"{ev.get('title','')}. {ev.get('purpose','')}. "
            f"{ev.get('location','')}. Semester {ev.get('semester','')}"
            for ev in events
        ]
        with torch.no_grad():
            q_emb  = model.encode(query, convert_to_tensor=True, device=DEVICE)
            d_embs = model.encode(docs,  convert_to_tensor=True, device=DEVICE)
            scores = F.cosine_similarity(q_emb.unsqueeze(0), d_embs, dim=1).cpu().tolist()

        ranked = sorted(zip(events, scores), key=lambda x: x[1], reverse=True)
        return [(ev, sc) for ev, sc in ranked if sc > 0.15][:top_k]

    # Keyword fallback
    def kw(ev):
        hay = f"{ev.get('title','')} {ev.get('purpose','')} {ev.get('location','')}".lower()
        q   = query.lower()
        return sum(10 for w in q.split() if w in hay) + (50 if q in hay else 0)

    results = [(ev, kw(ev)) for ev in events]
    return [(ev, sc) for ev, sc in sorted(results, key=lambda x: x[1], reverse=True) if sc > 0][:top_k]


# backward-compat alias
def semantic_search(query, events, top_k=10):
    return gpu_semantic_search(query, events, top_k)

enhance_banner = gpu_enhance_image


# ══════════════════════════════════════════════════════════
#  GPU FUNCTION 4 — Recommendation via Tensor Dot Product
# ══════════════════════════════════════════════════════════
def gpu_recommend(viewed_ids: list, all_events: list, top_k: int = 3) -> list:
    """
    If user has viewed events, embed those + all events,
    then compute mean of viewed embeddings and find closest unseen events.
    GPU accelerated via torch. Falls back to popularity scoring on CPU.
    """
    from datetime import date
    today_str = str(date.today())

    unseen = [ev for ev in all_events if str(ev.get("id")) not in [str(v) for v in viewed_ids]]
    future = [ev for ev in unseen if str(ev.get("date", "") or "") >= today_str]

    if not future:
        future = unseen

    model = _load_model()

    if model and TORCH_OK and viewed_ids:
        viewed = [ev for ev in all_events if str(ev.get("id")) in [str(v) for v in viewed_ids]]
        if viewed:
            def ev_text(e):
                return f"{e.get('title','')} {e.get('purpose','')} {e.get('semester','')}"

            with torch.no_grad():
                viewed_embs = model.encode([ev_text(e) for e in viewed],
                                           convert_to_tensor=True, device=DEVICE)
                future_embs = model.encode([ev_text(e) for e in future],
                                           convert_to_tensor=True, device=DEVICE)
                profile = viewed_embs.mean(dim=0)
                scores  = F.cosine_similarity(profile.unsqueeze(0), future_embs, dim=1).cpu().tolist()

            ranked = sorted(zip(future, scores), key=lambda x: x[1], reverse=True)
            return [ev for ev, _ in ranked[:top_k]]

    # CPU popularity fallback
    def pop_score(ev):
        reg = ev.get("registered") or 0
        cap = ev.get("capacity")   or 0
        fill = (reg / cap) if cap > 0 else 0
        return reg * 0.6 + fill * 40

    return sorted(future, key=pop_score, reverse=True)[:top_k]


# ══════════════════════════════════════════════════════════
#  MONITORING — Device Status
# ══════════════════════════════════════════════════════════
def get_device_status() -> dict:
    status = {
        "torch":          TORCH_OK,
        "cuda":           CUDA_OK,
        "transformers":   ST_OK,
        "model_name":     MODEL_NAME,
        "model_loaded":   _ST_MODEL is not None,
        "device_info":    "",
        "cpu_cores":      os.cpu_count(),
        "numpy":          NUMPY_OK,
        "gpu_name":       GPU_NAME,
        "gpu_vram_gb":    GPU_MEM,
    }

    # CPU info
    if PSUTIL_OK:
        status["cpu_percent"]  = psutil.cpu_percent(interval=0.1)
        status["ram_used_gb"]  = round(psutil.virtual_memory().used  / 1e9, 2)
        status["ram_total_gb"] = round(psutil.virtual_memory().total / 1e9, 2)
        status["ram_pct"]      = psutil.virtual_memory().percent

    # GPU info
    if CUDA_OK:
        status["gpu_mem_used_gb"] = round(torch.cuda.memory_allocated(0) / 1e9, 3)
        status["gpu_mem_total_gb"]= GPU_MEM
        status["device_info"]     = f"🟢 NVIDIA {GPU_NAME} ({GPU_MEM}GB)"
    elif TORCH_OK:
        status["device_info"] = f"🔵 CPU ({os.cpu_count()} cores)"
    else:
        status["device_info"] = "⚪ Keyword mode"

    return status
