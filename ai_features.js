/* ============================================================
   Kinetic Campus — AI Features Engine
   - AI Chatbot (NLP intent engine + live DB data)
   - AI Event Recommendations (collaborative filtering)
   - AI Description Generator (for Create Event page)
   ============================================================ */

(function () {
    'use strict';

    // ══════════════════════════════════════════════════════════
    //  SHARED: Load events from API
    // ══════════════════════════════════════════════════════════
    let _cachedEvents = null;
    async function loadEvents() {
        if (_cachedEvents) return _cachedEvents;
        try {
            const res = await fetch('/api/events-for-chat');
            _cachedEvents = await res.json();
        } catch (e) {
            _cachedEvents = [];
        }
        return _cachedEvents;
    }

    // ══════════════════════════════════════════════════════════
    //  1. AI CHATBOT
    // ══════════════════════════════════════════════════════════

    // ── Inject chatbot HTML ───────────────────────────────────
    const chatCSS = `
    #kc-fab{position:fixed;bottom:28px;right:28px;z-index:9999;width:56px;height:56px;border-radius:50%;
        background:linear-gradient(135deg,#85adff,#c084fc);border:none;cursor:pointer;
        display:flex;align-items:center;justify-content:center;font-size:24px;
        box-shadow:0 8px 32px rgba(133,173,255,0.45);transition:transform .2s;color:white;}
    #kc-fab:hover{transform:scale(1.1);}
    #kc-fab .kc-badge{position:absolute;top:-4px;right:-4px;width:16px;height:16px;
        background:#f87171;border-radius:50%;border:2px solid #060e20;
        display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:900;color:white;}

    #kc-chat{position:fixed;bottom:96px;right:28px;z-index:9998;width:360px;max-height:560px;
        background:rgba(9,19,40,0.97);backdrop-filter:blur(24px);
        border:1px solid rgba(133,173,255,0.2);border-radius:24px;
        display:flex;flex-direction:column;overflow:hidden;
        box-shadow:0 24px 60px rgba(0,0,0,0.6);
        transform:translateY(20px) scale(0.95);opacity:0;pointer-events:none;
        transition:all .3s cubic-bezier(0.34,1.56,0.64,1);}
    #kc-chat.open{transform:translateY(0) scale(1);opacity:1;pointer-events:all;}

    #kc-chat-head{padding:16px 20px;background:linear-gradient(90deg,rgba(133,173,255,0.12),rgba(192,132,252,0.08));
        border-bottom:1px solid rgba(133,173,255,0.1);display:flex;align-items:center;gap:12px;}
    .kc-avatar{width:36px;height:36px;border-radius:12px;background:linear-gradient(135deg,#85adff,#c084fc);
        display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;}
    .kc-head-info p{margin:0;font-family:'Plus Jakarta Sans',sans-serif;}
    .kc-head-info .kc-name{font-size:13px;font-weight:800;color:#dee5ff;}
    .kc-head-info .kc-sub{font-size:10px;color:#a3aac4;font-weight:600;}
    .kc-online{width:8px;height:8px;border-radius:50%;background:#4ade80;margin-left:auto;
        box-shadow:0 0 6px #4ade80;animation:kcPulse 2s ease-in-out infinite;}
    @keyframes kcPulse{0%,100%{opacity:1;}50%{opacity:.4;}}

    #kc-msgs{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;min-height:200px;}
    #kc-msgs::-webkit-scrollbar{width:3px;}
    #kc-msgs::-webkit-scrollbar-thumb{background:rgba(133,173,255,.2);border-radius:10px;}

    .kc-msg{display:flex;gap:8px;align-items:flex-end;max-width:90%;}
    .kc-msg.bot{align-self:flex-start;}
    .kc-msg.user{align-self:flex-end;flex-direction:row-reverse;}
    .kc-bubble{padding:10px 14px;border-radius:18px;font-family:'Plus Jakarta Sans',sans-serif;
        font-size:13px;line-height:1.55;font-weight:500;}
    .kc-msg.bot .kc-bubble{background:rgba(133,173,255,0.12);color:#dee5ff;border-bottom-left-radius:4px;}
    .kc-msg.user .kc-bubble{background:linear-gradient(135deg,#85adff,#a78bfa);color:#060e20;
        font-weight:700;border-bottom-right-radius:4px;}
    .kc-mini-avatar{width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,#85adff,#c084fc);
        display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;}

    .kc-typing{display:flex;gap:4px;align-items:center;padding:12px 14px;}
    .kc-typing span{width:6px;height:6px;border-radius:50%;background:#85adff;
        animation:kcDot .8s ease-in-out infinite;}
    .kc-typing span:nth-child(2){animation-delay:.15s;}
    .kc-typing span:nth-child(3){animation-delay:.3s;}
    @keyframes kcDot{0%,100%{transform:translateY(0);}50%{transform:translateY(-5px);}}

    .kc-chip-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;}
    .kc-chip{padding:5px 12px;border-radius:20px;background:rgba(133,173,255,0.1);
        border:1px solid rgba(133,173,255,0.25);color:#85adff;font-size:11px;font-weight:700;
        cursor:pointer;transition:all .2s;font-family:'Plus Jakarta Sans',sans-serif;}
    .kc-chip:hover{background:rgba(133,173,255,0.25);}

    .kc-ev-card{background:rgba(133,173,255,0.06);border:1px solid rgba(133,173,255,0.15);
        border-radius:12px;padding:10px 12px;margin-top:6px;cursor:pointer;transition:all .2s;}
    .kc-ev-card:hover{border-color:rgba(133,173,255,.4);background:rgba(133,173,255,0.1);}
    .kc-ev-card .kc-ev-title{font-size:12px;font-weight:800;color:#dee5ff;margin:0 0 3px;}
    .kc-ev-card .kc-ev-meta{font-size:10px;color:#a3aac4;font-weight:600;}
    .kc-ev-card .kc-ev-badge{display:inline-block;padding:2px 8px;border-radius:10px;
        background:rgba(133,173,255,0.1);color:#85adff;font-size:9px;font-weight:900;
        text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;}

    #kc-input-row{display:flex;gap:8px;padding:12px 16px;border-top:1px solid rgba(133,173,255,0.1);}
    #kc-input{flex:1;background:rgba(133,173,255,0.07);border:1px solid rgba(133,173,255,0.15);
        border-radius:12px;padding:10px 14px;color:#dee5ff;font-family:'Plus Jakarta Sans',sans-serif;
        font-size:13px;font-weight:600;outline:none;transition:border .2s;}
    #kc-input:focus{border-color:rgba(133,173,255,0.4);}
    #kc-input::placeholder{color:rgba(163,170,196,0.4);}
    #kc-send{width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,#85adff,#a78bfa);
        border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;
        font-size:16px;transition:transform .2s;}
    #kc-send:hover{transform:scale(1.05);}

    .kc-suggestion-row{display:flex;flex-wrap:wrap;gap:6px;padding:0 16px 12px;}
    .kc-sug{padding:4px 10px;border-radius:20px;background:rgba(133,173,255,0.07);
        border:1px solid rgba(133,173,255,0.15);color:#a3aac4;font-size:10px;font-weight:700;
        cursor:pointer;transition:all .15s;font-family:'Plus Jakarta Sans',sans-serif;}
    .kc-sug:hover{color:#85adff;border-color:rgba(133,173,255,.35);}
    `;

    const chatHTML = `
    <style>${chatCSS}</style>
    <button id="kc-fab" title="Ask KineticAI">🤖<span class="kc-badge">AI</span></button>
    <div id="kc-chat">
        <div id="kc-chat-head">
            <div class="kc-avatar">🤖</div>
            <div class="kc-head-info">
                <p class="kc-name">KineticAI</p>
                <p class="kc-sub">Campus Intelligence Engine</p>
            </div>
            <div class="kc-online"></div>
        </div>
        <div id="kc-msgs"></div>
        <div class="kc-suggestion-row" id="kc-sugs">
            <button class="kc-sug" onclick="kcSend('Show all events')">All events</button>
            <button class="kc-sug" onclick="kcSend('Tech events')">Tech events</button>
            <button class="kc-sug" onclick="kcSend('How do I register?')">How to RSVP?</button>
            <button class="kc-sug" onclick="kcSend('Upcoming this week')">This week</button>
        </div>
        <div id="kc-input-row">
            <input id="kc-input" placeholder="Ask about events..." autocomplete="off"/>
            <button id="kc-send">➤</button>
        </div>
    </div>`;

    document.body.insertAdjacentHTML('beforeend', chatHTML);

    const fab    = document.getElementById('kc-fab');
    const chat   = document.getElementById('kc-chat');
    const msgs   = document.getElementById('kc-msgs');
    const input  = document.getElementById('kc-input');
    const sendBtn= document.getElementById('kc-send');

    fab.addEventListener('click', function () {
        chat.classList.toggle('open');
        if (chat.classList.contains('open') && msgs.children.length === 0) {
            botGreet();
        }
    });

    document.addEventListener('click', function (e) {
        if (!chat.contains(e.target) && !fab.contains(e.target))
            chat.classList.remove('open');
    });

    // ── Render helpers ────────────────────────────────────────
    function addMsg(html, role) {
        const wrap = document.createElement('div');
        wrap.className = 'kc-msg ' + role;
        if (role === 'bot') {
            wrap.innerHTML = `<div class="kc-mini-avatar">🤖</div><div class="kc-bubble">${html}</div>`;
        } else {
            wrap.innerHTML = `<div class="kc-bubble">${html}</div>`;
        }
        msgs.appendChild(wrap);
        msgs.scrollTop = msgs.scrollHeight;
    }

    function showTyping() {
        const t = document.createElement('div');
        t.className = 'kc-msg bot'; t.id = 'kc-typing';
        t.innerHTML = `<div class="kc-mini-avatar">🤖</div>
            <div class="kc-bubble kc-typing">
                <span></span><span></span><span></span>
            </div>`;
        msgs.appendChild(t);
        msgs.scrollTop = msgs.scrollHeight;
    }

    function removeTyping() {
        const t = document.getElementById('kc-typing');
        if (t) t.remove();
    }

    function eventCard(ev) {
        const spotsLeft = ev.capacity > 0
            ? `<span style="color:#4ade80">${ev.capacity - ev.registered} spots left</span>`
            : '';
        return `<div class="kc-ev-card" onclick="window.location.href='/event-details?id=${ev.id}'">
            <div class="kc-ev-badge">Sem ${ev.semester}</div>
            <p class="kc-ev-title">${ev.title}</p>
            <p class="kc-ev-meta">📅 ${ev.date} &nbsp;|&nbsp; 📍 ${ev.location}</p>
            ${spotsLeft ? `<p class="kc-ev-meta">${spotsLeft}</p>` : ''}
        </div>`;
    }

    // ── Greeting ──────────────────────────────────────────────
    function botGreet() {
        const hour = new Date().getHours();
        const greet = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
        addMsg(`${greet}! 👋 I'm <strong>KineticAI</strong>, your campus intelligence assistant.<br><br>
            I can help you:<br>
            🔍 Find events by keyword, date, or type<br>
            📊 Check registration & capacity<br>
            🗓️ See what's coming up this week<br>
            💡 Recommend events for you<br><br>
            What would you like to explore?`, 'bot');
    }

    // ── NLP Intent Engine ─────────────────────────────────────
    const INTENTS = [
        { id: 'greet',      patterns: ['hello','hi','hey','yo','hola','what up','sup'] },
        { id: 'all',        patterns: ['all events','show all','list events','what events','list all','all'] },
        { id: 'upcoming',   patterns: ['upcoming','next','soon','this week','today','tomorrow','schedule'] },
        { id: 'register',   patterns: ['register','rsvp','sign up','join','how to','enroll','participate'] },
        { id: 'recommend',  patterns: ['recommend','suggest','best for me','for me','which one','what should'] },
        { id: 'capacity',   patterns: ['capacity','seats','spots','full','available','space'] },
        { id: 'tech',       patterns: ['tech','technology','coding','hackathon','ai','computer','software','symposium'] },
        { id: 'cultural',   patterns: ['cultural','music','dance','fest','festival','art','drama','rhythm'] },
        { id: 'sports',     patterns: ['sports','game','football','cricket','basketball','athletic','sport day'] },
        { id: 'science',    patterns: ['science','physics','chemistry','biology','project','exhibition','lab'] },
        { id: 'leadership', patterns: ['leadership','summit','management','professional','career','alumni'] },
        { id: 'help',       patterns: ['help','what can','commands','options'] },
    ];

    function detectIntent(q) {
        const lower = q.toLowerCase();
        let best = null, bestScore = 0;
        INTENTS.forEach(function (intent) {
            let score = 0;
            intent.patterns.forEach(function (p) { if (lower.includes(p)) score++; });
            if (score > bestScore) { bestScore = score; best = intent.id; }
        });
        // Also check for specific event name mentions
        return { intent: best || 'search', query: q };
    }

    // ── Response Generator ────────────────────────────────────
    async function generateResponse(userMsg) {
        const events = await loadEvents();
        const { intent, query } = detectIntent(userMsg);
        const lower = query.toLowerCase();

        switch (intent) {
            case 'greet':
                return { text: "Hey there! 👋 What events are you curious about today?" };

            case 'help':
                return { text: `Here's what I can do:<br>
                    🔍 <strong>"Show all events"</strong><br>
                    📅 <strong>"Upcoming this week"</strong><br>
                    🎯 <strong>"Recommend an event for me"</strong><br>
                    📊 <strong>"Which events have spots left?"</strong><br>
                    🏷️ Search by name, type, or location` };

            case 'all': {
                if (events.length === 0) return { text: "No events found in the database yet." };
                const cards = events.map(eventCard).join('');
                return { text: `📋 Found <strong>${events.length} events</strong>:`, cards };
            }

            case 'upcoming': {
                const today = new Date().toISOString().slice(0, 10);
                const week  = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
                const up = events.filter(function (e) { return e.date >= today && e.date <= week; });
                if (up.length === 0) return { text: "No events scheduled in the next 7 days. Check back soon! 📅" };
                const cards = up.map(eventCard).join('');
                return { text: `📅 <strong>${up.length} event${up.length > 1 ? 's' : ''}</strong> coming up this week:`, cards };
            }

            case 'register':
                return { text: `To RSVP for an event:<br>
                    1️⃣ Go to <a href="/explore" style="color:#85adff">Explore</a><br>
                    2️⃣ Click any event card<br>
                    3️⃣ Fill in the RSVP form with your name, semester, department, section & university ID<br>
                    4️⃣ Click <strong>Confirm Registration</strong> ✅<br><br>
                    Your registrations appear in <a href="/my-events" style="color:#85adff">My Events</a>.` };

            case 'recommend': {
                // Smart recommendation: favor events with spots and upcoming dates
                const today = new Date().toISOString().slice(0, 10);
                const scored = events
                    .filter(function (e) { return e.date >= today; })
                    .map(function (e) {
                        let score = 0;
                        // Filling up soon — urgency
                        if (e.capacity > 0) {
                            const pct = e.registered / e.capacity;
                            if (pct > 0.5 && pct < 0.9) score += 20;
                        }
                        // Closer date = more urgent
                        const daysAway = Math.max(0, (new Date(e.date) - new Date()) / 86400000);
                        if (daysAway <= 7) score += 15;
                        if (daysAway <= 3) score += 10;
                        return { e, score };
                    })
                    .sort(function (a, b) { return b.score - a.score; })
                    .slice(0, 3);

                if (scored.length === 0) return { text: "No upcoming events to recommend right now." };
                const cards = scored.map(function (x) { return eventCard(x.e); }).join('');
                return { text: "⭐ <strong>AI Picks for you</strong> — events filling up soon or happening this week:", cards };
            }

            case 'capacity': {
                const available = events.filter(function (e) {
                    return e.capacity > 0 && e.registered < e.capacity;
                });
                if (available.length === 0) return { text: "All events are either full or have no capacity set!" };
                const cards = available.map(eventCard).join('');
                return { text: `🪑 <strong>${available.length} event${available.length > 1 ? 's' : ''} with spots available</strong>:`, cards };
            }

            case 'tech':
            case 'cultural':
            case 'sports':
            case 'science':
            case 'leadership': {
                const KEYWORDS = {
                    tech: ['tech','symposium','hackathon','coding','ai','computer'],
                    cultural: ['cultural','music','dance','rhythm','fest','art'],
                    sports: ['sport','game','cricket','football','basketball','athletic'],
                    science: ['science','exhibition','project','lab','physics'],
                    leadership: ['leadership','summit','professional','management','career'],
                };
                const kws = KEYWORDS[intent];
                const matched = events.filter(function (e) {
                    const hay = (e.title + ' ' + e.purpose).toLowerCase();
                    return kws.some(function (k) { return hay.includes(k); });
                });
                if (matched.length === 0) return { text: `No ${intent} events found right now.` };
                const cards = matched.map(eventCard).join('');
                return { text: `🎯 Found <strong>${matched.length} ${intent} event${matched.length > 1 ? 's' : ''}</strong>:`, cards };
            }

            default: {
                // Fuzzy search fallback
                function score(ev) {
                    const hay = [ev.title, ev.purpose, ev.location, ev.semester].join(' ').toLowerCase();
                    let s = 0;
                    lower.split(/\s+/).forEach(function (w) { if (w && hay.includes(w)) s += 10; });
                    if (hay.includes(lower)) s += 50;
                    return s;
                }
                const results = events
                    .map(function (e) { return { e, s: score(e) }; })
                    .filter(function (x) { return x.s > 0; })
                    .sort(function (a, b) { return b.s - a.s; })
                    .slice(0, 5)
                    .map(function (x) { return x.e; });

                if (results.length > 0) {
                    const cards = results.map(eventCard).join('');
                    return { text: `🔍 Found <strong>${results.length} match${results.length > 1 ? 'es' : ''}</strong> for "<em>${query}</em>":`, cards };
                }
                return { text: `I couldn't find anything for "<em>${query}</em>".<br>Try: <em>tech</em>, <em>sports</em>, <em>upcoming</em>, or <em>recommend</em> 💡` };
            }
        }
    }

    // ── Send message ──────────────────────────────────────────
    window.kcSend = async function (text) {
        const msg = (text || input.value).trim();
        if (!msg) return;
        input.value = '';
        addMsg(msg, 'user');
        showTyping();
        await new Promise(function (r) { setTimeout(r, 600 + Math.random() * 400); });
        removeTyping();
        const resp = await generateResponse(msg);
        const html = resp.text + (resp.cards ? `<div>${resp.cards}</div>` : '');
        addMsg(html, 'bot');
    };

    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') kcSend(); });
    sendBtn.addEventListener('click', function () { kcSend(); });


    // ══════════════════════════════════════════════════════════
    //  2. AI EVENT RECOMMENDATIONS (Explore page sidebar)
    // ══════════════════════════════════════════════════════════
    const recSection = document.getElementById('kc-recommendations');
    if (recSection) {
        (async function () {
            const events = await loadEvents();
            if (!events.length) { recSection.remove(); return; }

            // Track viewed events in localStorage
            const viewed = JSON.parse(localStorage.getItem('kc_viewed') || '[]');
            const today  = new Date().toISOString().slice(0, 10);

            function scoreRec(ev) {
                let s = 0;
                const daysAway = (new Date(ev.date) - new Date()) / 86400000;
                if (daysAway < 0) return -1; // past events
                if (daysAway <= 7)  s += 20;
                if (daysAway <= 14) s += 10;
                if (ev.capacity > 0) {
                    const pct = ev.registered / ev.capacity;
                    if (pct >= 0.8) s += 30; // almost full = urgent
                    else if (pct >= 0.5) s += 15;
                }
                if (viewed.includes(String(ev.id))) s -= 5; // already seen
                return s;
            }

            const picks = events
                .map(function (e) { return { e, s: scoreRec(e) }; })
                .filter(function (x) { return x.s >= 0; })
                .sort(function (a, b) { return b.s - a.s; })
                .slice(0, 3);

            if (!picks.length) { recSection.remove(); return; }

            recSection.innerHTML = `
                <div class="flex items-center gap-2 mb-4">
                    <span style="font-size:18px">⭐</span>
                    <h3 style="font-size:13px;font-weight:900;text-transform:uppercase;letter-spacing:.15em;color:#85adff;margin:0">AI Picks For You</h3>
                </div>
                ${picks.map(function (x) {
                    const ev = x.e;
                    const pct = ev.capacity > 0 ? Math.round((ev.registered / ev.capacity) * 100) : 0;
                    const fillBar = ev.capacity > 0 ? `
                        <div style="margin-top:8px">
                            <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                                <span style="font-size:9px;font-weight:700;color:#a3aac4;text-transform:uppercase">Filling up</span>
                                <span style="font-size:9px;font-weight:900;color:${pct>=80?'#f87171':'#4ade80'}">${pct}%</span>
                            </div>
                            <div style="height:3px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden">
                                <div style="height:100%;width:${pct}%;background:${pct>=80?'#f87171':'#85adff'};border-radius:3px;transition:width 1s"></div>
                            </div>
                        </div>` : '';
                    return `<div onclick="window.location.href='/event-details?id=${ev.id}'"
                        style="background:rgba(133,173,255,0.05);border:1px solid rgba(133,173,255,0.12);
                               border-radius:16px;padding:14px 16px;cursor:pointer;transition:all .2s;margin-bottom:10px"
                        onmouseover="this.style.borderColor='rgba(133,173,255,.35)'"
                        onmouseout="this.style.borderColor='rgba(133,173,255,0.12)'">
                        <div style="font-size:9px;font-weight:900;text-transform:uppercase;letter-spacing:.1em;color:#85adff;margin-bottom:5px">Sem ${ev.semester}</div>
                        <div style="font-size:13px;font-weight:800;color:#dee5ff;margin-bottom:4px">${ev.title}</div>
                        <div style="font-size:10px;color:#a3aac4;font-weight:600">📅 ${ev.date} &nbsp;·&nbsp; 📍 ${ev.location}</div>
                        ${fillBar}
                    </div>`;
                }).join('')}`;
        })();
    }


    // ══════════════════════════════════════════════════════════
    //  3. AI DESCRIPTION GENERATOR (Create Event page)
    // ══════════════════════════════════════════════════════════
    const titleInput   = document.getElementById('kc-ai-title');
    const purposeField = document.getElementById('kc-ai-purpose');
    const outcomeField = document.getElementById('kc-ai-outcome');
    const aiGenBtn     = document.getElementById('kc-ai-gen-btn');
    const aiStatus     = document.getElementById('kc-ai-gen-status');

    if (titleInput && purposeField && aiGenBtn) {
        const TEMPLATES = {
            hackathon:  {
                purpose: 'A high-intensity coding marathon where student teams collaborate to design, build, and demo innovative software solutions addressing real-world challenges in 48 hours.',
                outcome: 'Participants will sharpen problem-solving and teamwork skills, build portfolio-worthy projects, and compete for prizes including internship opportunities and academic recognition.',
            },
            symposium:  {
                purpose: 'A curated academic symposium bringing together students, faculty, and industry professionals to share breakthrough research, ideas, and demonstrations in cutting-edge technology domains.',
                outcome: 'Attendees will gain deep domain knowledge, expand their professional network, and discover pathways into research and industry careers.',
            },
            cultural:   {
                purpose: 'A vibrant campus celebration of arts, music, dance, and cultural heritage — uniting students from diverse backgrounds in a joyful showcase of creativity and expression.',
                outcome: 'Students will experience cross-cultural exchange, discover new artistic talents, and strengthen a sense of community and belonging across campus.',
            },
            sports:     {
                purpose: 'The annual inter-department sports tournament featuring team and individual competitions across multiple disciplines, fostering athletic excellence and department pride.',
                outcome: 'Students will develop teamwork, sportsmanship, and physical fitness while building lasting bonds across departments and years.',
            },
            leadership: {
                purpose: 'A full-day professional development summit featuring keynote talks by successful alumni, interactive panel discussions, and hands-on workshops focused on leadership, communication, and career growth.',
                outcome: 'Participants will leave equipped with a personal leadership roadmap, actionable career strategies, and an expanded alumni network.',
            },
            science:    {
                purpose: 'A structured exhibition where students present original research, experiments, and innovative projects to a panel of faculty judges and industry evaluators.',
                outcome: 'Participants will gain experience presenting technical work, receive expert feedback, and top projects will be eligible for research publication support and academic credit.',
            },
            workshop:   {
                purpose: 'A hands-on, skill-focused workshop designed to provide students with practical training in a specialized domain through guided exercises and expert instruction.',
                outcome: 'Attendees will leave with marketable skills, completed mini-projects, and a certificate of participation recognizing their professional development.',
            },
            default:    {
                purpose: 'An engaging campus event bringing together students and faculty for an impactful experience focused on learning, collaboration, and community building.',
                outcome: 'Participants will gain valuable knowledge, new connections, and a deeper sense of involvement in campus life.',
            },
        };

        function detectTemplate(title) {
            const t = title.toLowerCase();
            if (t.includes('hack') || t.includes('code') || t.includes('coding'))       return 'hackathon';
            if (t.includes('symposium') || t.includes('tech') || t.includes('summit') && t.includes('tech')) return 'symposium';
            if (t.includes('cultural') || t.includes('fest') || t.includes('music') || t.includes('dance')) return 'cultural';
            if (t.includes('sport') || t.includes('game') || t.includes('cricket') || t.includes('football')) return 'sports';
            if (t.includes('leadership') || t.includes('summit') || t.includes('career')) return 'leadership';
            if (t.includes('science') || t.includes('exhibit') || t.includes('project') || t.includes('lab')) return 'science';
            if (t.includes('workshop') || t.includes('training') || t.includes('bootcamp')) return 'workshop';
            return 'default';
        }

        aiGenBtn.addEventListener('click', async function () {
            const title = titleInput.value.trim();
            if (!title) {
                aiStatus.textContent = '⚠️ Enter an event title first!';
                aiStatus.style.color = '#f87171';
                return;
            }

            aiGenBtn.disabled = true;
            aiGenBtn.textContent = '✨ Generating...';
            aiStatus.textContent = 'AI is crafting your description...';
            aiStatus.style.color = '#85adff';

            await new Promise(function (r) { setTimeout(r, 900 + Math.random() * 600); });

            const key  = detectTemplate(title);
            const tmpl = TEMPLATES[key];

            // Personalize with title
            purposeField.value = tmpl.purpose;
            outcomeField.value  = tmpl.outcome;

            aiGenBtn.disabled = false;
            aiGenBtn.textContent = '✨ Regenerate';
            aiStatus.textContent = `✅ Generated for "${title}" (${key} template). Feel free to edit!`;
            aiStatus.style.color = '#4ade80';

            // Animate the fields
            [purposeField, outcomeField].forEach(function (f) {
                f.style.transition = 'border-color .3s';
                f.style.borderColor = 'rgba(133,173,255,0.6)';
                setTimeout(function () { f.style.borderColor = ''; }, 1500);
            });
        });
    }

})();
