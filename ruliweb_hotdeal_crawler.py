#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from itertools import compress
import sys, os
from configparser import ConfigParser

if __name__ == "__main__":
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    with open(os.path.join(__location__, "last_id.txt"),'r') as f:
        last_id = int(f.read().strip())
    # crawling id and title
    search_url = 'http://bbs.ruliweb.com/market/board/1020/list?page=1'
    read_url = 'http://bbs.ruliweb.com/market/board/1020/read/'
    search = requests.get(search_url)
    html = search.text
    soup = BeautifulSoup(html, 'html.parser')

    # announcement counting
#    search_res = soup.select('#board_list > div > div.board_main.theme_default > table > tbody > tr > td.subject > a')
    search_res = soup.select('#board_list > div > div.board_main.theme_default.theme_white > table > tbody > tr > td.subject > a')
    num_announcement = len(search_res)

    # id
    search_res = soup.select('#board_list > div > div.board_main.theme_default.theme_white > table > tbody > tr.table_body > td.id')
    id_list = []
    for res in search_res[num_announcement:]:
        id_list.append(res.text.strip())

#    search = requests.get(search_url)
#    html = search.text
#    soup = BeautifulSoup(html, 'html.parser')
    # title
    search_res = soup.select('#board_list > div > div.board_main.theme_default.theme_white > table > tbody > tr > td.subject > div > a')
    title_list = []
    for res in search_res:
        title_list.append(res.text)

    # filter not seen
    filt = list(map(lambda x: int(x[0]) > last_id, zip(id_list, title_list)))
    id_list = list(compress(id_list, filt))
    title_list = list(compress(title_list, filt))
#    print(id_list)
#    print(title_list)

    if not id_list:
        print("No new item to see")
        sys.exit()

    # import list to search
    with open(os.path.join(__location__, "keywords.txt"),'r',encoding='utf8') as f:
        keywords = list(filter(None, f.read().splitlines()))
#    print(keywords)

    deal_titles = []
    deal_urls = []

    for (board_id, board_title) in zip(id_list, title_list):
        if any (word.lower() in board_title.lower() for word in keywords):
            deal_titles.append(board_title)
            deal_urls.append(read_url + board_id)

    print(deal_titles)

    config = ConfigParser()
    config.read(os.path.join(__location__, "key.ini"))
    mailgun_enable = config['Mailgun']['enable'] == 'True'
    mailgun_key = config['Mailgun']['key']
    mailgun_sandbox = config['Mailgun']['sandbox']
    mailgun_recipient = config['Mailgun']['recipient']
    mailgun_request_url = 'https://api.mailgun.net/v3/{0}/messages'.format(mailgun_sandbox)

    telegram_enable = config['Telegram']['enable'] == 'True'
    telegram_token = config['Telegram']['token']
    telegram_chat_ids = config['Telegram']['chat_ids'].split(",")
    telegram_request_url = 'https://api.telegram.org/bot{0}/sendMessage'.format(telegram_token)
    def telegram_post(telegram_request_url, chat_id, text, parse_mode=None):
        return requests.post(telegram_request_url, data={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
            })

    for deal_title, deal_url in zip(deal_titles, deal_urls):
        # item URL
        search = requests.get(deal_url)
        html = search.text
        soup = BeautifulSoup(html, 'html.parser')
        search_res = soup.select('#board_read > div > div.board_main > div.board_main_view > div.source_url > a')
        try:
            source_url = search_res[0].text.strip()
        except IndexError:
            source_url = ""

        # board content
        search_res = soup.select('#board_read > div > div.board_main > div.board_main_view > div.view_content')
        content = search_res[0].text.strip()

        # likes
        search_res = soup.select('#board_read > div > div.board_main > div.board_main_view > div.row > div > div > div.like > span')
        likes = search_res[0].text.strip()
    
        # dislikes
#        search_res = soup.select('#board_read > div > div.board_main > div.board_main_view > div.row > div > div > div.dislike > span')
#        dislikes = search_res[0].text.strip()

        if mailgun_enable:
            mail_title = 'Ruliweb Hotdeal: ' + deal_title
    #        mail_body = 'Board URL: %s\nLikes: %s\nDislikes: %s\n\nSource URL: %s\n\n%s' % (deal_url, likes, dislikes, source_url, content)
            mail_body = 'Board URL: %s\nLikes: %s\n\nSource URL: %s\n\n%s' % (deal_url, likes, source_url, content)
            mail_request = requests.post(mailgun_request_url, auth=('api', mailgun_key), data={
                'from': 'fcserver <fcserver-noreply@kiyoon.kim>',
                'to': mailgun_recipient,
                'subject': mail_title,
                'text': mail_body
                })

        if telegram_enable:
            for chat_id in telegram_chat_ids:
                tg_title = '<b>Ruliweb Hotdeal: ' + deal_title + '</b>'
        #        tg_body = 'Board URL: %s\nLikes: %s\nDislikes: %s\n\nSource URL: %s\n\n%s' % (deal_url, likes, dislikes, source_url, content)
                tg_body = 'Board URL: %s\nLikes: %s\n\nSource URL: %s\n\n%s' % (deal_url, likes, source_url, content)
                tg_request = telegram_post(telegram_request_url, chat_id, tg_title + '\n\n' + tg_body, parse_mode = 'HTML')
                if not tg_request.ok:
                    # If failed, try send normal text instead of HTML parsing
                    tg_title = 'Ruliweb Hotdeal: ' + deal_title
                    tg_request = telegram_post(telegram_request_url, chat_id, tg_title + '\n\n' + tg_body, parse_mode = None)



    # update last id that is seen
    with open(os.path.join(__location__, "last_id.txt"),'w') as f:
        f.write(id_list[0])
