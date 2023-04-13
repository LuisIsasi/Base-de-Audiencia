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


logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] %(message)s')  # [%(asctime)s] 
logger.handlers[0].setFormatter(formatter)


THREADS = 12

OFFICIAL_NATURAL_LISTS = ['defense_one', 'defense_one_hybrid', 'defense_one_tentpole', 'gemg', 'gemg_publisher', 'govexec', 'govexec_hybrid', 'govexec_tentpole', 'nextgov', 'next_gov', 'next_gov_hybrid', 'nextgov_hybrid', 'nextgov_tentpole', 'optin_3rd_party', 'optin_research', 'route_fifty', 'route_fifty_hybrid', 'route_fifty_launch', 'route_fifty_tentpole']
OFFICIAL_NEWSLETTERS = ['archive_newsletter_homeland_security_week', 'archive_newsletter_management_agenda', 'archive_newsletter_management_matters', 'archive_newsletter_national_defense_week', 'archive_newsletter_on_politics', 'archive_newsletter_the_week_ahead', 'custom_newsletter_cost_and_performance_management', 'custom_newsletter_data_nation', 'custom_newsletter_federal_collaborator', 'custom_newsletter_federal_innovator', 'newsletter_cio_briefing', 'newsletter_d1_alert', 'newsletter_d1_dbrief', 'newsletter_d1_today', 'newsletter_excellence_in_government', 'newsletter_ge_alert', 'newsletter_ge_today', 'newsletter_ge_today_pm', 'newsletter_ng_alert', 'newsletter_ng_big_data', 'newsletter_ng_cloud', 'newsletter_ng_cybersecurity', 'newsletter_ng_defense_it', 'newsletter_ng_health_it', 'newsletter_ng_mobility', 'newsletter_ng_threatwatch', 'newsletter_ng_today', 'newsletter_open_season', 'newsletter_pay_and_benefits_watch', 'newsletter_research_and_insights', 'newsletter_retirement_planning', 'newsletter_rf_alert', 'newsletter_rf_today', 'newsletter_state_and_local', 'newsletter_wired_workplace', 'newsletter_workforce_week']


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


_product_lookup_request = requests.get(
    'http://marklogic1.geprod.amc:9400/products/list.xml',
    params={"rows": 1000},
    auth=('acrewdson', '60ACCRETEDabstractions'),
)
_product_lookup_request.raise_for_status()

PRODUCT_LOOKUP = etree.fromstring(_product_lookup_request.text)

PRODUCT_CONSUMED_VERBS = {
    'app': 'used',
    'asset': 'downloaded',
    'event': 'attended',
    'questionnaire': 'completed'
}


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def report(results):

    all_keys = set()
    for i in results:
        [all_keys.add(x) for x in i.items()[0][1]]

    aggregates = {x:0 for x in all_keys}

    for res in results:
        email, info = res.items()[0]
        for k in all_keys:
            if info.get(k):
                aggregates[k] += 1

    print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
    for k in sorted(aggregates.keys()):
        print k, aggregates[k]
    print 'total compared', len(results)
    print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def product_uuid_to_slug(uuid):
    return PRODUCT_LOOKUP.xpath(
        '//p:product/p:uuid[normalize-space(.) = "{}"]/../p:nameSlug'.format(uuid),
        namespaces={'p': "http://www.govexec.com/product"}
    )[0].text.strip()


def product_slug_to_topics(slug):
    return sorted([x.text.strip() for x in PRODUCT_LOOKUP.xpath(
        '//p:product/p:nameSlug[. = "{}"]/../p:topics/p:topic'.format(slug),
        namespaces={'p': "http://www.govexec.com/product"}
    )])


def product_slug_to_type(slug):
    return PRODUCT_LOOKUP.xpath(
        '//p:product/p:nameSlug[. = "{}"]/../p:type'.format(slug),
        namespaces={'p': "http://www.govexec.com/product"}
    )[0].text.strip()


