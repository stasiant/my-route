const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    btnMain: "Создать маршрут", btnGen: "Написать гид", loading: "Собираю маршрут...",
    err: "Ошибка. Попробуйте еще раз.", saveBtn: "📥 Сохранить в чат"
  },
  en: {
    btnMain: "Create Route", btnGen: "Write Guide", loading: "Building route...",
    err: "Error. Try again.", saveBtn: "📥 Save to Chat"
  }
};
let lang = "ru";

// Переменная для хранения готового текста
let currentRouteHTML = "";

function show(id) {
  ["screenWelcome", "screenForm", "screenResult"].forEach(s => document.getElementById(s).classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  window.scrollTo(0,0);
  
  // Показываем MainButton только на экране результата
  if (id === "screenResult") {
      tg.MainButton.setText(i18n[lang].saveBtn).show();
  } else {
      tg.MainButton.hide();
  }
}

// Превращаем HTML сайта в текст для Telegram сообщения
function formatForTelegram(html) {
  let text = html;
  
  // Заголовки H2 (Разделы) -> Жирный текст + отступы
  text = text.replace(/<h2>(.*?)<\/h2>/gi, "\n\n<b>===== $1 =====</b>\n");
  
  // Заголовки H3 (Дни) -> Жирный текст
  text = text.replace(/<h3>(.*?)<\/h3>/gi, "\n\n<b>🗓 $1</b>\n");
  
  // Абзацы P -> Просто переносы строк
  text = text.replace(/<p>/gi, "").replace(/<\/p>/gi, "\n");
  
  // Логистика (курсив) -> оставляем как есть, Telegram понимает <i>
  // Жирный <b> -> оставляем как есть
  
  // Убираем лишние пробелы и двойные переносы
  text = text.replace(/<br>/gi, "\n");
  text = text.replace(/\n\s*\n/g, "\n\n");
  
  return text.trim();
}

async function generate() {
  const btn = document.getElementById("btnGen");
  const dest = document.getElementById("destination").value;
  const days = document.getElementById("days").value;
  
  if(!dest || !days) return alert("Заполните город и дни");
  
  btn.disabled = true; btn.textContent = i18n[lang].loading;
  tg.MainButton.hide(); // Скрываем кнопку пока грузится

  try {
    const userNotes = document.getElementById("notes").value;
    const budget = document.getElementById("budget").value;
    const companions = document.getElementById("companions").value;

    const contextPrompt = `
    Бюджет: ${budget}. Компания: ${companions}.
    User wishes: ${userNotes}`;

    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        language: lang, destination: dest, days: parseInt(days),
        budget: budget, pace: "normal", companions: companions, interests: [],
        notes: contextPrompt
      })
    });
    
    const data = await res.json();
    let html = "";
    let summary = data.summary || `Маршрут по ${dest}`;

    // СБОРКА HTML
    if (data.html_content) {
        html = data.html_content;
    } else if (data.daily_plan) {
       // Fallback для старого формата
       html += `<h2>Маршрут</h2>`;
       data.daily_plan.forEach(d => {
         html += `<h3>День ${d.day}</h3>`;
         const items = [...(d.morning||[]), ...(d.afternoon||[]), ...(d.evening||[])];
         items.forEach(it => html += `<p>${it}</p>`);
       });
    }

    // Сохраняем для отправки
    currentRouteHTML = `<b>${summary}</b>\n${html}`;
    
    // Вывод на экран
    document.getElementById("summary").textContent = summary;
    document.getElementById("bookBody").innerHTML = html;
    
    show("screenResult");

  } catch(e) {
    console.error(e);
    alert(i18n[lang].err);
  } finally {
    btn.disabled = false; btn.textContent = i18n[lang].btnGen;
  }
}

// ОБРАБОТЧИК НАЖАТИЯ НА СИНЮЮ КНОПКУ TELEGRAM
tg.onEvent('mainButtonClicked', function(){
    if (!currentRouteHTML) return;
    
    // Подготовка текста
    const telegramMessage = formatForTelegram(currentRouteHTML);
    
    // Отправка данных боту. Бот получит это как "web_app_data"
    tg.sendData(telegramMessage); 
});

document.getElementById("btnStart").onclick = () => show("screenForm");
document.getElementById("backBtn").onclick = () => show("screenWelcome");
document.getElementById("newBtn").onclick = () => show("screenForm");
document.getElementById("btnGen").onclick = generate;
document.getElementById("langToggle").onclick = (e) => {
    lang = lang === "ru" ? "en" : "ru";
    e.target.textContent = lang.toUpperCase();
};

if(tg) { 
    tg.ready(); 
    tg.expand(); 
    // Настраиваем цвета кнопки под тему
    tg.MainButton.setParams({
        text: i18n[lang].saveBtn,
        color: "#007AFF", // Apple Blue
        text_color: "#FFFFFF"
    });
}
