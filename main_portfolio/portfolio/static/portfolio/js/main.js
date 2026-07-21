/* ═══════════════════════════════════════════════════════════════════════════
   PORTFOLIO — MAIN.JS
   ═══════════════════════════════════════════════════════════════════════════ */

// TYPED ROLES — roles array is injected from Django template via window.TYPED_ROLES
const roles = window.TYPED_ROLES || ['Backend Engineer'];
let ri = 0, ci = 0, deleting = false;
const el = document.getElementById('typed-role');

function type() {
  if (!el) return;
  const cur = roles[ri];
  if (!deleting) {
    el.textContent = cur.slice(0, ++ci);
    if (ci === cur.length) { deleting = true; return setTimeout(type, 2000); }
  } else {
    el.textContent = cur.slice(0, --ci);
    if (ci === 0) { deleting = false; ri = (ri + 1) % roles.length; return setTimeout(type, 400); }
  }
  setTimeout(type, deleting ? 38 : 72);
}
type();

// SCROLL REVEAL
const obs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      const idx = Array.from(e.target.parentElement?.children || []).indexOf(e.target);
      setTimeout(() => e.target.classList.add('visible'), idx * 70);
      obs.unobserve(e.target);
    }
  });
}, { threshold: 0.1 });
document.querySelectorAll('.reveal').forEach(el => obs.observe(el));

// COUNTER ANIMATION
function animateCounter(el, target) {
  let cur = 0;
  const showPlus = el.dataset.showPlus === 'true';
  const step = Math.ceil(target / 40);
  const timer = setInterval(() => {
    cur = Math.min(cur + step, target);
    el.textContent = cur + (showPlus ? '+' : '');
    if (cur >= target) clearInterval(timer);
  }, 40);
}

const counterObs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      const num = e.target.querySelector('.stat-num');
      if (num) animateCounter(num, parseInt(num.dataset.target));
      counterObs.unobserve(e.target);
    }
  });
}, { threshold: 0.3 });
document.querySelectorAll('.stat').forEach(el => counterObs.observe(el));

// SCROLL PROGRESS BAR & ACTIVE NAV
const sects = document.querySelectorAll('section[id]');
const navAs = document.querySelectorAll('.nav-links a');
const scrollProgressBar = document.getElementById('scrollProgress');

window.addEventListener('scroll', () => {
  // Update top scroll progress line
  if (scrollProgressBar) {
    const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const scrolled = height > 0 ? (winScroll / height) * 100 : 0;
    scrollProgressBar.style.width = scrolled + '%';
  }

  // Active Nav Highlighting
  let cur = '';
  sects.forEach(s => { if (window.scrollY >= s.offsetTop - 130) cur = s.id; });
  navAs.forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === '#' + cur);
  });
});

// HERO TERMINAL COPY BUTTON
const termCopyBtn = document.getElementById('termCopyBtn');
if (termCopyBtn) {
  termCopyBtn.addEventListener('click', () => {
    const termBody = document.querySelector('.term-body');
    if (!termBody) return;
    const codeText = termBody.innerText || termBody.textContent;
    navigator.clipboard.writeText(codeText.trim()).then(() => {
      termCopyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
      termCopyBtn.style.color = '#10B981';
      termCopyBtn.style.borderColor = '#10B981';
      setTimeout(() => {
        termCopyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
        termCopyBtn.style.color = '#94a3b8';
        termCopyBtn.style.borderColor = 'rgba(255,255,255,0.15)';
      }, 2500);
    }).catch(() => {});
  });
}

// PROACTIVE AI THOUGHT BUBBLE NUDGE
setTimeout(() => {
  const bubble = document.getElementById('chatThoughtBubble');
  const textEl = document.getElementById('chatThoughtText');
  if (bubble && textEl && !sessionStorage.getItem('ai_nudge_shown')) {
    textEl.innerHTML = 'Hi! Click to schedule an interview with Sahil 👋';
    bubble.classList.add('visible');
    sessionStorage.setItem('ai_nudge_shown', 'true');
    setTimeout(() => {
      bubble.classList.remove('visible');
    }, 6000);
  }
}, 3500);

// MOBILE MENU
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');
const mobileClose = document.getElementById('mobileClose');

