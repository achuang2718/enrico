import json
import slack
import importlib.resources as pkg_resources

from .. import configs as c 

with pkg_resources.path(c, "fermi1bot_config.json") as json_config_path:
    with open(json_config_path) as json_config_file:
        data = json.load(json_config_file)
        token = data['token']

client = slack.WebClient(token=token)


def post_message(message):
    try:
        response = client.chat_postMessage(
            channel='#enrico_notifications',
            text=message)
        return response
    except:
        print('enrico_bot error')
        pass


def post_image(image_filepath):
    try:
        response = client.files_upload(
            file=image_filepath,
            channels='#enrico_notifications'
        )
        return response
    except:
        print('enrico_bot error')
        pass