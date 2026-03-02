const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

const i18n = {
  ru: {
    btnMain: "Создать маршрут", btnGen: "Написать гид", loading: "Пишу статью...",
    err: "Ошибка. Попробуйте еще раз."
  },
  en: {
    btnMain: "Create Route", btnGen: "Write Guide", loading: "Writing...",
    err: "Error. Try again."
  }
};
let lang = "ru";

function show(id) {
  ["screenWelcome", "screenForm", "screenResult"].forEach(s => document.getElementById(s).classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  window.scrollTo(0,0);
}

async function generate() {
  const btn = document.getElementById("btnGen");
  const dest = document.getElementById("destination").value;
  const days = document.getElementById("days").value;
  
  if(!dest || !days) return alert("Заполните город и дни");
  
  btn.disabled = true; btn.textContent = i18n[lang].loading;

  try {
    const notes = document.getElementById("notes").value;
    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        language: lang, destination: dest, days: parseInt(days),
        budget: "medium", pace: "normal", companions: "couple", interests: [],
        notes: notes
      })
    });
    const data = await res.json();
    
    // Вставляем контент
    let html = data.book_content || data.html_content || "<p>Сервер обновляется...</p>";
    
    // Если вдруг пришел старый формат списком - превращаем в текст
    if(data.daily_plan) {
       html = "";
       data.daily_plan.forEach(d => {
         const items = [...(d.morning||[]), ...(d.afternoon||[]), ...(d.evening||[])];
         if(items.length) items.forEach(it => html += `<p>${it}</p>`);
       });
    }

    document.getElementById("summary").textContent = data.summary || "";
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
