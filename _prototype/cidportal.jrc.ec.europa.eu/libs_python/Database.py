# Copyright (c) 2015, European Union
# All rights reserved.
# Authors: Simonetti Dario, Marelli Andrea
#
#
# This file is part of IMPACT toolbox.
#
# IMPACT toolbox is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# IMPACT toolbox is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with IMPACT toolbox.
# If not, see <http://www.gnu.org/licenses/>.


# Import global libraries
import sqlite3
import json


class Database:

    def __init__(self, database_file):
        self.db_conn = sqlite3.connect(database_file)
        self.db_conn.row_factory = self.__dict_factory

    @staticmethod
    def __dict_factory(cursor, row):
        """ Get query results ad dictionaries """
        d = {}
        for idx, col in enumerate(cursor.description):
            try:
                d[col[0]] = json.loads(row[idx])
            except:
                d[col[0]] = row[idx]
        return d

    def __execute_query(self, sql):
        """ Execute the given sql query """
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(sql)
            self.db_conn.commit()
            return cursor.fetchall()
        except Exception as error:
            print str(error)

    @staticmethod
    def __where(conditions=None):
        """ Prepare the WHERE clause """
        try:
            if conditions and len(conditions) > 0:
                where = []
                for condition in conditions:
                    where_clause = str(condition[0]) + " " + str(condition[1]) + " '" + str(condition[2]) + "'"
                    where.append(where_clause)
                return " AND ".join(where)
            return None
        except Exception as error:
            print str(error)

    def create_table(self, table_name, columns):
        """ Create the specified table if not exist in the database """
        try:
            # check if table already exist
            where = self.__where([
                ['type', '=', 'table'],
                ['name', '=', table_name],
            ])
            records = self.__execute_query("SELECT name FROM sqlite_master WHERE " + where + ";")
            # create table if not exist
            if not records:
                columns_string = " text, ".join(columns) + ' text'
                self.__execute_query("CREATE TABLE " + table_name + " (" + columns_string + ");")
        except Exception as error:
            print str(error)

    def insert(self, table_name, data):
        """ Prepare and execute an sql INSERT query """
        try:
            keys = values = ''
            for k, v in data.iteritems():
                if isinstance(v, list) or isinstance(v, dict):
                    v = json.dumps(v)
                keys += k + ","
                values += "'" + str(v) + "',"
            self.__execute_query("INSERT INTO " + table_name + " (" + keys[:-1] + ") VALUES (" + values[:-1] + ")")
        except Exception as error:
            print str(error)

    def update(self, table_name, data, conditions=None):
        """ Prepare and execute an sql UPDATE query """
        try:
            values = ''
            for k, v in data.iteritems():
                if isinstance(v, list) or isinstance(v, dict):
                    v = json.dumps(v)
                values += " " + k + "='" + str(v) + "',"
            values = values[:-1]
            where = self.__where(conditions)
            self.__execute_query("UPDATE " + table_name + " SET " + values + " WHERE " + where + ";")
        except Exception as error:
            print str(error)

    def delete(self, table_name, conditions=None):
        """ Prepare and execute an sql DELETE query """
        try:
            where = self.__where(conditions)
            where_clause = " WHERE " + where if where else ""
            self.__execute_query("DELETE FROM " + table_name + where_clause + ";")
        except Exception as error:
            print str(error)

    def select(self, table_name, fields='*', conditions=None, order_by=None):
        """ Prepare and execute an sql SELECT query """
        try:
            where = self.__where(conditions)
            where_clause = " WHERE " + where if where else ""
            order_by = " ORDER BY " + order_by if order_by else ""
            return self.__execute_query("SELECT " + fields + " FROM " + table_name + where_clause + order_by + ";")
        except Exception as error:
            print str(error)
