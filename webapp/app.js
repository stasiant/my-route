const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

function showScreen(screenId) {
  document.getElementById('screenForm').classList.add('hidden');
  document.getElementById('screenResult').classList.add('hidden');
  document.getElementById(screenId).classList.remove('hidden');
  window.scrollTo(0, 0);
}

// Теперь мы просто рендерим готовый HTML от сервера
function buildArticle(data) {
  let html = '';
  if (data.daily_plan && Array.isArray(data.daily_plan)) {
    data.daily_plan.forEach(day => {
      // Заголовок дня
      html += `<div class="day-block">`;
      html += `<h2 class="day-header">День ${day.day}</h2>`;
      
      // Вставляем контент, который прислал ИИ (это уже готовый HTML с <p> и <h3>)
      html += `<div class="day-content">${day.content}</div>`;
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
    
    // Дублируем инструкцию для надежности
    const prompt = " (IMPORTANT: Write a long, detailed article with HTML tags <h3> for titles and <p> for text. Include prices and opening hours.)";

    const payload = {
      language: "ru",
      destination: dest,
      days: days,
      budget: document.getElementById("budget").value,
      pace: document.getElementById("pace").value,
      companions: document.getElementById("companions").value,
      interests: [],
      notes: userNotes + prompt
    };
    
    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error("API Error");
    const data = await res.json();
    
    document.getElementById("articleTitle").textContent = `Путеводитель: ${dest}`;
    document.getElementById("articleSummary").textContent = data.summary;
    document.getElementById("guideContent").innerHTML = buildArticle(data);
    
    showScreen("screenResult");
  } catch (e) {
    console.error(e);
    alert("Ошибка. Попробуйте снова.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Сгенерировать";
  }
}

document.getElementById("generateBtn").onclick = generate;
document.getElementById("backBtn").onclick = () => showScreen("screenForm");
if (tg) { tg.ready(); tg.expand(); }
