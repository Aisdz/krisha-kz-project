import joblib
import numpy as np
import pandas as pd


model          = joblib.load('xgb_model.pkl')
cat_categories = joblib.load('cat_categories.pkl')
train_medians  = joblib.load('train_medians.pkl')

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Feature engineering — те же шаги что в ноутбуке секция 5."""
    df = df.copy()

    df['район']  = df['город'].str.split(',').str[1].str.strip()
    df['город']  = df['город'].str.split(',').str[0].str.strip()

    df[['этаж', 'всего_этажей']] = (
        df['flat.floor'].str.extract(r'(\d+) из (\d+)').astype(float)
    )
    df = df.drop(columns=['flat.floor'])

    df['площадь'] = df['live.square'].str.extract(r'([\d.]+)').astype(float)
    df = df.drop(columns=['live.square'])

    df['высота_потолков'] = df['ceiling'].str.extract(r'([\d.]+)').astype(float)
    df = df.drop(columns=['ceiling'])

    df['безопасность'] = (
        df['flat.security'].str.split(',').str.len().fillna(0).astype(int)
    )
    df = df.drop(columns=['flat.security', 'map.complex'], errors='ignore')

    return df


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    for col, median in train_medians.items():
        if col in df.columns:
            df[col] = df[col].fillna(median)

    cat_fill_cols = [
        'flat.building', 'flat.toilet', 'flat.balcony', 'flat.door',
        'flat.parking', 'live.furniture', 'flat.flooring', 'flat.priv_dorm',
        'has_change', 'flat.renovation', 'район',
    ]
    for col in cat_fill_cols:
        if col in df.columns:
            df[col] = df[col].fillna('неизвестно')

    return df


def encode_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Конвертируем категориальные колонки в dtype category."""
    for col, cats in cat_categories.items():
        if col in df.columns:
            # Значения не из обучающей выборки → NaN, XGBoost обработает
            df[col] = pd.Categorical(df[col], categories=cats)
    return df


def predict(df_raw: pd.DataFrame) -> np.ndarray:
    """
    Принимает сырой DataFrame (как из CSV),
    возвращает предсказанные цены в тенге.
    """
    df = preprocess(df_raw)
    df = fill_missing(df)
    df = encode_categories(df)

    # Убираем целевую колонку если вдруг есть
    df = df.drop(columns=['цена'], errors='ignore')

    price_log = model.predict(df)
    return np.expm1(price_log)


# ── Пример использования ────────────────────────────────────────────────────
if __name__ == '__main__':
    sample = pd.read_csv('krisha_final.csv').head(5)
    prices = predict(sample)

    for i, p in enumerate(prices):
        print(f'Объявление {i+1}: {p:,.0f} тенге  ({p/1_000_000:.1f}М)')