def add_ml_product_info(ml, d):
    d['products_info'] = {}

    products_consumed_base = maybe(ml)['productsConsumed']['productConsumed'].or_else(lambda: []) or []
    products_consumed_base = products_consumed_base if isinstance(products_consumed_base, type([])) else [products_consumed_base]
    products_consumed = [x['product'] for x in products_consumed_base]
    products_consumed = sorted([product_uuid_to_slug(x['@ref-uuid']) for x in products_consumed])

    products_registered_base = maybe(ml)['productsRegistered']['productRegistered'].or_else(lambda: []) or []
    products_registered_base = products_registered_base if isinstance(products_registered_base, type([])) else [products_registered_base]
    products_registered = [x['product'] for x in products_registered_base]
    products_registered = sorted([product_uuid_to_slug(x['@ref-uuid']) for x in products_registered])

    d['products_info']['product_topics'] = []
    for x in (products_consumed + products_registered):
        for pt in product_slug_to_topics(x):
            if pt not in d['products_info']['product_topics']:
                d['products_info']['product_topics'].append(pt)
    d['products_info']['product_topics'] = sorted(d['products_info']['product_topics']) if d['products_info']['product_topics'] else 0

    for product_type in ('app', 'asset', 'event', 'questionnaire'):
        d['products_info']["{}s_registered".format(product_type)] = sorted(list(set(
            [x for x in products_registered if product_slug_to_type(x) == product_type])))
        d['products_info']["{}s_registered".format(product_type)] = d['products_info']["{}s_registered".format(product_type)] if d['products_info']["{}s_registered".format(product_type)] else 0
        d['products_info']["{}s_{}".format(product_type, PRODUCT_CONSUMED_VERBS[product_type])] = sorted(list(set(
            [x for x in products_consumed if product_slug_to_type(x) == product_type])))
        d['products_info']["{}s_{}".format(product_type, PRODUCT_CONSUMED_VERBS[product_type])] = d['products_info']["{}s_{}".format(product_type, PRODUCT_CONSUMED_VERBS[product_type])] if d['products_info']["{}s_{}".format(product_type, PRODUCT_CONSUMED_VERBS[product_type])] else 0

    for product_action_consumed in products_consumed_base:
        p_slug = product_uuid_to_slug(product_action_consumed['product']['@ref-uuid'])
        p_type = product_slug_to_type(p_slug)
        p_key = "{}_{}_{}_time".format(p_type, p_slug, PRODUCT_CONSUMED_VERBS[p_type])
        if product_action_consumed.get('details', None) is not None:
            raise Exception('unexpected details for product action')
        d['products_info'][p_key] = int(time.mktime(isodate.parse_datetime(product_action_consumed['consumedDatetime']).timetuple()))

    for product_action_reg in products_registered_base:
        p_slug = product_uuid_to_slug(product_action_reg['product']['@ref-uuid'])
        p_type = product_slug_to_type(p_slug)
        p_key = "{}_{}_{}_time".format(p_type, p_slug, 'registered')
        if product_action_reg.get('details', None) is not None:
            raise Exception('unexpected details for product action')
        d['products_info'][p_key] = int(time.mktime(isodate.parse_datetime(product_action_reg['registrationDatetime']).timetuple()))


# use log level ERROR here
def extract_ml_info(ml):
    ret = {}

    ret['sailthru_id'] = ml['sailthruId'].strip() if ml.get('sailthruId') else None

    ml_listsub = maybe(ml)['listSubscriptions']['listSubscription'].or_else(lambda: [])
    ml_listsub = ml_listsub if isinstance(ml_listsub, type([])) else [ml_listsub]
    ret['lists'] = sorted([x['list']['#text'].strip() for x in ml_listsub if x['optedOut'] == "false"])

    ml_nlsubs = maybe(ml)['subscriptions']['subscription'].or_else(lambda: [])
    ml_nlsubs = ml_nlsubs if isinstance(ml_nlsubs, type([])) else [ml_nlsubs]
    ret['newsletters'] = sorted([x['list']['#text'].strip() for x in ml_nlsubs if x['enabled'] == "1"])

    add_ml_product_info(ml, ret)

    return ret


# use log level ERROR here
def extract_st_info(st):
    ret = {}

    st_vars = st.get('vars', {}) or {}

    ret['sailthru_id'] = st['sid'].strip()
    ret['lists'] = sorted([x for x in st['lists'].keys() if x in OFFICIAL_NATURAL_LISTS]) if st['lists'] else []
    try:
        ret['newsletters'] = [x for x in OFFICIAL_NEWSLETTERS if int(st_vars.get(x, "0") or 0)]
    except:
        ret['newsletters'] = None

    ret['st_vars'] = st_vars

    return ret


