#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('sidecar/data/vproptrader.db')
cursor = conn.cursor()

cursor.execute("SELECT symbol, COUNT(*), MIN(timestamp), MAX(timestamp) FROM historical_bars GROUP BY symbol")
print('Symbol data:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} bars from {row[2]} to {row[3]}')

cursor.execute("SELECT * FROM historical_bars LIMIT 3")
print('\nSample bars:')
for row in cursor.fetchall():
    print(f'  {row}')

conn.close()
