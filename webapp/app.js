const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    subtitle: "Планировщик", welcomeTitle: "Привет! Я My Route", welcomeText: "Я составлю подробнейший лонгрид по дням (с ценами и логистикой).", startBtn: "Начать",
    formTitle: "Детали поездки", backBtn: "← Назад", lblDestination: "Город/Страна", lblDays: "Дней", lblNights: "Ночей", lblBudget: "Бюджет",
    optBudgetLow: "Эконом", optBudgetMed: "Средний", optBudgetHigh: "Комфорт", lblNotes: "Пожелания",
    generateBtn: "Написать лонгрид", resultTitle: "Ваш путеводитель", newBtn: "Новый", loading: "Пишу огромную статью...", errFill: "Заполните город и дни."
  },
  en: {
    subtitle: "Planner", welcomeTitle: "Hi! I'm My Route", welcomeText: "I'll create a detailed daily longread with prices.", startBtn: "Start",
    formTitle: "Trip Details", backBtn: "← Back", lblDestination: "Destination", lblDays: "Days", lblNights: "Nights", lblBudget: "Budget",
    optBudgetLow: "Low", optBudgetMed: "Medium", optBudgetHigh: "Comfort", lblNotes: "Wishes",
    generateBtn: "Write Longread", resultTitle: "Your Guide", newBtn: "New", loading: "Writing huge article...", errFill: "Fill destination & days."
  }
};

let currentLang = localStorage.getItem("lang") || "ru";

function render() {
  const t = i18n[currentLang];
  document.getElementById("btnRu").className = `chip ${currentLang === 'ru' ? 'active' : ''}`;
  document.getElementById("btnEn").className = `chip ${currentLang === 'en' ? 'active' : ''}`;
  
  const ids = ["subtitle", "welcomeTitle", "welcomeText", "startBtn", "formTitle", "backBtn", "lblDestination", "lblDays", "lblNights", "lblBudget", "optBudgetLow", "optBudgetMed", "optBudgetHigh", "lblNotes", "generateBtn", "resultTitle", "newBtn"];
  ids.forEach(id => { const el = document.getElementById(id); if (el && t[id]) el.textContent = t[id]; });
}

function showScreen(id) {
  ["screenWelcome", "screenForm", "screenResult"].forEach(s => document.getElementById(s).classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  window.scrollTo(0, 0);
}

// Умный парсер: выделяет жирным названия мест
function formatText(text) {
  let clean = text.replace(/^(Утро|День|Вечер|Morning|Afternoon|Evening)[:.-]?\s*/i, '');
  if (clean.includes('**')) {
    clean = clean.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
  } else {
    const parts = clean.split('. ');
    if (parts.length > 1 && parts[0].length < 80) clean = `<b>${parts[0]}.</b> ` + parts.slice(1).join('. ');
  }
  return clean;
}

// Склеиваем массивы утра/дня/вечера в сплошной текст
function buildArticle(data) {
  let html = '';
  if (data.daily_plan && Array.isArray(data.daily_plan)) {
    data.daily_plan.forEach(d => {
      html += `<h2 class="blog-day-title">День ${d.day}</h2>`;
      const activities = [];
      if (d.morning) activities.push(...d.morning);
      if (d.afternoon) activities.push(...d.afternoon);
      if (d.evening) activities.push(...d.evening);

      if (activities.length > 0) {
        html += `<div class="blog-list">`;
        activities.forEach(act => {
          html += `<p class="blog-paragraph">${formatText(act)}</p>`;
        });
        html += `</div>`;
      }
    });
  }
  return html;
}

async function generate() {
  const btn = document.getElementById("generateBtn");
  const dest = document.getElementById("destination").value.trim();
  const days = parseInt(document.getElementById("days").value);
  if (!dest || !days) return alert(i18n[currentLang].errFill);
  
  btn.disabled = true; btn.textContent = i18n[currentLang].loading;
  
  try {
    const notes = document.getElementById("notes").value;
    // ЖЕСТКИЙ ПРИКАЗ: Писать длинно в стандартный JSON
    const hackPrompt = currentLang === 'ru' 
      ? " (ВНИМАНИЕ: Для каждой точки (morning/afternoon/evening) пиши ОГРОМНЫЙ текст сплошняком. Обязательно: История, Цены (в рублях/валюте), Часы работы, Логистика (как добраться). Формат: **Название**. Длинное описание на 5-6 предложений. Никаких коротких списков!)"
      : " (ATTENTION: For every item write a HUGE paragraph. Must include: History, Prices, Hours, Logistics. Format: **Name**. Long 5-6 sentence description.)";

    const payload = {
      language: currentLang, destination: dest, days: days,
      budget: document.getElementById("budget").value, pace: "normal", companions: "couple", interests: [],
      notes: notes + hackPrompt
    };
    
    const res = await fetch(`${API_BASE}/route/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const data = await res.json();
    
    document.getElementById("resultSummary").textContent = data.summary || "";
    document.getElementById("guide").innerHTML = buildArticle(data);
    showScreen("screenResult");
  } catch (e) {
    alert("Ошибка сервера. Попробуйте еще раз.");
  } finally {
    btn.disabled = false; btn.textContent = i18n[currentLang].generateBtn;
  }
}

document.getElementById("btnRu").onclick = () => { currentLang = "ru"; localStorage.setItem("lang", "ru"); render(); };
document.getElementById("btnEn").onclick = () => { currentLang = "en"; localStorage.setItem("lang", "en"); render(); };
document.getElementById("startBtn").onclick = () => showScreen("screenForm");
document.getElementById("backBtn").onclick = () => showScreen("screenWelcome");
document.getElementById("newBtn").onclick = () => showScreen("screenForm");
document.getElementById("generateBtn").onclick = generate;

if (tg) { tg.ready(); tg.expand(); }
render();
