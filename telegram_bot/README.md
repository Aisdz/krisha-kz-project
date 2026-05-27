# 🏠 Krisha ML Bot

Telegram-бот для оценки стоимости квартир в Казахстане на основе XGBoost-модели, обученной на данных [krisha.kz](https://krisha.kz).

---

## 📌 Возможности

- **Оценить квартиру** — модель называет рыночную стоимость по параметрам
- **Проверить цену** — сравнение цены продавца с оценкой модели
- Поддерживаемые города: Алматы, Астана, Шымкент, Караганда

  <img width="1378" height="1049" alt="Screenshot 2026-05-27 at 15 02 42" src="https://github.com/user-attachments/assets/bd313828-3107-4c19-adac-5dfe33e2c1da" />

  <img width="1378" height="1050" alt="Screenshot 2026-05-27 at 15 03 51" src="https://github.com/user-attachments/assets/ddc3bd22-bc9d-4633-955b-495a7d3388f3" />



---

## 🗂 Структура репозитория

```
krisha-kz-project
  └── telegram_bot/
      ├── main.py        # Логика бота (aiogram)
      ├── .env           # Секреты — НЕ в git (см. .gitignore)
      ├── .gitignore
      └── README.md
```

> Модель (`xgb_model.pkl`, `cat_categories.pkl`, `train_medians.pkl`) и скрипт предсказания (`predict.py`) находятся в папке `ml/` и не включены в git согласно правилам `.gitignore`.

---

## ⚙️ Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/Aisdz/krisha-kz-project.git
cd krisha-kz-project/telegram_bot
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Установить зависимости

```bash
pip install aiogram python-dotenv pandas numpy xgboost joblib
```

### 4. Создать файл `.env`

```bash
cp .env.example .env
```

Заполнить `.env`:

```
BOT_TOKEN=your_telegram_bot_token_here
```

Получить токен можно у [@BotFather](https://t.me/BotFather).

### 5. Положить модель рядом с `main.py`

Скопировать из папки `ml/` в `telegram_bot/`:

```
xgb_model.pkl
cat_categories.pkl
train_medians.pkl
predict.py
```

### 6. Запустить бота

```bash
python3 main.py
```

---

## 🧠 Модель

| Параметр       | Значение         |
|----------------|------------------|
| Алгоритм       | XGBoost          |
| Целевая метка  | log(цена)        |
| R²             | 0.87             |
| Средняя ошибка | ~7М ₸            |
| Данные         | krisha.kz        |

Подробности обучения — в `ml/ml.ipynb`.

---

## 🔒 Безопасность

- Токен бота хранится в `.env` и **не попадает в git**
- Файлы модели (`.pkl`) также исключены из репозитория

---

## 📄 Лицензия

MIT
