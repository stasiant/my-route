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
  
  if (tg && id === "screenResult") {
      tg.MainButton.setText(i18n[lang].saveBtn).show();
  } else if (tg) {
      tg.MainButton.hide();
  }
}

function formatForTelegram(html) {
  let text = html;
  text = text.replace(/<h2>(.*?)<\/h2>/gi, "\n\n<b>===== $1 =====</b>\n");
  text = text.replace(/<h3>(.*?)<\/h3>/gi, "\n\n<b>🗓 $1</b>\n");
  text = text.replace(/<b>(.*?)<\/b>/gi, "<b>$1</b>");
  text = text.replace(/<i>(.*?)<\/i>/gi, "<i>$1</i>");
  text = text.replace(/<p>/gi, "").replace(/<\/p>/gi, "\n");
  text = text.replace(/<br>/gi, "\n");
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
    let html = data.html_content || "";
    
    currentRouteHTML = `<b>Маршрут: ${dest} (${days} дн.)</b>\n` + html;
    
    document.getElementById("summary").textContent = data.summary || `Ваш маршрут по ${dest}`;
    document.getElementById("bookBody").innerHTML = html;
    show("screenResult");

  } catch(e) {
    console.error(e);
    alert(i18n[lang].err);
  } finally {
    btn.disabled = false; btn.textContent = i18n[lang].btnGen;
  }
}

// СНАЧАЛА НАЗНАЧАЕМ КНОПКИ (чтобы работали везде)
document.getElementById("btnStart").onclick = () => show("screenForm");
document.getElementById("backBtn").onclick = () => show("screenWelcome");
document.getElementById("newBtn").onclick = () => show("screenForm");
document.getElementById("btnGen").onclick = generate;
document.getElementById("langToggle").onclick = (e) => {
    lang = lang === "ru" ? "en" : "ru";
    e.target.textContent = lang.toUpperCase();
};

// ПОТОМ БЕЗОПАСНО ДОБАВЛЯЕМ ФУНКЦИИ ТЕЛЕГРАМА (только если они есть)
if(tg) { 
    tg.onEvent('mainButtonClicked', function(){
        if (!currentRouteHTML) {
            tg.sendData("Ошибка: пустой маршрут"); 
            return;
        }
        const msg = formatForTelegram(currentRouteHTML);
        tg.sendData(msg); 
    });

    tg.ready(); 
    tg.expand();
    tg.MainButton.setParams({ text: i18n[lang].saveBtn, color: "#007AFF" });
}