if (hamburger && mobileMenu) {
  hamburger.addEventListener('click', () => {
    mobileMenu.classList.add('open');
  });
}
if (mobileClose && mobileMenu) {
  mobileClose.addEventListener('click', () => {
    mobileMenu.classList.remove('open');
  });
}
document.querySelectorAll('.mm-link').forEach(a => a.addEventListener('click', () => {
  if (mobileMenu) mobileMenu.classList.remove('open');
}));

// ═══════════════════════════════════════════════════════════════════════════
// AI CHAT — LANGUAGE SELECTION + CHAT LOGIC
// ═══════════════════════════════════════════════════════════════════════════

// ── Meeting UI Helpers ─────────────────────────────────────────────────────

function createMeetingProgressBar(progress) {
  if (!progress || progress.cancelled) return null;
  const pct = Math.round((progress.step / progress.total) * 100);
  const wrap = document.createElement('div');
  wrap.className = 'meeting-progress-bar';
  wrap.innerHTML = `
    <div class="meeting-progress-header">
      <span class="meeting-progress-label"><i class="fa-solid fa-clipboard-list"></i> Interview Details</span>
      <span class="meeting-progress-step">Step ${progress.step}/${progress.total}</span>
    </div>
    <div class="meeting-progress-track">
      <div class="meeting-progress-fill" style="width: ${pct}%"></div>
    </div>
  `;
  return wrap;
}

function createMeetingConfirmationCard(progress, botText) {
  const card = document.createElement('div');
  card.className = 'meeting-confirmation-card';

  // Build details from the botText (which contains the summary)
  let detailsHtml = botText.replace(/\n/g, '<br>');

  card.innerHTML = `
    <div class="meeting-card-header">
      <i class="fa-solid fa-clipboard-check"></i>
      <span>Review Interview Details</span>
    </div>
    <div class="meeting-card-body">${detailsHtml}</div>
    <div class="meeting-card-actions">
      <button class="meeting-btn meeting-btn-confirm" data-action="confirm">
        <i class="fa-solid fa-check"></i> Confirm
      </button>
      <button class="meeting-btn meeting-btn-edit" data-action="edit">
        <i class="fa-solid fa-pen"></i> Edit
      </button>
      <button class="meeting-btn meeting-btn-cancel" data-action="cancel">
        <i class="fa-solid fa-xmark"></i> Cancel
      </button>
    </div>
  `;
  return card;
}

function createMeetingSuccessCard(botText) {
  const card = document.createElement('div');
  card.className = 'meeting-success-card';
  let detailsHtml = botText.replace(/\n/g, '<br>');
  card.innerHTML = `
    <div class="meeting-success-icon">
      <i class="fa-solid fa-calendar-check"></i>
    </div>
    <div class="meeting-success-body">${detailsHtml}</div>
  `;
  return card;
}

function createMeetingCancelBar() {
  const bar = document.createElement('div');
  bar.className = 'meeting-cancel-bar';
  bar.innerHTML = `
    <span class="meeting-cancel-hint">Interview scheduling in progress</span>
    <button class="meeting-cancel-btn" data-action="cancel">
      <i class="fa-solid fa-xmark"></i> Cancel
    </button>
  `;
  return bar;
}

function removeMeetingUi(bodyEl) {
  if (!bodyEl) return;
  bodyEl.querySelectorAll('.meeting-progress-bar, .meeting-cancel-bar').forEach(el => el.remove());
}


const CHAT_API_URL = window.CHAT_API_URL || '/api/chat/';
const chatBtn = document.getElementById('chatBtn');
const chatWindow = document.getElementById('chatWindow');
const chatClose = document.getElementById('chatClose');
const chatMaximize = document.getElementById('chatMaximize');
const chatBody = document.getElementById('chatBody');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');

const chatFullscreen = document.getElementById('chatFullscreen');
const chatFsClose = document.getElementById('chatFsClose');
const chatFsBody = document.getElementById('chatFsBody');
const chatFsInput = document.getElementById('chatFsInput');
const chatFsSend = document.getElementById('chatFsSend');
const avatarRing = document.getElementById('avatarRing');
const avatarStatus = document.getElementById('avatarStatus');

const CHAT_SESSION_KEY = 'CHAT_SESSION_ID';
let chatSessionId = localStorage.getItem(CHAT_SESSION_KEY);
if (!chatSessionId) {
  chatSessionId = 'web_' + Math.random().toString(36).substring(2, 12);
  localStorage.setItem(CHAT_SESSION_KEY, chatSessionId);
}

