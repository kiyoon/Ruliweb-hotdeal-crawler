#!/usr/bin/env python3


# For command line usage, include the token and chat ids in advance in the script.
# If you want to use only the functions, there's no need to include this.
telegram_token = ""
telegram_chat_ids = [""]



import requests
import io
import argparse
def get_parser():
    parser = argparse.ArgumentParser(description="Send Telegram message",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--title", help="Title")
    parser.add_argument("--body", help="Body", required=True)
    return parser


def send_text(telegram_token, chat_id, text, parse_mode=None):
    telegram_request_url = "https://api.telegram.org/bot{0}/sendMessage".format(telegram_token)
    return requests.post(telegram_request_url, data={
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
        })

def send_text_with_title(telegram_token, chat_id, title, body):
    if title:
        text = '<b>' + title + '</b>\n\n' + body
        tg_request = send_text(telegram_token, chat_id, text, parse_mode = 'HTML')
        if not tg_request.ok:
            # If failed, try send normal text instead of HTML parsing
            text = title + '\n\n' + body
            tg_request = send_text(telegram_token, chat_id, text, parse_mode = None)
    else:
        text = body
        tg_request = send_text(telegram_token, chat_id, text, parse_mode = None)

    return tg_request


def _send_photo_bytes(telegram_token, chat_id, bytes_io):
    """Send photo in open() or io.BytesIO form.
    """
    url = "https://api.telegram.org/bot{}/sendPhoto".format(telegram_token);
    files = {'photo': bytes_io}
    data = {'chat_id' : chat_id}
    r= requests.post(url, files=files, data=data)
    return r


def send_photo(telegram_token, chat_id, img_path):
    photo = open(img_path, 'rb')
    return _send_photo_bytes(telegram_token, chat_id, photo)


def send_remote_photo(telegram_token, chat_id, img_url):
    remote_image = requests.get(img_url)
    photo = io.BytesIO(remote_image.content)
    photo.name = 'img.png'
    return _send_photo_bytes(telegram_token, chat_id, photo)


def send_matplotlib_fig(telegram_token, chat_id, fig):
    photo = io.BytesIO()
    fig.savefig(photo, format='png')
    photo.seek(0)       # to start reading from the beginning. (After writing, the cursor is at the end)
    photo.name = 'img.png'
    return _send_photo_bytes(telegram_token, chat_id, photo)


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()

    for chat_id in telegram_chat_ids:
        print(send_text_with_title(telegram_token, chat_id, args.title, args.body))