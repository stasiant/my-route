const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    subtitle: "Планировщик путешествий",
    welcomeTitle: "Привет! Я My Route",
    welcomeText: "Заполни форму — я соберу маршрут по дням, дам советы и чек‑лист.",
    features: ["Маршрут единым текстом", "Советы и лайфхаки", "Чек‑лист перед поездкой", "Список точек (в конце)"],
    startBtn: "Создать маршрут",
    priceNote: "1 маршрут = 50⭐ (бесплатно в бете).",
    
    formTitle: "Параметры", backBtn: "← Назад", 
    lblDestination: "Куда едем?",
    lblDays: "Дней", lblNights: "Ночей", lblBudget: "Бюджет",
    optBudgetLow: "Эконом", optBudgetMed: "Средний", optBudgetHigh: "Комфорт", optBudgetPremium: "Премиум",
    lblInterests: "Интересы", lblPace: "Темп",
    optPaceSlow: "Спокойно", optPaceNormal: "Нормально", optPaceFast: "Активно",
    lblCompanions: "Кто едет",
    optCompSolo: "Я один", optCompCouple: "Пара", optCompFamily: "Семья", optCompGroup: "Компания",
    lblNotes: "Пожелания", notesPh: "Люблю парки, не люблю музеи...", notesHelper: "Детали улучшают результат.",
    generateBtn: "Сгенерировать", formHint: "Ждите 5–15 сек.",
    
    resultTitle: "Готово", newBtn: "Заново",
    guideTitle: "Ваш маршрут", pointsTitle: "Точки для карты",
    loading: "Думаю...", errFill: "Укажите куда и на сколько дней.", errApi: "Ошибка генерации."
  },
  en: {
    subtitle: "Travel Planner",
    welcomeTitle: "Hi! I'm My Route",
    welcomeText: "I'll generate an itinerary, tips, and checklist.",
    features: ["Single text itinerary", "Tips & Hacks", "Checklist", "Points list"],
    startBtn: "Start",
    priceNote: "1 itinerary = 50⭐ (free in beta).",
    
    formTitle: "Trip Details", backBtn: "← Back", 
    lblDestination: "Destination",
    lblDays: "Days", lblNights: "Nights", lblBudget: "Budget",
    optBudgetLow: "Low", optBudgetMed: "Medium", optBudgetHigh: "High", optBudgetPremium: "Premium",
    lblInterests: "Interests", lblPace: "Pace",
    optPaceSlow: "Slow", optPaceNormal: "Normal", optPaceFast: "Fast",
    lblCompanions: "Companions",
    optCompSolo: "Solo", optCompCouple: "Couple", optCompFamily: "Family", optCompGroup: "Group",
    lblNotes: "Wishes", notesPh: "Love parks, hate museums...", notesHelper: "Details help.",
    generateBtn: "Generate", formHint: "Wait 5-15s.",
    
    resultTitle: "Done", newBtn: "New",
    guideTitle: "Your Route", pointsTitle: "Map Points",
    loading: "Thinking...", errFill: "Fill destination & days.", errApi: "Error generating."
  }
};

const INTERESTS = [
  { key: "food", ru: "еда", en: "food" }, 
  { key: "museums", ru: "музеи", en: "museums" },
  { key: "nature", ru: "природа", en: "nature" }, 
  { key: "shopping", ru: "шопинг", en: "shopping" }
];

function getLang() { return localStorage.getItem("lang") || "ru"; }
function setLang(l) { localStorage.setItem("lang", l); render(); }

// --- Управление экранами ---
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

// --- Отрисовка интерфейса ---
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

  const ids = [
    "lblDestination", "lblDays", "lblNights", "lblBudget", "lblInterests", "lblPace", "lblCompanions", "lblNotes", "notesHelper",
    "optBudgetLow", "optBudgetMed", "optBudgetHigh", "optBudgetPremium",
    "optPaceSlow", "optPaceNormal", "optPaceFast",
    "optCompSolo", "optCompCouple", "optCompFamily", "optCompGroup"
  ];
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

// === КРАСИВАЯ СБОРКА ТЕКСТА (HTML) ===
function buildGuideHTML(data, lang) {
  const t = (r, e) => (lang === "ru" ? r : e);
  let html = "";

  // 1. Дни
  if (Array.isArray(data.daily_plan)) {
    data.daily_plan.forEach(d => {
      // Заголовок дня
      html += `<div class="day-block">`;
      html += `<div class="day-header">${t("День", "Day")} ${d.day}</div>`;
      
      // Список активностей (точки)
      html += `<ul class="day-activities">`;
      if (d.morning && d.morning.length) {
         html += `<li><b>${t("Утро","Morning")}:</b> ${d.morning.join(", ")}</li>`;
      }
      if (d.afternoon && d.afternoon.length) {
         html += `<li><b>${t("День","Afternoon")}:</b> ${d.afternoon.join(", ")}</li>`;
      }
      if (d.evening && d.evening.length) {
         html += `<li><b>${t("Вечер","Evening")}:</b> ${d.evening.join(", ")}</li>`;
      }
      html += `</ul>`;
      html += `</div>`;
    });
  }

  // 2. Советы
  if (Array.isArray(data.tips) && data.tips.length > 0) {
    html += `<div class="section-block">`;
    html += `<div class="section-title">💡 ${t("Советы", "Tips")}</div>`;
    html += `<ul class="simple-list">`;
    data.tips.forEach(x => html += `<li>${x}</li>`);
    html += `</ul></div>`;
  }

  // 3. Чек-лист
  if (Array.isArray(data.checklist) && data.checklist.length > 0) {
    html += `<div class="section-block">`;
    html += `<div class="section-title">✅ ${t("Чек-лист", "Checklist")}</div>`;
    html += `<ul class="simple-list">`;
    data.checklist.forEach(x => html += `<li>${x}</li>`);
    html += `</ul></div>`;
  }

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
    const payload = {
      language: lang, destination: dest, days: days,
      budget: document.getElementById("budget").value,
      pace: document.getElementById("pace").value,
      companions: document.getElementById("companions").value,
      interests: Array.from(document.querySelectorAll(".pill.active")).map(x => x.dataset.key),
      notes: document.getElementById("notes").value
    };
    
    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("API Error");
    const data = await res.json();
    
    // Вставляем Summary
    const summaryEl = document.getElementById("resultSummary");
    if(summaryEl) summaryEl.textContent = data.summary || "";

    // Вставляем Красивый HTML
    const guideEl = document.getElementById("guide");
    if(guideEl) guideEl.innerHTML = buildGuideHTML(data, lang);
    
    // Вставляем точки
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

// Events
document.getElementById("btnRu").onclick = () => setLang("ru");
document.getElementById("btnEn").onclick = () => setLang("en");
document.getElementById("startBtn").onclick = () => showScreen("screenForm");
document.getElementById("backBtn").onclick = () => showScreen("screenWelcome");
document.getElementById("newBtn").onclick = () => showScreen("screenForm");
document.getElementById("generateBtn").onclick = generate;

// Init
if (tg) { tg.ready(); tg.expand(); }
render();