def demo_var_discrep(ml, st):
    mappings = {
        'address1': 'postal_address',
        'address2': 'postal_address2',
        'agencyDepartment': 'agency_department',
        'appInterestRouteFifty': 'app_interest_route_fifty',
        'birthDate': 'birth_date',
        'city': 'postal_city',
        'companySize': 'company_size',
        'country': 'country',
        'educationLevel': 'education_level',
        'employer': 'employer',
        'fax': 'fax',
        'firstName': 'first_name',
        'gender': 'gender',
        'gradeRank': 'grade_rank',
        'homePhone': 'home_phone',
        'income': 'income',
        'industry': 'industry',
        'jobFunction': 'job_function',
        'jobSector': 'job_sector',
        'jobSectorType': 'job_sector_type',
        'jobTitle': 'job_title',
        'lastName': 'last_name',
        'locale': 'locale',
        'marital': 'marital',
        'mobilePhone': 'mobile_phone',
        'postalCode': 'postal_code',
        'procurementArea': 'procurement_area',
        'procurementIntent': 'procurement_intent',
        'procurementLevel': 'procurement_level',
        'procurementRole': 'procurement_role',
        'state': 'postal_state',
        'timezone': 'timezone',
        'workPhone': 'phone',
    }

    st_vars = st.get('vars', {}) or {}

    discrep = False

    for ml_var, st_var in mappings.items():
        ml_value = ml.get(ml_var, None) or None
        ml_value = ml_value.strip() if ml_value else None
        ml_value = ml_value if ml_value else None

        st_value = st_vars.get(st_var, None) or None
        if st_value:
            if isinstance(st_value, type(int())):
                st_value = unicode(st_value)
            else:
                if not st_value.strip():
                    st_value = None
                else:
                    st_value = st_value.strip()

        if ml_value != st_value:
            discrep = True
            logger.error("%s / %s, %s, %s", ml['email'], ml_var, ml_value, st_value)

    if ml.get('firstName') and ml.get('lastName'):
        ml_concat_name = ' '.join([ml['firstName'], ml['lastName']])
        if st_vars.get('name') != ml_concat_name:
            logger.error("%s, %s, %s, %s", ml['email'], 'name', ml_concat_name, st_vars.get('name'))
            discrep = True

    ml_proc_sub = ml.get('procurementSubject', []) or []
    ml_proc_sub = ml_proc_sub if isinstance(ml_proc_sub, type(list())) else [ml_proc_sub]
    ml_proc_sub = ','.join(ml_proc_sub)

    st_proc_sub = st_vars.get('procurement_subject', "") or ""

    if ml_proc_sub.strip() != st_proc_sub.strip():
        logger.error("%s, %s, %s, %s", ml['email'], 'procurementSubject', ml_proc_sub, st_proc_sub)
        discrep = True

    return discrep


def source_signup_discrep(ml, st):
    discrep = False
    st_vars = st.get('vars', {}) or {}

    st_source = st_vars.get("source", None) or None
    st_source = st_source.strip() if st_source else None
    st_source = st_source if st_source else None

    ml_source = ml.get("sourceSignups", {}) or {}
    ml_source = ml_source.get('sourceSignup', []) or []
    ml_source = ml_source if isinstance(ml_source, type([])) else [ml_source]

    final_ml_source = ml_source[0]['source'] if ml_source else None
    final_ml_source = final_ml_source.strip() if final_ml_source else None

    if st_source != final_ml_source:
        logger.error("%s / source signup mismatch / %s / %s", ml['email'], final_ml_source, st_source)
        discrep = True

    st_ssdate = st_vars.get('source_signup_date', None) or None
    st_ssdate = st_ssdate.strip() if st_ssdate else None
    parsed_st_ssdate = datetime.datetime.strptime(st_ssdate, "%Y-%m-%d %H:%M") if st_ssdate else None

    ml_ssdate = ml_source[0]['date'] if ml_source else None
    ml_ssdate = ml_ssdate.split('.')[0] if ml_ssdate else None
    ml_ssdate = ":".join(ml_ssdate.split(':')[:-1]) if ml_ssdate and len(ml_ssdate.split(':')) == 3 else ml_ssdate
    parsed_ml_ssdate = isodate.parse_datetime(ml_ssdate) if ml_ssdate else None

    if parsed_ml_ssdate != parsed_st_ssdate:
        ssdate_discrep = False
        if parsed_ml_ssdate and parsed_st_ssdate:
            # account for some weirdnesses -- rounding (b/c ST does not store seconds)?
            if abs((parsed_ml_ssdate - parsed_st_ssdate).total_seconds()) > 90:
                discrep = True
                ssdate_discrep = True
        else:
            discrep = True
            ssdate_discrep = True
        if ssdate_discrep:
            logger.error("%s source signup date / %s / %s", ml['email'], unicode(parsed_ml_ssdate), unicode(parsed_st_ssdate))

    return discrep


