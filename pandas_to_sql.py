from copy import copy
from lib.Table import Table
from lib.utils.helpers import  create_schema_from_df
from lib.utils.PandasDataFrameIntercepter import PandasDataFrameIntercepter


def wrap_df(df, table_name):
    t = Table(table_name, column_dtype_map=create_schema_from_df(df))
    return PandasDataFrameIntercepter(copy(df), copy(t))