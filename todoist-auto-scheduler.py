#-*- coding:utf-8 -*-

# TOKEN = 'api_token' in API_TOKEN.py
from conf import *

# todoist api
import todoist

# parser
import urllib.request
from bs4 import BeautifulSoup
import re

if __name__ == '__main__':
#    api = todoist.TodoistAPI(TOKEN)
    api = todoist.TodoistAPI()
    user = api.user.login(EMAIL, PASSWORD)
    print (user['full_name'])
    response = api.sync()
    for project in response['projects']:
        print(project['name'])


    url = TargetURL
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')

    main_content = soup.title.string

    print(main_content)