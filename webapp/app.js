cat > webapp/app.js <<'EOF'
const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    subtitle: "Планировщик путешествий (Mini App)",
    welcomeTitle: "Привет! Я My Route",
    welcomeText: "Заполни форму — я соберу маршрут, дам советы и чек‑лист.",
    features: ["Маршрут единым текстом", "Советы и лайфхаки", "Чек‑лист перед поездкой", "Список точек (в конце)"],
    startBtn: "Создать маршрут",
    priceNote: "1 маршрут = 50⭐ (скоро).",
    formTitle: "Параметры", backBtn: "← Назад", lblDestination: "Куда едем?",
    lblDays: "Дней", lblNights: "Ночей", lblBudget: "Бюджет",
    optBudgetLow: "Эконом", optBudgetMed: "Средний", optBudgetHigh: "Комфорт", optBudgetPremium: "Премиум",
    lblInterests: "Интересы", lblPace: "Темп",
    optPaceSlow: "Спокойно", optPaceNormal: "Нормально", optPaceFast: "Активно",
    lblCompanions: "Кто едет",
    optCompSolo: "Я один", optCompCouple: "Пара", optCompFamily: "Семья", optCompGroup: "Компания",
    lblNotes: "Пожелания", notesPh: "Люблю парки, не люблю музеи...", notesHelper: "Детали улучшают результат.",
    generateBtn: "Сгенерировать", formHint: "Ждите 5–15 сек.",
    resultTitle: "Готово", newBtn: "Заново",
    guideTitle: "Ваш маршрут", pointsTitle: "Точки",
    loading: "Думаю...", errFill: "Укажите куда и на сколько.", errApi: "Ошибка генерации."
  },
  en: {
    subtitle: "Travel Planner", welcomeTitle: "Hi! I'm My Route",
    welcomeText: "I'll generate an itinerary, tips, and checklist.",
    features: ["Single text itinerary", "Tips & Hacks", "Checklist", "Points list"],
    startBtn: "Start", priceNote: "1 itinerary = 50⭐ (soon).",
    formTitle: "Trip Details", backBtn: "← Back", lblDestination: "Destination",
    lblDays: "Days", lblNights: "Nights", lblBudget: "Budget",
    optBudgetLow: "Low", optBudgetMed: "Medium", optBudgetHigh: "High", optBudgetPremium: "Premium",
    lblInterests: "Interests", lblPace: "Pace",
    optPaceSlow: "Slow", optPaceNormal: "Normal", optPaceFast: "Fast",
    lblCompanions: "Companions",
    optCompSolo: "Solo", optCompCouple: "Couple", optCompFamily: "Family", optCompGroup: "Group",
    lblNotes: "Wishes", notesPh: "Love parks, hate museums...", notesHelper: "Details help.",
    generateBtn: "Generate", formHint: "Wait 5-15s.",
    resultTitle: "Done", newBtn: "New",
    guideTitle: "Your Route", pointsTitle: "Points",
    loading: "Thinking...", errFill: "Fill destination & days.", errApi: "Error generating."
  }
};

const INTERESTS = [
  { key: "food", ru: "еда", en: "food" }, { key: "museums", ru: "музеи", en: "museums" },
  { key: "nature", ru: "природа", en: "nature" }, { key: "shopping", ru: "шопинг", en: "shopping" }
];

function getLang() { return localStorage.getItem("lang") || "en"; }
function setLang(l) { localStorage.setItem("lang", l); render(); }
function showScreen(n) { ["screenWelcome", "screenForm", "screenResult"].forEach(id => document.getElementById(id).classList.add("hidden")); document.getElementById({welcome:"screenWelcome",form:"screenForm",result:"screenResult"}[n]).classList.remove("hidden"); }
function selectedInterests() { return Array.from(document.querySelectorAll(".pill.active")).map(x => x.dataset.key); }

