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

let chatSessionId = null;

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
      chatWindow.classList.add('open');
      if (chatInput) {
        setTimeout(() => chatInput.focus(), 300);
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

  // SUGGESTION CHIP CLICKS
  const suggestions = document.getElementById('chatSuggestions');
  if (suggestions) {
    suggestions.querySelectorAll('.suggestion-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const question = chip.dataset.q;
        if (chatInput) {
          chatInput.value = question;
          suggestions.style.display = 'none';
          handleSend(question, chatInput, chatSend, chatBody, chatFsBody);
        }
      });
    });
  }

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
    wrap.innerHTML = '<span></span><span></span><span></span>';
    return wrap;
  }

  // Handle send logic for either input
  async function handleSend(text, inputEl, sendBtnEl, targetBody, altBody) {
    if (!text) return;

    // Disable inputs while waiting
    if (chatInput) chatInput.disabled = true;
    if (chatSend) chatSend.disabled = true;
    if (chatFsInput) chatFsInput.disabled = true;
    if (chatFsSend) chatFsSend.disabled = true;

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
      bodyEl.scrollTop = bodyEl.scrollHeight;
      return tickEl;
    };

    const tick1 = addUserMsg(chatBody);
    const tick2 = addUserMsg(chatFsBody);

    if (inputEl) inputEl.value = '';

    if (suggestions) suggestions.style.display = 'none';

    // Short delay then show double gray tick (delivered)
    await new Promise(r => setTimeout(r, 400));
    if (tick1) { tick1.className = 'chat-tick chat-tick--delivered'; tick1.innerHTML = '✓✓'; }
    if (tick2) { tick2.className = 'chat-tick chat-tick--delivered'; tick2.innerHTML = '✓✓'; }

    // Show typing dots in both
    const typing1 = createTypingIndicator();
    const typing2 = createTypingIndicator();
    if (chatBody) { chatBody.appendChild(typing1); chatBody.scrollTop = chatBody.scrollHeight; }
    if (chatFsBody) { chatFsBody.appendChild(typing2); chatFsBody.scrollTop = chatFsBody.scrollHeight; }

    // Avatar thinking state
    if (avatarRing) avatarRing.classList.add('thinking');
    if (avatarStatus) { avatarStatus.classList.add('thinking-status'); avatarStatus.textContent = 'Typing...'; }

    try {
      const response = await fetch('/api/web-chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: chatSessionId })
      });

      const data = await response.json();
      if (data.session_id) chatSessionId = data.session_id;

      // Remove typing indicators
      typing1.remove();
      typing2.remove();

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

      const botHtml = data.response
        ? data.response.replace(/\n/g, '<br>')
        : "Sorry, I'm having trouble connecting right now.";

      const addBotMsg = (bodyEl) => {
        if (!bodyEl) return;
        const bMsg = document.createElement('div');
        bMsg.className = 'chat-msg bot bot-new';
        bMsg.innerHTML = botHtml;
        bodyEl.appendChild(bMsg);
        bodyEl.scrollTop = bodyEl.scrollHeight;
      };

      addBotMsg(chatBody);
      addBotMsg(chatFsBody);

      // Upgrade user ticks to blue double tick (seen)
      if (tick1) tick1.className = 'chat-tick chat-tick--seen';
      if (tick2) tick2.className = 'chat-tick chat-tick--seen';

    } catch (err) {
      console.error('Chat error:', err);
      typing1.remove();
      typing2.remove();
      const errMsg = "An error occurred while connecting to the AI.";
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

    // Re-enable inputs
    if (chatInput) chatInput.disabled = false;
    if (chatSend) chatSend.disabled = false;
    if (chatFsInput) chatFsInput.disabled = false;
    if (chatFsSend) chatFsSend.disabled = false;

    if (inputEl) inputEl.focus();
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

