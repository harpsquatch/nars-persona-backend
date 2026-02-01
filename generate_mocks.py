import os
import json
import random
import string
import mysql.connector
from datetime import datetime, timedelta

# Database Connection Config (Change this to your actual credentials)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'mysql',
    'database': 'narsbeauty'
}

# Output Folder
MOCK_FOLDER = 'mocks'

# Helper to generate random data
def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters, k=length))

def random_date():
    start_date = datetime(2023, 1, 1)
    end_date = datetime.now()
    return start_date + (end_date - start_date) * random.random()

def random_int(min_val=1, max_val=100):
    return random.randint(min_val, max_val)

def random_email():
    return f"{random_string(5).lower()}@example.com"

# Column type to mock value mapper
def mock_value(column):
    col_type = column['Type'].lower()

    if 'int' in col_type:
        return random_int()
    elif 'varchar' in col_type or 'text' in col_type:
        return random_string(12)
    elif 'date' in col_type or 'timestamp' in col_type or 'datetime' in col_type:
        return random_date().strftime('%Y-%m-%d %H:%M:%S')
    elif 'float' in col_type or 'double' in col_type or 'decimal' in col_type:
        return round(random.uniform(1, 100), 2)
    elif 'email' in column['Field'].lower():
        return random_email()
    elif 'id' in column['Field'].lower():
        return random_int(1, 9999)
    else:
        return random_string(8)

# Create /mocks directory if not exists
os.makedirs(MOCK_FOLDER, exist_ok=True)

def fetch_tables(cursor):
    cursor.execute("SHOW TABLES")
    return [table[0] for table in cursor.fetchall()]

def fetch_columns(cursor, table_name):
    cursor.execute(f"DESCRIBE {table_name}")
    columns = []
    for column in cursor.fetchall():
        columns.append({
            'Field': column[0],
            'Type': column[1]
        })
    return columns

def generate_mock_data(table_name, columns, row_count=5):
    mock_data = []
    for _ in range(row_count):
        row = {}
        for column in columns:
            row[column['Field']] = mock_value(column)
        mock_data.append(row)
    return mock_data

def write_mock_file(table_name, mock_data):
    file_content = f"""const mock{table_name.capitalize()} = {json.dumps(mock_data, indent=2)};

export default mock{table_name.capitalize()};
"""
    file_path = os.path.join(MOCK_FOLDER, f"mock{table_name.capitalize()}.js")
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(file_content)

def main():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    tables = fetch_tables(cursor)
    print(f"Found tables: {tables}")

    for table in tables:
        columns = fetch_columns(cursor, table)
        mock_data = generate_mock_data(table, columns)
        write_mock_file(table, mock_data)
        print(f"Generated mock for table: {table}")

    cursor.close()
    connection.close()
    print(f"✅ All mock files saved in: {MOCK_FOLDER}/")

if __name__ == '__main__':
    main()
