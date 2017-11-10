import os

import sqlite3

import urllib.request
from bs4 import BeautifulSoup

# To use pit with Python 3.X, reffer to below.
# https://falog.net/python3-pit/
from pit import Pit
import todoist

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
def parse_tasks_from_blog (targetURL, keyword, mark, tag_class):
    html = urllib.request.urlopen(targetURL).read()
    soup = BeautifulSoup(html, 'html.parser')

    # In hatenablog, the body of latest article is tagged with 'entry-content'
    main_content = soup.find(class_ = tag_class)
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

def rename_table(source_table, new_table):
    delete_sql = 'drop table ' + new_table
    c.execute(delete_sql)
    rename_sql = 'alter table ' + source_table + ' rename to ' + new_table
    c.execute(rename_sql)
    conn.commit()

def add_task_to_database(table_name, tasks):
    create_table = '''create table if not exists ''' + table_name + ''' (   id int, 
                                                                            task_name varchar(64) )'''
    c.execute(create_table)

    insert_sql = 'insert into ' + table_name + ' (id, task_name) values (?,?)'
    id_num = 1
    for task_name in tasks:
        blog_task = (id_num, task_name)
        c.execute(insert_sql, blog_task)
        id_num += 1
    conn.commit()

def compare_tables(table1, table2):
    # table1とtable2の内容が一致している場合はTrueを返す
    # 結合元のテーブルがタスクの全体集合になるとき，テーブルの内容一致が検出できないため，結合元を交換して２パターンの比較を行う
    compare_sql1 = 'select * from ' + table1 + ' left outer join ' + table2 + ' on ( ' + table1 + '.task_name = ' + table2 + '.task_name) where ' + table2 + '.task_name is null'
    compare_sql2 = 'select * from ' + table2 + ' left outer join ' + table1 + ' on ( ' + table2 + '.task_name = ' + table1 + '.task_name) where ' + table1 + '.task_name is null'
    comparison_result1 = c.execute(compare_sql1).fetchone()
    comparison_result2 = c.execute(compare_sql2).fetchone()

    comparison_result = comparison_result1 == None and comparison_result2 == None
    return comparison_result

def is_empty_table(table_name):
    # テーブルが存在すれば1を，存在しなければ0を返す
    exist_sql = "select count(*) from sqlite_master where type='table' and name='" + table_name + "';"
    result = c.execute(exist_sql).fetchone()[0]

    return result

if __name__ == '__main__':
    if (not os.environ.get('EDITOR')):
        os.environ['EDITOR'] = 'vi'

    User_info = Pit.get('todoist', {'require': {'Email':'your todoist\'s email', 'Password':'your todoist\'s password', 'Website':'your website url'}})
    keyword = '明日やること'
    mark = '・'
    tag_class = 'entry-content'
    tasks = parse_tasks_from_blog(User_info['Website'], keyword, mark, tag_class)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if (is_empty_table('latest_task') == 0):
        # 初回起動時には最新記事のタスクをdatabase.dbに登録する
        add_task_to_database('latest_task', tasks)
        add_task_to_todoist(tasks, User_info['Email'], User_info['Password'])
    else:
        # 2回目以降の起動時にはlatest_taskと比較してブログ更新の有無を判断する
        add_task_to_database('today', tasks)

        if (compare_tables('latest_task', 'today')):
            pass
        else:
            add_task_to_todoist(tasks, User_info['Email'], User_info['Password'])
        
        # latest_taskテーブルを削除し，todayテーブルをlatest_taskテーブルにリネームする
        rename_table('today', 'latest_task')

    conn.close()


