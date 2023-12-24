from pandas_to_sql.engine.columns.column import Column
from pandas_to_sql.engine.columns.common import value_to_sql_string, add_common_operators_to_class
from pandas_to_sql.utils.helpers import convert_df_type
from pandas_to_sql.engine.columns.common import get_column_class_from_type

class BoolColumn(Column):
    def __init__(self, sql_string):
        super().__init__(dtype='BOOL', sql_string=sql_string)
    
    def __neg__(self):
        return BoolColumn(sql_string=f'(NOT({value_to_sql_string(self)}))')

    def __invert__(self):
        return BoolColumn(sql_string=f'(NOT({value_to_sql_string(self)}))')


def __my_astype__(col, t):
    print("here", value_to_sql_string(col))
    tt = convert_df_type(t)
    dtype = get_column_class_from_type(tt)
    return dtype(sql_string=f'(CASE WHEN {value_to_sql_string(col)} THEN 1::{tt} ELSE 0::{tt} END)')


add_common_operators_to_class(BoolColumn)

BoolColumn.astype = lambda self, t: __my_astype__(self, t)
