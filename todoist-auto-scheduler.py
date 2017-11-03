#-*- coding:utf-8 -*-

# conf.py contains the Email, Password and Blog's url
# (e.g.) conf.py
#   EMAIL = 'example@your.email'
#   PASSWORD = 'YourPassword123'
#   TargetURL = 'http://example.com'
from conf import *

import todoist

import urllib.request
from bs4 import BeautifulSoup

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
    keyword = '明日やること'
    mark = '・'
    
    tasks = parse_tasks_from_blog(TargetURL, keyword, mark)
    add_task_to_todoist(tasks, EMAIL, PASSWORD)