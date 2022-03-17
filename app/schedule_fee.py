import schedule
import time
import sqlite3 
from datetime import date
from wishlist_recurring import main as recurring_main
import configparser
import sys
sys.path.insert(1, './static/')
from static_html_loop import main as static_main
#deleteccron?
#create table if not exists.
#we can also pass it an array of values

def job():
    if date.today().day != 1:
        return
    config = configparser.ConfigParser()
    config.read('./db/wishlist.ini')
    #1st of every month
    con = sqlite3.connect('./db/recurring_fees.db')
    cur = con.cursor()
    create_fees_table = """ CREATE TABLE IF NOT EXISTS fees (
                                wish_id text PRIMARY KEY
                            ); """

    cur.execute(create_fees_table)
    cur.execute('SELECT * FROM fees')
    rows = cur.fetchall()
    if len(rows):
        for row in rows:
            recurring_main(row[0])
        static_main(config)

def schedule_main():
    #schedule.every(1).minutes.do(job)
    schedule.every().day.at("10:30").do(job)

    while 1:
        schedule.run_pending()
        time.sleep(1)
