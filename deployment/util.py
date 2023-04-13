
import requests

from fabric import api as fab


GREEN_APPLE = u'\U0001f34f'

RED_EXCLAMATION = u'\U00002757'

DEV_FIGLET = """
    .___
  __| _/_______  __
 / __ |/ __ \  \/ /
/ /_/ \  ___/\   /
\____ |\___  >\_/
     \/    \/      """

PROD_FIGLET = """
                        .___
_____________  ____   __| _/
\____ \_  __ \/  _ \ / __ |
|  |_> >  | \(  <_> ) /_/ |
|   __/|__|   \____/\____ |
|__|                     \/ """


def slack(text):
    channel = "#release" if fab.env.prod else "#developer-announce"
    data = {
        "text": "Audb : " + "`" + fab.env.user + " =>` " + text,
        "channel": channel,
    }
    WEBHOOK = "https://hooks.slack.com/services/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"
    requests.post(WEBHOOK, json=data)
