import pandas as pd
import logging

def transform_sheet_to_long_format(df_raw: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    df = df_raw.copy()

    # --- Special case: Density per Wafer
    if sheet_name == "Density per Wafer":
        if df.shape[0] < 1:
            logging.warning(f"⚠️ La hoja '{sheet_name}' está vacía. Se omitirá.")
            return pd.DataFrame()

        # Caso correcto: una fila de datos
        headers = df.columns.tolist()
        values = df.iloc[0].tolist()

        long_df = pd.DataFrame({
            "Product ID": headers,
            "Value": pd.to_numeric(values, errors="coerce")
        }).dropna()

        long_df["Attribute"] = "Density"
        long_df["Sheet"] = sheet_name
        logging.info(f"Transformed data for sheet '{sheet_name}':\n{long_df.head(20)}")
        return long_df


    # --- Special case: Supply_Demand (has 'Attribute' column)
    if sheet_name == "Supply_Demand":
        if df.shape[0] < 2:
            raise ValueError(f"Sheet '{sheet_name}' has insufficient rows.")

        # Asumimos que ya tiene encabezados correctos
        if "Attribute" not in df.columns or "Product ID" not in df.columns:
            raise ValueError(f"'Product ID' or 'Attribute' columns not found in '{sheet_name}'. Got columns: {df.columns.tolist()}")

        df = df.dropna(subset=["Product ID", "Attribute"])
        df["Attribute"] = df["Attribute"].str.strip()

        long_df = df.melt(id_vars=["Product ID", "Attribute"], var_name="Period", value_name="Value")
        long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
        long_df = long_df.dropna(subset=["Value"])
        long_df["Sheet"] = sheet_name

        logging.info(f"Transformed data for sheet '{sheet_name}':\n{long_df.head(20)}")
        return long_df

    # --- Special case: Wafer Plan (no 'Attribute' column)
    if sheet_name == "Wafer Plan":
        if df.shape[0] < 2:
            raise ValueError(f"Sheet '{sheet_name}' has insufficient data.")

        logging.info(f"Antes de transformación:\n{df.head(5)}")

        df.columns = df.iloc[1]
        df = df.drop([0, 1]).reset_index(drop=True)

        if pd.isna(df.columns[0]) or "Product" not in str(df.columns[0]):
            df.rename(columns={df.columns[0]: "Product ID"}, inplace=True)
        else:
            df.columns.values[0] = "Product ID"

        df = df.dropna(subset=["Product ID"])

        if df.empty:
            logging.warning(f"No hay datos válidos en '{sheet_name}' tras limpieza.")
            return pd.DataFrame()

        long_df = df.melt(id_vars=["Product ID"], var_name="Period", value_name="Value")
        long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
        long_df = long_df.dropna(subset=["Value"])
        long_df["Attribute"] = "Available Capacity"
        long_df["Sheet"] = sheet_name

        if long_df.empty:
            logging.warning(f"No se pudo extraer datos numéricos de '{sheet_name}' para 'Available Capacity'.")
        else:
            logging.info(f"Transformed data for sheet '{sheet_name}':\n{long_df.head(20)}")

        return long_df

    # --- Default format: Yield, Boundary Conditions, etc.
    df.columns = df.iloc[1]
    df = df.drop([0, 1]).reset_index(drop=True)

    if "Attribute" in df.columns:
        df.rename(columns={df.columns[0]: "Product ID", df.columns[1]: "Attribute"}, inplace=True)
        id_vars = ["Product ID", "Attribute"]
    else:
        df.rename(columns={df.columns[0]: "Product ID"}, inplace=True)
        id_vars = ["Product ID"]

    df = df.dropna(subset=["Product ID"])
    long_df = df.melt(id_vars=id_vars, var_name="Period", value_name="Value")
    long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
    long_df = long_df.dropna(subset=["Value"])
    long_df["Sheet"] = sheet_name

    logging.info(f"Transformed data for sheet '{sheet_name}':\n{long_df.head(20)}")
    return long_df


def build_data_dict(df: pd.DataFrame, sheet_name: str, attribute_filter: str = None) -> dict:
    filtered = df[df["Sheet"] == sheet_name]

    if attribute_filter:
        if "Attribute" not in filtered.columns:
            logging.warning(f"La hoja '{sheet_name}' no tiene columna 'Attribute'. No se puede aplicar el filtro '{attribute_filter}'.")
            filtered = pd.DataFrame()
        else:
            filtered = filtered[
                filtered["Attribute"].str.strip().str.lower() == attribute_filter.strip().lower()
            ]

    logging.info(f"Filtered data for '{attribute_filter}' in sheet '{sheet_name}':\n{filtered}")

    if filtered.empty:
        raise ValueError(f"No data found for attribute '{attribute_filter}' in sheet '{sheet_name}'.")

    result = {}
    for _, row in filtered.iterrows():
        product = row["Product ID"]
        period = row["Period"]
        value = row["Value"]
        if product not in result:
            result[product] = {}
        result[product][period] = value
    return result
