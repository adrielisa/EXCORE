
import pandas as pd

def transform_sheet_to_long_format(df_raw: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    df = df_raw.copy()

    # --- Special case: Density per Wafer (1 row, no headers)
    if sheet_name == "Density per Wafer":
        if df.shape[0] < 1:
            raise ValueError(f"Sheet '{sheet_name}' has insufficient data.")
        headers = df.iloc[0].tolist()
        values = df.iloc[1].tolist() if df.shape[0] > 1 else [0] * len(headers)
        long_df = pd.DataFrame({
            "Product ID": headers,
            "Value": pd.to_numeric(values, errors="coerce")
        }).dropna()
        long_df["Attribute"] = "Density"
        long_df["Sheet"] = sheet_name
        return long_df

    # --- Default format: at least 2 rows (Supply_Demand, Yield, etc.)
    if df.shape[0] < 2:
        raise ValueError(f"Sheet '{sheet_name}' has insufficient data.")

    df.columns = df.iloc[1]
    df = df.drop([0, 1]).reset_index(drop=True)

    if "Attribute" in df.columns:
        df.rename(columns={df.columns[0]: "Product ID", df.columns[1]: "Attribute"}, inplace=True)
        id_vars = ["Product ID", "Attribute"]
    else:
        df.rename(columns={df.columns[0]: "Product ID"}, inplace=True)
        id_vars = ["Product ID"]

    long_df = df.melt(id_vars=id_vars, var_name="Period", value_name="Value")
    long_df = long_df.dropna(subset=["Value"])
    long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
    long_df = long_df.dropna(subset=["Value"])
    long_df["Sheet"] = sheet_name
    return long_df

def build_data_dict(df: pd.DataFrame, sheet_name: str, attribute_filter: str = None) -> dict:
    filtered = df[df["Sheet"] == sheet_name]
    if attribute_filter:
        filtered = filtered[filtered["Attribute"] == attribute_filter]

    result = {}
    for _, row in filtered.iterrows():
        product = row["Product ID"]
        period = row["Period"]
        value = row["Value"]
        if product not in result:
            result[product] = {}
        result[product][period] = value
    return result