const LANGUAGE_KEY = 'USER_LANGUAGE';
let userLanguage = localStorage.getItem(LANGUAGE_KEY) || '';

let chatSocket = null;
let inMeetingFlow = false;

function removeTypingIndicators() {
  document.querySelectorAll('.typing-indicator').forEach(el => el.remove());
}

function resetAvatarState() {
  if (avatarRing) avatarRing.classList.remove('thinking');
  if (avatarStatus) { avatarStatus.classList.remove('thinking-status'); avatarStatus.textContent = 'Online'; }
}

function connectWebSocket() {
  console.log('Chat endpoint initialized.');
  chatSocket = {
    readyState: 1,
    send: async function(dataStr) {
      const data = JSON.parse(dataStr);
      const incomingMsg = (data.message || "").trim();
      const sid = data.session_id || chatSessionId;
      const lang = data.language || userLanguage;

      const payload = { ...data, session_id: sid, language: lang };
      const payloadStr = JSON.stringify(payload);

      try {
        const response = await fetch(CHAT_API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Internal-API-Key': 'd59e355c3c0a2b0b14467d55ed59e211e40562e8484196144e54823293883bfd'
          },
          body: payloadStr
        });

        if (!response.ok) {
          throw new Error("Server error, please try again.");
        }

        const resData = await response.json();
        const responseText = resData.message;
        const meetingProgress = resData.meeting_progress || null;
        const intentType = resData.intent || '';

        removeTypingIndicators();

        if (avatarRing) {
          avatarRing.classList.remove('thinking');
          avatarRing.classList.add('speaking');
          setTimeout(() => avatarRing.classList.remove('speaking'), 3000);
        }
        if (avatarStatus) {
          avatarStatus.classList.remove('thinking-status');
          avatarStatus.textContent = 'Online';
        }

        let botHtml = responseText || "Hello! I'm Daisy, Sahil's AI assistant.";
        botHtml = botHtml.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" style="color:var(--cyan);text-decoration:underline;font-weight:600;">$1</a>');
        botHtml = botHtml.replace(/(^|[^"'=])(https?:\/\/[^\s<">]+)/g, '$1<a href="$2" target="_blank" style="color:var(--cyan);text-decoration:underline;font-weight:600;">$2</a>');
        botHtml = botHtml.replace(/\n/g, '<br>');

        const addBotMsg = (bodyEl) => {
          if (!bodyEl) return;

          // Remove old meeting UI elements
          removeMeetingUi(bodyEl);

          // Meeting confirmed/success — show plain message, reset meeting flow
          if (intentType === 'meeting_confirmed') {
            inMeetingFlow = false;
            startSuggestionCycle();
            const bMsg = document.createElement('div');
            bMsg.className = 'chat-msg bot bot-new';
            bMsg.innerHTML = botHtml;
            bodyEl.appendChild(bMsg);
            setTimeout(() => bodyEl.scrollTop = bodyEl.scrollHeight, 50);
            return;
          }

          // Meeting cancelled — show plain message, reset meeting flow
          if (intentType === 'meeting_cancelled') {
            inMeetingFlow = false;
            startSuggestionCycle();
            const bMsg = document.createElement('div');
            bMsg.className = 'chat-msg bot bot-new';
            bMsg.innerHTML = botHtml;
            bodyEl.appendChild(bMsg);
            setTimeout(() => bodyEl.scrollTop = bodyEl.scrollHeight, 50);
            return;
          }

          // Active meeting flow state tracking
          if (meetingProgress && !meetingProgress.cancelled && (intentType === 'meeting' || intentType === 'meeting_edit' || intentType === 'meeting_confirmation')) {
            inMeetingFlow = true;
            stopSuggestionCycle();
          } else {
            if (!meetingProgress || meetingProgress.cancelled) {
              inMeetingFlow = false;
              if (userLanguage) {
                startSuggestionCycle();
              }
            }
          }

          // 1. Append Bot Chat Message bubble FIRST
          const bMsg = document.createElement('div');
          bMsg.className = 'chat-msg bot bot-new';
          bMsg.innerHTML = botHtml;

          const activeTypings = Array.from(bodyEl.querySelectorAll('.typing-indicator'));
          if (activeTypings.length > 0) {
              bodyEl.insertBefore(bMsg, activeTypings[0]);
          } else {
              bodyEl.appendChild(bMsg);
          }

          // 2. Append Progress Bar & Cancel Bar BELOW the bot message
          if (meetingProgress && !meetingProgress.cancelled && inMeetingFlow) {
            const progressBar = createMeetingProgressBar(meetingProgress);
            if (progressBar) bodyEl.appendChild(progressBar);
            const cancelBar = createMeetingCancelBar();
            if (cancelBar) bodyEl.appendChild(cancelBar);
          }

          setTimeout(() => {
              bodyEl.scrollTop = bodyEl.scrollHeight;
          }, 50);
        };

        addBotMsg(chatBody);
        addBotMsg(chatFsBody);

        document.querySelectorAll('.chat-tick--delivered').forEach(tick => {
          tick.className = 'chat-tick chat-tick--seen';
          tick.innerHTML = '✓✓';
        });
      } catch (err) {
        console.error('Chat API error:', err);
        removeTypingIndicators();
        resetAvatarState();

        const errMsg = err.message || "An error occurred while connecting to the AI.";
        const addErrorMsg = (bodyEl) => {
          if (!bodyEl) return;
          const d = document.createElement('div');
          d.className = 'chat-msg bot';
          d.textContent = errMsg;
          bodyEl.appendChild(d);
          bodyEl.scrollTop = bodyEl.scrollHeight;
        };
        addErrorMsg(chatBody);
        addErrorMsg(chatFsBody);
      }
    }
  };

  setTimeout(() => {
    if (chatSocket.onopen) chatSocket.onopen();
  }, 100);
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// ── Suggestion Chips ────────────────────────────────────────────────────────

