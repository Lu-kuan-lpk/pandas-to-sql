import pandas as pd
from lib.Table import Table
from lib.Column import Column
from lib.GroupedTable import GroupedTable
from lib.utils.PandasDataFrameIntercepter import PandasDataFrameIntercepter
from copy import copy

## Conventions
def flatten_grouped_dataframe(df):
    if not isinstance(df, PandasDataFrameIntercepter):
        raise Exception(f"can only get type {str(type(PandasDataFrameIntercepter))}")
    df_c = copy(df.df_pandas)
    df_c.columns = df_c.columns.map('_'.join)
    df_c = df_c.reset_index()
    return PandasDataFrameIntercepter(df_c, copy(df.df_sql_convert_table))


## Types
def convert_df_type(col_type):
    if pd.api.types.is_bool_dtype(col_type): return 'BOOL'
    elif pd.api.types.is_integer_dtype(col_type): return 'INT'
    elif pd.api.types.is_numeric_dtype(col_type): return 'FLOAT'
    elif pd.api.types.is_string_dtype(col_type): return 'VARCHAR'
    elif pd.api.types.is_datetime64_any_dtype(col_type): return 'TIMESTAMP'
    else: raise Exception(f"could not convert column type. got: {str(col_type)}")

def create_schema_from_df(df):        
    schema = {}
    for col_name, col_type in df.dtypes.items():
        schema[col_name] = convert_df_type(col_type)
    return schema