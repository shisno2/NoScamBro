/**
 * GameDev Tycoon: Studio Master
 * Полная логика симулятора разработки игр
 */

// --- Аудио-синтезатор для звуковых эффектов (без внешних файлов) ---
class SoundManager {
  constructor() {
    this.enabled = true;
    this.ctx = null;
  }

  init() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.ctx = new AudioContext();
      }
    }
  }

  playTone(freq, duration = 0.1, type = 'sine') {
    if (!this.enabled) return;
    this.init();
    if (!this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      // Audio autoplay policy
    }
  }

  playClick() { this.playTone(600, 0.05, 'triangle'); }
  playCodePoint() { this.playTone(800 + Math.random() * 200, 0.04, 'sine'); }
  playArtPoint() { this.playTone(1000 + Math.random() * 200, 0.04, 'triangle'); }
  playBugPoint() { this.playTone(250, 0.08, 'sawtooth'); }
  playRelease() {
    this.playTone(400, 0.1, 'sine');
    setTimeout(() => this.playTone(600, 0.1, 'sine'), 100);
    setTimeout(() => this.playTone(900, 0.25, 'triangle'), 200);
  }
  playCash() {
    this.playTone(987.77, 0.08, 'sine');
    setTimeout(() => this.playTone(1318.51, 0.15, 'sine'), 80);
  }
  playLevelUp() {
    [523, 659, 783, 1046].forEach((f, i) => {
      setTimeout(() => this.playTone(f, 0.15, 'sine'), i * 90);
    });
  }
}

const sounds = new SoundManager();

// --- ИГРОВАЯ БАЗА ДАННЫХ ---
const GAME_DB = {
  genres: [
    { id: 'rpg', name: 'RPG (Ролевая игра)', cost: 1500, unlockRp: 0, bestThemes: ['fantasy', 'scifi', 'postapoc'], weights: { code: 40, design: 35, sound: 25 } },
    { id: 'action', name: 'Экшен / Шутер', cost: 1800, unlockRp: 0, bestThemes: ['scifi', 'military', 'zombie', 'cyberpunk'], weights: { code: 45, design: 35, sound: 20 } },
    { id: 'strategy', name: 'Стратегия', cost: 2000, unlockRp: 20, bestThemes: ['history', 'space', 'medieval'], weights: { code: 50, design: 30, sound: 20 } },
    { id: 'simulator', name: 'Симулятор', cost: 1200, unlockRp: 0, bestThemes: ['business', 'city', 'transport'], weights: { code: 45, design: 30, sound: 25 } },
    { id: 'horror', name: 'Хоррор на выживание', cost: 1600, unlockRp: 25, bestThemes: ['zombie', 'mystery', 'paranormal'], weights: { code: 30, design: 35, sound: 35 } },
    { id: 'puzzle', name: 'Головоломка / Казуалка', cost: 800, unlockRp: 15, bestThemes: ['abstract', 'fantasy', 'mystery'], weights: { code: 35, design: 45, sound: 20 } }
  ],

  themes: [
    { id: 'fantasy', name: 'Фэнтези и Магия', unlockRp: 0 },
    { id: 'scifi', name: 'Научная фантастика', unlockRp: 0 },
    { id: 'cyberpunk', name: 'Киберпанк 2099', unlockRp: 20 },
    { id: 'postapoc', name: 'Постапокалипсис', unlockRp: 25 },
    { id: 'zombie', name: 'Зомби-эпидемия', unlockRp: 15 },
    { id: 'space', name: 'Космическая одиссея', unlockRp: 20 },
    { id: 'medieval', name: 'Средневековье', unlockRp: 0 },
    { id: 'business', name: 'Бизнес и корпорации', unlockRp: 15 },
    { id: 'city', name: 'Строительство городов', unlockRp: 20 },
    { id: 'military', name: 'Военные спецоперации', unlockRp: 15 },
    { id: 'paranormal', name: 'Мистика и призраки', unlockRp: 30 },
    { id: 'abstract', name: 'Абстрактный минимализм', unlockRp: 0 }
  ],

  platforms: [
    { id: 'pc', name: 'Персональный компьютер (Steam)', cost: 1000, audienceShare: 0.9, unlockRp: 0 },
    { id: 'playbox', name: 'Консоль PlayBox 5', cost: 5000, audienceShare: 1.3, unlockRp: 30 },
    { id: 'nintento', name: 'Портативка Switchy', cost: 3500, audienceShare: 1.1, unlockRp: 25 },
    { id: 'mobile', name: 'Мобильные телефоны (iOS/Android)', cost: 2500, audienceShare: 1.4, unlockRp: 20 },
    { id: 'vr', name: 'Шлем виртуальной реальности (VR)', cost: 8000, audienceShare: 0.8, unlockRp: 50 }
  ],

  engines: [
    { id: 'custom_basic', name: 'Базовый 2D движок', cost: 0, mult: 1.0, unlockRp: 0 },
    { id: 'unity_style', name: 'Voxel3D Engine v1.0', cost: 3000, mult: 1.25, unlockRp: 35 },
    { id: 'unreal_style', name: 'Titan 5 Engine (RayTracing)', cost: 10000, mult: 1.6, unlockRp: 80 }
  ],

  offices: [
    { id: 'garage', name: 'Гараж родителей', capacity: 2, rent: 0, price: 0, desc: 'Тесный гараж. Хватит на двух энтузиастов.' },
    { id: 'coworking', name: 'Коворкинг в центре', capacity: 4, rent: 1500, price: 15000, desc: 'Современный офис со скоростным интернетом и кофе.' },
    { id: 'studio', name: 'Просторная студия разработки', capacity: 6, rent: 4500, price: 60000, desc: 'Собственное здание, переговорки и мощная техника.' },
    { id: 'skyscraper', name: 'Небоскрёб GameDev Corp', capacity: 8, rent: 12000, price: 250000, desc: 'Легендарная штаб-квартира мирового гиганта индустрии!' }
  ],

  upgrades: [
    { id: 'ergonomic_chairs', name: 'Эргономичные кресла Herman', cost: 3000, desc: '+15% к скорости генерации очков сотрудниками', owned: false },
    { id: 'coffee_machine', name: 'Итальянская кофемашина', cost: 2000, desc: '-20% к шансу появления багов', owned: false },
    { id: 'dual_monitors', name: 'Сверхширокие 4K мониторы', cost: 5000, desc: '+25% к очкам дизайна и арта', owned: false },
    { id: 'sound_booth', name: 'Акустическая студия звукозаписи', cost: 6500, desc: '+30% к качеству саундтрека', owned: false },
    { id: 'server_rack', name: 'Локальный CI/CD сервер билдов', cost: 12000, desc: '+35% к скорости компиляции и кодинга', owned: false }
  ],

  marketingCampaigns: [
    { id: 'social', name: 'Таргетинг в соцсетях и TikTok', cost: 1500, boostSales: 1.3, duration: 4, desc: 'Привлекает казуальную молодую аудиторию.' },
    { id: 'streamers', name: 'Спонсорские стримы у топ-блогеров', cost: 6000, boostSales: 1.7, duration: 4, desc: 'Взрывной интерес геймеров и хайп в прямом эфире.' },
    { id: 'gamescom', name: 'Стенд на игровой выставке E3 / Gamescom', cost: 18000, boostSales: 2.4, duration: 6, desc: 'Мировое признание, внимание прессы и куча вишлистов!' }
  ]
};

