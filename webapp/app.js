const tg = window.Telegram?.WebApp;

const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    subtitle: "Планировщик путешествий (Mini App)",
    welcomeTitle: "Привет! Я My Route",
    welcomeText:
      "Заполни форму — я соберу маршрут по дням, дам советы и чек‑лист.",
    features: [
      "Маршрут по дням: утро / день / вечер",
      "Советы и лайфхаки (транспорт, безопасность, как не переплачивать)",
      "Чек‑лист перед поездкой",
      "Интерактивная карта (добавим дальше)"
    ],
    startBtn: "Создать маршрут",
    priceNote: "1 маршрут = 50⭐ (оплата Stars будет на следующем шаге).",

    formTitle: "Параметры поездки",
    backBtn: "← Назад",
    lblDestination: "Страна / город(а)",
    lblDays: "Дней",
    lblNights: "Ночей (опционально)",
    lblBudget: "Бюджет",
    optBudgetLow: "Эконом",
    optBudgetMed: "Средний",
    optBudgetHigh: "Комфорт",
    optBudgetPremium: "Премиум",
    lblInterests: "Интересы",
    lblPace: "Темп",
    optPaceSlow: "Спокойно",
    optPaceNormal: "Нормально",
    optPaceFast: "Активно",
    lblCompanions: "Кто едет",
    optCompSolo: "1 человек",
    optCompCouple: "Пара",
    optCompFamily: "Семья",
    optCompGroup: "Компания",
    lblNotes: "Дополнительные пожелания",
    notesPh: "Например: люблю ходить пешком, без музеев, больше еды…",
    notesHelper:
      "Чем подробнее, тем лучше: отель/район, время подъёма, бюджет на день, предпочтения в еде, что исключить, как перемещаться (пешком/такси/авто), обязательные места.",
    generateBtn: "Сгенерировать",
    formHint: "Генерация занимает 5–15 секунд.",

    resultTitle: "Готово",
    newBtn: "Новый маршрут",
    planTitle: "План по дням",
    tipsTitle: "Советы",
    checklistTitle: "Чек‑лист",
    loading: "Генерирую маршрут…",
    errFill: "Заполни хотя бы 'Страна/город' и 'Дней'.",
    errApi: "Не получилось сгенерировать. Попробуй ещё раз."
  },
  en: {
    subtitle: "Travel Planner (Mini App)",
    welcomeTitle: "Hi! I'm My Route",
    welcomeText:
      "Fill the form — I’ll generate a day-by-day itinerary with tips and a checklist.",
    features: [
      "Day-by-day plan: morning / afternoon / evening",
      "Tips & hacks (transport, safety, avoid overpaying)",
      "Pre-trip checklist",
      "Interactive map (next step)"
    ],
    startBtn: "Create itinerary",
    priceNote: "1 itinerary = 50⭐ (Stars payment will be added next).",

    formTitle: "Trip details",
    backBtn: "← Back",
    lblDestination: "Country / city(ies)",
    lblDays: "Days",
    lblNights: "Nights (optional)",
    lblBudget: "Budget",
    optBudgetLow: "Low",
    optBudgetMed: "Medium",
    optBudgetHigh: "Comfort",
    optBudgetPremium: "Premium",
    lblInterests: "Interests",
    lblPace: "Pace",
    optPaceSlow: "Slow",
    optPaceNormal: "Normal",
    optPaceFast: "Fast",
    lblCompanions: "Who’s going",
    optCompSolo: "Solo",
    optCompCouple: "Couple",
    optCompFamily: "Family",
    optCompGroup: "Group",
    lblNotes: "Extra wishes",
    notesPh: "E.g., love walking, no museums, more food spots…",
    notesHelper:
      "Write as much detail as possible: hotel/area, wake-up time, daily budget, food preferences, what to exclude, how you move (walk/taxi/car), must-see places.",
    generateBtn: "Generate",
    formHint: "Generation takes 5–15 seconds.",

    resultTitle: "Done",
    newBtn: "New itinerary",
    planTitle: "Day-by-day plan",
    tipsTitle: "Tips",
    checklistTitle: "Checklist",
    loading: "Generating itinerary…",
    errFill: "Please fill at least Destination and Days.",
    errApi: "Could not generate. Please try again."
  }
};