const suggestionQuestionsEn = [
  "Who is the portfolio owner?",
  "What projects have been built?",
  "What skills are available?",
  "Can I see the resume?",
  "How can I contact?",
  "I want to schedule an interview",
];

const suggestionQuestionsHi = [
  "Portfolio owner kaun hain?",
  "Kaun se projects banaye hain?",
  "Kya skills hain?",
  "Kya main resume dekh sakta hoon?",
  "Kaise contact karun?",
  "Main interview schedule karna chahta hoon",
];

let suggestionInterval = null;

function updateSuggestions() {
  const suggestions = document.getElementById('chatSuggestions');
  const fsSuggestions = document.getElementById('chatFsSuggestions');
  if (!suggestions && !fsSuggestions) return;

  if (!userLanguage) {
    if (suggestions) suggestions.style.display = 'none';
    if (fsSuggestions) fsSuggestions.style.display = 'none';
    return;
  }

  const list = userLanguage === 'hindi' ? suggestionQuestionsHi : suggestionQuestionsEn;
  const shuffled = [...list].sort(() => 0.5 - Math.random());
  const selected = shuffled.slice(0, 4);

  let html = '';
  selected.forEach(q => {
    html += `<button class="suggestion-chip" data-q="${q}"><i class="fa-regular fa-comment-dots"></i> ${q}</button>`;
  });

  if (suggestions) { suggestions.style.display = 'flex'; suggestions.innerHTML = html; }
  if (fsSuggestions) { fsSuggestions.style.display = 'flex'; fsSuggestions.innerHTML = html; }
}

function startSuggestionCycle() {
  if (suggestionInterval) clearInterval(suggestionInterval);
  updateSuggestions();
  suggestionInterval = setInterval(() => updateSuggestions(), 7000);
}

function stopSuggestionCycle() {
  if (suggestionInterval) { clearInterval(suggestionInterval); suggestionInterval = null; }
  const suggestions = document.getElementById('chatSuggestions');
  const fsSuggestions = document.getElementById('chatFsSuggestions');
  if (suggestions) suggestions.style.display = 'none';
  if (fsSuggestions) fsSuggestions.style.display = 'none';
}

// ── Language Selection ─────────────────────────────────────────────────────

