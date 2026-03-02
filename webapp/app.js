const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    btnMain: "Создать маршрут", btnGen: "Написать гид", loading: "Анализирую параметры...",
    err: "Ошибка. Попробуйте еще раз."
  },
  en: {
    btnMain: "Create Route", btnGen: "Write Guide", loading: "Analyzing...",
    err: "Error. Try again."
  }
};
let lang = "ru";

function show(id) {
  ["screenWelcome", "screenForm", "screenResult"].forEach(s => document.getElementById(s).classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  window.scrollTo(0,0);
}

// Умный парсер для текста
function formatText(text) {
  let clean = text.replace(/^(Утро|День|Вечер|Morning|Afternoon|Evening)[:.-]?\s*/i, '');
  if (clean.includes('**')) {
    return clean.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
  } else {
    const parts = clean.split('. ');
    if (parts.length > 1 && parts[0].length < 100) {
      return `<b>${parts[0]}.</b> ` + parts.slice(1).join('. ');
    }
  }
  return clean;
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

    // Формируем промпт для ИИ, чтобы он учитывал новые параметры
    // Мы добавляем их прямо в текст, чтобы ИИ точно обратил внимание.
    const contextPrompt = `
    [CONTEXT: 
    Budget Level: ${budget} (Adjust recommendations accordingly. If premium - luxury places. If economy - cheap/free places).
    Travel Group: ${companions} (If family - kid friendly. If couple - romantic. If solo - safe/social).
    User Wishes: ${userNotes}]
    
    [SYSTEM RULE: WRITE A LONG TRAVEL STORY (HTML). NO LISTS.]
    `;

    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        language: lang, destination: dest, days: parseInt(days),
        budget: budget, pace: "normal", companions: companions, interests: [],
        notes: contextPrompt // Отправляем всё вместе
      })
    });
    
    const data = await res.json();
    
    let html = "";
    if (data.book_content || data.html_content) {
        html = data.book_content || data.html_content;
    } else if (data.daily_plan) {
       data.daily_plan.forEach(d => {
         html += `<h3>День ${d.day}</h3>`;
         const items = [...(d.morning||[]), ...(d.afternoon||[]), ...(d.evening||[])];
         if(items.length) {
             items.forEach(it => {
                 html += `<p>${formatText(it)}</p>`;
             });
         }
       });
    }

    document.getElementById("summary").textContent = data.summary || "Маршрут готов.";
    document.getElementById("bookBody").innerHTML = html;
    
    show("screenResult");

  } catch(e) {
    console.error(e);
    alert(i18n[lang].err);
  } finally {
    btn.disabled = false; btn.textContent = i18n[lang].btnGen;
  }
}

document.getElementById("btnStart").onclick = () => show("screenForm");
document.getElementById("backBtn").onclick = () => show("screenWelcome");
document.getElementById("newBtn").onclick = () => show("screenForm");
document.getElementById("btnGen").onclick = generate;
document.getElementById("langToggle").onclick = (e) => {
    lang = lang === "ru" ? "en" : "ru";
    e.target.textContent = lang.toUpperCase();
};

if(tg) { tg.ready(); tg.expand(); }