// Генератор случайных названий игр
const RANDOM_TITLES = {
  prefixes: ['Cyber', 'Super', 'Dark', 'Pixel', 'Mega', 'Shadow', 'Final', 'Eternal', 'Neon', 'Grand', 'Pocket', 'Quantum'],
  nouns: ['Quest', 'Strike', 'Legends', 'Simulator', 'Revenge', 'Chronicles', 'Tactics', 'Hunters', 'Runner', 'Empire', 'Warriors', 'Odyssey']
};

// --- СОСТОЯНИЕ ИГРЫ (STATE) ---
let state = {
  money: 15000,
  fans: 10,
  researchPoints: 10,
  
  date: { year: 1, month: 1, week: 1 },
  speed: 1, // 0 = pause, 1 = 1x, 2 = 2x, 5 = 5x
  timer: null,

  officeIndex: 0,
  staff: [
    {
      id: 1,
      name: 'Вы (Основатель)',
      role: 'Универсал',
      avatar: '👨‍💻',
      code: 15,
      design: 12,
      sound: 10,
      salary: 0,
      energy: 100
    }
  ],

  candidatePool: [],
  games: [],
  unlockedTech: ['rpg', 'action', 'simulator', 'fantasy', 'scifi', 'medieval', 'abstract', 'pc', 'custom_basic'],
  ownedUpgrades: [],
  activeCampaigns: [],

  // Текущая разработка
  dev: {
    active: false,
    title: '',
    genre: null,
    theme: null,
    platform: null,
    engine: null,
    progress: 0, // 0 - 100
    phase: 1,    // 1, 2, 3
    points: { code: 0, design: 0, sound: 0, bugs: 0 },
    sliders: { gameplay: 40, graphics: 30, sound: 30 },
    marketingBonus: 1.0,
    costSpent: 0
  },

  // Баг хант мини-игра
  bugHunt: {
    active: false,
    timer: 10,
    squashed: 0,
    interval: null
  }
};

// --- ИНИЦИАЛИЗАЦИЯ ИНТЕРФЕЙСА ---
document.addEventListener('DOMContentLoaded', () => {
  initUI();
  renderOffice();
  renderStaff();
  renderResearchTree();
  renderUpgrades();
  renderMarketing();
  renderGamesHistory();
  updateTopStats();
  startGameLoop();
});

function initUI() {
  // Навигация по вкладкам
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const targetTab = document.getElementById(btn.dataset.tab);
      if (targetTab) targetTab.classList.add('active');
      sounds.playClick();
    });
  });

  // Кнопки скорости
  document.getElementById('btn-pause').addEventListener('click', () => setSpeed(0));
  document.getElementById('btn-speed-1').addEventListener('click', () => setSpeed(1));
  document.getElementById('btn-speed-2').addEventListener('click', () => setSpeed(2));
  document.getElementById('btn-speed-3').addEventListener('click', () => setSpeed(5));

  // Звук
  const soundBtn = document.getElementById('btn-toggle-sound');
  soundBtn.addEventListener('click', () => {
    sounds.enabled = !sounds.enabled;
    soundBtn.innerHTML = sounds.enabled 
      ? '<i class="fa-solid fa-volume-high"></i> Звуки: ВКЛ'
      : '<i class="fa-solid fa-volume-xmark"></i> Звуки: ВЫКЛ';
  });

  // Быстрые кнопки сайдбара
  document.getElementById('btn-start-dev-main').addEventListener('click', () => {
    if (state.dev.active) {
      showToast('Разработка уже идёт! Завершите текущую игру.', 'bad');
      switchTab('office-tab');
      return;
    }
    switchTab('develop-tab');
  });

  document.getElementById('btn-contract-work').addEventListener('click', openContractsModal);

  // Конструктор новой игры
  populateDevDropdowns();
  setupSliders();
  document.getElementById('btn-random-name').addEventListener('click', generateRandomGameName);
  document.getElementById('btn-start-dev-confirm').addEventListener('click', startNewGameDevelopment);

  // Кнопки управления в плашке разработки
  document.getElementById('btn-finish-game-now').addEventListener('click', finishGameDevelopment);
  document.getElementById('btn-fix-bugs-now').addEventListener('click', startBugHuntMiniGame);

  // Модальные окна закрытие
  document.getElementById('btn-close-hire').addEventListener('click', () => hideModal('hire-modal'));
  document.getElementById('btn-close-train').addEventListener('click', () => hideModal('train-modal'));
  document.getElementById('btn-close-contracts').addEventListener('click', () => hideModal('contracts-modal'));
  document.getElementById('btn-close-reviews').addEventListener('click', () => {
    hideModal('reviews-modal');
    switchTab('games-history-tab');
  });
  document.getElementById('btn-finish-bug-hunt').addEventListener('click', endBugHuntMiniGame);
  document.getElementById('btn-open-hire-modal').addEventListener('click', openHireAgency);
}

function switchTab(tabId) {
  const btn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  if (btn) btn.click();
}

function setSpeed(sp) {
  state.speed = sp;
  ['btn-pause', 'btn-speed-1', 'btn-speed-2', 'btn-speed-3'].forEach(id => {
    document.getElementById(id).classList.remove('active');
  });
  if (sp === 0) document.getElementById('btn-pause').classList.add('active');
  if (sp === 1) document.getElementById('btn-speed-1').classList.add('active');
  if (sp === 2) document.getElementById('btn-speed-2').classList.add('active');
  if (sp === 5) document.getElementById('btn-speed-3').classList.add('active');
}

// --- ИГРОВОЙ ЦИКЛ (ТИК ВРЕМЕНИ) ---
function startGameLoop() {
  if (state.timer) clearInterval(state.timer);
  state.timer = setInterval(() => {
    if (state.speed === 0) return; // Пауза
    
    // Число шагов за такт зависит от скорости
    for (let i = 0; i < state.speed; i++) {
      tickWeek();
    }
  }, 1000);
}

function tickWeek() {
  state.date.week++;
  if (state.date.week > 4) {
    state.date.week = 1;
    state.date.month++;
    onMonthPassed();
  }
  if (state.date.month > 12) {
    state.date.month = 1;
    state.date.year++;
    showToast(`🎉 С Новым Годом! Наступил ${state.date.year}-й год работы студии!`, 'gold');
  }

  // Обновляем разработку игры, если активна
  if (state.dev.active) {
    progressGameDev();
  }

  // Продажи всех активных выпущенных игр
  processGameSales();

  // Маркетинговые кампании
  processMarketingCampaigns();

  updateTopStats();
}

function onMonthPassed() {
  // Выплата зарплат персоналу и аренда
  const currentOffice = GAME_DB.offices[state.officeIndex];
  const rent = currentOffice.rent;
  const salaries = state.staff.reduce((acc, s) => acc + s.salary, 0);
  const totalMonthlyExpenses = rent + salaries;

  state.money -= totalMonthlyExpenses;
  
  if (totalMonthlyExpenses > 0) {
    addFeedItem(`Ежемесячные расходы: Зарплаты -$${salaries}, Аренда офиса -$${rent}.`, 'info');
  }

  if (state.money < 0) {
    showToast(`⚠️ Внимание! Отрицательный баланс ($${state.money.toLocaleString()})! Выполняйте контракты во избежание банкротства!`, 'bad');
  }
}

