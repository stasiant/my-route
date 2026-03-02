const tg = window.Telegram?.WebApp;
const API_BASE = "https://my-route-api.onrender.com";

function showScreen(screenId) {
  document.getElementById('screenForm').classList.add('hidden');
  document.getElementById('screenResult').classList.add('hidden');
  document.getElementById(screenId).classList.remove('hidden');
  window.scrollTo(0, 0);
}

// Умное форматирование текста
function formatParagraph(text) {
  let clean = text.replace(/^(Утро|День|Вечер|Morning|Afternoon|Evening)[:.-]?\s*/i, '');
  
  if (clean.includes('**') || clean.includes('*')) {
    clean = clean.replace(/\*{1,2}(.*?)\*{1,2}/g, '<b>$1</b>');
  } else {
    const parts = clean.split('. ');
    if (parts.length > 1 && parts[0].length < 70) {
      clean = `<b>${parts[0]}.</b> ` + parts.slice(1).join('. ');
    }
  }
  return clean;
}

// Генерация HTML статьи
function buildArticle(data) {
  let html = '';
  if (data.daily_plan && Array.isArray(data.daily_plan)) {
    data.daily_plan.forEach(day => {
      html += `<h2 class="day-title">День ${day.day}</h2>`;
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
      }
    });
  }
  return html;
}

async function generate() {
  const btn = document.getElementById("generateBtn");
  const dest = document.getElementById("destination").value.trim();
  const days = parseInt(document.getElementById("days").value);
  
  if (!dest || !days) {
    alert("Пожалуйста, укажите город и количество дней.");
    return;
  }
  
  btn.disabled = true;
  btn.textContent = "Пишу огромный лонгрид (≈30 сек)...";
  
  try {
    const userNotes = document.getElementById("notes").value;
    
    // === СУПЕР-ЖЕСТКИЙ ПРОМПТ ДЛЯ ИИ ===
    // Эта скрытая инструкция заставит ИИ писать как книгу.
    const hackPrompt = `
      [ВНИМАНИЕ, СИСТЕМНОЕ ПРАВИЛО: ПИШИ ОГРОМНЫЙ ТЕКСТ. 
      ЗАПРЕЩЕНО отвечать короткими предложениями. Это должен быть детализированный лонгрид. 
      Для КАЖДОГО места ты ОБЯЗАН написать минимум 80-150 слов сплошным текстом. 
      Для КАЖДОЙ локации обязательно укажи:
      1. Глубокую историю и описание места.
      2. Точные или примерные цены (на билеты, экскурсии, средний чек в кафе).
      3. Часы работы (когда открыты кассы, во сколько лучше приходить).
      4. Логистику: как добраться от предыдущей точки (какое метро, сколько минут идти пешком).
      5. Секретные советы.
      Формат: **Название места**. И далее длинный, подробный, увлекательный рассказ. Не сокращай!]
    `;

    const payload = {
      language: "ru",
      destination: dest,
      days: days,
      budget: document.getElementById("budget").value,
      pace: document.getElementById("pace").value,
      companions: document.getElementById("companions").value,
      interests: [],
      notes: userNotes + hackPrompt // Подмешиваем нашу инструкцию
    };
    
    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error("API Error");
    const data = await res.json();
    
    document.getElementById("articleTitle").textContent = `Маршрут: ${dest} на ${days} дн.`;
    document.getElementById("articleSummary").textContent = data.summary || "Подробный путеводитель с ценами, графиком работы и логистикой.";
    document.getElementById("guideContent").innerHTML = buildArticle(data);
    
    showScreen("screenResult");
  } catch (e) {
    console.error(e);
    alert("Произошла ошибка при генерации. Попробуйте еще раз.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Сгенерировать путеводитель";
  }
}

document.getElementById("generateBtn").onclick = generate;
document.getElementById("backBtn").onclick = () => showScreen("screenForm");

if (tg) { tg.ready(); tg.expand(); }
