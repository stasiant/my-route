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
  // 1. Убираем слова Утро, День, Вечер
  let clean = text.replace(/^(Утро|День|Вечер|Morning|Afternoon|Evening)[:.-]?\s*/i, '');
  
  // 2. Если ИИ прислал текст со звездочками (Markdown)
  if (clean.includes('**') || clean.includes('*')) {
    clean = clean.replace(/\*{1,2}(.*?)\*{1,2}/g, '<b>$1</b>');
  } 
  // 3. Если ИИ прислал просто текст, мы искусственно делаем первое предложение жирным (как название места)
  else {
    const parts = clean.split('. ');
    if (parts.length > 1 && parts[0].length < 70) {
      clean = `<b>${parts[0]}.</b> ` + parts.slice(1).join('. ');
    } else if (parts.length === 1) {
      // Если предложение всего одно, выделяем первые несколько слов
      const words = clean.split(' ');
      if (words.length > 3) {
        clean = `<b>${words.slice(0, 3).join(' ')}</b> ${words.slice(3).join(' ')}`;
      }
    }
  }
  return clean;
}

// Генерация HTML статьи
function buildArticle(data) {
  let html = '';
  
  if (data.daily_plan && Array.isArray(data.daily_plan)) {
    data.daily_plan.forEach(day => {
      // Заголовок дня
      html += `<h2 class="day-title">День ${day.day}</h2>`;
      
      // Собираем все активности дня в один массив
      const activities = [];
      if (day.morning) activities.push(...day.morning);
      if (day.afternoon) activities.push(...day.afternoon);
      if (day.evening) activities.push(...day.evening);

      // Рисуем список
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
  btn.textContent = "Составляю путеводитель (≈20 сек)...";
  
  try {
    const userNotes = document.getElementById("notes").value;
    // Жесткий промпт
    const promptInjection = " (ПРАВИЛО: Напиши ОЧЕНЬ ПОДРОБНО. Для каждой точки маршрута пиши минимум 3-4 предложения с историей и деталями. Обязательно выделяй название каждого места двойными звездочками **Вот так**. Не пиши списком дел, пиши как увлекательную статью в журнал.)";

    const payload = {
      language: "ru",
      destination: dest,
      days: days,
      budget: document.getElementById("budget").value,
      pace: document.getElementById("pace").value,
      companions: document.getElementById("companions").value,
      interests: [],
      notes: userNotes + promptInjection
    };
    
    const res = await fetch(`${API_BASE}/route/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error("API Error");
    const data = await res.json();
    
    // Заполняем интерфейс
    document.getElementById("articleTitle").textContent = `Маршрут: ${dest} на ${days} дн.`;
    document.getElementById("articleSummary").textContent = data.summary || "Я составил для вас насыщенный маршрут, который охватывает главные достопримечательности. Вы можете менять дни местами.";
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
