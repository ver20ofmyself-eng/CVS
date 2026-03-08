#!/usr/bin/env python3
"""
Скрипт для инициализации таблиц в базе данных.
Запускать после старта контейнера PostgreSQL.
"""

import os
import sys
import time
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import OperationalError

def wait_for_postgres(host='localhost', port=5433, user='cvs_user', 
                     password='cvs_password', database='cvs_analyzer', 
                     max_attempts=30):
    """Ждём пока PostgreSQL не станет доступен"""
    print("🔄 Ожидание доступности PostgreSQL...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            conn.close()
            print("✅ PostgreSQL доступен!")
            return True
        except OperationalError as e:
            print(f"   Попытка {attempt}/{max_attempts}: {e}")
            time.sleep(2)
    
    print(f"❌ PostgreSQL не стал доступен после {max_attempts} попыток")
    return False

def execute_sql_from_file(conn, filepath):
    """Выполняет SQL команды из файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor = conn.cursor()
        
        # Разделяем SQL команды (учитываем что некоторые могут быть многострочными)
        commands = []
        current_command = []
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            
            current_command.append(line)
            
            if line.endswith(';'):
                command = ' '.join(current_command)
                commands.append(command)
                current_command = []
        
        # Если осталась незавершённая команда
        if current_command:
            commands.append(' '.join(current_command))
        
        # Выполняем команды
        for command in commands:
            try:
                print(f"   Выполняем: {command[:80]}...")
                cursor.execute(command)
                conn.commit()
            except Exception as e:
                print(f"   ⚠️  Предупреждение: {e}")
                conn.rollback()  # Откатываем транзакцию при ошибке
                continue  # Продолжаем выполнение других команд
        
        cursor.close()
        print("✅ SQL команды выполнены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении SQL: {e}")
        return False

def main():
    # Параметры подключения (совпадают с docker-compose.yml)
    db_config = {
        'host': 'localhost',
        'port': 5433,
        'user': 'cvs_user',
        'password': 'cvs_password',
        'database': 'cvs_analyzer'
    }
    
    print("🚀 Начало инициализации базы данных CVS Analyzer")
    
    # Ждём доступности PostgreSQL
    if not wait_for_postgres(**db_config):
        sys.exit(1)
    
    # Подключаемся к базе данных
    try:
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("✅ Подключение к базе данных установлено")
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        sys.exit(1)
    
    # Выполняем SQL из файла
    sql_file = os.path.join(os.path.dirname(__file__), 'init.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Файл {sql_file} не найден!")
        sys.exit(1)
    
    print(f"📄 Чтение SQL файла: {sql_file}")
    execute_sql_from_file(conn, sql_file)
    
    # Закрываем соединение
    conn.close()
    print("🎉 Инициализация базы данных завершена!")
    print("📊 Проверьте доступность API: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