# use log level ERROR here
def compare(email, ml, st):
    mle = extract_ml_info(ml)
    ste = extract_st_info(st)

    # split profiles -- so we do not compare, because we can't really
    if mle['sailthru_id'] and mle['sailthru_id'] != ste['sailthru_id']:
        msg = '{} / Sailthru ID discrepancy (and no further comparison) / ML: {} / ST: {}'.format(email, mle['sailthru_id'], ste['sailthru_id'])
        logger.error(msg)
        return {email: {'split_profiles': True}}

    ret = {email: {}}

    # natural lists
    if mle['lists'] != ste['lists']:
        lists_in_ml_not_in_st = [x for x in mle['lists'] if x not in ste['lists']]
        lists_in_st_not_in_ml = [x for x in ste['lists'] if x not in mle['lists']]
        if lists_in_ml_not_in_st:
            msg = "{} / lists in ml not st: {}".format(email, unicode(lists_in_ml_not_in_st))
            logger.error(msg)
            ret[email]['lists_in_ml_not_st'] = lists_in_ml_not_in_st
        if lists_in_st_not_in_ml:
            msg = "{} / lists in st not ml: {}".format(email, unicode(lists_in_st_not_in_ml))
            logger.error(msg)
            ret[email]['lists_in_st_not_ml'] = lists_in_st_not_in_ml

    # newsletters
    if ste['newsletters'] is None:
        msg = '{} / skipping newsletters comparison'.format(email)
        logger.error(msg)
        ret[email]['could_not_compare_newsletters'] = True
    else:
        if mle['newsletters'] != ste['newsletters']:
            nls_in_ml_not_in_st = [x for x in mle['newsletters'] if x not in ste['newsletters']]
            nls_in_st_not_in_ml = [x for x in ste['newsletters'] if x not in mle['newsletters']]
            if nls_in_ml_not_in_st:
                msg = "{} / newsletters in ml not st: {}".format(email, unicode(nls_in_ml_not_in_st))
                logger.error(msg)
                ret[email]['nls_in_ml_not_st'] = nls_in_ml_not_in_st
            if nls_in_st_not_in_ml:
                msg = "{} / newsletters in st not ml: {}".format(email, unicode(nls_in_st_not_in_ml))
                logger.error(msg)
                ret[email]['nls_in_st_not_ml'] = nls_in_st_not_in_ml

    # demographic vars
    ret[email]['demo_vars_discrep'] = demo_var_discrep(ml, st)

    # source signups
    ret[email]['source_signup_discrep'] = source_signup_discrep(ml, st)

    prod_agg_vars = ('product_topics', 'apps_registered', 'questionnaires_completed', 'assets_downloaded', 'events_registered', 'questionnaires_registered', 'events_attended', 'apps_used', 'assets_registered')
    for prod_var, prod_var_val in mle['products_info'].items():
        st_prod_var = ste['st_vars'].get(prod_var)
        if (prod_var in prod_agg_vars) and not st_prod_var:
            st_prod_var = 0
        if prod_var_val != st_prod_var:
            logger.error("%s / product var discrep: %s / %s / %s", email, prod_var, prod_var_val, ste['st_vars'].get(prod_var))
            ret[email]['products_discrep'] = True

    return ret


# use log level WARNING here
def compare_users(email):
    c = r.connect("localhost", 28015, db="audb")

    ml_user = list(r.table("users").get_all(email, index="email").run(c))
    try:
        assert len(ml_user) == 1
    except:
        assert len(ml_user) > 1
        logger.warning('%s / skipping dupe ml email', email)
        return {email: {'dupe_email': True}}

    ml_user = ml_user[0]
    st_user = list(r.table("sailthru").get_all(email, index="email").run(c))

    if not len(st_user):
        logger.warning('%s / could not find ST data -- cannot compare', email)
        ret = {email: {'no_sailthru_data_found': True}}
    elif len(st_user) > 1:
        logger.warning("%s / got more than one ST doc for user, cannot compare", email)
        ret = {email: {'multiple_matching_sailthru_users': True}}
    else:
        ret = compare(email, ml_user, st_user[0])

    c.close()
    return ret


# use log level DEBUG here
def main():
    conn = r.connect("localhost", 28015, db="audb")

    logger.debug('getting ml emails')
    ml_emails = sorted(
        [x['email'] for x in list(r.table("users").pluck('email').run(conn))
        if x['email'] and not x['email'].isdigit()]
    )
    logger.debug('got %s emails', unicode(len(ml_emails)))
    conn.close()

    if [x for x in sys.argv if x.startswith('limit-')]:
        ml_emails = ml_emails[0:int([x for x in sys.argv if x.startswith('limit-')][0].split('-')[-1])]

    if 'multi' not in sys.argv:
        results = []
        for e in ml_emails:
            results.append(compare_users(e))
    else:
        pool = multiprocessing.Pool(processes=THREADS)
        map_result = pool.map_async(compare_users, ml_emails)
        map_result.wait()
        results = map_result.get()
        pool.close()

    pickle_filename = datetime.datetime.now().strftime("st-compare-%d-%b-%Y-%H-%M-%S").lower() + '.pickle'
    logger.debug('pickling results to %s', pickle_filename)
    with open(pickle_filename, 'wb') as pickle_outfile:
        pickle.dump(results, pickle_outfile)

    report(results)


if __name__ == "__main__":
    main()
