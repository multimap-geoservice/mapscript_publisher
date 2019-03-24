
from interface import psqldb, gdaldb

if __name__ == '__main__':
    print psqldb().connString
    print gdaldb(table='str')()
    