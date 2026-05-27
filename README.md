# 🏠 Krisha.kz — ML Pipeline

> Полный цикл: сбор данных → обучение модели → Telegram-бот

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-red)
![R²](https://img.shields.io/badge/R²-0.872-brightgreen)
![MAE](https://img.shields.io/badge/MAE-6.9M%20₸-yellow)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Проект предсказывает рыночную стоимость квартир в Казахстане. Данные собраны с [krisha.kz](https://krisha.kz), модель доступна через Telegram-бот.

---

## 🗂 Структура

```
krisha-kz-project/
├── scraping/          # Парсинг объявлений с krisha.kz
├── ml/                # Обучение XGBoost-модели
├── telegram_bot/      # Telegram-бот на aiogram
├── LICENSE
└── README.md
```

---

## 🔄 Пайплайн

```
scraping/  ──►  ml/  ──►  telegram_bot/
  сбор        обучение       деплой
  данных       модели         бота
```

### 1. [`scraping/`](./scraping/)
Парсинг ~17 000 уникальных объявлений с krisha.kz, случайная выборка 7 000, сохранение в `krisha_final.csv`.

- Стек: `requests`, `BeautifulSoup`, `pandas`
- Надёжность: auto-retry при бане, checkpoint каждые 500 записей
- Результат: 7 000 объявлений, 26 признаков

### 2. [`ml/`](./ml/)
EDA, feature engineering, обучение и сравнение моделей. Финальная модель сохраняется в `.pkl`.

- Стек: `xgboost`, `scikit-learn`, `pandas`, `numpy`
- Финальный результат: **R² 0.872 / MAE 6.9М ₸**

| Модель | MAE | R² |
|---|---|---|
| Random Forest (baseline) | 8 656 302 ₸ | 0.799 |
| XGBoost базовый | 7 954 046 ₸ | 0.842 |
| XGBoost + log transform | 7 050 796 ₸ | 0.872 |
| **XGBoost финальный** | **6 911 874 ₸** | **0.872** |

### 3. [`telegram_bot/`](./telegram_bot/)
Telegram-бот принимает параметры квартиры через inline-кнопки и возвращает оценку модели.

- Стек: `aiogram`, `python-dotenv`
- Режимы: **Оценить квартиру** и **Проверить цену продавца**
- Города: Алматы, Астана, Шымкент, Караганда

---

## 🚀 Быстрый старт

Подробные инструкции по установке — в README каждой папки. Общая последовательность:

```bash
git clone https://github.com/Aisdz/krisha-kz-project.git
cd krisha-kz-project
```

1. Запустить `scraping/krisha_scraping.ipynb` → получить `krisha_final.csv`
2. Запустить `ml/krisha_ml.ipynb` → получить `.pkl` файлы модели
3. Скопировать `.pkl` и `predict.py` в `telegram_bot/`, настроить `.env`, запустить `main.py`

---

## 📄 Лицензия

MIT — подробнее в [LICENSE](./LICENSE)
