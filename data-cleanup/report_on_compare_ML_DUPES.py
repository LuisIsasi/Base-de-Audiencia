"""
could_not_compare_newsletters 4
demo_vars_discrep 40328
dupe_email 363
lists_in_ml_not_st 220
lists_in_st_not_ml 276385
multiple_matching_sailthru_users 26
nls_in_ml_not_st 37
nls_in_st_not_ml 2450
no_sailthru_data_found 1004
products_discrep 78
source_signup_discrep 10121
split_profiles 93
total compared 455844
"""

import jq
import json
import multiprocessing
import logging
import datetime
import pickle
import sys
from pprint import pprint as p
import time

import diff_match_patch
import isodate
import rethinkdb as r

from pymaybe import maybe

import requests
from lxml import etree


def first_and_only(iterable):
    assert len(iterable) == 1, "List is not of length 1"
    return iterable[0]


"""
logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] %(message)s')  # [%(asctime)s] 
logger.handlers[0].setFormatter(formatter)
"""


OFFICIAL_NATURAL_LISTS = ['defense_one', 'defense_one_hybrid', 'defense_one_tentpole', 'gemg_publisher', 'govexec', 'govexec_hybrid', 'govexec_tentpole', 'nextgov', 'next_gov', 'next_gov_hybrid', 'nextgov_hybrid', 'nextgov_tentpole', 'optin_3rd_party', 'optin_research', 'route_fifty', 'route_fifty_hybrid', 'route_fifty_launch', 'route_fifty_tentpole']
OFFICIAL_NEWSLETTERS = ['archive_newsletter_homeland_security_week', 'archive_newsletter_management_agenda', 'archive_newsletter_management_matters', 'archive_newsletter_national_defense_week', 'archive_newsletter_on_politics', 'archive_newsletter_the_week_ahead', 'custom_newsletter_cost_and_performance_management', 'custom_newsletter_data_nation', 'custom_newsletter_federal_collaborator', 'custom_newsletter_federal_innovator', 'newsletter_cio_briefing', 'newsletter_d1_alert', 'newsletter_d1_dbrief', 'newsletter_d1_today', 'newsletter_excellence_in_government', 'newsletter_ge_alert', 'newsletter_ge_today', 'newsletter_ge_today_pm', 'newsletter_ng_alert', 'newsletter_ng_big_data', 'newsletter_ng_cloud', 'newsletter_ng_cybersecurity', 'newsletter_ng_defense_it', 'newsletter_ng_health_it', 'newsletter_ng_mobility', 'newsletter_ng_threatwatch', 'newsletter_ng_today', 'newsletter_open_season', 'newsletter_pay_and_benefits_watch', 'newsletter_research_and_insights', 'newsletter_retirement_planning', 'newsletter_rf_alert', 'newsletter_rf_today', 'newsletter_state_and_local', 'newsletter_wired_workplace', 'newsletter_workforce_week']


NEWSLETTER_RELATED_SUBSCRIPTIONS = {
    'newsletter_ge_alert': 'newsletter_ge_today',
    'newsletter_ng_alert': 'newsletter_ng_today',
    'newsletter_d1_alert': 'newsletter_d1_today',
    'newsletter_rf_alert': 'newsletter_rf_today',
}


def combine_submissions(submissions):
    combined = {}
    for s in submissions:
        combined.update(s)
    return combined


def prettify_json(json_str):
    import subprocess
    proc = subprocess.Popen('jq -S "."', stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    proc.stdin.write(json_str)
    proc.stdin.close()
    ret = proc.stdout.read()
    proc.stdout.close()
    return ret


def main():
    conn = r.connect("localhost", 28015, db="audb")

    with open(sys.argv[1], 'rb') as o:
        results = pickle.load(o)

    dupe_emails = set()

    for res in results:
        email, info = res.items()[0]
        if 'dupe_email' in info:
            #ml_doc = first_and_only(list(r.db('audb').table('users').get_all(email, index='email').run(conn)))
            #submissions = list(r.db('audb').table('submissions').order_by(index='pk').filter({'email': email.strip()}).run(conn))
            #composite_sub = combine_submissions(submissions)
            dupe_emails.add(email)

    for dupe in sorted(dupe_emails):

        ml_docs = [x for x in list(r.db('audb').table('users').filter(lambda user: user["email"].match(dupe)).run(conn)) if x['email'].strip() == dupe]
        ml_uuids = sorted([x['uuid'] for x in ml_docs])
        assert len(ml_uuids) > 1

        jsons = []
        jsons_uuids = []
        for uuid in ml_uuids:
            req = requests.get(
                'http://marklogic1.geprod.amc:9400/users/get.json',
                params={"uuid": uuid},
                auth=('acrewdson', '60ACCRETEDabstractions'),
            )
            user_json = req.json()
            j_uuid = user_json['uuid']
            del user_json['uuid']
            del user_json['create-user']
            [x.pop('_id') for x in user_json.get('sourceSignups', {}).get('sourceSignup', [])]
            jsons.append(prettify_json(unicode(json.dumps(user_json)).encode('utf-8')))
            jsons_uuids.append(j_uuid)

        if len(ml_uuids) == 2:
            dmp = diff_match_patch.diff_match_patch()
            json_diff_html = dmp.diff_prettyHtml(dmp.diff_main(*jsons))
            json_diff_html = json_diff_html.replace('&para;', '')
            print "<div class='container' style='display: flex; font-family: Consolas, fixed-width;'>"
            print "<div style='padding-right: 1em;'>" + "<h2>" + jsons_uuids[1] + "</h2><pre>" + jsons[1] + "</pre></div>"
            print "<div style='padding-right: 1em;'>" + "<h2>" + jsons_uuids[0] + "</h2><pre>" + jsons[0] + "</pre></div>"
            print "<div style='white-space: pre; font-size: 13px;'>" + json_diff_html + "</div>"
            print "</div>"
        else:
            print "<h2>more than two (no diff performed):</h2>"
            print "<div class='container' style='display: flex; font-family: Consolas, fixed-width;'>"
            for j in jsons:
                print "<div><pre>" + j + "</pre></div>"
            print "</div>"
        print "<hr/>"


if __name__ == "__main__":
    main()