function buildGuideText(data, lang) {
  const t = (r, e) => (lang === "ru" ? r : e);
  const lines = [];
  if (data?.summary) { lines.push(data.summary); lines.push(""); }
  if (data?.daily_plan) {
    lines.push(t("МАРШРУТ:", "ITINERARY:"));
    data.daily_plan.forEach(d => {
      lines.push("");
      lines.push(t(`День ${d.day}:`, `Day ${d.day}:`));
      if(d.morning && d.morning.length) lines.push(`${t("Утро","Morning")}: ${d.morning.join(", ")}`);
      if(d.afternoon && d.afternoon.length) lines.push(`${t("День","Afternoon")}: ${d.afternoon.join(", ")}`);
      if(d.evening && d.evening.length) lines.push(`${t("Вечер","Evening")}: ${d.evening.join(", ")}`);
    });
    lines.push("");
  }
  if (data?.tips) { lines.push(t("СОВЕТЫ:", "TIPS:")); data.tips.forEach(x => lines.push(`- ${x}`)); lines.push(""); }
  if (data?.checklist) { lines.push(t("ЧЕК-ЛИСТ:", "CHECKLIST:")); data.checklist.forEach(x => lines.push(`- ${x}`)); }
  return lines.join("\n");
}

function render() {
  const t = i18n[getLang()];
  document.getElementById("subtitle").textContent = t.subtitle;
  document.getElementById("welcomeTitle").textContent = t.welcomeTitle;
  document.getElementById("welcomeText").textContent = t.welcomeText;
  const ul = document.getElementById("featureList"); ul.innerHTML = "";
  t.features.forEach(x => { const li = document.createElement("li"); li.textContent = x; ul.appendChild(li); });
  document.getElementById("startBtn").textContent = t.startBtn;
  document.getElementById("priceNote").textContent = t.priceNote;
  document.getElementById("formTitle").textContent = t.formTitle;
  document.getElementById("backBtn").textContent = t.backBtn;
  document.getElementById("generateBtn").textContent = t.generateBtn;
  document.getElementById("resultTitle").textContent = t.resultTitle;
  document.getElementById("newBtn").textContent = t.newBtn;
  document.getElementById("guideTitle").textContent = t.guideTitle;
  document.getElementById("pointsTitle").textContent = t.pointsTitle;
  
  // Labels
  const ids = ["lblDestination", "lblDays", "lblNights", "lblBudget", "lblInterests", "lblPace", "lblCompanions", "lblNotes", "notesHelper", "formHint", "optBudgetLow", "optBudgetMed", "optBudgetHigh", "optBudgetPremium", "optPaceSlow", "optPaceNormal", "optPaceFast", "optCompSolo", "optCompCouple", "optCompFamily", "optCompGroup"];
  ids.forEach(id => { const el = document.getElementById(id); if(el && t[id]) el.textContent = t[id]; });
  document.getElementById("notes").placeholder = t.notesPh;

  // Interests
  const wrap = document.getElementById("interests");
  if(wrap.innerHTML === "") {
    INTERESTS.forEach(it => {
      const el = document.createElement("div"); el.className = "pill";
      el.dataset.key = it.key; el.textContent = getLang() === "ru" ? it.ru : it.en;
      el.addEventListener("click", () => el.classList.toggle("active"));
      wrap.appendChild(el);
    });
  }
}

async function generate() {
  const lang = getLang();
  const t = i18n[lang];
  const btn = document.getElementById("generateBtn");
  
  const dest = document.getElementById("destination").value.trim();
  const days = parseInt(document.getElementById("days").value);
  
  if(!dest || !days) { alert(t.errFill); return; }
  
  btn.disabled = true; btn.textContent = t.loading;
  
  try {
    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        language: lang, destination: dest, days: days,
        budget: document.getElementById("budget").value,
        pace: document.getElementById("pace").value,
        companions: document.getElementById("companions").value,
        interests: selectedInterests(),
        notes: document.getElementById("notes").value
      })
    });
    if(!res.ok) throw new Error();
    const data = await res.json();
    
    document.getElementById("guide").textContent = buildGuideText(data, lang);
    
    const pl = document.getElementById("pointsList"); pl.innerHTML = "";
    (data.map_points || []).forEach(p => {
       const li = document.createElement("li");
       li.textContent = `${p.name} (Day ${p.day || "?"})`;
       pl.appendChild(li);
    });
    
    showScreen("result");
  } catch(e) {
    alert(t.errApi);
  } finally {
    btn.disabled = false; btn.textContent = t.generateBtn;
  }
}

document.getElementById("btnRu").onclick = () => setLang("ru");
document.getElementById("btnEn").onclick = () => setLang("en");
document.getElementById("startBtn").onclick = () => showScreen("form");
document.getElementById("backBtn").onclick = () => showScreen("welcome");
document.getElementById("newBtn").onclick = () => showScreen("form");
document.getElementById("generateBtn").onclick = generate;

if(tg) { tg.ready(); tg.expand(); }
render();
EOF
