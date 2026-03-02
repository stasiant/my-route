const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    subtitle: "Трэвел-блогер",
    welcomeTitle: "Привет! Я My Route",
    welcomeText: "Я напишу для вас подробный путеводитель в стиле блога.",
    features: ["Подробные описания", "История и цены", "Маршрут по дням", "Карта локаций"],
    startBtn: "Начать",
    priceNote: "Бесплатно в бета-версии.",
    formTitle: "Детали поездки", backBtn: "← Назад", 
    lblDestination: "Город / Страна",
    lblDays: "Дней", lblNights: "Ночей", lblBudget: "Бюджет",
    optBudgetLow: "Эконом", optBudgetMed: "Средний", optBudgetHigh: "Высокий", optBudgetPremium: "Премиум",
    lblInterests: "Интересы", lblPace: "Темп",
    optPaceSlow: "Расслабленный", optPaceNormal: "Обычный", optPaceFast: "Насыщенный",
    lblCompanions: "Кто едет",
    optCompSolo: "Я один", optCompCouple: "Пара", optCompFamily: "Семья", optCompGroup: "Компания",
    lblNotes: "Пожелания", notesPh: "Люблю архитектуру, вкусную еду...", notesHelper: "Чем больше деталей, тем интереснее статья.",
    generateBtn: "Написать гид", formHint: "Пишу статью (15-20 сек)...",
    resultTitle: "Ваш путеводитель", newBtn: "Новый",
    guideTitle: "Программа", pointsTitle: "Карта мест",
    loading: "Пишу статью...", errFill: "Куда едем и на сколько дней?", errApi: "Ошибка. Попробуйте снова."
  },
  en: {
    subtitle: "Travel Blogger",
    welcomeTitle: "Hi! I'm My Route",
    welcomeText: "I will write a detailed travel-blog style guide for you.",
    features: ["Detailed descriptions", "History & Prices", "Daily itinerary", "Map locations"],
    startBtn: "Start",
    priceNote: "Free in beta.",
    formTitle: "Trip Details", backBtn: "← Back", 
    lblDestination: "City / Country",
    lblDays: "Days", lblNights: "Nights", lblBudget: "Budget",
    optBudgetLow: "Low", optBudgetMed: "Medium", optBudgetHigh: "High", optBudgetPremium: "Premium",
    lblInterests: "Interests", lblPace: "Pace",
    optPaceSlow: "Relaxed", optPaceNormal: "Normal", optPaceFast: "Intense",
    lblCompanions: "Companions",
    optCompSolo: "Solo", optCompCouple: "Couple", optCompFamily: "Family", optCompGroup: "Group",
    lblNotes: "Wishes", notesPh: "Architecture, food...", notesHelper: "More details = better article.",
    generateBtn: "Write Guide", formHint: "Writing article (15-20s)...",
    resultTitle: "Your Guide", newBtn: "New",
    guideTitle: "Itinerary", pointsTitle: "Map Locations",
    loading: "Writing...", errFill: "Fill destination & days.", errApi: "Error."
  }
};

const INTERESTS = [
  { key: "food", ru: "Еда", en: "Food" }, 
  { key: "history", ru: "История", en: "History" },
  { key: "art", ru: "Искусство", en: "Art" },
  { key: "nature", ru: "Природа", en: "Nature" }, 
  { key: "shopping", ru: "Шопинг", en: "Shopping" }
];

function getLang() { return localStorage.getItem("lang") || "ru"; }
function setLang(l) { localStorage.setItem("lang", l); render(); }

function showScreen(screenId) {
  ["screenWelcome", "screenForm", "screenResult"].forEach(id => {
    document.getElementById(id).classList.add("hidden");
  });
  document.getElementById(screenId).classList.remove("hidden");
  window.scrollTo(0, 0);
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el && text) el.textContent = text;
}

function render() {
  const lang = getLang();
  const t = i18n[lang];

  document.getElementById("btnRu").className = `chip ${lang === 'ru' ? 'active' : ''}`;
  document.getElementById("btnEn").className = `chip ${lang === 'en' ? 'active' : ''}`;

  setText("subtitle", t.subtitle);
  setText("welcomeTitle", t.welcomeTitle);
  setText("welcomeText", t.welcomeText);
  setText("startBtn", t.startBtn);
  setText("priceNote", t.priceNote);
  
  const ul = document.getElementById("featureList");
  if(ul) {
    ul.innerHTML = "";
    t.features.forEach(x => {
      const li = document.createElement("li");
      li.textContent = x;
      ul.appendChild(li);
    });
  }

  setText("formTitle", t.formTitle);
  setText("backBtn", t.backBtn);
  setText("generateBtn", t.generateBtn);
  setText("formHint", t.formHint);
  setText("resultTitle", t.resultTitle);
  setText("newBtn", t.newBtn);
  setText("guideTitle", t.guideTitle);
  setText("pointsTitle", t.pointsTitle);

  const ids = ["lblDestination", "lblDays", "lblNights", "lblBudget", "lblInterests", "lblPace", "lblCompanions", "lblNotes", "notesHelper", "optBudgetLow", "optBudgetMed", "optBudgetHigh", "optBudgetPremium", "optPaceSlow", "optPaceNormal", "optPaceFast", "optCompSolo", "optCompCouple", "optCompFamily", "optCompGroup"];
  ids.forEach(id => { if (t[id]) setText(id, t[id]); });

  const notesEl = document.getElementById("notes");
  if(notesEl) notesEl.placeholder = t.notesPh;

  const wrap = document.getElementById("interests");
  if (wrap) {
    if (wrap.children.length === 0) {
      INTERESTS.forEach(it => {
        const el = document.createElement("div");
        el.className = "pill";
        el.dataset.key = it.key;
        el.textContent = lang === "ru" ? it.ru : it.en;
        el.onclick = () => el.classList.toggle("active");
        wrap.appendChild(el);
      });
    } else {
      Array.from(wrap.children).forEach(el => {
        const it = INTERESTS.find(i => i.key === el.dataset.key);
        if(it) el.textContent = lang === "ru" ? it.ru : it.en;
      });
    }
  }
}

