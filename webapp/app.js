const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

let lang = "ru";
let currentRouteHTML = "";

const i18n = {
  ru: { btnGen: "Создать маршрут", loading: "Маршрут строится...", saveBtn: "📥 Сохранить в чат" }
};

function show(id) {
  ["screenWelcome", "screenForm", "screenResult"].forEach(s => document.getElementById(s).classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  
  if (id === "screenResult") {
      tg.MainButton.setText(i18n[lang].saveBtn).show();
  } else {
      tg.MainButton.hide();
  }
}

// Упрощенная функция: просто чистит теги
function formatForTelegram(html) {
    // Убираем вообще все теги для надежности теста
    let temp = document.createElement("div");
    temp.innerHTML = html;
    return temp.textContent || temp.innerText || "";
}

async function generate() {
  const btn = document.getElementById("btnGen");
  const dest = document.getElementById("destination").value;
  const days = document.getElementById("days").value;
  
  btn.disabled = true; btn.textContent = i18n[lang].loading;
  
  try {
    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        language: lang, destination: dest, days: parseInt(days),
        budget: "medium", pace: "normal", companions: "couple", notes: "Test"
      })
    });
    
    const data = await res.json();
    let html = data.html_content || "<h2>Маршрут готов</h2><p>Тестовый маршрут.</p>";
    
    currentRouteHTML = html; // Сохраняем оригинал
    document.getElementById("bookBody").innerHTML = html;
    show("screenResult");

  } catch(e) {
    alert("Ошибка");
  } finally {
    btn.disabled = false; btn.textContent = i18n[lang].btnGen;
  }
}

// ГЛАВНОЕ: КНОПКА ОТПРАВКИ
tg.onEvent('mainButtonClicked', function(){
    // ТЕСТ: Отправляем короткое сообщение, чтобы проверить связь
    // Если это сработает, значит бот жив, а проблема была в длине текста
    tg.sendData("ТЕСТОВАЯ ОТПРАВКА: Маршрут успешно создан!"); 
});

document.getElementById("btnStart").onclick = () => show("screenForm");
document.getElementById("backBtn").onclick = () => show("screenWelcome");
document.getElementById("newBtn").onclick = () => show("screenForm");
document.getElementById("btnGen").onclick = generate;

if(tg) { 
    tg.ready(); 
    tg.expand();
    tg.MainButton.setParams({ text: "Сохранить", color: "#007AFF" });
}
