const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    subtitle: "Трэвел-блог", welcomeTitle: "Привет! Я My Route", welcomeText: "Я напишу для вас уникальную историю путешествия.", startBtn: "Начать",
    formTitle: "Детали", backBtn: "← Назад", lblDestination: "Куда?", lblDays: "Дней", lblNights: "Ночей", lblBudget: "Бюджет",
    optBudgetLow: "Эконом", optBudgetMed: "Средний", optBudgetHigh: "Комфорт", lblNotes: "Пожелания",
    generateBtn: "Написать историю", resultTitle: "Ваша история", newBtn: "Новый", loading: "Пишу книгу (30 сек)...", errFill: "Заполните поля."
  },
  en: {
    subtitle: "Travel Blog", welcomeTitle: "Hi! I'm My Route", welcomeText: "I will write a unique travel story for you.", startBtn: "Start",
    formTitle: "Details", backBtn: "← Back", lblDestination: "Where?", lblDays: "Days", lblNights: "Nights", lblBudget: "Budget",
    optBudgetLow: "Low", optBudgetMed: "Medium", optBudgetHigh: "Comfort", lblNotes: "Wishes",
    generateBtn: "Write Story", resultTitle: "Your Story", newBtn: "New", loading: "Writing book...", errFill: "Fill fields."
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

async function generate() {
  const btn = document.getElementById("generateBtn");
  const dest = document.getElementById("destination").value.trim();
  const days = parseInt(document.getElementById("days").value);
  if (!dest || !days) return alert(i18n[currentLang].errFill);
  
  btn.disabled = true; btn.textContent = i18n[currentLang].loading;
  
  try {
    const notes = document.getElementById("notes").value;
    const hackPrompt = " (КРИТИЧЕСКИ ВАЖНО: ПИШИ СПЛОШНЫМ ТЕКСТОМ! Никаких списков, никаких коротких предложений! Пиши как писатель. Абзацы должны быть ОГРОМНЫМИ. В каждом абзаце пиши цены и историю. Используй теги <h3> для заголовков и <p> для длинного текста.)";

    const payload = {
      language: currentLang, destination: dest, days: days,
      budget: document.getElementById("budget").value, pace: "normal", companions: "couple", interests: [],
      notes: notes + hackPrompt
    };
    
    const res = await fetch(`${API_BASE}/route/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const data = await res.json();
    
    document.getElementById("resultSummary").textContent = data.summary || "";
    
    let finalHtml = "";
    if (data.full_article_html) {
        finalHtml = data.full_article_html;
    } else if (data.daily_plan) {
        // Если сервер еще не обновился, заставляем старый формат выглядеть как абзацы
        data.daily_plan.forEach(d => {
            const arr = [...(d.morning||[]), ...(d.afternoon||[]), ...(d.evening||[])];
            if(arr.length) {
                arr.forEach(txt => finalHtml += `<p style="margin-bottom: 25px; line-height: 1.6;"><b>${txt}</b></p>`);
            }
        });
    }

    document.getElementById("guide").innerHTML = `<div class="story-content">${finalHtml}</div>`;
    showScreen("screenResult");
  } catch (e) {
    alert("Ошибка. Попробуйте еще раз.");
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
