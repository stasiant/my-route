const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    btnMain: "Создать маршрут", btnGen: "Написать гид", loading: "Маршрут строится...",
    err: "Ошибка. Попробуйте еще раз.", saveBtn: "📥 Сохранить в чат"
  },
  en: {
    btnMain: "Create Route", btnGen: "Write Guide", loading: "Building route...",
    err: "Error. Try again.", saveBtn: "📥 Save to Chat"
  }
};
let lang = "ru";
let currentRouteHTML = "";

function show(id) {
  ["screenWelcome", "screenForm", "screenResult"].forEach(s => document.getElementById(s).classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  
  if (id === "screenResult") {
      tg.MainButton.setText(i18n[lang].saveBtn).show();
  } else {
      tg.MainButton.hide();
  }
}

// ПРЕВРАЩАЕМ HTML В КРАСИВЫЙ ТЕКСТ ДЛЯ ЧАТА
function formatForTelegram(html) {
  let text = html;
  
  // Заголовки разделов -> Жирный + отступы
  text = text.replace(/<h2>(.*?)<\/h2>/gi, "\n\n<b>===== $1 =====</b>\n");
  
  // Заголовки дней -> Жирный со смайликом
  text = text.replace(/<h3>(.*?)<\/h3>/gi, "\n\n<b>🗓 $1</b>\n");
  
  // Логистика (курсив) -> оставляем тег <i>
  text = text.replace(/<i>(.*?)<\/i>/gi, "<i>$1</i>");
  
  // Жирный текст -> оставляем тег <b>
  text = text.replace(/<b>(.*?)<\/b>/gi, "<b>$1</b>");
  
  // Обычные абзацы -> просто перенос строки
  text = text.replace(/<p>/gi, "").replace(/<\/p>/gi, "\n");
  
  // Убираем лишние теги, если остались
  text = text.replace(/<br>/gi, "\n");
  
  // Чистим двойные пробелы и переносы
  return text.trim();
}

async function generate() {
  const btn = document.getElementById("btnGen");
  const dest = document.getElementById("destination").value;
  const days = document.getElementById("days").value;
  
  if(!dest || !days) return alert("Заполните город и дни");
  
  btn.disabled = true; btn.textContent = i18n[lang].loading;
  
  try {
    const userNotes = document.getElementById("notes").value;
    const budget = document.getElementById("budget").value;
    const companions = document.getElementById("companions").value;

    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        language: lang, destination: dest, days: parseInt(days),
        budget: budget, pace: "normal", companions: companions, interests: [],
        notes: userNotes
      })
    });
    
    const data = await res.json();
    
    // Получаем HTML от ИИ
    let html = data.html_content || "";
    if (!html && data.daily_plan) {
        // Если вдруг старый формат
        data.daily_plan.forEach(d => html += `<p>${d.day}</p>`);
    }

    currentRouteHTML = html;
    
    // Показываем на экране телефона
    document.getElementById("summary").textContent = data.summary || `Маршрут: ${dest}`;
    document.getElementById("bookBody").innerHTML = html;
    
    show("screenResult");

  } catch(e) {
    console.error(e);
    alert(i18n[lang].err);
  } finally {
    btn.disabled = false; btn.textContent = i18n[lang].btnGen;
  }
}

// ОТПРАВЛЯЕМ НАСТОЯЩИЙ МАРШРУТ
tg.onEvent('mainButtonClicked', function(){
    if (!currentRouteHTML) return;
    const msg = formatForTelegram(currentRouteHTML);
    // Отправляем данные (Telegram сам закроет приложение)
    tg.sendData(msg); 
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
    tg.MainButton.setParams({ text: i18n[lang].saveBtn, color: "#007AFF" });
}