function syncLanguageUi() {
  if (!userLanguage) {
    if (chatInput) { chatInput.disabled = true; chatInput.placeholder = "Please select a language above..."; }
    if (chatSend) chatSend.disabled = true;
    if (chatFsInput) { chatFsInput.disabled = true; chatFsInput.placeholder = "Please select a language above..."; }
    if (chatFsSend) chatFsSend.disabled = true;
    stopSuggestionCycle();
    return;
  }

  if (chatInput) { chatInput.disabled = false; chatInput.placeholder = "Ask me anything about Sahil..."; }
  if (chatSend) chatSend.disabled = false;
  if (chatFsInput) { chatFsInput.disabled = false; chatFsInput.placeholder = "Ask me anything about Sahil..."; }
  if (chatFsSend) chatFsSend.disabled = false;

  const langChips = document.querySelectorAll('.lang-gate-options');
  langChips.forEach(c => c.style.display = 'none');

  if (!inMeetingFlow) {
    startSuggestionCycle();
  } else {
    stopSuggestionCycle();
  }
}

function insertLanguagePrompt(bodyEl) {
  if (!bodyEl || bodyEl.querySelector('.lang-gate')) return;

  const prompt = document.createElement('div');
  prompt.className = 'lang-gate';
  prompt.innerHTML = `
    <div class="chat-msg bot">
      <i class="fa-solid fa-globe" style="color:var(--cyan);margin-right:6px;"></i>
      Hello! Please select your preferred language / Apni pasandida bhasha chunein:
    </div>
    <div class="chat-suggestions lang-gate-options" style="flex-wrap: wrap; margin-top: 10px;">
      <button class="suggestion-chip lang-chip" data-lang="english"><i class="fa-solid fa-language"></i> English</button>
      <button class="suggestion-chip lang-chip" data-lang="hindi"><i class="fa-solid fa-language"></i> हिन्दी</button>
    </div>
  `;
  bodyEl.insertBefore(prompt, bodyEl.firstChild);
}

function ensureLanguageSelection() {
  if (userLanguage) {
    syncLanguageUi();
    return;
  }

  const introTargets = [chatBody, chatFsBody];
  introTargets.forEach(bodyEl => {
    if (!bodyEl) return;
    const firstBot = bodyEl.querySelector('.chat-msg.bot');
    if (firstBot) {
      firstBot.remove();
    }
  });
  insertLanguagePrompt(chatBody);
  insertLanguagePrompt(chatFsBody);
  syncLanguageUi();
}

document.addEventListener('click', (e) => {
  const chip = e.target.closest('.lang-chip');
  if (chip) {
    const lang = chip.dataset.lang;
    if (lang === 'english' || lang === 'hindi') {
      userLanguage = lang;
      localStorage.setItem(LANGUAGE_KEY, lang);
      syncLanguageUi();

      if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
          message: "",
          language: lang
        }));
      }
    }
  }
});

// ── Chat Window Logic ──────────────────────────────────────────────────────

