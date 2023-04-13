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

import multiprocessing
import logging
import datetime
import pickle
import sys
from pprint import pprint as p
import time

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


def main():
    conn = r.connect("localhost", 28015, db="audb")

    with open(sys.argv[1], 'rb') as o:
        results = pickle.load(o)

    for res in results:
        email, info = res.items()[0]
        if 'nls_in_ml_not_st' in info or 'lists_in_ml_not_st' in info:
            ml_doc = first_and_only(list(r.db('audb').table('users').get_all(email, index='email').run(conn)))

            submissions = list(r.db('audb').table('submissions').order_by(index='pk').filter({'email': email.strip()}).run(conn))
            for su in submissions:
                assert su['status'] == 'complete'
            composite_sub = combine_submissions(submissions)

            nls = info.get('nls_in_ml_not_st', [])

            for n in nls:
                assert composite_sub.get('newsletters_string', {}).get(n, None) not in (0, '0', False)
                found_date = None
                for sub in submissions:
                    nl_val = sub.get('newsletters_string', {}).get(n)
                    if nl_val and nl_val not in (0, '0', False):
                        found_date = sub['date_created']
                        break
                if not found_date and n in NEWSLETTER_RELATED_SUBSCRIPTIONS.keys():
                    found_date = None
                    for sub in submissions:
                        nl_val = sub.get('newsletters_string', {}).get(NEWSLETTER_RELATED_SUBSCRIPTIONS[n])
                        if nl_val and nl_val not in (0, '0', False):
                            found_date = sub['date_created']
                            break

                print email, n, (found_date if found_date else '[no date]')

            list_subs = maybe(ml_doc)['listSubscriptions']['listSubscription'].or_else(lambda: [])
            list_subs = list_subs if isinstance(list_subs, type([])) else [list_subs]

            lists_ = info.get('lists_in_ml_not_st', [])
            for ell in lists_:
                assert composite_sub.get('lists_string', {}).get(ell, None) not in (0, '0', False)
                print email, ell, first_and_only([x['signupDate'] for x in list_subs if x['list']['#text'] == ell])





if __name__ == "__main__":
    main()
