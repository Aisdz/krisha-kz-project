import joblib
import numpy as np
import pandas as pd

# load
model = joblib.load("xgb_model.pkl")
cat_categories = joblib.load("cat_categories.pkl")
train_medians = joblib.load("train_medians.pkl")

# порядок колонок как при обучении
MODEL_COLUMNS = [
    'комнаты',
    'город',
    'flat.building',
    'house.year',
    'flat.toilet',
    'flat.balcony',
    'flat.door',
    'flat.parking',
    'live.furniture',
    'flat.flooring',
    'flat.priv_dorm',
    'has_change',
    'flat.renovation',
    'район',
    'этаж',
    'всего_этажей',
    'площадь',
    'высота_потолков',
    'безопасность'
]

# preprocess 
def preprocess(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # string safety
    str_cols = ['город', 'flat.floor', 'live.square', 'ceiling', 'flat.security']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)

    # ГОРОД / РАЙОН
    city_split = df['город'].str.split(',', expand=True)
    df['город'] = city_split[0].str.strip()
    df['район'] = city_split[1].str.strip() if city_split.shape[1] > 1 else 'неизвестно'

    # ЭТАЖИ
    floor_extract = df['flat.floor'].str.extract(r'(\d+)\D+(\d+)')
    df['этаж'] = pd.to_numeric(floor_extract[0], errors='coerce')
    df['всего_этажей'] = pd.to_numeric(floor_extract[1], errors='coerce')

    # ПЛОЩАДЬ
    df['площадь'] = pd.to_numeric(
        df['live.square'].str.extract(r'([\d.]+)')[0], errors='coerce'
    )

    # ПОТОЛКИ
    df['высота_потолков'] = pd.to_numeric(
        df['ceiling'].str.extract(r'([\d.]+)')[0], errors='coerce'
    )

    # БЕЗОПАСНОСТЬ
    df['безопасность'] = (
        df['flat.security']
        .fillna('')
        .astype(str)
        .str.split(',')
        .str.len()
    )

    # DROP UNUSED
    drop_cols = ['flat.floor', 'live.square', 'ceiling', 'flat.security', 'map.complex']
    df.drop(columns=drop_cols, errors='ignore', inplace=True)

    return df


# FILL MISSING
def fill_missing(df: pd.DataFrame):

    for col, median in train_medians.items():
        if col in df.columns:
            df[col] = df[col].fillna(median)

    cat_fill_cols = [
        'город', 'flat.building', 'flat.toilet', 'flat.balcony', 'flat.door',
        'flat.parking', 'live.furniture', 'flat.flooring', 'flat.priv_dorm',
        'has_change', 'flat.renovation', 'район'
    ]
    for col in cat_fill_cols:
        if col in df.columns:
            df[col] = df[col].fillna('неизвестно')

    return df


# CATEGORIES
def encode_categories(df: pd.DataFrame):

    for col, cats in cat_categories.items():
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=cats)

    return df

# MAIN PREDICT
def predict(df_raw: pd.DataFrame):

    df = preprocess(df_raw)
    df = fill_missing(df)
    df = encode_categories(df)

    # гарантируем ВСЕ колонки
    for col in MODEL_COLUMNS:
        if col not in df.columns:
            if col in cat_categories:
                df[col] = 'неизвестно'
            else:
                df[col] = 0

    df = df[MODEL_COLUMNS]

    preds_log = model.predict(df)

    return np.expm1(preds_log)
