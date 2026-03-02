const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

function showScreen(screenId) {
  document.getElementById('screenForm').classList.add('hidden');
  document.getElementById('screenResult').classList.add('hidden');
  document.getElementById(screenId).classList.remove('hidden');
  window.scrollTo(0, 0);
}

// Форматирование текста, если ИИ вернул старый формат (списком)
function formatParagraph(text) {
  let clean = text.replace(/^(Утро|День|Вечер|Morning|Afternoon|Evening)[:.-]?\s*/i, '');
  if (clean.includes('**') || clean.includes('*')) {
    clean = clean.replace(/\*{1,2}(.*?)\*{1,2}/g, '<b>$1</b>');
  } else {
    const parts = clean.split('. ');
    if (parts.length > 1 && parts[0].length < 100) {
      clean = `<b>${parts[0]}.</b> ` + parts.slice(1).join('. ');
    }
  }
  return clean;
}

// Построение статьи
function buildArticle(data) {
  let html = '';
  if (data.daily_plan && Array.isArray(data.daily_plan)) {
    data.daily_plan.forEach(day => {
      html += `<div class="day-block">`;
      html += `<h2 class="day-header">День ${day.day}</h2>`;
      
      // 1. ПРОВЕРЯЕМ НОВЫЙ ФОРМАТ (HTML content)
      if (day.content && typeof day.content === 'string') {
        html += `<div class="day-content">${day.content}</div>`;
      } 
      // 2. ПРОВЕРЯЕМ СТАРЫЙ ФОРМАТ (Массивы morning, afternoon)
      else {
        const activities = [];
        if (day.morning) activities.push(...day.morning);
        if (day.afternoon) activities.push(...day.afternoon);
        if (day.evening) activities.push(...day.evening);

        if (activities.length > 0) {
          html += `<ul class="article-list">`;
          activities.forEach(act => {
            html += `<li>${formatParagraph(act)}</li>`;
          });
          html += `</ul>`;
        } else {
           html += `<p>План на день формируется...</p>`;
        }
      }
      
      html += `</div>`;
    });
  }
  return html;
}

async function generate() {
  const btn = document.getElementById("generateBtn");
  const dest = document.getElementById("destination").value.trim();
  const days = parseInt(document.getElementById("days").value);
  
  if (!dest || !days) { alert("Заполните поля"); return; }
  
  btn.disabled = true;
  btn.textContent = "Пишу статью (30 сек)...";
  
  try {
    const userNotes = document.getElementById("notes").value;
    
    // Агрессивный промпт для лонгрида
    const hackPrompt = `
      (ВНИМАНИЕ СИСТЕМЕ: ПИШИ ОЧЕНЬ ПОДРОБНО! Минимум 100 слов на каждое место.
      ОБЯЗАТЕЛЬНО указывай: Цены, Часы работы, Как добраться.
      Если возвращаешь списки (morning/afternoon), делай каждую строку ОГРОМНОЙ по длине, в формате: **Название**. Длинный текст описания с ценами.)
    `;

    const payload = {
      language: "ru",
      destination: dest,
      days: days,
      budget: document.getElementById("budget").value,
      pace: document.getElementById("pace").value,
      companions: document.getElementById("companions").value,
      interests: [],
      notes: userNotes + hackPrompt
    };
    
    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error("API Error");
    const data = await res.json();
    
    document.getElementById("articleTitle").textContent = `Путеводитель: ${dest}`;
    document.getElementById("articleSummary").textContent = data.summary || "Ваш подробный маршрут.";
    document.getElementById("guideContent").innerHTML = buildArticle(data);
    
    showScreen("screenResult");
  } catch (e) {
    console.error(e);
    alert("Ошибка. Попробуйте снова.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Сгенерировать путеводитель";
  }
}

document.getElementById("generateBtn").onclick = generate;
document.getElementById("backBtn").onclick = () => showScreen("screenForm");
if (tg) { tg.ready(); tg.expand(); }
