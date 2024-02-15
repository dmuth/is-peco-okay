

from datetime import datetime


def main(event, context):
    now = datetime.now()
    now_str = now.strftime("%d/%m/%Y %H:%M:%S")

    print("TEST", now_str)