// --- СИСТЕМА РАЗРАБОТКИ ИГРЫ ---
function populateDevDropdowns() {
  const genreSel = document.getElementById('select-game-genre');
  const themeSel = document.getElementById('select-game-theme');
  const platSel = document.getElementById('select-game-platform');
  const engSel = document.getElementById('select-game-engine');

  genreSel.innerHTML = '';
  GAME_DB.genres.forEach(g => {
    if (state.unlockedTech.includes(g.id)) {
      genreSel.innerHTML += `<option value="${g.id}">${g.name} (Затраты: $${g.cost})</option>`;
    }
  });

  themeSel.innerHTML = '';
  GAME_DB.themes.forEach(t => {
    if (state.unlockedTech.includes(t.id)) {
      themeSel.innerHTML += `<option value="${t.id}">${t.name}</option>`;
    }
  });

  platSel.innerHTML = '';
  GAME_DB.platforms.forEach(p => {
    if (state.unlockedTech.includes(p.id)) {
      platSel.innerHTML += `<option value="${p.id}">${p.name} (Лицензия: $${p.cost})</option>`;
    }
  });

  engSel.innerHTML = '';
  GAME_DB.engines.forEach(e => {
    if (state.unlockedTech.includes(e.id)) {
      engSel.innerHTML += `<option value="${e.id}">${e.name}</option>`;
    }
  });

  genreSel.addEventListener('change', updateSynergyHint);
  themeSel.addEventListener('change', updateSynergyHint);
  updateSynergyHint();
  generateRandomGameName();
}

function updateSynergyHint() {
  const gId = document.getElementById('select-game-genre').value;
  const tId = document.getElementById('select-game-theme').value;
  const genre = GAME_DB.genres.find(g => g.id === gId);
  const hintText = document.getElementById('synergy-hint-text');

  if (genre && genre.bestThemes.includes(tId)) {
    hintText.innerHTML = `✨ <strong>Отличная синергия!</strong> Тематика идеально ложится на выбранный жанр. Критики оценят!`;
    hintText.parentElement.style.borderColor = 'var(--accent-green)';
  } else {
    hintText.innerHTML = `💡 Экспериментальное сочетание. Результат зависит от баланса команды и скилла.`;
    hintText.parentElement.style.borderColor = 'rgba(99, 102, 241, 0.3)';
  }

  // Расчет стоимости
  const pId = document.getElementById('select-game-platform').value;
  const plat = GAME_DB.platforms.find(p => p.id === pId) || { cost: 0 };
  const cost = (genre ? genre.cost : 1000) + plat.cost;
  document.getElementById('est-dev-cost').innerText = `$${cost.toLocaleString()}`;
}

function generateRandomGameName() {
  const pre = RANDOM_TITLES.prefixes[Math.floor(Math.random() * RANDOM_TITLES.prefixes.length)];
  const n = RANDOM_TITLES.nouns[Math.floor(Math.random() * RANDOM_TITLES.nouns.length)];
  document.getElementById('input-game-name').value = `${pre} ${n}`;
}

function setupSliders() {
  const slGameplay = document.getElementById('slider-gameplay');
  const slGraphics = document.getElementById('slider-graphics');
  const slSound = document.getElementById('slider-sound');

  function update() {
    const valG = parseInt(slGameplay.value);
    const valGr = parseInt(slGraphics.value);
    const valS = parseInt(slSound.value);

    document.getElementById('slider-gameplay-val').innerText = `${valG}%`;
    document.getElementById('slider-graphics-val').innerText = `${valGr}%`;
    document.getElementById('slider-sound-val').innerText = `${valS}%`;

    const total = valG + valGr + valS;
    const totalEl = document.getElementById('slider-total-val');
    const statusEl = document.getElementById('slider-total-status');
    totalEl.innerText = `${total}%`;

    if (total === 100) {
      statusEl.innerText = 'Идеально (100%)';
      statusEl.className = 'status-valid';
    } else {
      statusEl.innerText = total > 100 ? `Перебор (+${total - 100}%)` : `Недобор (${total - 100}%)`;
      statusEl.className = 'status-invalid';
    }
  }

  slGameplay.addEventListener('input', update);
  slGraphics.addEventListener('input', update);
  slSound.addEventListener('input', update);
  update();
}

function startNewGameDevelopment() {
  const name = document.getElementById('input-game-name').value.trim() || 'Без названия';
  const gId = document.getElementById('select-game-genre').value;
  const tId = document.getElementById('select-game-theme').value;
  const pId = document.getElementById('select-game-platform').value;
  const eId = document.getElementById('select-game-engine').value;

  const totalSliders = parseInt(document.getElementById('slider-gameplay').value) +
                       parseInt(document.getElementById('slider-graphics').value) +
                       parseInt(document.getElementById('slider-sound').value);

  if (totalSliders !== 100) {
    showToast('Сумма приоритетов должна равняться ровно 100%!', 'bad');
    return;
  }

  const genre = GAME_DB.genres.find(g => g.id === gId);
  const theme = GAME_DB.themes.find(t => t.id === tId);
  const plat = GAME_DB.platforms.find(p => p.id === pId);
  const eng = GAME_DB.engines.find(e => e.id === eId);

  const mktType = document.getElementById('select-launch-marketing').value;
  let mktCost = 0;
  let mktMult = 1.0;
  if (mktType === 'social') { mktCost = 1000; mktMult = 1.25; }
  else if (mktType === 'streamers') { mktCost = 4000; mktMult = 1.6; }
  else if (mktType === 'trailers') { mktCost = 12000; mktMult = 2.2; }

  const totalCost = genre.cost + plat.cost + mktCost;
  if (state.money < totalCost) {
    showToast(`Недостаточно средств! Требуется $${totalCost.toLocaleString()}`, 'bad');
    return;
  }

  // Списание затрат
  state.money -= totalCost;
  sounds.playClick();

  // Инициализация объекта активной разработки
  state.dev = {
    active: true,
    title: name,
    genre: genre,
    theme: theme,
    platform: plat,
    engine: eng,
    progress: 0,
    phase: 1,
    points: { code: 0, design: 0, sound: 0, bugs: 0 },
    sliders: {
      gameplay: parseInt(document.getElementById('slider-gameplay').value),
      graphics: parseInt(document.getElementById('slider-graphics').value),
      sound: parseInt(document.getElementById('slider-sound').value)
    },
    marketingBonus: mktMult,
    costSpent: totalCost
  };

  document.getElementById('dev-busy-indicator').style.display = 'inline-block';
  document.getElementById('active-dev-bar-widget').style.display = 'block';
  document.getElementById('dev-active-title').innerText = name;
  updateDevBarWidget();

  addFeedItem(`Стартовала разработка «${name}» (${genre.name} / ${theme.name})!`, 'info');
  showToast(`Разработка «${name}» успешно началась!`, 'good');
  switchTab('office-tab');
}