const INTERESTS = [
  { key: "food", ru: "еда", en: "food" },
  { key: "museums", ru: "музеи", en: "museums" },
  { key: "nature", ru: "природа", en: "nature" },
  { key: "nightlife", ru: "ночная жизнь", en: "nightlife" },
  { key: "kids", ru: "дети", en: "kids" },
  { key: "shopping", ru: "шопинг", en: "shopping" },
  { key: "beach", ru: "пляжный отдых", en: "beach" },
  { key: "business", ru: "деловая поездка", en: "business" }
];

function getLang() {
  return localStorage.getItem("lang") || "en";
}
function setLang(lang) {
  localStorage.setItem("lang", lang);
  render();
}

function showScreen(name) {
  const map = { welcome: "screenWelcome", form: "screenForm", result: "screenResult" };
  Object.values(map).forEach((id) => document.getElementById(id).classList.add("hidden"));
  document.getElementById(map[name]).classList.remove("hidden");
}

function selectedInterests() {
  return Array.from(document.querySelectorAll(".pill.active")).map((x) => x.dataset.key);
}

function setLoading(isLoading, text) {
  const btn = document.getElementById("generateBtn");
  btn.disabled = isLoading;
  btn.textContent = isLoading ? text : i18n[getLang()].generateBtn;
}

function renderInterests() {
  const lang = getLang();
  const wrap = document.getElementById("interests");
  wrap.innerHTML = "";
  INTERESTS.forEach((it) => {
    const el = document.createElement("div");
    el.className = "pill";
    el.dataset.key = it.key;
    el.textContent = lang === "ru" ? it.ru : it.en;
    el.addEventListener("click", () => el.classList.toggle("active"));
    wrap.appendChild(el);
  });
}

function render() {
  const lang = getLang();
  const t = i18n[lang];

  document.getElementById("subtitle").textContent = t.subtitle;
  document.getElementById("welcomeTitle").textContent = t.welcomeTitle;
  document.getElementById("welcomeText").textContent = t.welcomeText;

  const ul = document.getElementById("featureList");
  ul.innerHTML = "";
  t.features.forEach((x) => {
    const li = document.createElement("li");
    li.textContent = x;
    ul.appendChild(li);
  });

  document.getElementById("startBtn").textContent = t.startBtn;
  document.getElementById("priceNote").textContent = t.priceNote;

  document.getElementById("btnRu").classList.toggle("active", lang === "ru");
  document.getElementById("btnEn").classList.toggle("active", lang === "en");

  document.getElementById("formTitle").textContent = t.formTitle;
  document.getElementById("backBtn").textContent = t.backBtn;
  document.getElementById("lblDestination").textContent = t.lblDestination;
  document.getElementById("lblDays").textContent = t.lblDays;
  document.getElementById("lblNights").textContent = t.lblNights;
  document.getElementById("lblBudget").textContent = t.lblBudget;
  document.getElementById("optBudgetLow").textContent = t.optBudgetLow;
  document.getElementById("optBudgetMed").textContent = t.optBudgetMed;
  document.getElementById("optBudgetHigh").textContent = t.optBudgetHigh;
  document.getElementById("optBudgetPremium").textContent = t.optBudgetPremium;

  document.getElementById("lblInterests").textContent = t.lblInterests;
  document.getElementById("lblPace").textContent = t.lblPace;
  document.getElementById("optPaceSlow").textContent = t.optPaceSlow;
  document.getElementById("optPaceNormal").textContent = t.optPaceNormal;
  document.getElementById("optPaceFast").textContent = t.optPaceFast;

  document.getElementById("lblCompanions").textContent = t.lblCompanions;
  document.getElementById("optCompSolo").textContent = t.optCompSolo;
  document.getElementById("optCompCouple").textContent = t.optCompCouple;
  document.getElementById("optCompFamily").textContent = t.optCompFamily;
  document.getElementById("optCompGroup").textContent = t.optCompGroup;

  document.getElementById("lblNotes").textContent = t.lblNotes;
  document.getElementById("notes").placeholder = t.notesPh;
  document.getElementById("notesHelper").textContent = t.notesHelper;

  document.getElementById("generateBtn").textContent = t.generateBtn;
  document.getElementById("formHint").textContent = t.formHint;

  document.getElementById("resultTitle").textContent = t.resultTitle;
  document.getElementById("newBtn").textContent = t.newBtn;
  document.getElementById("planTitle").textContent = t.planTitle;
  document.getElementById("tipsTitle").textContent = t.tipsTitle;
  document.getElementById("checklistTitle").textContent = t.checklistTitle;

  renderInterests();

  if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor("#0b1220");
    tg.setBackgroundColor("#0b1220");
  }
}

