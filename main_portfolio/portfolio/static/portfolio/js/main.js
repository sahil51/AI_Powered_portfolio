/* ═══════════════════════════════════════════════════════════════════════════
   PORTFOLIO — MAIN.JS
   Extracted from index.html — exact same functionality
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

// ACTIVE NAV
const sects = document.querySelectorAll('section[id]');
const navAs = document.querySelectorAll('.nav-links a');
window.addEventListener('scroll', () => {
  let cur = '';
  sects.forEach(s => { if (window.scrollY >= s.offsetTop - 130) cur = s.id; });
  navAs.forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === '#' + cur);
  });
});

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

// AI CHAT FLOATING WINDOW LOGIC
const CHAT_API_URL = window.CHAT_API_URL || '/api/chat/'; // Update this to your microservice API URL
const chatBtn = document.getElementById('chatBtn');
const chatWindow = document.getElementById('chatWindow');
const chatClose = document.getElementById('chatClose');
const chatMaximize = document.getElementById('chatMaximize');
const chatBody = document.getElementById('chatBody');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');

// Fullscreen elements
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

let chatSocket = null;

function removeTypingIndicators() {
  document.querySelectorAll('.typing-indicator').forEach(el => el.remove());
}

function resetAvatarState() {
  if (avatarRing) avatarRing.classList.remove('thinking');
  if (avatarStatus) { avatarStatus.classList.remove('thinking-status'); avatarStatus.textContent = 'Online'; }
}

function connectWebSocket() {
  console.log('Django API mode: Chat endpoint initialized.');
  chatSocket = {
    readyState: 1, // WebSocket.OPEN
    send: async function(dataStr) {
      const data = JSON.parse(dataStr);
      const incomingMsg = (data.message || "").trim();
      const role = data.visitor_role || visitorRole;
      
      // If it's a role update message, show role confirmation
      if (!incomingMsg && role) {
        try {
          await fetch(CHAT_API_URL, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken')
            },
            body: dataStr
          });
          setTimeout(() => {
            showRoleConfirmation(role);
          }, 300);
        } catch (err) {
          console.error('Role update error:', err);
        }
        return;
      }
      
      try {
        const response = await fetch(CHAT_API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: dataStr
        });
        
        if (!response.ok) {
          throw new Error("Server error, please try again.");
        }
        
        const resData = await response.json();
        const responseText = resData.message;
        
        // Remove typing indicators
        removeTypingIndicators();
        
        // Avatar speaking state
        if (avatarRing) {
          avatarRing.classList.remove('thinking');
          avatarRing.classList.add('speaking');
          setTimeout(() => avatarRing.classList.remove('speaking'), 3000);
        }
        if (avatarStatus) {
          avatarStatus.classList.remove('thinking-status');
          avatarStatus.textContent = 'Online';
        }
        
        // Render bot message
        let botHtml = responseText || "Hi! I am Daisy, Sahil's AI assistant.";
        botHtml = botHtml.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" style="color:var(--cyan);text-decoration:underline;font-weight:600;">$1</a>');
        botHtml = botHtml.replace(/(^|[^"'=])(https?:\/\/[a-zA-Z0-9\-\.\/\?\&\=\+\%_:]+)/g, '$1<a href="$2" target="_blank" style="color:var(--cyan);text-decoration:underline;font-weight:600;">$2</a>');
        botHtml = botHtml.replace(/\n/g, '<br>');
        
        const addBotMsg = (bodyEl) => {
          if (!bodyEl) return;
          const bMsg = document.createElement('div');
          bMsg.className = 'chat-msg bot bot-new';
          bMsg.innerHTML = botHtml;
          
          const activeTypings = Array.from(bodyEl.querySelectorAll('.typing-indicator'));
          if (activeTypings.length > 0) {
              bodyEl.insertBefore(bMsg, activeTypings[0]);
          } else {
              bodyEl.appendChild(bMsg);
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
        
        syncRoleUi();
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


const VISITOR_ROLE_KEY = 'VISITOR_ROLE';
let visitorRole = localStorage.getItem(VISITOR_ROLE_KEY) || '';

function normalizeRole(role) {
  const value = (role || '').trim().toLowerCase();
  return value === 'client' || value === 'recruiter' || value === 'visitor' ? value : '';
}

const clientQuestions = [
  "What services do you offer?",
  "Can you build a custom AI agent for me?",
  "What is your tech stack for backend development?",
  "Have you built any complex platforms?",
  "Where can I find Sahil's resume?",
  "Can we discuss a project?",
  "Can you integrate AI into my existing app?",
  "What is your availability for a new contract?",
  "I want to schedule a meeting with Sahil."
];

const recruiterQuestions = [
  "Are you open to full-time roles?",
  "Can I get your latest resume?",
  "Where can I find Sahil's resume?",
  "What is your notice period?",
  "Do you have experience with system design?",
  "Which programming languages are you most comfortable with?",
  "Are you willing to relocate?",
  "What are your salary expectations?",
  "Can we schedule a technical interview?"
];

const visitorQuestions = [
  "Who is Sahil Thakur?",
  "What projects has Sahil built?",
  "Where can I find Sahil's resume?",
  "What AI tools does Sahil work with?",
  "What is Sahil's main tech stack?",
  "How can I contact Sahil?",
  "Where did Sahil study?"
];

function getRandomQuestions(role, count = 3) {
  let list = visitorQuestions;
  if (role === 'client') list = clientQuestions;
  if (role === 'recruiter') list = recruiterQuestions;
  
  const shuffled = [...list].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

let suggestionInterval = null;

function updateDynamicSuggestions(role) {
  const suggestions = document.getElementById('chatSuggestions');
  const fsSuggestions = document.getElementById('chatFsSuggestions');
  
  if (suggestionInterval) {
    clearInterval(suggestionInterval);
    suggestionInterval = null;
  }
  
  if (!role) {
    if (suggestions) suggestions.style.display = 'none';
    if (fsSuggestions) fsSuggestions.style.display = 'none';
    return;
  }
  
  if (suggestions) suggestions.style.display = 'flex';
  if (fsSuggestions) fsSuggestions.style.display = 'flex';
  
  function render() {
    const randomQs = getRandomQuestions(role, 3);
    let html = '';
    randomQs.forEach(q => {
      html += `<button class="suggestion-chip" style="animation: fadein 0.5s;" data-q="${q}"><i class="fa-regular fa-comment-dots"></i> ${q}</button>`;
    });
    
    if (suggestions && suggestions.style.display !== 'none') {
      suggestions.innerHTML = html;
    }
    if (fsSuggestions && fsSuggestions.style.display !== 'none') {
      fsSuggestions.innerHTML = html;
    }
  }

  render();
  
  // Automatically cycle questions every 6 seconds
  suggestionInterval = setInterval(() => {
    // Clear interval if user sent a message and suggestions were hidden
    if ((!suggestions || suggestions.style.display === 'none') && 
        (!fsSuggestions || fsSuggestions.style.display === 'none')) {
      clearInterval(suggestionInterval);
      suggestionInterval = null;
      return;
    }
    render();
  }, 6000);
}

function syncRoleUi() {
  if (!visitorRole) {
    if (chatInput) { chatInput.disabled = true; chatInput.placeholder = "Please select an option above..."; }
    if (chatSend) chatSend.disabled = true;
    if (chatFsInput) { chatFsInput.disabled = true; chatFsInput.placeholder = "Please select an option above..."; }
    if (chatFsSend) chatFsSend.disabled = true;
    updateDynamicSuggestions(null);
    return;
  }
  
  if (chatInput) { chatInput.disabled = false; chatInput.placeholder = "Ask me anything about Sahil..."; }
  if (chatSend) chatSend.disabled = false;
  if (chatFsInput) { chatFsInput.disabled = false; chatFsInput.placeholder = "Ask me anything about Sahil..."; }
  if (chatFsSend) chatFsSend.disabled = false;
  
  updateDynamicSuggestions(visitorRole);

  const chipContainers = document.querySelectorAll('.role-gate-options');
  chipContainers.forEach(c => c.style.display = 'none');
}

function showRoleConfirmation(role) {
  let message = "Thanks. I will keep the conversation tailored for a general visitor.";
  if (role === "client") message = "Thanks. I will keep the conversation tailored for a client.";
  if (role === "recruiter") message = "Thanks. I will keep the conversation tailored for a recruiter.";

  [chatBody, chatFsBody].forEach(bodyEl => {
    if (!bodyEl) return;
    const msgEl = document.createElement('div');
    msgEl.className = 'chat-msg bot role-confirmation';
    msgEl.textContent = message;
    bodyEl.appendChild(msgEl);
    bodyEl.scrollTop = bodyEl.scrollHeight;
  });
  syncRoleUi();
}

function insertRolePrompt(bodyEl, text) {
  if (!bodyEl || bodyEl.querySelector('.role-gate')) return;

  const promptText = text || "Hello! I am Sahil's AI assistant. To ensure I provide the most relevant information, could you tell me if you are connecting as a Recruiter, a Client/Service Inquiry, or just exploring?";

  const prompt = document.createElement('div');
  prompt.className = 'role-gate';
  prompt.innerHTML = `
    <div class="chat-msg bot">
      <i class="fa-solid fa-hand-wave" style="color:var(--cyan);margin-right:6px;"></i>
      ${promptText}
    </div>
    <div class="chat-suggestions role-gate-options" style="flex-wrap: wrap; margin-top: 10px;">
      <button class="suggestion-chip role-chip" data-role="client"><i class="fa-solid fa-briefcase"></i> Client</button>
      <button class="suggestion-chip role-chip" data-role="recruiter"><i class="fa-solid fa-user-tie"></i> Recruiter</button>
      <button class="suggestion-chip role-chip" data-role="visitor"><i class="fa-solid fa-compass"></i> Just Exploring</button>
    </div>
  `;
  bodyEl.insertBefore(prompt, bodyEl.firstChild);
}

function ensureRoleGate(dynamicText) {
  if (visitorRole) {
    syncRoleUi();
    return;
  }
  const introText = dynamicText || "Hello! I am Sahil's AI assistant. To ensure I provide the most relevant information, could you tell me if you are connecting as a Recruiter, a Client/Service Inquiry, or just exploring?";
  const introTargets = [chatBody, chatFsBody];
  introTargets.forEach(bodyEl => {
    if (!bodyEl) return;
    const firstBot = bodyEl.querySelector('.chat-msg.bot');
    if (firstBot && !firstBot.classList.contains('role-confirmation') && !firstBot.closest('.role-gate')) {
      firstBot.remove();
    }
  });
  insertRolePrompt(chatBody, introText);
  insertRolePrompt(chatFsBody, introText);
  syncRoleUi();
}

document.addEventListener('click', (e) => {
  const chip = e.target.closest('.role-chip');
  if (chip) {
    const rawRole = chip.dataset.role;
    const role = normalizeRole(rawRole);
    if (role) {
      visitorRole = role;
      localStorage.setItem(VISITOR_ROLE_KEY, role);
      syncRoleUi();
      
      // Notify WebSocket of the selected role
      if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
          message: "",
          visitor_role: role
        }));
      }
    }
  }
});


if (chatBtn && chatWindow) {
  // Toggle mini chat window
  chatBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    chatWindow.classList.toggle('open');
    if (chatWindow.classList.contains('open') && chatInput) {
      setTimeout(() => chatInput.focus(), 300);
    }
  });

  // Open chat from nav links
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

  // Click outside to minimize mini chat
  document.addEventListener('click', (e) => {
    if (chatWindow.classList.contains('open') && !chatWindow.contains(e.target) && !chatBtn.contains(e.target) && !e.target.closest('.open-chat')) {
      chatWindow.classList.remove('open');
    }
  });

  // Maximize chat
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

  // Close Fullscreen chat
  if (chatFsClose) {
    chatFsClose.addEventListener('click', (e) => {
      e.stopPropagation();
      chatFullscreen.classList.remove('open');
      chatWindow.classList.add('open');
    });
  }

  // SUGGESTION CHIP CLICKS (Delegated so it works with dynamically generated chips)
  document.addEventListener('click', (e) => {
    const chip = e.target.closest('.suggestion-chip[data-q]');
    if (chip) {
      const question = chip.dataset.q;
      const suggestions = document.getElementById('chatSuggestions');
      const fsSuggestions = document.getElementById('chatFsSuggestions');
      
      if (chatFullscreen && chatFullscreen.classList.contains('open')) {
        if (chatFsInput) {
          chatFsInput.value = question;
          if (fsSuggestions) fsSuggestions.style.display = 'none';
          if (suggestions) suggestions.style.display = 'none';
          handleSend(question, chatFsInput, chatFsSend, chatFsBody, chatBody);
        }
      } else {
        if (chatInput) {
          chatInput.value = question;
          if (suggestions) suggestions.style.display = 'none';
          if (fsSuggestions) fsSuggestions.style.display = 'none';
          handleSend(question, chatInput, chatSend, chatBody, chatFsBody);
        }
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

  // ── Typing dots indicator ───────────────────────────────────────────────
  function createTypingIndicator() {
    const wrap = document.createElement('div');
    wrap.className = 'chat-msg bot typing-indicator';
    wrap.innerHTML = '<span></span><span></span><span></span><span></span>';
    return wrap;
  }

  // Handle send logic for either input
  async function handleSend(text, inputEl, sendBtnEl, targetBody, altBody) {
    if (!text) return;

    // Do NOT disable inputs, allowing the user to continue chatting asynchronously.

    // Helper to add user msg to a body
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

    const suggestionsEl = document.getElementById('chatSuggestions');
    const fsSuggestionsEl = document.getElementById('chatFsSuggestions');
    if (suggestionsEl) suggestionsEl.style.display = 'none';
    if (fsSuggestionsEl) fsSuggestionsEl.style.display = 'none';

    // Short delay then show double gray tick (delivered)
    await new Promise(r => setTimeout(r, 400));
    if (tick1) { tick1.className = 'chat-tick chat-tick--delivered'; tick1.innerHTML = '✓✓'; }
    if (tick2) { tick2.className = 'chat-tick chat-tick--delivered'; tick2.innerHTML = '✓✓'; }

    // Show typing dots in both
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

    // Avatar thinking state
    if (avatarRing) avatarRing.classList.add('thinking');
    if (avatarStatus) { avatarStatus.classList.add('thinking-status'); avatarStatus.textContent = 'Typing...'; }

    try {
      if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
          message: text,
          visitor_role: visitorRole
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

    // Keep inputs enabled
    syncRoleUi();
    if (visitorRole && inputEl) {
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

// Ensure the chat inputs and role gate are correctly initialized on load
ensureRoleGate();
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
    "Are you a recruiter?",
    "Looking for a developer?",
    "Need a custom AI solution?",
    "Want to collaborate?",
    "Looking for Sahil's resume?",
    "Curious about Sahil's work?",
    "Want to schedule a meeting?",
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
    // Fade out
    bubble.classList.remove('visible');
    setTimeout(() => {
      // Update text and re-trigger CSS animation
      const liveText = document.getElementById('chatThoughtText');
      if (liveText) {
        liveText.textContent = thoughts[idx];
        // Re-trigger animation by toggling the class
        liveText.classList.remove('chat-thought-text');
        void liveText.offsetWidth; // force reflow
        liveText.classList.add('chat-thought-text');
      }
      bubble.classList.add('visible');
      idx = (idx + 1) % thoughts.length;
    }, 350);
  }

  // Start after 2 seconds, then every 4s
  setTimeout(() => {
    showThought();
    cycleTimer = setInterval(showThought, 4000);
  }, 2000);

  // Hide when chat opens
  function hideOnOpen() {
    bubble.classList.remove('visible');
    hidden = true;
    clearInterval(cycleTimer);
  }

  // Reshow when chat closes
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