if (chatBtn && chatWindow) {
  chatBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    chatWindow.classList.toggle('open');
    if (chatWindow.classList.contains('open') && chatInput) {
      setTimeout(() => chatInput.focus(), 300);
    }
  });

  document.querySelectorAll('.open-chat').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (chatFullscreen) {
        chatFullscreen.classList.add('open');
        if (chatFsInput) setTimeout(() => chatFsInput.focus(), 300);
      } else {
        chatWindow.classList.add('open');
        if (chatInput) setTimeout(() => chatInput.focus(), 300);
      }
      if (typeof mobileMenu !== 'undefined' && mobileMenu) {
        mobileMenu.classList.remove('open');
      }
    });
  });

  if (chatClose) {
    chatClose.addEventListener('click', (e) => {
      e.stopPropagation();
      chatWindow.classList.remove('open');
    });
  }

  document.addEventListener('click', (e) => {
    if (chatWindow.classList.contains('open') && !chatWindow.contains(e.target) && !chatBtn.contains(e.target) && !e.target.closest('.open-chat')) {
      chatWindow.classList.remove('open');
    }
  });

  if (chatMaximize && chatFullscreen) {
    chatMaximize.addEventListener('click', (e) => {
      e.stopPropagation();
      chatWindow.classList.remove('open');
      chatFullscreen.classList.add('open');
      if (chatFsInput) {
        setTimeout(() => chatFsInput.focus(), 300);
      }
    });
  }

  if (chatFsClose) {
    chatFsClose.addEventListener('click', (e) => {
      e.stopPropagation();
      chatFullscreen.classList.remove('open');
      chatWindow.classList.add('open');
    });
  }

  // ── Suggestion chip clicks ──────────────────────────────────────────────
  document.addEventListener('click', (e) => {
    const chip = e.target.closest('.suggestion-chip[data-q]');
    if (chip) {
      const question = chip.dataset.q;
      stopSuggestionCycle();

      if (chatFullscreen && chatFullscreen.classList.contains('open')) {
        if (chatFsInput) {
          chatFsInput.value = question;
          handleSend(question, chatFsInput, chatFsSend, chatFsBody, chatBody);
        }
      } else {
        if (chatInput) {
          chatInput.value = question;
          handleSend(question, chatInput, chatSend, chatBody, chatFsBody);
        }
      }
    }
  });

  // ── Meeting action button clicks (confirm/edit/cancel) ─────────────────
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.meeting-btn, .meeting-cancel-btn');
    if (!btn) return;
    const action = btn.dataset.action;
    if (!action) return;

    // Disable all meeting buttons to prevent double-clicks
    document.querySelectorAll('.meeting-btn, .meeting-cancel-btn').forEach(b => b.disabled = true);

    // Send the action as a chat message
    if (chatFullscreen && chatFullscreen.classList.contains('open')) {
      if (chatFsInput) {
        chatFsInput.value = action;
        handleSend(action, chatFsInput, chatFsSend, chatFsBody, chatBody);
      }
    } else {
      if (chatInput) {
        chatInput.value = action;
        handleSend(action, chatInput, chatSend, chatBody, chatFsBody);
      }
    }
  });

  // ── WhatsApp-style tick states ──────────────────────────────────────────
  function createTick(state) {
    const tick = document.createElement('span');
    tick.className = `chat-tick chat-tick--${state}`;
    if (state === 'sent')      tick.innerHTML = '✓';
    if (state === 'delivered') tick.innerHTML = '✓✓';
    if (state === 'seen')      tick.innerHTML = '✓✓';
    return tick;
  }

  function createTypingIndicator() {
    const wrap = document.createElement('div');
    wrap.className = 'chat-msg bot typing-indicator';
    wrap.innerHTML = '<span></span><span></span><span></span><span></span>';
    return wrap;
  }

  async function handleSend(text, inputEl, sendBtnEl, targetBody, altBody) {
    if (!text) return;

    const addUserMsg = (bodyEl) => {
      if (!bodyEl) return null;
      const uWrap = document.createElement('div');
      uWrap.className = 'chat-msg-wrap user-wrap';
      const uMsg = document.createElement('div');
      uMsg.className = 'chat-msg user';

      const textSpan = document.createElement('span');
      textSpan.textContent = text;

      const tickEl = createTick('sent');

      uMsg.appendChild(textSpan);
      uMsg.appendChild(tickEl);
      uWrap.appendChild(uMsg);
      bodyEl.appendChild(uWrap);
      setTimeout(() => bodyEl.scrollTop = bodyEl.scrollHeight, 50);
      return tickEl;
    };

    const tick1 = addUserMsg(chatBody);
    const tick2 = addUserMsg(chatFsBody);

    if (inputEl) inputEl.value = '';

    await new Promise(r => setTimeout(r, 400));
    if (tick1) { tick1.className = 'chat-tick chat-tick--delivered'; tick1.innerHTML = '✓✓'; }
    if (tick2) { tick2.className = 'chat-tick chat-tick--delivered'; tick2.innerHTML = '✓✓'; }

    const typing1 = createTypingIndicator();
    const typing2 = createTypingIndicator();
    if (chatBody) {
        chatBody.appendChild(typing1);
        setTimeout(() => chatBody.scrollTop = chatBody.scrollHeight, 50);
    }
    if (chatFsBody) {
        chatFsBody.appendChild(typing2);
        setTimeout(() => chatFsBody.scrollTop = chatFsBody.scrollHeight, 50);
    }

    if (avatarRing) avatarRing.classList.add('thinking');
    if (avatarStatus) { avatarStatus.classList.add('thinking-status'); avatarStatus.textContent = 'Typing...'; }

    try {
      if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
          message: text,
          language: userLanguage
        }));
      } else {
        console.warn("WebSocket is not open. Trying to reconnect...");
        connectWebSocket();
        throw new Error("Connection lost. Please try sending again.");
      }
    } catch (err) {
      console.error('Chat error:', err);
      if (typing1.parentNode) typing1.remove();
      if (typing2.parentNode) typing2.remove();
      const errMsg = err.message || "An error occurred while connecting to the AI.";
      if (chatBody) {
          const d = document.createElement('div'); d.className='chat-msg bot'; d.textContent=errMsg;
          chatBody.appendChild(d); chatBody.scrollTop=chatBody.scrollHeight;
      }
      if (chatFsBody) {
          const d = document.createElement('div'); d.className='chat-msg bot'; d.textContent=errMsg;
          chatFsBody.appendChild(d); chatFsBody.scrollTop=chatFsBody.scrollHeight;
      }
      if (avatarRing) avatarRing.classList.remove('thinking');
      if (avatarStatus) { avatarStatus.classList.remove('thinking-status'); avatarStatus.textContent = 'Online'; }
    }

    if (!inMeetingFlow) {
        syncLanguageUi();
    }
    if (userLanguage && inputEl) {
        inputEl.focus();
    }
  }

  if (chatSend && chatInput) {
    chatSend.addEventListener('click', () => handleSend(chatInput.value.trim(), chatInput, chatSend, chatBody, chatFsBody));
    chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') handleSend(chatInput.value.trim(), chatInput, chatSend, chatBody, chatFsBody);
    });
  }

  if (chatFsSend && chatFsInput) {
    chatFsSend.addEventListener('click', () => handleSend(chatFsInput.value.trim(), chatFsInput, chatFsSend, chatFsBody, chatBody));
    chatFsInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') handleSend(chatFsInput.value.trim(), chatFsInput, chatFsSend, chatFsBody, chatBody);
    });
  }
}

