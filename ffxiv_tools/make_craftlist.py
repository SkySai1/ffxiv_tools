import pandas as pd
from pathlib import Path

# === Пути к CSV ===
DATA_DIR = Path("../ffxiv-datamining/csv")
RECIPE_CSV = DATA_DIR / "Recipe.csv"
ITEM_CSV = DATA_DIR / "Item.csv"
RECIPELEVEL_CSV = DATA_DIR / "RecipeLevelTable.csv"

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
    - колонка 'key' содержит '#', 'int32', затем числовые ID.
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
    levels = load_and_clean(RECIPELEVEL_CSV)

    # === RECIPE ===
    # В Recipe.csv:
    #   '1' -> CraftType
    #   '2' -> RecipeLevelTable (ID строки уровня)
    #   '4' -> Item{Result} (ID предмета)
    recipes_small = recipes[["1", "2", "4"]].copy()
    recipes_small.columns = ["CraftTypeID", "LevelID", "ItemID"]

    recipes_small["CraftTypeID"] = pd.to_numeric(
        recipes_small["CraftTypeID"], errors="coerce"
    ).astype("Int64")
    recipes_small["ItemID"] = pd.to_numeric(
        recipes_small["ItemID"], errors="coerce"
    ).astype("Int64")
    recipes_small["LevelID"] = pd.to_numeric(
        recipes_small["LevelID"], errors="coerce"
    ).astype("Int64")

    # Маппим CraftType -> название крафт-класса
    recipes_small["class"] = recipes_small["CraftTypeID"].map(CRAFT_TYPE_MAP)
    recipes_small = recipes_small.dropna(subset=["class", "ItemID", "LevelID"])

    # === ITEM ===
    # В Item.csv:
    #   'key' -> ID предмета
    #   '9'   -> Name (название предмета)
    items_small = items[["key", "9"]].copy()
    items_small.columns = ["ItemID", "item_name"]
    items_small["ItemID"] = pd.to_numeric(
        items_small["ItemID"], errors="coerce"
    ).astype("Int64")
    items_small = items_small.dropna(subset=["ItemID"])

    # === RECIPE LEVEL TABLE ===
    # В RecipeLevelTable.csv (по структуре SaintCoinach):
    #   'key' -> ID уровня (тот самый RecipeLevelTable)
    #   '0'   -> ClassJobLevel (требуемый уровень крафта)
    levels_small = levels[["key", "0"]].copy()
    levels_small.columns = ["LevelID", "craft_level"]
    levels_small["LevelID"] = pd.to_numeric(
        levels_small["LevelID"], errors="coerce"
    ).astype("Int64")
    levels_small["craft_level"] = pd.to_numeric(
        levels_small["craft_level"], errors="coerce"
    ).astype("Int64")

    # 2. Джойним всё вместе
    #   a) рецепты + уровни (по LevelID)
    recipes_with_levels = recipes_small.merge(
        levels_small, on="LevelID", how="left"
    )

    #   b) добавляем имена предметов
    merged = recipes_with_levels.merge(items_small, on="ItemID", how="left")

    # 3. Формируем финальный результат
    #   level_id — внутренний ID строки RecipeLevelTable
    #   craft_level — реальный уровень крафта для рецепта
    result = merged[["class", "LevelID", "craft_level", "item_name"]].copy()
    result = result.rename(columns={"LevelID": "level_id"})
    result = result.dropna(subset=["item_name", "craft_level"])

    out_path = "ffxiv_recipes_export.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Готово. Записал {len(result)} строк в {out_path}")


if __name__ == "__main__":
    main()
