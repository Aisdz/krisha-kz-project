# 🏠 Krisha.kz — Предсказание цены квартиры
> 🇰🇿 ~7 000 объявлений · 📐 18 признаков · 🎯 R² 0.872

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-red?logo=xgboost)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-orange?logo=scikit-learn&logoColor=white)
![R²](https://img.shields.io/badge/R²-0.872-brightgreen)
![MAE](https://img.shields.io/badge/MAE-6.9M%20₸-yellow)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![GitHub stars](https://img.shields.io/github/stars/Aisdz/krisha-kz-project?style=social)

Модель предсказывает цену квартиры по её характеристикам на основе объявлений с krisha.kz.

**Данные:** ~7 000 объявлений о продаже квартир по Казахстану  
**Финальная модель:** XGBoost + log transform  
**Test R²: 0.872 | MAE: 6 911 874 ₸ | CV R² (5-fold): 0.900 ± 0.005**

---

## 📊 Результаты моделей

| Модель | MAE (тенге) | R² |
|---|---|---|
| Random Forest (baseline) | 8 656 302 | 0.799 |
| XGBoost базовый | 7 954 046 | 0.842 |
| XGBoost tuned | 7 527 912 | 0.861 |
| XGBoost + log transform | 7 050 796 | 0.872 |
| **XGBoost финальный** | **6 911 874** | **0.872** |

CV R² по фолдам: `[0.896, 0.909, 0.895, 0.898, 0.901]`

---

## 🔍 Важность признаков

Топ-3 фичи объясняют ~59% важности модели:

1. **`площадь`** - 29.6%
2. **`flat.toilet`** — 15.3%
3. **`район`** — 13.8%
   
<img width="1193" height="646" alt="Screenshot 2026-05-18 at 14 35 05" src="https://github.com/user-attachments/assets/e844587f-7758-414f-83b3-4d61bafcc307" />


---

## 📁 Структура репозитория

```
ml
├── krisha_ml.ipynb      # EDA → feature engineering → обучение → сохранение
├── predict.py              # инференс на сырых данных
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md

```

> `xgb_model.pkl`, `cat_categories.pkl`, `train_medians.pkl` — в `.gitignore`, в репо не входят.

---

## Установка

```bash
git clone https://github.com/<your-username>/krisha-price-prediction
cd krisha-price-prediction
pip install -r requirements.txt
```

Требуется Python 3.9+.

---

## 🚀 Как запустить

### 1. Получить модель

Положи `krisha_final.csv` в корень проекта и запусти ноутбук полностью — на выходе появятся три файла:

```
xgb_model.pkl
cat_categories.pkl
train_medians.pkl
```

### 2. Инференс на сырых данных

`predict.py` принимает DataFrame в формате **сырого CSV** (как из krisha.kz) и возвращает цены в тенге.

```python
import pandas as pd
from predict import predict

df = pd.read_csv('krisha_final.csv').head(5)
prices = predict(df)

for i, p in enumerate(prices):
    print(f'Объявление {i+1}: {p:,.0f} ₸  ({p/1_000_000:.1f}М)')
```

Или напрямую из командной строки:

```bash
python predict.py
```

### 3. Формат входных данных

`predict.py` сам делает feature engineering (как в ноутбуке, секция 5). На вход нужны **сырые колонки**:

| Колонка | Пример |
|---|---|
| `город` | `'Алматы, Бостандыкский район'` |
| `комнаты` | `2` |
| `flat.floor` | `'5 из 9'` |
| `live.square` | `'65.0 м²'` |
| `ceiling` | `'2.7 м'` |
| `flat.security` | `'Домофон, Видеонаблюдение'` |
| `flat.building` | `'Панельный'` |
| `flat.toilet` | `'Раздельный'` |
| `flat.balcony` | `'Балкон'` |
| `flat.door` | `'Металлическая'` |
| `flat.parking` | `NaN` |
| `live.furniture` | `'Частично'` |
| `flat.flooring` | `'Ламинат'` |
| `flat.priv_dorm` | `NaN` |
| `has_change` | `NaN` |
| `flat.renovation` | `'Евроремонт'` |
| `map.complex` | любое (удаляется) |

Пропуски в категориальных → автоматически заполняются `'неизвестно'`.  
Пропуски в числовых (`этаж`, `всего_этажей`, `высота_потолков`) → медиана из обучающей выборки.

---

## Технологии

`pandas` · `numpy` · `scikit-learn` · `xgboost` · `matplotlib` · `seaborn` · `joblib`
