import pandas as pd
from pathlib import Path

# === Пути к CSV ===
# Здесь лежат Recipe.csv и Item.csv из репо xivapi/ffxiv-datamining
DATA_DIR = Path("ffxiv-datamining/csv")
RECIPE_CSV = DATA_DIR / "Recipe.csv"
ITEM_CSV = DATA_DIR / "Item.csv"

# === Маппинг CraftType -> название крафтерского класса ===
CRAFT_TYPE_MAP = {
    0: "Carpenter",
    1: "Blacksmith",
    2: "Armorer",
    3: "Goldsmith",
    4: "Leatherworker",
    5: "Weaver",
    6: "Alchemist",
    7: "Culinarian",
}


def load_and_clean(csv_path: Path) -> pd.DataFrame:
    """
    Читаем CSV SaintCoinach-формата:
    - колонка 'key' содержит: '#', 'int32', затем числовые ID.
    Оставляем только строки, где key можно привести к числу.
    """
    df = pd.read_csv(csv_path, low_memory=False)
    df = df[pd.to_numeric(df["key"], errors="coerce").notna()].copy()
    df["key"] = df["key"].astype(int)
    return df


def main():
    # 1. Загружаем и чистим данные
    recipes = load_and_clean(RECIPE_CSV)
    items = load_and_clean(ITEM_CSV)

    # === RECIPE ===
    # В Recipe.csv:
    #   '1' -> CraftType
    #   '2' -> RecipeLevelTable (ID уровня; используем как level)
    #   '4' -> Item{Result} (ID предмета)
    recipes_small = recipes[["1", "2", "4"]].copy()
    recipes_small.columns = ["CraftTypeID", "LevelID", "ItemID"]

    # Приводим CraftTypeID и ItemID к числу
    recipes_small["CraftTypeID"] = pd.to_numeric(
        recipes_small["CraftTypeID"], errors="coerce"
    ).astype("Int64")

    recipes_small["ItemID"] = pd.to_numeric(
        recipes_small["ItemID"], errors="coerce"
    ).astype("Int64")

    # Маппим CraftType -> название класса
    recipes_small["class"] = recipes_small["CraftTypeID"].map(CRAFT_TYPE_MAP)
    # Оставляем только крафтерские классы и валидные ItemID
    recipes_small = recipes_small.dropna(subset=["class", "ItemID"])

    # === ITEM ===
    # В Item.csv:
    #   'key' -> ID предмета
    #   '9'   -> Name (человекочитаемое имя)
    items_small = items[["key", "9"]].copy()
    items_small.columns = ["ItemID", "item_name"]

    items_small["ItemID"] = pd.to_numeric(
        items_small["ItemID"], errors="coerce"
    ).astype("Int64")

    items_small = items_small.dropna(subset=["ItemID"])

    # 3. Джоин по ItemID (типы теперь совпадают)
    merged = recipes_small.merge(items_small, on="ItemID", how="left")

    # 4. Формируем финальный результат
    result = merged[["class", "LevelID", "item_name"]].copy()
    result = result.rename(columns={"LevelID": "level"})
    result = result.dropna(subset=["item_name"])

    # Опционально: level тоже в число
    result["level"] = pd.to_numeric(result["level"], errors="ignore")

    # 5. Сохраняем
    out_path = "ffxiv_recipes_export.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Готово. Записал {len(result)} строк в {out_path}")


if __name__ == "__main__":
    main()
