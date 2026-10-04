'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const synth = ('speechSynthesis' in window) ? window.speechSynthesis : null;
  const entries = [...document.querySelectorAll('.entry')];
  const chapters = [...document.querySelectorAll('.chapter')];
  const groups = [...document.querySelectorAll('.place-group')];
  const byId = new Map(entries.map(e => [e.dataset.id, e]));
  const KEY = 'mz-portuguese-v5';
  let prefs = {};
  try { prefs = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (_) { prefs = {}; }
  if (typeof prefs !== 'object' || Array.isArray(prefs)) prefs = {};
  const store = () => { try { localStorage.setItem(KEY, JSON.stringify(prefs)); return true; } catch (_) { return false; } };
  const normalise = s => String(s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  entries.forEach(e => e._search = normalise(e.dataset.search));

  /* ---------- 内置音频库 ---------- */
  const EMB_PREFIX = 'embedded:';
  const EMBED_LABEL = {
    main: '内置声音一 · pt-PT 女声（清晰合成 · 离线）',
    fish: '内置声音二 · Valentino 葡语（高质量合成 · 离线）',
    fernanda: '内置女声 · Fernanda（pt-PT 神经网络 · 离线）',
    duarte: '内置男声 · Duarte（pt-PT 神经网络 · 离线）'
  };
  let bank = { meta: {}, voices: {} };
  try {
    const bankEl = document.getElementById('audio-bank');
    if (bankEl) bank = JSON.parse(bankEl.textContent);
  } catch (_) { bank = { meta: {}, voices: {} }; }
  bank.voices = bank.voices || {};
  const embeddedKeys = Object.keys(bank.voices).filter(k => bank.voices[k] && Object.keys(bank.voices[k]).length);
  const embeddedCount = embeddedKeys.length ? Object.keys(bank.voices[embeddedKeys[0]]).length : 0;
  const embVoice = key => ({ embedded: true, key });
  const isEmbKey = k => typeof k === 'string' && k.startsWith(EMB_PREFIX);
  const clipsFor = v => (v && v.embedded && bank.voices[v.key]) || null;

  // 单一 Audio 元素复用：iOS 上首次手势解锁后，后续队列播放不会被拦截。
  const player = ('Audio' in window) ? new Audio() : null;
  if (player) { try { player.preload = 'auto'; } catch (_) {} }

  /* ---------- 队列与声音状态 ---------- */
  let available = [];
  let currentVoice = null;
  let queue = [];
  let active = null; /* utterance（系统）或 player（内置） */
  let activeCard = null;
  let nextTimer = null;
  let startTimer = null;
  let generation = 0;
  let lastVoiceKey = '';
  const keyOf = v => v.embedded ? EMB_PREFIX + v.key : [v.voiceURI || '', v.lang || '', v.name || ''].join('|');
  const voiceLabel = v => v.embedded ? (EMBED_LABEL[v.key] || v.key) : `${v.name} · ${v.lang}${v.localService === true ? ' · 本机服务' : v.localService === false ? ' · 在线服务' : ''}`;
  const isPortuguese = v => /^pt(?:[-_]|$)/i.test(v.lang || '');
  const isReed = v => /\breed\b/i.test(v.name || '');
  const isRocko = v => /\brocko\b/i.test(v.name || '');
  const rank = v => (isReed(v) ? 0 : isRocko(v) ? 10 : 20) + (/^pt[-_]MZ$/i.test(v.lang) ? 0 : /^pt[-_]PT$/i.test(v.lang) ? 1 : /^pt[-_]BR$/i.test(v.lang) ? 2 : 3);

  function status(text) { $('statusText').textContent = text; updateQueueLabel(); }
  function updateQueueLabel() {
    $('queueText').textContent = queue.length ? `还有 ${queue.length} 次朗读在队列中` : active ? '点击另一条会排队，不截断前一句。' : '';
  }
  function clearHighlight() { if (activeCard) { activeCard.classList.remove('playing'); activeCard.removeAttribute('aria-busy'); } activeCard = null; }
  function stop(message = '已停止朗读并清空队列。') {
    generation++;
    queue = [];
    if (nextTimer) { clearTimeout(nextTimer); nextTimer = null; }
    if (startTimer) { clearTimeout(startTimer); startTimer = null; }
    if (player) { try { player.pause(); } catch (_) {} }
    if (synth) { try { synth.cancel(); } catch (_) {} }
    active = null; clearHighlight();
    status(message);
  }
  function updateVoiceUI(message = '') {
    const ready = !!currentVoice;
    document.querySelectorAll('[data-play],#testVoice,#sequence').forEach(b => b.disabled = !ready);
    if (currentVoice && currentVoice.embedded) {
      $('voiceInfo').textContent = `当前：${EMBED_LABEL[currentVoice.key]}。已内置 ${embeddedCount} 条，离线可播，不需要系统下载语音包；这是机器合成音，不是当地人真人录音。`;
    } else if (currentVoice) {
      $('voiceInfo').textContent = `当前：${voiceLabel(currentVoice)}。这是设备提供的系统声音，不是内置录音。`;
    } else if (message) { $('voiceInfo').textContent = message; }
  }
  function refreshVoices() {
    const opts = [];
    embeddedKeys.forEach(k => opts.push({ value: EMB_PREFIX + k, label: EMBED_LABEL[k] }));
    available = [];
    if (synth && typeof window.SpeechSynthesisUtterance !== 'undefined') {
      let found = []; try { found = synth.getVoices(); } catch (_) { found = []; }
      const unique = new Map(); found.filter(isPortuguese).forEach(v => unique.set(keyOf(v), v));
      available = [...unique.values()].sort((a, b) => rank(a) - rank(b) || (a.name + ' ' + a.lang).localeCompare(b.name + ' ' + b.lang));
      available.forEach(v => opts.push({ value: keyOf(v), label: voiceLabel(v) }));
    }
    const wanted = prefs.voice || lastVoiceKey || (embeddedKeys.length ? EMB_PREFIX + embeddedKeys[0] : '');
    let match = null;
    if (isEmbKey(wanted) && embeddedKeys.includes(wanted.slice(EMB_PREFIX.length))) {
      match = embVoice(wanted.slice(EMB_PREFIX.length));
    } else if (wanted) {
      match = available.find(v => keyOf(v) === wanted) || null;
    }
    if (active && wanted && !match) { stop('所选声音暂不可用，请重新选择。'); }
    $('voiceSelect').replaceChildren();
    if (!opts.length) {
      currentVoice = null; $('voiceSelect').append(new Option('没有检测到可用的朗读声音', ''));
      $('voiceSelect').disabled = true;
      updateVoiceUI('没有检测到任何朗读声音；全部文字仍可阅读。');
      return;
    }
    $('voiceSelect').disabled = false;
    const missing = !!wanted && !match;
    if (missing) { const op = new Option('上次所选声音未列出，请重新选择', ''); op.disabled = true; $('voiceSelect').append(op); }
    opts.forEach(o => $('voiceSelect').append(new Option(o.label, o.value)));
    if (!match && embeddedKeys.length) match = embVoice(embeddedKeys[0]);
    if (!match) match = available[0] || null;
    currentVoice = match;
    $('voiceSelect').value = match ? keyOf(match) : '';
    if (match) lastVoiceKey = keyOf(match);
    updateVoiceUI(missing ? '上次选择的声音当前未列出，请重新选择。' : '');
  }
  function requireVoice() {
    if (!currentVoice) refreshVoices();
    if (!currentVoice) { status('请先在“朗读声音”里选择一个可用声音。'); return false; }
    return true;
  }
  function runQueue() {
    if (active || nextTimer || !queue.length) return;
    if (!requireVoice()) { queue = []; updateQueueLabel(); return; }
    const task = queue.shift();
    const token = generation;
    if (currentVoice.embedded) {
      if (!player) { stop('此浏览器不支持内置音频播放。'); return; }
      const clips = clipsFor(currentVoice) || {};
      const url = clips[task.id];
      if (!url) {
        status(`第 ${task.id} 条暂无内置音频，已跳过；可切换系统声音试听。`);
        nextTimer = setTimeout(() => { nextTimer = null; runQueue(); }, 350);
        return;
      }
      active = player; activeCard = task.card || null;
      if (activeCard) { activeCard.classList.add('playing'); activeCard.setAttribute('aria-busy', 'true'); }
      status(`正在播放：${task.text}`);
      const rate = task.rate || 1;
      try { player.preservesPitch = true; } catch (_) {}
      if ('webkitPreservesPitch' in player) player.webkitPreservesPitch = true;
      const applyRate = () => { try { player.defaultPlaybackRate = rate; player.playbackRate = rate; } catch (_) {} };
      const finish = () => {
        if (token !== generation || active !== player) return;
        if (startTimer) { clearTimeout(startTimer); startTimer = null; }
        active = null; clearHighlight();
        if (queue.length) {
          updateQueueLabel();
          nextTimer = setTimeout(() => { nextTimer = null; runQueue(); }, 350);
        } else status('播放完成。');
      };
      player.onended = finish;
      player.onloadeddata = () => { if (token === generation && active === player) applyRate(); };
      player.oncanplay = () => { if (token === generation && active === player) applyRate(); };
      player.onerror = () => { if (token === generation && active === player) stop('这条内置音频播放失败，请重新点按。'); };
      startTimer = setTimeout(() => { if (token === generation && active === player) stop('内置音频未能开始播放。'); }, 20000);
      player.src = url;
      applyRate(); // defaultPlaybackRate 会在换源后保持生效
      const p = player.play();
      if (p && p.catch) p.catch(() => { if (token === generation && active === player) stop('内置音频无法播放，请重新点按一次。'); });
      return;
    }
    if (!synth || typeof window.SpeechSynthesisUtterance === 'undefined') { stop('当前选择的是系统声音，但此环境不支持系统朗读。'); return; }
    const utterance = new SpeechSynthesisUtterance(task.text);
    utterance.voice = currentVoice;
    utterance.lang = currentVoice.lang;
    utterance.rate = task.rate;
    utterance.pitch = 1;
    active = utterance; activeCard = task.card || null;
    if (activeCard) { activeCard.classList.add('playing'); activeCard.setAttribute('aria-busy', 'true'); }
    status(`正在朗读：${task.text}`);
    const finish = () => {
      if (token !== generation || active !== utterance) return;
      if (startTimer) { clearTimeout(startTimer); startTimer = null; }
      active = null; clearHighlight();
      if (queue.length) {
        updateQueueLabel();
        nextTimer = setTimeout(() => { nextTimer = null; runQueue(); }, 350);
      } else status('朗读完成。');
    };
    utterance.onstart = () => { if (token === generation && startTimer) { clearTimeout(startTimer); startTimer = null; } };
    utterance.onend = finish;
    utterance.onerror = event => {
      if (token !== generation || active !== utterance) return;
      stop(`这次朗读未完成（${event.error || '系统语音错误'}）。请检查所选声音后重新点读。`);
    };
    startTimer = setTimeout(() => { if (token === generation && active === utterance) { stop('系统没有开始朗读。请刷新声音或换一个可用的葡语声音。'); } }, 20000);
    try { synth.speak(utterance); if (synth.paused) synth.resume(); }
    catch (_) { stop('系统未能开始朗读，请重新选择声音。'); }
  }
  function enqueueBatch(items) {
    if (!requireVoice()) return;
    // Limit accidental tapping without interrupting a sentence already in progress.
    if (queue.length + items.length > 80) { status('待播内容较多，请先听完，或点“停止”清空。'); return; }
    queue.push(...items); updateQueueLabel(); runQueue();
  }
  function enqueueCard(id, rate) {
    const card = byId.get(id); if (!card) return;
    const task = { id, text: card.querySelector('.ptxt').textContent.trim(), rate, card };
    enqueueBatch($('repeatTwice').checked ? [task, { ...task }] : [task]);
  }
  function applyFilters() {
    const section = $('chapterSelect').value;
    const group = section === 's14' ? $('provinceSelect').value : 'all';
    const q = normalise($('search').value.trim());
    const terms = q.split(/\s+/).filter(Boolean);
    $('provinceFilterWrap').hidden = section !== 's14';
    let n = 0;
    for (const e of entries) {
      const sectionOK = section === 'all' || e.dataset.section === section;
      const groupOK = group === 'all' || e.dataset.group === group;
      const textOK = terms.every(t => e._search.includes(t));
      e.hidden = !(sectionOK && groupOK && textOK); if (!e.hidden) n++;
    }
    groups.forEach(g => g.hidden = ![...g.querySelectorAll('.entry')].some(e => !e.hidden));
    chapters.forEach(s => s.hidden = ![...s.querySelectorAll('.entry')].some(e => !e.hidden));
    $('count').textContent = `当前显示 ${n} 条${section === 's14' ? '地名卡' : ''} ／ 全册 203 条`;
    $('empty').hidden = n !== 0;
  }
  function selectChapter(id) {
    $('chapterSelect').value = id; $('provinceSelect').value = 'all'; $('search').value = '';
    prefs.chapter = id; store(); applyFilters();
  }
  document.addEventListener('click', event => {
    const b = event.target.closest('button[data-play]');
    if (b && !b.disabled) enqueueCard(b.dataset.play, Number(b.dataset.rate) || 1);
  });
  $('voiceSelect').addEventListener('change', () => {
    const val = $('voiceSelect').value;
    if (isEmbKey(val)) {
      const key = val.slice(EMB_PREFIX.length);
      if (!bank.voices[key]) return;
      stop('声音已切换，请重新点击需要听读的内容。');
      currentVoice = embVoice(key); lastVoiceKey = val; prefs.voice = val;
      const saved = store(); updateVoiceUI();
      status(`已选择 ${EMBED_LABEL[key]}${saved ? '；已保存选择。' : ''}`);
      return;
    }
    const choice = available.find(v => keyOf(v) === val);
    if (!choice) return;
    stop('声音已切换，请重新点击需要听读的内容。');
    currentVoice = choice; lastVoiceKey = keyOf(choice); prefs.voice = lastVoiceKey;
    const saved = store(); updateVoiceUI();
    status(`已选择 ${choice.name} · ${choice.lang}${saved ? '；已保存选择。' : ''}`);
  });
  $('refreshVoices').addEventListener('click', refreshVoices);
  $('testVoice').addEventListener('click', () => {
    if (currentVoice && currentVoice.embedded) {
      const card = entries.find(e => /^bom dia/i.test(e.querySelector('.ptxt').textContent.trim())) || entries[0];
      enqueueBatch([{ id: card.dataset.id, text: card.querySelector('.ptxt').textContent.trim(), rate: 1, card: null }]);
      return;
    }
    enqueueBatch([{ id: null, text: 'Bom dia. Maputo. Sofala. Beira. Montepuez.', rate: 1, card: null }]);
  });
  $('stop').addEventListener('click', () => stop());
  $('repeatTwice').checked = !!prefs.repeat;
  $('repeatTwice').addEventListener('change', () => { prefs.repeat = $('repeatTwice').checked; store(); });
  if ([...$('chapterSelect').options].some(o => o.value === prefs.chapter)) $('chapterSelect').value = prefs.chapter;
  $('chapterSelect').addEventListener('change', () => { $('provinceSelect').value = 'all'; prefs.chapter = $('chapterSelect').value; store(); applyFilters(); });
  $('provinceSelect').addEventListener('change', applyFilters);
  $('search').addEventListener('input', applyFilters);
  $('reset').addEventListener('click', () => selectChapter('all'));
  $('goPlaces').addEventListener('click', () => { selectChapter('s14'); $('learningContent').scrollIntoView({ block: 'start', behavior: 'smooth' }); });
  $('goNumbers').addEventListener('click', () => selectChapter('s01'));
  $('sequence').addEventListener('click', () => {
    const visible = entries.filter(e => !e.hidden).slice(0, 20);
    const tasks = [];
    visible.forEach(card => { const t = { id: card.dataset.id, text: card.querySelector('.ptxt').textContent.trim(), rate: 1, card }; tasks.push(t); if ($('repeatTwice').checked) tasks.push({ ...t }); });
    enqueueBatch(tasks);
  });
  if (synth) {
    if (synth.addEventListener) synth.addEventListener('voiceschanged', refreshVoices);
    else synth.onvoiceschanged = refreshVoices;
  }
  refreshVoices(); applyFilters();
  setTimeout(refreshVoices, 250); setTimeout(refreshVoices, 1250);
  window.addEventListener('pagehide', () => stop('页面已关闭或切换。'));

  /* ---------- 卡片滚动入场（respect prefers-reduced-motion 由 CSS 处理） ---------- */
  document.documentElement.classList.add('js');
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion || !('IntersectionObserver' in window)) {
    entries.forEach(e => e.classList.add('in'));
  } else {
    const io = new IntersectionObserver(es => {
      es.forEach(x => { if (x.isIntersecting) { x.target.classList.add('in'); io.unobserve(x.target); } });
    }, { rootMargin: '0px 0px -4% 0px', threshold: 0 });
    entries.forEach(e => io.observe(e));
  }
})();
