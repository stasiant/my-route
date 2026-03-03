const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    btnMain: "Создать маршрут", btnGen: "Написать гид", loading: "Собираю маршрут...",
    err: "Ошибка. Попробуйте еще раз."
  },
  en: {
    btnMain: "Create Route", btnGen: "Write Guide", loading: "Building route...",
    err: "Error. Try again."
  }
};
let lang = "ru";

function show(id) {
  ["screenWelcome", "screenForm", "screenResult"].forEach(s => document.getElementById(s).classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  window.scrollTo(0,0);
}

// Выделяем жирным первое предложение (название места)
function highlightPlace(text) {
  let clean = text.replace(/^(Утро|День|Вечер|Morning|Afternoon|Evening)[:.-]?\s*/i, '');
  if (clean.includes('**')) {
    return clean.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
  } else {
    const parts = clean.split('. ');
    if (parts.length > 1 && parts[0].length < 150) {
      return `<b>${parts[0]}.</b> ${parts.slice(1).join('. ')}`;
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

    const contextPrompt = `
    [КРИТИЧЕСКИ ВАЖНО: ПИШИ ПОДРОБНО!]
    Бюджет: ${budget}. Компания: ${companions}.
    Для каждого места в daily_plan пиши ОГРОМНЫЙ абзац (что посмотреть, цены, как добраться). 
    В конце обязательно заполни поле "tips" подробными советами по транспорту и жилью.
    Пожелания пользователя: ${userNotes}`;

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
    
    // 1. Вступление
    if(data.summary) {
        document.getElementById("summary").textContent = data.summary;
    } else {
        document.getElementById("summary").textContent = `Маршрут по ${dest} на ${days} дней.`;
    }

    // 2. Основной маршрут
    if (data.html_content) {
        // Если сервер всё-таки обновился
        html = data.html_content;
    } else if (data.daily_plan) {
       // Если работает старый сервер
       html += `<h2>Маршрут по дням</h2>`;
       
       data.daily_plan.forEach(d => {
         html += `<h3>День ${d.day}</h3>`;
         const items = [...(d.morning||[]), ...(d.afternoon||[]), ...(d.evening||[])];
         if(items.length) {
             items.forEach(it => {
                 html += `<p>${highlightPlace(it)}</p>`;
             });
         }
       });

       // 3. Полезные советы (берем из старого JSON)
       if(data.tips && data.tips.length > 0) {
           html += `<h2>Полезные советы для поездки</h2>`;
           data.tips.forEach(tip => {
               html += `<p>${highlightPlace(tip)}</p>`;
           });
       }
       if(data.budget_notes) {
           html += `<p><b>Бюджет:</b> ${data.budget_notes}</p>`;
       }
    }

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
