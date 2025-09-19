const express = require('express');
const bodyParser = require('body-parser');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(bodyParser.json());
app.use(express.static('public')); // тут ваша папка з index.html

// Глобальна змінна для блокування
let currentTest = null; // { fullName, startTime }

// Перевірка стану тесту
app.get('/status', (req, res) => {
  if (currentTest) {
    const elapsed = Date.now() - currentTest.startTime;
    const remaining = 10 * 60 * 1000 - elapsed;
    if (remaining > 0) {
      return res.json({
        active: true,
        fullName: currentTest.fullName,
        remaining
      });
    } else {
      // Час минув — знімаємо блокування
      currentTest = null;
    }
  }
  res.json({ active: false });
});

// Початок тесту
app.post('/start', (req, res) => {
  const { fullName } = req.body;
  if (!fullName) return res.status(400).json({ error: 'Потрібне ПІБ' });

  if (currentTest) {
    const elapsed = Date.now() - currentTest.startTime;
    const remaining = 10 * 60 * 1000 - elapsed;
    if (remaining > 0) {
      return res.status(403).json({
        error: `Зараз тест проходить ${currentTest.fullName}`,
        remaining
      });
    } else {
      currentTest = null;
    }
  }

  currentTest = { fullName, startTime: Date.now() };
  res.json({ message: 'Тест розпочато', startTime: currentTest.startTime });
});

// Завершення тесту
app.post('/finish', (req, res) => {
  const { fullName } = req.body;
  if (currentTest && currentTest.fullName === fullName) {
    currentTest = null;
    return res.json({ message: 'Тест завершено' });
  }
  res.json({ message: 'Не було активного тесту або інша особа' });
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