ensureLanguageSelection();
connectWebSocket();

// ─────────────────────────────────────────────────────────────────
//  THOUGHT BUBBLE  — cycles curious AI thoughts above the avatar
// ─────────────────────────────────────────────────────────────────
(function initThoughtBubble() {
  const bubble    = document.getElementById('chatThoughtBubble');
  const textEl    = document.getElementById('chatThoughtText');
  const chatWin   = document.getElementById('chatWindow');
  const chatFs    = document.getElementById('chatFullscreen');

  if (!bubble || !textEl) return;

  const thoughts = [
    "Who are you?",
    "What brings you here?",
    "Looking for a developer?",
    "Need a custom AI solution?",
    "Want to collaborate?",
    "Looking for Sahil's resume?",
    "Curious about Sahil's work?",
    "Want to schedule an interview?",
    "Got a project in mind?",
  ];

  let idx = Math.floor(Math.random() * thoughts.length);
  let cycleTimer = null;
  let hidden = false;

  function isChatOpen() {
    return (chatWin && chatWin.classList.contains('open')) ||
           (chatFs && chatFs.classList.contains('open'));
  }

  function showThought() {
    if (isChatOpen() || hidden) {
      bubble.classList.remove('visible');
      return;
    }
    bubble.classList.remove('visible');
    setTimeout(() => {
      const liveText = document.getElementById('chatThoughtText');
      if (liveText) {
        liveText.textContent = thoughts[idx];
        liveText.classList.remove('chat-thought-text');
        void liveText.offsetWidth;
        liveText.classList.add('chat-thought-text');
      }
      bubble.classList.add('visible');
      idx = (idx + 1) % thoughts.length;
    }, 350);
  }

  setTimeout(() => {
    showThought();
    cycleTimer = setInterval(showThought, 4000);
  }, 2000);

  function hideOnOpen() {
    bubble.classList.remove('visible');
    hidden = true;
    clearInterval(cycleTimer);
  }

  function reshowOnClose() {
    hidden = false;
    idx = Math.floor(Math.random() * thoughts.length);
    setTimeout(() => {
      showThought();
      cycleTimer = setInterval(showThought, 4000);
    }, 800);
  }

  if (chatWin) {
    const observer = new MutationObserver(() => {
      if (isChatOpen()) hideOnOpen();
      else reshowOnClose();
    });
    observer.observe(chatWin, { attributes: true, attributeFilter: ['class'] });
  }
  if (chatFs) {
    const observer = new MutationObserver(() => {
      if (isChatOpen()) hideOnOpen();
      else reshowOnClose();
    });
    observer.observe(chatFs, { attributes: true, attributeFilter: ['class'] });
  }
})();
