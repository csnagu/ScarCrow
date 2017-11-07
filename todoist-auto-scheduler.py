import os

# To use pit with Python 3.X, reffer to below.
# https://falog.net/python3-pit/
from pit import Pit

import todoist

import urllib.request
from bs4 import BeautifulSoup

import sqlite3

# This function add some tasks to your todoist.
# The default added task's date is the next day.  
# tasks get from parse_tasks_from_blog
# Please use Email and Password from your todoist account 
def add_task_to_todoist(tasks, Email, Password):
    # Login to your account
    api = todoist.TodoistAPI()
    api.user.login(Email, Password)
    api.sync()

    # Add tasks
    # Default project_id='' is "inbox" project
    for task_name in tasks:
        api.items.add(content=task_name, project_id='', date_string='tomorrow')
    api.commit()

# This function parse tasks from hatenablog.
# targetURL is http://~~~~ (your blog URL)
# keyword and mark
# (e.g.) keyword is 'What to do tomorro', mark is '-', in the blog article
#       ~~~
#       What to do tomorrow
#        - task1
#        - task2 ...
# (e.g.) keyword is '明日やること', mark is '・', in the blog article
#       ~~~
#       明日やること
#       ・やること１
#       ・やること２ ...
def parse_tasks_from_blog (targetURL, keyword, mark):
    html = urllib.request.urlopen(targetURL).read()
    soup = BeautifulSoup(html, 'html.parser')

    # In hatenablog, the body of latest article is tagged with 'entry-content'
    main_content = soup.find(class_='entry-content')
    body_text = main_content.get_text().split(mark)

    tasks = []
    flag = False
    # tasks variable contains the tasks of next day.
    for target_task in body_text:
        if (flag == True):
            tasks.append(target_task.strip().replace('　', ' '))
        if ('明日やること' in target_task):
            flag = True
    return tasks        

if __name__ == '__main__':
    if (not os.environ.get('EDITOR')):
        os.environ['EDITOR'] = 'vi'

    User_info = Pit.get('todoist', {'require': {'Email':'your todoist\'s email', 'Password':'your todoist\'s password', 'Website':'your website url'}})

    keyword = '明日やること'
    mark = '・'    
    tasks = parse_tasks_from_blog(User_info['Website'], keyword, mark)

    dbname = 'database.db'

    conn = sqlite3.connect(dbname)
    c = conn.cursor()

    # テーブルが存在すれば1を，存在しなければ0を返す
    exist_sql = "select count(*) from sqlite_master where type='table' and name='latest_task';"
    print (c.execute(exist_sql).fetchone())
    if (c.execute(exist_sql).fetchone()[0] == 0):
        # 初回起動時には最新記事のタスクをdatabase.dbに登録する
        create_table = '''create table if not exists latest_task (  id int, 
                                                                    task_name varchar(64) )'''
        c.execute(create_table)

        insert_sql = 'insert into latest_task (id, task_name) values (?,?)'
        id_num = 1
        for task_name in tasks:
            blog_task = (id_num, task_name)
            c.execute(insert_sql, blog_task)
            id_num += 1
        conn.commit()

        for row in (c.execute('select * from latest_task')):
            print (row)

        add_task_to_todoist(tasks, User_info['Email'], User_info['Password'])
    else:
        # 2回目以降の起動時にはlatest_taskと比較してブログ更新の有無を判断する
        create_table = '''create table if not exists today (id int, task_name varchar(64))'''
        c.execute(create_table)

        insert_sql = 'insert into today (id, task_name) values (?,?)'
        id_num = 1
        for task_name in tasks:
            blog_task = (id_num, task_name)
            c.execute(insert_sql, blog_task)
            id_num += 1
        conn.commit()

        for row in (c.execute('select * from latest_task')):
            print (row)

        print()
        for row in (c.execute('select * from today')):
            print (row)

        # 結合元のテーブルがタスクの全体集合になるとき，テーブルの完全一致が検出できないため，結合元を交換して２パターンの比較を行う
        compare_sql1 = 'select * from latest_task left outer join today on (latest_task.task_name = today.task_name) where today.task_name is null'
        compare_sql2 = 'select * from today left outer join latest_task on (today.task_name = latest_task.task_name) where latest_task.task_name is null'
        if (c.execute(compare_sql1).fetchone() == None and c.execute(compare_sql2).fetchone() == None) :
            # 前回の更新分との差分がNone，ブログが更新されていない場合
            pass
        else:
            add_task_to_todoist(tasks, User_info['Email'], User_info['Password'])
        
        # latest_taskテーブルを削除し，todayテーブルをlatest_taskテーブルにリネームする
        delete_sql = 'drop table latest_task'
        c.execute(delete_sql)
        rename_sql = 'alter table today rename to latest_task'
        c.execute(rename_sql)
        conn.commit()

    conn.close()

