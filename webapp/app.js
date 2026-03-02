const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    subtitle: "Планировщик путешествий",
    welcomeTitle: "Привет! Я My Route",
    welcomeText: "Заполни форму — я создам подробный гид сплошным текстом.",
    features: ["Гид в стиле статьи", "История и цены", "Чек‑лист перед поездкой", "Список точек (в конце)"],
    startBtn: "Создать маршрут",
    priceNote: "1 маршрут = 50⭐ (бесплатно в бете).",
    
    formTitle: "Параметры поездки", backBtn: "← Назад", 
    lblDestination: "Куда едем?",
    lblDays: "Дней", lblNights: "Ночей", lblBudget: "Бюджет",
    optBudgetLow: "Эконом", optBudgetMed: "Средний", optBudgetHigh: "Комфорт", optBudgetPremium: "Премиум",
    lblInterests: "Интересы", lblPace: "Темп",
    optPaceSlow: "Спокойно", optPaceNormal: "Нормально", optPaceFast: "Активно",
    lblCompanions: "Кто едет",
    optCompSolo: "Я один", optCompCouple: "Пара", optCompFamily: "Семья", optCompGroup: "Компания",
    lblNotes: "Пожелания", notesPh: "Например: люблю историю, вкусно поесть...", notesHelper: "Чем больше деталей, тем лучше результат.",
    generateBtn: "Сгенерировать гид", formHint: "Это займет 10–20 секунд.",
    
    resultTitle: "Программа путешествия", newBtn: "Новый",
    guideTitle: "Ваш маршрут", pointsTitle: "Карта локаций",
    loading: "Пишу статью...", errFill: "Напишите, куда едете и на сколько дней.", errApi: "Ошибка генерации. Попробуйте снова."
  },
  en: {
    subtitle: "Travel Planner",
    welcomeTitle: "Hi! I'm My Route",
    welcomeText: "I'll generate a detailed continuous guide.",
    features: ["Article style itinerary", "History & Prices", "Checklist", "Map points"],
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
    lblNotes: "Wishes", notesPh: "Love history, food...", notesHelper: "More details = better guide.",
    generateBtn: "Generate Guide", formHint: "Takes 10-20 seconds.",
    
    resultTitle: "Itinerary", newBtn: "New",
    guideTitle: "Your Route", pointsTitle: "Map Locations",
    loading: "Writing article...", errFill: "Fill destination & days.", errApi: "Error generating."
  }
};

const INTERESTS = [
  { key: "food", ru: "еда", en: "food" }, 
  { key: "history", ru: "история", en: "history" },
  { key: "nature", ru: "природа", en: "nature" }, 
  { key: "shopping", ru: "шопинг", en: "shopping" }
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

// === ФОРМАТ СПЛОШНОЙ СТАТЬИ ===
function buildGuideHTML(data, lang) {
  const t = (r, e) => (lang === "ru" ? r : e);
  let html = `<div class="blog-article">`;

  if (Array.isArray(data.daily_plan)) {
    data.daily_plan.forEach(d => {
      // Заголовок дня (просто текст, без карточек)
      html += `<h3 class="blog-day-title">${t("День", "Day")} ${d.day}</h3>`;
      
      // Собираем всё (утро, день, вечер) в один единый массив
      const allActivities = [];
      if (d.morning) allActivities.push(...d.morning);
      if (d.afternoon) allActivities.push(...d.afternoon);
      if (d.evening) allActivities.push(...d.evening);

      // Выводим сплошным списком с точками
      if (allActivities.length > 0) {
        html += `<ul class="blog-list">`;
        allActivities.forEach(item => {
          html += `<li>${item}</li>`;
        });
        html += `</ul>`;
      }
    });
  }

  // Добавляем советы без цветастых карточек
  if (Array.isArray(data.tips) && data.tips.length > 0) {
    html += `<h3 class="blog-day-title">💡 ${t("Советы", "Tips")}</h3>`;
    html += `<ul class="blog-list">`;
    data.tips.forEach(x => html += `<li>${x}</li>`);
    html += `</ul>`;
  }

  if (Array.isArray(data.checklist) && data.checklist.length > 0) {
    html += `<h3 class="blog-day-title">✅ ${t("Чек-лист", "Checklist")}</h3>`;
    html += `<ul class="blog-list">`;
    data.checklist.forEach(x => html += `<li>${x}</li>`);
    html += `</ul>`;
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
    
    // СТРОГАЯ ИНСТРУКЦИЯ ДЛЯ ИИ: Делать жирным места и писать сплошным текстом
    const systemInstruction = lang === 'ru' 
      ? " (ИНСТРУКЦИЯ ДЛЯ ИИ: Не пиши слова Утро/День/Вечер! Просто перечисляй места. Каждый пункт ВСЕГДА начинай с названия локации, обернутого в тег <b>Название</b>, затем ставь точку и пиши 3-4 предложения с историей, описанием и ценой.)"
      : " (AI INSTRUCTION: Do not write Morning/Afternoon/Evening! Start every item with the location name wrapped in <b>Name</b> tags, followed by a period and a detailed 3-4 sentence description with history and prices.)";

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
    
    const summaryEl = document.getElementById("resultSummary");
    if(summaryEl) summaryEl.textContent = data.summary || "";

    const guideEl = document.getElementById("guide");
    if(guideEl) guideEl.innerHTML = buildGuideHTML(data, lang);
    
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
