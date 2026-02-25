const tg = window.Telegram?.WebApp;

const i18n = {
  ru: {
    subtitle: "Планировщик путешествий (Mini App)",
    welcomeTitle: "Привет! Я My Route",
    welcomeText:
      "Опиши куда хочешь поехать, на сколько дней, бюджет и интересы — я соберу маршрут по дням, дам советы и ссылки на карты.",
    features: [
      "Маршрут по дням: утро / день / вечер",
      "Советы и лайфхаки (транспорт, безопасность, как не переплачивать)",
      "Чек‑лист перед поездкой",
      "Интерактивная карта (добавим дальше)"
    ],
    startBtn: "Создать маршрут",
    priceNote: "1 маршрут = 50⭐ (оплата Stars будет на следующем шаге)."
  },
  en: {
    subtitle: "Travel Planner (Mini App)",
    welcomeTitle: "Hi! I'm My Route",
    welcomeText:
      "Tell me where you want to go, for how many days, your budget and interests — I’ll build a day-by-day itinerary with tips and map links.",
    features: [
      "Day-by-day plan: morning / afternoon / evening",
      "Tips & hacks (transport, safety, avoid overpaying)",
      "Pre-trip checklist",
      "Interactive map (next step)"
    ],
    startBtn: "Create itinerary",
    priceNote: "1 itinerary = 50⭐ (Stars payment will be added next)."
  }
};

function getLang() {
  return localStorage.getItem("lang") || "ru";
}

function setLang(lang) {
  localStorage.setItem("lang", lang);
  render();
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

  if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor("#0b1220");
    tg.setBackgroundColor("#0b1220");
  }
}

document.getElementById("btnRu").addEventListener("click", () => setLang("ru"));
document.getElementById("btnEn").addEventListener("click", () => setLang("en"));

document.getElementById("startBtn").addEventListener("click", () => {
  // На следующем шаге сделаем экран формы. Пока просто покажем alert.
  const lang = getLang();
  if (lang === "ru") alert("Дальше будет форма запроса маршрута.");
  else alert("Next step: request form.");
});

render();