function progressGameDev() {
  if (!state.dev.active) return;

  // Суммарные мощности сотрудников
  let totalCode = 0;
  let totalDesign = 0;
  let totalSound = 0;

  state.staff.forEach(s => {
    totalCode += s.code;
    totalDesign += s.design;
    totalSound += s.sound;
  });

  // Эффекты улучшений
  const chairBonus = state.ownedUpgrades.includes('ergonomic_chairs') ? 1.15 : 1.0;
  const monitorBonus = state.ownedUpgrades.includes('dual_monitors') ? 1.25 : 1.0;
  const soundBonus = state.ownedUpgrades.includes('sound_booth') ? 1.30 : 1.0;
  const serverBonus = state.ownedUpgrades.includes('server_rack') ? 1.35 : 1.0;
  const coffeeBugReduction = state.ownedUpgrades.includes('coffee_machine') ? 0.8 : 1.0;

  // Генерация очков за тик с учётом слайдеров
  const codeGen = Math.round((totalCode * (state.dev.sliders.gameplay / 40) * chairBonus * serverBonus * state.dev.engine.mult) / 4);
  const designGen = Math.round((totalDesign * (state.dev.sliders.graphics / 30) * chairBonus * monitorBonus * state.dev.engine.mult) / 4);
  const soundGen = Math.round((totalSound * (state.dev.sliders.sound / 30) * chairBonus * soundBonus * state.dev.engine.mult) / 4);
  
  // Шанс бага зависит от сложности и спешки
  const bugChance = 0.35 * coffeeBugReduction;
  const bugsGen = Math.random() < bugChance ? Math.floor(Math.random() * 2) + 1 : 0;

  // Очки опыта/исследований RP
  const rpGen = Math.random() < 0.25 ? 1 : 0;
  if (rpGen > 0) {
    state.researchPoints += rpGen;
    spawnFloatingBubble('+1 RP', 'bubble-research');
  }

  state.dev.points.code += Math.max(1, codeGen);
  state.dev.points.design += Math.max(1, designGen);
  state.dev.points.sound += Math.max(1, soundGen);
  state.dev.points.bugs += bugsGen;

  // Звуки и пузырьки на сцене
  if (Math.random() < 0.4) {
    spawnFloatingBubble(`+${codeGen} Код`, 'bubble-code');
    sounds.playCodePoint();
  }
  if (Math.random() < 0.35) {
    spawnFloatingBubble(`+${designGen} Арт`, 'bubble-design');
    sounds.playArtPoint();
  }
  if (bugsGen > 0 && Math.random() < 0.3) {
    spawnFloatingBubble(`+${bugsGen} Баг!`, 'bubble-bug');
    sounds.playBugPoint();
  }

  // Прирост прогресса (100% за ~16-24 тиков в зависимости от команды)
  const progressStep = (totalCode + totalDesign + totalSound) / 40;
  state.dev.progress = Math.min(100, state.dev.progress + Math.max(3, progressStep));

  // Фазы разработки
  if (state.dev.progress < 35) {
    state.dev.phase = 1;
    document.getElementById('dev-active-phase').innerText = 'Фаза 1: Движок & Механики';
  } else if (state.dev.progress < 75) {
    state.dev.phase = 2;
    document.getElementById('dev-active-phase').innerText = 'Фаза 2: Контент, Арт & Левелдизайн';
  } else {
    state.dev.phase = 3;
    document.getElementById('dev-active-phase').innerText = 'Фаза 3: Полировка & Звук';
  }

  updateDevBarWidget();

  // Автоматический финиш при 100% если игрок не делает этого вручную
  if (state.dev.progress >= 100) {
    document.getElementById('btn-finish-game-now').classList.add('pulse-anim');
  }
}

function updateDevBarWidget() {
  document.getElementById('dev-pts-code').innerText = state.dev.points.code;
  document.getElementById('dev-pts-design').innerText = state.dev.points.design;
  document.getElementById('dev-pts-sound').innerText = state.dev.points.sound;
  document.getElementById('dev-pts-bugs').innerText = state.dev.points.bugs;
  document.getElementById('dev-progress-fill').style.width = `${Math.floor(state.dev.progress)}%`;
}

// Мини-игра полировки багов
function startBugHuntMiniGame() {
  if (!state.dev.active) return;
  if (state.dev.points.bugs <= 0) {
    showToast('В игре нет известных багов! Код кристально чист.', 'good');
    return;
  }

  state.bugHunt.active = true;
  state.bugHunt.timer = 10;
  state.bugHunt.squashed = 0;
  document.getElementById('bugs-squashed-counter').innerText = '0';
  document.getElementById('bug-timer-badge').innerText = 'Осталось: 10 сек';

  const arena = document.getElementById('bug-arena');
  arena.innerHTML = '';

  showModal('bug-hunt-modal');

  // Спавн жуков
  spawnHuntBugs();

  if (state.bugHunt.interval) clearInterval(state.bugHunt.interval);
  state.bugHunt.interval = setInterval(() => {
    state.bugHunt.timer--;
    document.getElementById('bug-timer-badge').innerText = `Осталось: ${state.bugHunt.timer} сек`;

    if (state.bugHunt.timer <= 0) {
      endBugHuntMiniGame();
    }
  }, 1000);
}

function spawnHuntBugs() {
  const arena = document.getElementById('bug-arena');
  arena.innerHTML = '';
  const count = Math.min(12, Math.max(4, state.dev.points.bugs));
  
  for (let i = 0; i < count; i++) {
    const bug = document.createElement('div');
    bug.className = 'bug-target';
    bug.innerHTML = ['🐛', '🪲', '👾', '🐞'][Math.floor(Math.random() * 4)];
    bug.style.left = `${Math.floor(Math.random() * 85)}%`;
    bug.style.top = `${Math.floor(Math.random() * 80)}%`;

    bug.addEventListener('click', () => {
      sounds.playTone(1200, 0.05, 'triangle');
      state.bugHunt.squashed++;
      state.dev.points.bugs = Math.max(0, state.dev.points.bugs - 1);
      document.getElementById('bugs-squashed-counter').innerText = state.bugHunt.squashed;
      updateDevBarWidget();
      bug.remove();

      // Доспавнить, если ещё есть баги
      if (state.dev.points.bugs > 0) {
        setTimeout(spawnHuntBugs, 300);
      }
    });

    arena.appendChild(bug);
  }
}

function endBugHuntMiniGame() {
  if (state.bugHunt.interval) clearInterval(state.bugHunt.interval);
  state.bugHunt.active = false;
  hideModal('bug-hunt-modal');
  showToast(`Отличная работа! Уничтожено ${state.bugHunt.squashed} багов перед релизом!`, 'good');
}

// Финиш разработки и релиз
function finishGameDevelopment() {
  if (!state.dev.active) return;

  if (state.dev.progress < 50) {
    if (!confirm('Игра готова меньше чем наполовину! Релиз в сыром виде приведёт к разгромным оценкам. Всё равно выпустить?')) {
      return;
    }
  }

  // Расчет финальной оценки (1.0 - 10.0)
  const isSynergy = state.dev.genre.bestThemes.includes(state.dev.theme.id);
  const synergyScore = isSynergy ? 9.2 : 7.0;

  // Влияние баланса очков
  const targetWeights = state.dev.genre.weights;
  const totalPts = (state.dev.points.code + state.dev.points.design + state.dev.points.sound) || 1;
  const cRatio = (state.dev.points.code / totalPts) * 100;
  const dRatio = (state.dev.points.design / totalPts) * 100;
  const sRatio = (state.dev.points.sound / totalPts) * 100;

  const diff = Math.abs(cRatio - targetWeights.code) +
               Math.abs(dRatio - targetWeights.design) +
               Math.abs(sRatio - targetWeights.sound);
  
  const balanceFactor = Math.max(0.5, 1.0 - (diff / 100));

  // Штраф за оставшиеся баги
  const bugPenalty = Math.min(4.5, (state.dev.points.bugs * 0.35));

  // Базовый балл
  let rawScore = (synergyScore * balanceFactor) - bugPenalty + (state.dev.progress / 50);
  rawScore = Math.min(10.0, Math.max(1.5, rawScore + (Math.random() * 1.2 - 0.6)));
  const finalScore = Math.round(rawScore * 10) / 10;

  // Опыт сотрудникам
  state.staff.forEach(s => {
    s.code += Math.floor(Math.random() * 3) + 1;
    s.design += Math.floor(Math.random() * 3) + 1;
    s.sound += Math.floor(Math.random() * 2) + 1;
  });

  // Прирост фанатов
  const fansGain = Math.round(Math.pow(finalScore, 2.5) * 8 + (state.fans * 0.15));
  state.fans += fansGain;

  // Очки RP за релиз
  const rpReward = Math.round(finalScore * 3);
  state.researchPoints += rpReward;

  // Создаём запись в истории игр
  const gameRecord = {
    id: Date.now(),
    title: state.dev.title,
    genre: state.dev.genre.name,
    theme: state.dev.theme.name,
    platform: state.dev.platform.name,
    score: finalScore,
    copiesSold: 0,
    revenue: 0,
    weeksOnMarket: 0,
    price: 15 + Math.floor(finalScore * 2), // $17 - $35 за копию
    marketDecay: 1.0,
    marketingMultiplier: state.dev.marketingBonus,
    audiencePool: Math.round(15000 * state.dev.platform.audienceShare * Math.pow(finalScore / 4, 3))
  };

  state.games.unshift(gameRecord);

  // Сброс активного дева
  state.dev.active = false;
  document.getElementById('dev-busy-indicator').style.display = 'none';
  document.getElementById('active-dev-bar-widget').style.display = 'none';

  // Звук и конфетти при хорошей оценке
  sounds.playRelease();
  if (finalScore >= 7.5 && window.confetti) {
    window.confetti({ particleCount: 120, spread: 70, origin: { y: 0.6 } });
  }

  // Показ модалки обзоров
  showReviewsModal(gameRecord, fansGain);
  renderGamesHistory();
  renderStaff();
  updateTopStats();
}