// Форматируем текст: жирный шрифт
function formatAIText(text) {
  // Убираем "Утро:" и прочее
  let clean = text.replace(/^(Утро|День|Вечер|Morning|Afternoon|Evening)[:.-]?\s*/i, '');
  
  // Делаем жирным то, что в звездочках **
  clean = clean.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
  
  // Если звездочек нет, пробуем выделить первое предложение до точки (если оно короткое) как заголовок
  if (!clean.includes('<b>')) {
     const parts = clean.split('. ');
     if (parts.length > 1 && parts[0].length < 60) {
        clean = `<b>${parts[0]}.</b> ${parts.slice(1).join('. ')}`;
     }
  }
  return clean;
}

// === СТРОИМ СТАТЬЮ ===
function buildGuideHTML(data, lang) {
  const t = (r, e) => (lang === "ru" ? r : e);
  let html = `<div class="blog-article">`;

  if (Array.isArray(data.daily_plan)) {
    data.daily_plan.forEach(d => {
      // Заголовок дня
      html += `<h3 class="blog-day-title">${t("День", "Day")} ${d.day}</h3>`;
      
      // Сливаем всё в один список
      const allActivities = [];
      if (d.morning) allActivities.push(...d.morning);
      if (d.afternoon) allActivities.push(...d.afternoon);
      if (d.evening) allActivities.push(...d.evening);

      if (allActivities.length > 0) {
        html += `<ul class="blog-list">`;
        allActivities.forEach(item => {
          html += `<li>${formatAIText(item)}</li>`;
        });
        html += `</ul>`;
      }
    });
  }
  
  html += `</div>`;
  return html;
}

async function generate() {
  const lang = getLang();
  const t = i18n[lang];
  const btn = document.getElementById("generateBtn");
  
  const dest = document.getElementById("destination").value.trim();
  const days = parseInt(document.getElementById("days").value);
  
  if (!dest || !days) { alert(t.errFill); return; }
  
  btn.disabled = true; btn.textContent = t.loading;
  
  try {
    const userNotes = document.getElementById("notes").value;
    
    // === САМОЕ ГЛАВНОЕ: ПРИКАЗ ДЛЯ ИИ ===
    // Это скрытая часть запроса, которая заставляет AI писать много текста.
    const systemInstruction = lang === 'ru' 
      ? " (КРИТИЧЕСКИ ВАЖНО: Не пиши списком дел! Пиши как трэвел-блогер. Для каждого пункта сначала пиши **Название Места** (в звездочках), затем ставь точку, а затем пиши ПОДРОБНОЕ описание на 3-4 предложения: историю, атмосферу, цены билетов. Не разделяй на Утро/Вечер. Просто список мест.)"
      : " (CRITICAL: Do not write a to-do list! Write like a travel blogger. For every item, start with **Location Name** (in stars), then a period, then a DETAILED paragraph (3-4 sentences) about history, atmosphere, prices. Do not separate Morning/Evening.)";

    const payload = {
      language: lang, destination: dest, days: days,
      budget: document.getElementById("budget").value,
      pace: document.getElementById("pace").value,
      companions: document.getElementById("companions").value,
      interests: Array.from(document.querySelectorAll(".pill.active")).map(x => x.dataset.key),
      notes: userNotes + systemInstruction
    };
    
    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("API Error");
    const data = await res.json();
    
    // Summary
    const summaryEl = document.getElementById("resultSummary");
    if(summaryEl) summaryEl.textContent = data.summary || "";

    // Guide
    const guideEl = document.getElementById("guide");
    if(guideEl) guideEl.innerHTML = buildGuideHTML(data, lang);
    
    // Points
    const pl = document.getElementById("pointsList");
    if (pl) {
      pl.innerHTML = "";
      (data.map_points || []).forEach(p => {
        const li = document.createElement("li");
        li.textContent = p.name;
        pl.appendChild(li);
      });
    }
    
    showScreen("screenResult");
  } catch (e) {
    console.error(e);
    alert(t.errApi);
  } finally {
    btn.disabled = false; btn.textContent = t.generateBtn;
  }
}

document.getElementById("btnRu").onclick = () => setLang("ru");
document.getElementById("btnEn").onclick = () => setLang("en");
document.getElementById("startBtn").onclick = () => showScreen("screenForm");
document.getElementById("backBtn").onclick = () => showScreen("screenWelcome");
document.getElementById("newBtn").onclick = () => showScreen("screenForm");
document.getElementById("generateBtn").onclick = generate;

if (tg) { tg.ready(); tg.expand(); }
render();
