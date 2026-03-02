const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    generateBtn: "Написать историю", resultTitle: "Ваша история", loading: "Пишу книгу (30 сек)...", 
    errFill: "Заполните поля.", errOldServer: "Сервер обновляется, подождите 2 минуты и попробуйте снова."
  },
  en: {
    generateBtn: "Write Story", resultTitle: "Your Story", loading: "Writing book...", 
    errFill: "Fill fields.", errOldServer: "Server is updating, wait 2 mins and try again."
  }
};

let currentLang = localStorage.getItem("lang") || "ru";

function render() {
  const t = i18n[currentLang];
  document.getElementById("btnRu").className = `chip ${currentLang === 'ru' ? 'active' : ''}`;
  document.getElementById("btnEn").className = `chip ${currentLang === 'en' ? 'active' : ''}`;
  // Простая локализация кнопок
  document.getElementById("generateBtn").textContent = t.generateBtn;
  document.getElementById("resultTitle").textContent = t.resultTitle;
}

function showScreen(id) {
  ["screenWelcome", "screenForm", "screenResult"].forEach(s => document.getElementById(s).classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
}

async function generate() {
  const btn = document.getElementById("generateBtn");
  const dest = document.getElementById("destination").value.trim();
  const days = parseInt(document.getElementById("days").value);
  if (!dest || !days) return alert(i18n[currentLang].errFill);
  
  btn.disabled = true; btn.textContent = i18n[currentLang].loading;
  
  try {
    const notes = document.getElementById("notes").value;
    // Взлом промпта на случай, если сервер тупит
    const hack = " (SYSTEM: OUTPUT ONLY HTML in 'travel_book_chapter'. NO LISTS. USE <p> TAGS FOR LONG TEXT.)";

    const payload = {
      language: currentLang, destination: dest, days: days,
      budget: document.getElementById("budget").value, pace: "normal", companions: "couple", interests: [],
      notes: notes + hack
    };
    
    const res = await fetch(`${API_BASE}/route/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const data = await res.json();
    
    document.getElementById("resultSummary").textContent = data.summary || "";
    
    // === ПРОВЕРКА ОБНОВЛЕНИЯ ===
    if (data.travel_book_chapter) {
        // УРА! ЭТО НОВЫЙ ФОРМАТ
        document.getElementById("guide").innerHTML = `<div class="story-content">${data.travel_book_chapter}</div>`;
        showScreen("screenResult");
    } else {
        // ПРИШЕЛ СТАРЫЙ ФОРМАТ -> СЕРВЕР НЕ ОБНОВИЛСЯ
        console.log("Old format received:", data);
        alert(i18n[currentLang].errOldServer);
    }

  } catch (e) {
    console.error(e);
    alert("Ошибка соединения.");
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