function showReviewsModal(game, fansGain) {
  document.getElementById('rev-modal-game-title').innerText = game.title;
  const scoreEl = document.getElementById('rev-overall-score');
  scoreEl.innerText = game.score.toFixed(1);

  // Классы цвета оценки
  scoreEl.className = 'score-circle';
  if (game.score >= 9.0) scoreEl.style.borderColor = 'var(--accent-gold)';
  else if (game.score >= 7.0) scoreEl.style.borderColor = 'var(--accent-green)';
  else if (game.score >= 5.0) scoreEl.style.borderColor = 'var(--accent-cyan)';
  else scoreEl.style.borderColor = 'var(--accent-red)';

  // Звезды
  const fullStars = Math.round(game.score / 2);
  document.getElementById('rev-stars-box').innerText = '★'.repeat(fullStars) + '☆'.repeat(5 - fullStars);

  const verdictEl = document.getElementById('rev-verdict-title');
  if (game.score >= 9.5) verdictEl.innerText = 'ШЕДЕВР ДЕСЯТИЛЕТИЯ! Пресса аплодирует стоя!';
  else if (game.score >= 8.0) verdictEl.innerText = 'Великолепная игра! Обязательна к покупке!';
  else if (game.score >= 6.5) verdictEl.innerText = 'Добротный проект со своими плюсами и минусами.';
  else if (game.score >= 4.5) verdictEl.innerText = 'Посредственно. Много багов и скучный геймплей.';
  else verdictEl.innerText = 'Полный провал! Неиграбельный кошмар.';

  // Отзывы 4 журналов
  const mags = [
    { name: 'Игромания Онлайн', score: genReviewScore(game.score), quote: genReviewQuote(game.score, 'tech') },
    { name: 'GameSpot Global', score: genReviewScore(game.score), quote: genReviewQuote(game.score, 'fun') },
    { name: 'PC Gamer Pro', score: genReviewScore(game.score), quote: genReviewQuote(game.score, 'art') },
    { name: 'Kotaku Insider', score: genReviewScore(game.score), quote: genReviewQuote(game.score, 'general') }
  ];

  const grid = document.getElementById('reviews-magazines-grid');
  grid.innerHTML = mags.map(m => `
    <div class="review-item-card">
      <div class="review-mag-title">
        <span>${m.name}</span>
        <strong>${m.score}/10</strong>
      </div>
      <div class="review-mag-quote">«${m.quote}»</div>
    </div>
  `).join('');

  document.getElementById('rev-fans-gain-alert').innerHTML = `<i class="fa-solid fa-users"></i> +${fansGain.toLocaleString()} новых преданных фанатов!`;
  showModal('reviews-modal');
}

function genReviewScore(base) {
  const s = Math.min(10, Math.max(1, base + (Math.random() * 0.8 - 0.4)));
  return s.toFixed(1);
}

function genReviewQuote(score, type) {
  if (score >= 8.5) {
    const quotes = [
      'Мы не могли оторваться ни на минуту!',
      'Графика, звук и геймплей сочетаются идеально.',
      'Это явный кандидат на Игру Года!',
      'Невероятная глубина механик и потрясающая полировка.'
    ];
    return quotes[Math.floor(Math.random() * quotes.length)];
  } else if (score >= 6.5) {
    const quotes = [
      'Очень увлекательно, хотя шероховатости встречаются.',
      'Фанатам жанра точно зайдёт на несколько вечеров.',
      'Крепкий релиз, но до шедевра чуть-чуть не дотянули.',
      'Хорошая идея, ждём патчей и продолжения.'
    ];
    return quotes[Math.floor(Math.random() * quotes.length)];
  } else {
    const quotes = [
      'Огромное количество критических багов и вылетов.',
      'Скучно, вторично и быстро надоедает.',
      'Разработчикам стоило потратить больше времени на полировку.',
      'Потенциал был, но реализация полностью подкачала.'
    ];
    return quotes[Math.floor(Math.random() * quotes.length)];
  }
}

// --- СИСТЕМА ПРОДАЖ ВЫПУЩЕННЫХ ИГР ---
function processGameSales() {
  state.games.forEach(game => {
    // Игра продаётся активно около 12-20 игровых недель
    if (game.weeksOnMarket > 24) return;

    game.weeksOnMarket++;
    
    // Экспоненциальное затухание интереса
    const decay = Math.pow(0.88, game.weeksOnMarket);
    const mktBonus = game.marketingMultiplier || 1.0;

    let weeklyCopies = Math.round(
      (game.audiencePool * 0.12 * decay * mktBonus) + (state.fans * 0.05 * decay)
    );

    weeklyCopies = Math.max(0, weeklyCopies);
    if (weeklyCopies > 0) {
      const revenue = weeklyCopies * game.price;
      game.copiesSold += weeklyCopies;
      game.revenue += revenue;
      state.money += revenue;
    }
  });

  renderGamesHistory();
}

