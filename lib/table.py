from lib.column import Column
from lib.grouped_table import GroupedTable
from copy import copy

class Table:
    table_name = None
    columns = None
    filters = None
    sql_string = None
    had_changed = None
    
    '''
        column_dtype_map: ...
    '''
    def __init__(self, table_name, column_dtype_map={}, sql_string=None, filters=[], columns=None, had_changed=False):
        self.table_name = table_name
        self.columns = {}
        self.filters = filters
        self.sql_string = sql_string
        self.had_changed = had_changed
        if columns:
            self.columns = columns
        else:
            for column_name in column_dtype_map.keys():
                self[column_name] = Column(dtype=column_dtype_map[column_name], 
                                          sql_string=column_name,
                                          is_direct_column=True)

    def __getitem__(self, key):
        if isinstance(key, Column):
            if key.dtype != 'BOOL':
                raise Exception('Can only filter/where using column of type BOOL. got %s' % (key.dtype))
            return self.where(key)
        if isinstance(key, list):
            if all(map(lambda x: isinstance(x, str), key)) == False:
                raise Exception('List must be all strings. got %s' % (key))
            if all(map(lambda x: x in self.columns, key)) == False:
                raise Exception('All columns names must be a column in the table. got %s' % (key))
            return self.select(key)

        c = copy(self.columns[key])
        if c.is_direct_column:
            c.sql_string = f'{self.table_name}.{key}'
        return c

    def __setitem__(self, key, newvalue):
        if isinstance(newvalue, Column) == False:
            raise Exception('trying to set table column with wrong type. expected type: %s, got type: %s' % (str(type(Column)), str(type(newvalue))))
        self.had_changed = True
        newvalue.is_direct_column=False
        self.columns[key] = newvalue
    
    def __getattr__(self, attribute_name):
        return self[attribute_name]
    
    def __copy__(self):
        result_table = Table(table_name=self.table_name,
                             sql_string=self.sql_string, 
                             had_changed=self.had_changed,
                             filters=[])
        for c in self.columns.keys(): result_table[c] = self[c] # column deep copy will occur in __getitem__
        for f in self.filters: result_table.filters.append(copy(f))
        return result_table

    def reset_index(self, level=None, drop=False, inplace=False, col_level=0, col_fill=''):
        return copy(self)
    
    def to_frame(self):
        return copy(self)

    def where(self, cond_column):
        self.had_changed = True
        new_table = copy(self)
        new_table.filters.append(cond_column)
        return new_table

    def select(self, columns_names):
        self.had_changed = True
        new_table = copy(self)
        # filter only selected columns from columns dictionary
        new_table.columns = \
            {col_name:col_val for (col_name, col_val) in new_table.columns.items() if col_name in columns_names}
        return new_table
    
    def merge(self, right, how='inner', on=None, left_on=None, right_on=None):
        if not isinstance(right, Table):
            raise Exception("merge expects right to be of type: %s, got: %s" %  (str(type(Table)), str(type(right))))
        if how not in ['left', 'right', 'inner']:
            raise Exception("merge 'how' value must be in [‘left’, ‘right’, ‘inner’]")
        if on is not None and left_on is None and right_on is None:
            left = copy(self)
            right = copy(right)
            if len(set(left.columns.keys()) & set(right.columns.keys())) > 1:
                raise Exception("merge got duplicates columns in both tables (except 'on' value)")
            if on not in left.columns or on not in right.columns:
                raise Exception("merge 'on' value must be in both tables as column")
            
            # creating new table columns
            left_columns = dict(zip(left.columns.keys(), map(lambda x: left[x], left.columns.keys())))
            right_columns = dict(zip(right.columns.keys(), map(lambda x: right[x], right.columns.keys())))
            right_columns.pop(on)
            new_table_columns = {**left_columns, **right_columns}

            # creating new table sql string
            single_select_field_format = 't1.%s AS %s'
            selected_fields_left = ', '.join(list(map(lambda x: single_select_field_format % (x, x), left.columns.keys())))
            single_select_field_format = 't2.%s AS %s'
            selected_fields_right = ', '.join(list(map(lambda x: single_select_field_format % (x, x), filter(lambda x: x!=on, right.columns.keys()))))
            selected_fields = selected_fields_left
            if selected_fields_right:
                selected_fields += ', ' + selected_fields_right
            new_table_sql_string = f'SELECT {selected_fields} FROM ({left.get_sql_string()}) AS t1 {how.upper()} JOIN ({right.get_sql_string()}) AS t2 ON t1.{on}=t2.{on}'
            
            return Table(table_name='Temp',
                         columns=new_table_columns,
                         filters=[],
                         sql_string=new_table_sql_string)
        
        elif on is None and (left_on is not None and right_on is not None):
            raise Exception('TODO: support left_on right_on for merge')
        else:
            raise Exception('merge supports: on OR left_on + right_on. cant have both or missing values')
    
    def groupby(self, by):
        def __get_column_key(col):
            for k in self.columns.keys():
                if self.columns[k].sql_string==col.sql_string: return k
            raise Exception('groupby got column that is not in table')
                
        groupings = None
        if isinstance(by, str):
            groupings = {by:self[by]}
        elif isinstance(by, Column):
            groupings = {__get_column_key(by): copy(by)}
        elif isinstance(by, list):
            groupings = {}
            for b in by:
                if isinstance(b, str): groupings[b] = self[b]
                elif isinstance(b, Column): groupings[__get_column_key(by)] = copy(b)
                else: raise Exception(f'groupby got unexpected type. expect str or column, got: {str(type(b))}')
        else:
            raise Exception("groupby 'by' value must be str OR list[str] OR Column OR list[Column]")
        
        return GroupedTable(copy(self), groupings=groupings)
        
    def get_sql_string(self):
        if self.sql_string and not self.had_changed: #maybe not had_changes equivalent to all columns is_direct_column==true 
            return self.sql_string
        
        from_field = None
        selected_fields = None
        if self.sql_string:
            from_field = '(%s) AS %s' % (self.sql_string, self.table_name)
        else:
            from_field = self.table_name

#         print(self.columns.keys())
#         print(list(map(lambda x: x.sql_string, self.columns.values())))
        single_select_field_format = '(%s) AS %s'
        selected_fields = ', '.join(list(map(lambda x: single_select_field_format % (self[x].sql_string, x if self[x].is_direct_column else "'"+x+"'"), self.columns.keys())))

        single_where_field_format = '(%s)'
        where_cond = ' AND '.join(list(map(lambda c: single_where_field_format % (c.sql_string), self.filters)))
        
        if where_cond == '':
            return f'SELECT {selected_fields} FROM {from_field}'
        else:
            return f'SELECT {selected_fields} FROM {from_field} WHERE {where_cond} '