async function generate() {
  const lang = getLang();
  const t = i18n[lang];

  const destination = document.getElementById("destination").value.trim();
  const daysRaw = document.getElementById("days").value;
  const nightsRaw = document.getElementById("nights").value;
  const budget = document.getElementById("budget").value;
  const pace = document.getElementById("pace").value;
  const companions = document.getElementById("companions").value;
  const notes = document.getElementById("notes").value.trim();

  const days = parseInt(daysRaw, 10);
  const nights = nightsRaw === "" ? null : parseInt(nightsRaw, 10);

  if (!destination || !Number.isFinite(days) || days <= 0) {
    alert(t.errFill);
    return;
  }

  const payload = {
    language: lang,
    destination,
    days,
    nights,
    budget,
    interests: selectedInterests(),
    pace,
    companions,
    notes: notes || null
  };

  try {
    setLoading(true, t.loading);

    const resp = await fetch(`${API_BASE}/route/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    document.getElementById("resultSummary").textContent = data.summary || "";

    const plan = document.getElementById("plan");
    plan.innerHTML = "";
    (data.daily_plan || []).forEach((d) => {
      const card = document.createElement("div");
      card.className = "dayCard";

      const title = document.createElement("div");
      title.className = "dayTitle";
      title.textContent = `Day ${d.day ?? ""}`.trim();

      const m = document.createElement("div");
      m.className = "small";
      m.textContent = `Morning: ${(d.morning || []).join(", ")}`;

      const a = document.createElement("div");
      a.className = "small";
      a.textContent = `Afternoon: ${(d.afternoon || []).join(", ")}`;

      const e = document.createElement("div");
      e.className = "small";
      e.textContent = `Evening: ${(d.evening || []).join(", ")}`;

      card.appendChild(title);
      card.appendChild(m);
      card.appendChild(a);
      card.appendChild(e);
      plan.appendChild(card);
    });

    const tips = document.getElementById("tips");
    tips.innerHTML = "";
    (data.tips || []).forEach((x) => {
      const li = document.createElement("li");
      li.textContent = x;
      tips.appendChild(li);
    });

    const checklist = document.getElementById("checklist");
    checklist.innerHTML = "";
    (data.checklist || []).forEach((x) => {
      const li = document.createElement("li");
      li.textContent = x;
      checklist.appendChild(li);
    });

    showScreen("result");
  } catch (e) {
    console.error(e);
    alert(t.errApi);
  } finally {
    setLoading(false);
  }
}

document.getElementById("btnRu").addEventListener("click", () => setLang("ru"));
document.getElementById("btnEn").addEventListener("click", () => setLang("en"));

document.getElementById("startBtn").addEventListener("click", () => showScreen("form"));
document.getElementById("backBtn").addEventListener("click", () => showScreen("welcome"));
document.getElementById("newBtn").addEventListener("click", () => showScreen("form"));

document.getElementById("generateBtn").addEventListener("click", generate);

render();