function renderGamesHistory() {
  const container = document.getElementById('games-grid');
  document.getElementById('games-count-badge').innerText = state.games.length;

  if (state.games.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-ghost"></i>
        <p>Вы пока не выпустили ни одной игры. Нажмите «Создать игру», чтобы покорить чарты продаж!</p>
      </div>
    `;
    return;
  }

  let totalSold = 0;
  let totalRev = 0;

  container.innerHTML = state.games.map(game => {
    totalSold += game.copiesSold;
    totalRev += game.revenue;

    let scoreClass = 'score-mediocre';
    if (game.score >= 9.0) scoreClass = 'score-legendary';
    else if (game.score >= 7.0) scoreClass = 'score-great';
    else if (game.score < 5.0) scoreClass = 'score-bad';

    const isActive = game.weeksOnMarket <= 24;

    return `
      <div class="game-card">
        <div class="game-card-header">
          <div>
            <div class="game-card-title">${game.title}</div>
            <div class="subtitle" style="font-size: 0.8rem;">Цена: $${game.price}</div>
          </div>
          <div class="game-score-badge ${scoreClass}">${game.score.toFixed(1)}</div>
        </div>

        <div class="game-card-tags">
          <span class="game-tag">${game.genre}</span>
          <span class="game-tag">${game.theme}</span>
          <span class="game-tag">${game.platform}</span>
        </div>

        <div class="game-financial-row">
          <div>
            <div class="stat-sub">Продано копий</div>
            <strong>${game.copiesSold.toLocaleString()} шт.</strong>
          </div>
          <div>
            <div class="stat-sub">Выручка</div>
            <strong style="color: var(--accent-green)">+$${game.revenue.toLocaleString()}</strong>
          </div>
        </div>

        <div class="game-sales-trend">
          <span>Статус: ${isActive ? '<b style="color:#10b981">В топе продаж 🔥</b>' : 'Архив'}</span>
          <span>На рынке: ${game.weeksOnMarket} нед.</span>
        </div>
      </div>
    `;
  }).join('');

  document.getElementById('total-copies-sold').innerText = totalSold.toLocaleString();
  document.getElementById('total-revenue-sum').innerText = `$${totalRev.toLocaleString()}`;
}

// --- ВИЗУАЛИЗАЦИЯ ОФИСА И СОТРУДНИКОВ ---
function renderOffice() {
  const currentOffice = GAME_DB.offices[state.officeIndex];
  document.getElementById('office-room-name').innerText = currentOffice.name;
  document.getElementById('office-room-desc').innerText = currentOffice.desc;
  document.getElementById('studio-tier-badge').innerText = `${currentOffice.name} (Ур. ${state.officeIndex + 1})`;
  document.getElementById('staff-slots-val').innerText = `${state.staff.length}/${currentOffice.capacity}`;
  document.getElementById('staff-count-badge').innerText = `${state.staff.length}/${currentOffice.capacity}`;

  const desksGrid = document.getElementById('desks-container');
  desksGrid.innerHTML = '';

  // Рендерим столы для занятых сотрудников
  state.staff.forEach(emp => {
    const pod = document.createElement('div');
    pod.className = `desk-pod ${state.dev.active ? 'working' : ''}`;
    pod.innerHTML = `
      <div class="desk-avatar">${emp.avatar}</div>
      <div class="desk-name">${emp.name}</div>
      <div class="desk-role">${emp.role}</div>
      <div class="desk-stats-mini">
        <span title="Кодинг"><i class="fa-solid fa-code"></i> ${emp.code}</span>
        <span title="Арт"><i class="fa-solid fa-palette"></i> ${emp.design}</span>
        <span title="Звук"><i class="fa-solid fa-music"></i> ${emp.sound}</span>
      </div>
    `;
    desksGrid.appendChild(pod);
  });

  // Пустые рабочие места в рамках лимита офиса
  const emptySlots = currentOffice.capacity - state.staff.length;
  for (let i = 0; i < emptySlots; i++) {
    const emptyPod = document.createElement('div');
    emptyPod.className = 'desk-empty';
    emptyPod.innerHTML = `
      <i class="fa-solid fa-chair" style="font-size: 2rem; margin-bottom: 8px;"></i>
      <span>Свободное место</span>
      <small style="color: #6366f1;">Нанять таланта +</small>
    `;
    emptyPod.addEventListener('click', openHireAgency);
    desksGrid.appendChild(emptyPod);
  }
}

function spawnFloatingBubble(text, cls) {
  const layer = document.getElementById('bubbles-layer');
  if (!layer) return;

  const bubble = document.createElement('div');
  bubble.className = `float-bubble ${cls}`;
  bubble.innerText = text;
  
  // Рандомная позиция над персонажами
  bubble.style.left = `${20 + Math.random() * 60}%`;
  bubble.style.top = `${40 + Math.random() * 30}%`;

  layer.appendChild(bubble);
  setTimeout(() => bubble.remove(), 1400);
}

// --- УПРАВЛЕНИЕ ПЕРСОНАЛОМ ---
function renderStaff() {
  const container = document.getElementById('staff-list-grid');
  if (!container) return;

  container.innerHTML = state.staff.map(emp => `
    <div class="staff-card">
      <div class="staff-card-top">
        <div class="staff-avatar-circle">${emp.avatar}</div>
        <div>
          <h3 style="font-size: 1.1rem;">${emp.name}</h3>
          <span class="sub-badge">${emp.role}</span>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">
            Зарплата: <strong>$${emp.salary}/мес</strong>
          </div>
        </div>
      </div>

      <div class="staff-skills-bars">
        <div class="skill-bar-row">
          <span class="skill-bar-label"><i class="fa-solid fa-code"></i> Код: ${emp.code}</span>
          <div class="skill-bar-track">
            <div class="skill-fill-prog" style="width: ${Math.min(100, emp.code * 2)}%"></div>
          </div>
        </div>

        <div class="skill-bar-row">
          <span class="skill-bar-label"><i class="fa-solid fa-palette"></i> Арт: ${emp.design}</span>
          <div class="skill-bar-track">
            <div class="skill-fill-art" style="width: ${Math.min(100, emp.design * 2)}%"></div>
          </div>
        </div>

        <div class="skill-bar-row">
          <span class="skill-bar-label"><i class="fa-solid fa-music"></i> Звук: ${emp.sound}</span>
          <div class="skill-bar-track">
            <div class="skill-fill-sound" style="width: ${Math.min(100, emp.sound * 2)}%"></div>
          </div>
        </div>
      </div>

      <div class="staff-actions">
        <button class="btn btn-secondary btn-sm" onclick="openTrainModal(${emp.id})">
          <i class="fa-solid fa-graduation-cap"></i> Обучить
        </button>
        ${emp.id !== 1 ? `
          <button class="btn btn-outline btn-sm" style="color:#ef4444" onclick="fireEmployee(${emp.id})">
            Уволить
          </button>
        ` : ''}
      </div>
    </div>
  `).join('');
}

function openHireAgency() {
  const currentOffice = GAME_DB.offices[state.officeIndex];
  if (state.staff.length >= currentOffice.capacity) {
    showToast('В офисе нет свободных столов! Улучшите офис во вкладке «Улучшения».', 'bad');
    return;
  }

  // Генерация 3 кандидатов
  const names = ['Алексей Смирнов', 'Елена Ковалёва', 'Дмитрий Волков', 'Анна Морозова', 'Сергей Петров', 'Кристина Ким', 'Максим Орлов'];
  const roles = [
    { title: 'Ведущий Программист', icon: '👨‍💻', c: 28, d: 8, s: 6, sal: 1200 },
    { title: 'Концепт-Художник 3D', icon: '👩‍🎨', c: 6, d: 30, s: 8, sal: 1100 },
    { title: 'Саунд-дизайнер', icon: '🎧', c: 7, d: 10, s: 32, sal: 1050 },
    { title: 'Геймдизайнер-Дженералист', icon: '🧙‍♂️', c: 18, d: 20, s: 15, sal: 1300 }
  ];

  state.candidatePool = [];
  for (let i = 0; i < 3; i++) {
    const r = roles[Math.floor(Math.random() * roles.length)];
    const n = names[Math.floor(Math.random() * names.length)];
    state.candidatePool.push({
      id: Date.now() + i,
      name: n,
      role: r.title,
      avatar: r.icon,
      code: r.c + Math.floor(Math.random() * 8 - 4),
      design: r.d + Math.floor(Math.random() * 8 - 4),
      sound: r.s + Math.floor(Math.random() * 8 - 4),
      salary: r.sal + Math.floor(Math.random() * 200 - 100),
      hireFee: r.sal * 2
    });
  }

  const container = document.getElementById('candidates-grid');
  container.innerHTML = state.candidatePool.map(c => `
    <div class="candidate-card">
      <div style="display:flex; align-items:center; gap: 14px;">
        <span style="font-size: 2.2rem;">${c.avatar}</span>
        <div>
          <strong>${c.name}</strong> (${c.role})
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">
            Навыки: Код <b>${c.code}</b> | Арт <b>${c.design}</b> | Звук <b>${c.sound}</b>
          </div>
          <div style="font-size: 0.8rem; color: #38bdf8; margin-top: 2px;">
            Зарплата: $${c.salary}/мес | Разовый бонус найма: $${c.hireFee}
          </div>
        </div>
      </div>
      <button class="btn btn-primary btn-sm" onclick="hireCandidate(${c.id})">
        Нанять
      </button>
    </div>
  `).join('');

  showModal('hire-modal');
}

window.hireCandidate = function(candId) {
  const currentOffice = GAME_DB.offices[state.officeIndex];
  if (state.staff.length >= currentOffice.capacity) {
    showToast('Нет места в офисе!', 'bad');
    return;
  }

  const cand = state.candidatePool.find(c => c.id === candId);
  if (!cand) return;

  if (state.money < cand.hireFee) {
    showToast(`Недостаточно средств на бонус найма ($${cand.hireFee})!`, 'bad');
    return;
  }

  state.money -= cand.hireFee;
  state.staff.push({
    id: cand.id,
    name: cand.name,
    role: cand.role,
    avatar: cand.avatar,
    code: cand.code,
    design: cand.design,
    sound: cand.sound,
    salary: cand.salary,
    energy: 100
  });

  hideModal('hire-modal');
  sounds.playCash();
  showToast(`${cand.name} присоединился к вашей команде!`, 'good');
  addFeedItem(`Новый сотрудник: ${cand.name} (${cand.role}) принят в студию.`, 'info');

  renderOffice();
  renderStaff();
  updateTopStats();
};

window.fireEmployee = function(empId) {
  if (!confirm('Вы уверены, что хотите уволить этого сотрудника?')) return;
  state.staff = state.staff.filter(s => s.id !== empId);
  renderOffice();
  renderStaff();
  updateTopStats();
  showToast('Сотрудник уволен.', 'info');
};

window.openTrainModal = function(empId) {
  const emp = state.staff.find(s => s.id === empId);
  if (!emp) return;

  document.getElementById('train-employee-name').innerText = emp.name;

  const courses = [
    { title: 'Интенсив по C++ и Vulkan', cost: 1200, skill: 'code', boost: 8, icon: 'fa-code' },
    { title: 'Мастер-класс по Blender & 3D Анимации', cost: 1100, skill: 'design', boost: 8, icon: 'fa-palette' },
    { title: 'Сведение оркестровых саундтреков', cost: 900, skill: 'sound', boost: 8, icon: 'fa-music' },
    { title: 'Курс по комплексному геймдизайну', cost: 2000, skill: 'all', boost: 5, icon: 'fa-brain' }
  ];

  const list = document.getElementById('trainings-list');
  list.innerHTML = courses.map((c, i) => `
    <div class="contract-card" style="margin-bottom: 10px;">
      <div>
        <strong><i class="fa-solid ${c.icon}"></i> ${c.title}</strong>
        <div style="font-size:0.8rem; color:var(--text-muted);">
          Прирост: +${c.boost} к ${c.skill === 'all' ? 'всем характеристикам' : c.skill}
        </div>
      </div>
      <button class="btn btn-action-primary btn-sm" onclick="applyTraining(${emp.id}, ${i})">
        Оплатить $${c.cost}
      </button>
    </div>
  `).join('');

  window.currentTrainCourses = courses;
  showModal('train-modal');
};

window.applyTraining = function(empId, courseIdx) {
  const course = window.currentTrainCourses[courseIdx];
  const emp = state.staff.find(s => s.id === empId);

  if (state.money < course.cost) {
    showToast('Недостаточно денег на обучение!', 'bad');
    return;
  }

  state.money -= course.cost;
  sounds.playLevelUp();

  if (course.skill === 'all') {
    emp.code += course.boost;
    emp.design += course.boost;
    emp.sound += course.boost;
  } else {
    emp[course.skill] += course.boost;
  }

  hideModal('train-modal');
  showToast(`${emp.name} успешно завершил обучение! Навыки повышены!`, 'good');
  renderStaff();
  renderOffice();
  updateTopStats();
};

// --- ФРИЛАНС КОНТРАКТЫ ---
function openContractsModal() {
  const contracts = [
    { title: 'Редизайн мобильного интерфейса', payout: 2500, timeWeeks: 1, req: 'Графика' },
    { title: 'Сетевой модуль для чужого шутера', payout: 5000, timeWeeks: 2, req: 'Код' },
    { title: 'Написание 8-битного саундтрека', payout: 1800, timeWeeks: 1, req: 'Звук' },
    { title: 'Портирование инди-проекта на Linux', payout: 3800, timeWeeks: 1, req: 'Код & Тест' }
  ];

  const list = document.getElementById('contracts-list');
  list.innerHTML = contracts.map((c, idx) => `
    <div class="contract-card">
      <div>
        <strong>${c.title}</strong>
        <div style="font-size: 0.8rem; color: var(--text-muted);">Требование: ${c.req} | Срок: ${c.timeWeeks} нед.</div>
      </div>
      <button class="btn btn-action-secondary" onclick="completeContract(${idx})">
        Выполнить (+$${c.payout})
      </button>
    </div>
  `).join('');

  window.availableContracts = contracts;
  showModal('contracts-modal');
}

window.completeContract = function(idx) {
  const c = window.availableContracts[idx];
  state.money += c.payout;
  sounds.playCash();
  hideModal('contracts-modal');
  showToast(`Контракт «${c.title}» выполнен! Получено +$${c.payout.toLocaleString()}`, 'good');
  addFeedItem(`Выполнен контракт: ${c.title} (+ $${c.payout}).`, 'good');
  updateTopStats();
};

// --- СИСТЕМА ИССЛЕДОВАНИЙ ---
function renderResearchTree() {
  document.getElementById('research-tab-rp-val').innerText = state.researchPoints;
  const grid = document.getElementById('research-tree-grid');

  const allResearchables = [
    ...GAME_DB.genres.map(g => ({ ...g, type: 'Жанр' })),
    ...GAME_DB.themes.map(t => ({ ...t, type: 'Тематика' })),
    ...GAME_DB.platforms.map(p => ({ ...p, type: 'Платформа' })),
    ...GAME_DB.engines.map(e => ({ ...e, type: 'Движок' }))
  ].filter(item => item.unlockRp > 0);

  grid.innerHTML = allResearchables.map(item => {
    const isUnlocked = state.unlockedTech.includes(item.id);

    return `
      <div class="research-card ${isUnlocked ? 'unlocked' : ''}">
        <div>
          <span class="sub-badge">${item.type}</span>
          <h3 style="margin-top: 8px;">${item.name}</h3>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">
            Стоимость: <strong>${item.unlockRp} RP</strong>
          </div>
        </div>

        ${isUnlocked ? `
          <button class="btn btn-sm btn-outline" disabled style="color:var(--accent-green); border-color:var(--accent-green);">
            <i class="fa-solid fa-check"></i> Изучено
          </button>
        ` : `
          <button class="btn btn-primary btn-sm" onclick="unlockResearch('${item.id}', ${item.unlockRp})">
            Изучить
          </button>
        `}
      </div>
    `;
  }).join('');
}

window.unlockResearch = function(id, rpCost) {
  if (state.researchPoints < rpCost) {
    showToast(`Не хватает очков исследований! Нужно ${rpCost} RP.`, 'bad');
    return;
  }

  state.researchPoints -= rpCost;
  state.unlockedTech.push(id);
  sounds.playLevelUp();
  showToast('Технология успешно исследована и доступна для новых игр!', 'good');
  
  populateDevDropdowns();
  renderResearchTree();
  updateTopStats();
};

// --- УЛУЧШЕНИЯ И ОФИСЫ ---
function renderUpgrades() {
  const container = document.getElementById('upgrades-list-grid');
  
  // Доступный апгрейд офиса
  const nextOffice = GAME_DB.offices[state.officeIndex + 1];
  let officeHtml = '';
  if (nextOffice) {
    officeHtml = `
      <div class="upgrade-card" style="border: 2px solid var(--primary);">
        <div>
          <span class="sub-badge" style="background:var(--primary); color:white;">Переезд в новый офис</span>
          <h3 style="margin-top: 8px;">🏢 ${nextOffice.name}</h3>
          <p class="subtitle">${nextOffice.desc}</p>
          <div style="font-size:0.85rem; margin-top: 8px;">
            Вместимость команды: <strong>до ${nextOffice.capacity} человек</strong><br>
            Аренда: <strong>$${nextOffice.rent}/мес</strong>
          </div>
        </div>
        <button class="btn btn-action-primary btn-lg" onclick="buyOfficeUpgrade(${state.officeIndex + 1})">
          Арендовать за $${nextOffice.price.toLocaleString()}
        </button>
      </div>
    `;
  } else {
    officeHtml = `
      <div class="upgrade-card owned">
        <h3>🏆 Максимальный офис достигнут!</h3>
        <p class="subtitle">Ваша компания занимает вершину небоскрёба индустрии!</p>
      </div>
    `;
  }

  // Оборудование
  const hardwareHtml = GAME_DB.upgrades.map(up => {
    const isOwned = state.ownedUpgrades.includes(up.id);
    return `
      <div class="upgrade-card ${isOwned ? 'owned' : ''}">
        <div>
          <span class="sub-badge">Оборудование</span>
          <h3 style="margin-top: 8px;">${up.name}</h3>
          <p class="subtitle">${up.desc}</p>
          <div style="font-size: 0.9rem; font-weight:700; color:var(--accent-gold); margin-top: 8px;">
            $${up.cost.toLocaleString()}
          </div>
        </div>
        ${isOwned ? `
          <button class="btn btn-outline" disabled style="color:var(--accent-green);"><i class="fa-solid fa-check"></i> Установлено</button>
        ` : `
          <button class="btn btn-secondary" onclick="buyHardwareUpgrade('${up.id}', ${up.cost})">Купить</button>
        `}
      </div>
    `;
  }).join('');

  container.innerHTML = officeHtml + hardwareHtml;
}

window.buyOfficeUpgrade = function(nextIdx) {
  const office = GAME_DB.offices[nextIdx];
  if (state.money < office.price) {
    showToast(`Недостаточно средств для переезда ($${office.price.toLocaleString()})!`, 'bad');
    return;
  }

  state.money -= office.price;
  state.officeIndex = nextIdx;
  sounds.playLevelUp();
  if (window.confetti) window.confetti({ particleCount: 150 });

  showToast(`Поздравляем с переездом! Новый офис: ${office.name}!`, 'gold');
  addFeedItem(`Студия переехала в «${office.name}»! Вместимость выросла до ${office.capacity} мест.`, 'gold');

  renderOffice();
  renderUpgrades();
  updateTopStats();
};

window.buyHardwareUpgrade = function(id, cost) {
  if (state.money < cost) {
    showToast('Недостаточно денег на покупку улучшения!', 'bad');
    return;
  }

  state.money -= cost;
  state.ownedUpgrades.push(id);
  sounds.playCash();
  showToast('Улучшение студии успешно установлено!', 'good');

  renderUpgrades();
  updateTopStats();
};

// --- МАРКЕТИНГОВЫЕ КАМПАНИИ ---
function renderMarketing() {
  const container = document.getElementById('marketing-actions-grid');

  container.innerHTML = GAME_DB.marketingCampaigns.map(camp => `
    <div class="market-card">
      <div>
        <h3>${camp.name}</h3>
        <p class="subtitle">${camp.desc}</p>
        <div style="font-size:0.85rem; margin-top:8px;">
          Бонус к продажам: <strong>x${camp.boostSales}</strong><br>
          Длительность: <strong>${camp.duration} нед.</strong>
        </div>
        <div style="font-size: 1.1rem; font-weight:800; color:var(--accent-gold); margin-top:8px;">
          $${camp.cost.toLocaleString()}
        </div>
      </div>
      <button class="btn btn-action-primary" onclick="launchMarketingCampaign('${camp.id}')">
        Запустить кампанию
      </button>
    </div>
  `).join('');
}

window.launchMarketingCampaign = function(campId) {
  const camp = GAME_DB.marketingCampaigns.find(c => c.id === campId);
  if (!camp) return;

  if (state.money < camp.cost) {
    showToast(`Недостаточно средств на маркетинг ($${camp.cost.toLocaleString()})!`, 'bad');
    return;
  }

  state.money -= camp.cost;
  sounds.playCash();

  state.activeCampaigns.push({
    ...camp,
    weeksLeft: camp.duration
  });

  // Усиливаем все текущие продаваемые игры
  state.games.forEach(g => {
    if (g.weeksOnMarket <= 24) {
      g.marketingMultiplier = (g.marketingMultiplier || 1.0) * camp.boostSales;
    }
  });

  showToast(`Рекламная кампания «${camp.name}» запущена! Продажи резко возросли!`, 'good');
  addFeedItem(`Запущена маркетинговая кампания «${camp.name}». Интерес публики на пике!`, 'info');
  updateTopStats();
};

function processMarketingCampaigns() {
  state.activeCampaigns = state.activeCampaigns.filter(c => {
    c.weeksLeft--;
    return c.weeksLeft > 0;
  });
}

// --- УТИЛИТЫ И ОБНОВЛЕНИЕ ДАННЫХ ---
function updateTopStats() {
  const cashValEl = document.getElementById('cash-val');
  cashValEl.innerText = `$${state.money.toLocaleString()}`;
  cashValEl.style.color = state.money < 0 ? 'var(--accent-red)' : 'var(--text-main)';

  document.getElementById('fans-val').innerText = state.fans.toLocaleString();
  document.getElementById('research-val').innerText = state.researchPoints;
  document.getElementById('date-val').innerText = `Год ${state.date.year}, Мес ${state.date.month}, Нед ${state.date.week}`;

  // Расчет ежемесячной прибыли
  const currentOffice = GAME_DB.offices[state.officeIndex];
  const rent = currentOffice.rent;
  const salaries = state.staff.reduce((acc, s) => acc + s.salary, 0);
  const monthlyCost = rent + salaries;
  document.getElementById('cash-rate').innerText = `-$${monthlyCost.toLocaleString()}/мес`;
}

function addFeedItem(text, type = 'info') {
  const feed = document.getElementById('feed-list');
  if (!feed) return;

  const item = document.createElement('div');
  item.className = `feed-item ${type}`;
  item.innerText = text;

  feed.prepend(item);
  while (feed.children.length > 20) {
    feed.removeChild(feed.lastChild);
  }
}

function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  let icon = 'fa-info-circle';
  if (type === 'good') icon = 'fa-circle-check';
  if (type === 'bad') icon = 'fa-triangle-exclamation';
  if (type === 'gold') icon = 'fa-award';

  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${msg}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function showModal(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'flex';
}

function hideModal(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}
