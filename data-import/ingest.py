# [SublimeLinter pylint-@python:2]

import multiprocessing
import logging
import os
import sys
import requests
import StringIO

from lxml import etree


"""
     STEPS BEFORE RUNNING THIS:

  0  hard-code PRODUCT_LOOKUP so that we do not need to query marklogic for user import

  1  get a new dump of the user xml data using mlcp (see README)

  2  make sure the 'target_base_url' is pointing to the right host

  3  make sure you have the right auth token in the 'api_req_headers' config setting

  4  make sure all the marklogic endpoints are pointing to the right marklogic host

  5  grab the latest set of 'custom' UserVars from the production db by running this query

        SELECT `marklogic_name` FROM `marklogic_uservar` WHERE `var_type` = 'custom'

     and then use those values to update the CUSTOM_VARS_TO_CREATE list below
"""


CONFIG = {
    'threads': 8,

    'user_xml_dir': '/Users/acrewdson/ml_prod_dump/FINAL_14_april/users',

    'target_base_url': 'https://audb.govexec.com',
    'api_req_headers': {'Authorization': 'Token 398536e6afd037b8efb37fec56f2d8bc28881800'},

    'audienceusers_endpoint': '/api/audience-users',
    'lists_endpoint': '/api/lists',
    'products_endpoint': '/api/products',
    'product_topics_endpoint': '/api/product-topics',
    'product_subtypes_endpoint': '/api/product-subtypes',
    'vars_endpoint': '/api/vars',

    'marklogic_lists_endpoint': 'http://marklogic1.geprod.amc:9400/lists/list.xml',
    'marklogic_newsletters_endpoint': 'http://marklogic1.geprod.amc:9400/newsletters/list.xml',
    'marklogic_newsletterlistsignups_endpoint': 'http://marklogic1.geprod.amc:9400/newsletterListSignups/list.xml',
    'marklogic_products_endpoint': 'http://marklogic1.geprod.amc:9400/products/list.xml',
    'marklogic_product_subtypes_endpoint': 'http://marklogic1.geprod.amc:9400/productSubtypes/list.xml',
    'marklogic_product_topics_endpoint': 'http://marklogic1.geprod.amc:9400/productTopics/list.xml',
    'marklogic_users_endpoint': 'http://marklogic1.geprod.amc:9400/users/get.xml',

    'marklogic_http_credentials': ('acrewdson', '60ACCRETEDabstractions')  # it's ok, it's only my MarkLogic password
}


assert os.path.isdir(CONFIG['user_xml_dir'])
assert os.listdir(CONFIG['user_xml_dir'])


logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s/%(processName)s] [%(asctime)s] %(message)s')
logger.handlers[0].setFormatter(formatter)



USER_NAMESPACE = {'u': "http://www.govexec.com/user"}
LIST_NAMESPACE = {'l': "http://www.govexec.com"}
PRODUCT_NAMESPACE = {'p': "http://www.govexec.com/product"}


demographic_var_names = (
    'firstName',
    'lastName',
    'address1',
    'address2',
    'city',
    'state',
    'postalCode',
    'country',
    'locale',
    'workPhone',
    'homePhone',
    'mobilePhone',
    'fax',
    'timezone',
    'gender',
    'birthDate',
    'marital',
    'income',
    'educationLevel',
    'industry',
    'jobTitle',
    'jobFunction',
    'jobSector',
    'jobSectorType',
    'employer',
    'companySize',
    'agencyDepartment',
    'gradeRank',
    'procurementSubject',
    'procurementLevel',
    'procurementArea',
    'procurementRole',
    'procurementIntent',
    'appInterestRouteFifty',
)

var_name_transform_mapping = {
    'address1': 'postal_address',
    'address2': 'postal_address2',
    'agencyDepartment': 'agency_department',
    'appInterestRouteFifty': 'rf_app_interest',
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
    'procurementSubject': 'procurement_subject',
    'state': 'postal_state',
    'timezone': 'timezone',
    'workPhone': 'phone',
}


CUSTOM_VARS_TO_CREATE = [
    'address_NA',
    'city_NA',
    'custom_companyname',
    'download_date',
    'email_verification',
    'phone_verification',
    'zipcode_NA',
    'zipcode_verification',
    'custom_country'
]


LEGACY_VARS_TO_CREATE = ['legacy_company', 'legacy_topicalInterest', 'legacy_otherOmedaIds']


"""
_product_lookup_request = requests.get(
    CONFIG['marklogic_products_endpoint'],
    params={"rows": 1000},
    auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1]),
)
_product_lookup_request.raise_for_status()
"""

PRODUCT_LOOKUP = etree.parse('products_lookup.xml')



EXTRA_SUBSCRIPTION_TRIGGERS_TO_CREATE = {
    'newsletter_ge_today': ['newsletter_ge_alert',],
    'newsletter_ng_today': ['newsletter_ng_alert',],
    'newsletter_d1_today': ['newsletter_d1_alert',],
    'newsletter_rf_today': ['newsletter_rf_alert',],
}


def extract_element(elem_name, doc, optional=False):
    nodes = doc.xpath('//u:{}'.format(elem_name), namespaces=USER_NAMESPACE)
    if not optional:
        assert len(nodes) == 1
    else:
        if not nodes:
            return None
        assert len(nodes) == 1
    assert not nodes[0].xpath('*')
    elem_text = nodes[0].text
    return elem_text.strip() if elem_text else None


def add_var(var_name, var_dict, doc):
    nodes = doc.xpath('//u:{}'.format(var_name), namespaces=USER_NAMESPACE)
    if not nodes:
        return

    if var_name != 'procurementSubject':
        try:
            assert len(nodes) == 1
        except:
            raise Exception("> 1 node found for var %s in %s", var_name, doc.docinfo.URL)

    assert not [x for x in nodes if x.xpath('*')]

    if var_name == 'birthDate':
        if nodes[0].text:
            # adding this assert b/c 'birthDate' is the only MarkLogic user var that
            # has a non-string type and we do not want to have to think about the
            # implications of that; it should not be a problem because as far as we
            # can tell there is no birthDate data in MarkLogic
            assert not nodes[0].text.strip(), "we do not expect to find birthDate"

    mapped_var_name = var_name_transform_mapping[var_name]

    if var_name == 'procurementSubject':
        ps_nodes = [n.text.strip() for n in nodes if n.text]
        if ps_nodes:
            var_dict[mapped_var_name] = '::'.join(ps_nodes)
    else:
        if nodes[0].text:
            var_dict[mapped_var_name] = nodes[0].text.strip()


def add_legacy_vars(var_dict, doc):
    company_nodes = doc.xpath('//u:company', namespaces=USER_NAMESPACE)
    if len(company_nodes) > 1:
        raise Exception("found more than one company element in %s", doc.docinfo.URL)
    if company_nodes and company_nodes[0].text and company_nodes[0].text.strip():
        assert not company_nodes[0].xpath('*')
        var_dict['legacy_company'] = company_nodes[0].text.strip()

    topical_interest_nodes = doc.xpath('//u:topicalInterest', namespaces=USER_NAMESPACE)
    if len(topical_interest_nodes) > 1:
        raise Exception("found more than one topicalInterest element in %s", doc.docinfo.URL)
    if topical_interest_nodes and topical_interest_nodes[0].text and topical_interest_nodes[0].text.strip():
        assert not topical_interest_nodes[0].xpath('*')
        var_dict['legacy_topicalInterest'] = topical_interest_nodes[0].text.strip()

    main_omeda_id = (
        doc.xpath('//u:omedaId', namespaces=USER_NAMESPACE)[0].text.strip()
        if doc.xpath('//u:omedaId[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)
        else None
    )
    assert not doc.xpath('//u:otherOmedaIds/u:otherOmedaId/*', namespaces=USER_NAMESPACE)
    other_omeda_ids = [
        x.text.strip() for x in
        doc.xpath('//u:otherOmedaIds/u:otherOmedaId[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)
        if x.text.strip() != main_omeda_id
    ]
    if other_omeda_ids:
        var_dict['legacy_otherOmedaIds'] = '::'.join(other_omeda_ids)


def add_source_signups(d, xmldoc):
    assert 'source_signups' not in d
    ss_nodes = xmldoc.xpath("//u:sourceSignups/u:sourceSignup", namespaces=USER_NAMESPACE)
    if not ss_nodes:
        return
    for ss in ss_nodes:
        assert len(ss.xpath('.//*')) == 2
    d['source_signups'] = []
    for x in ss_nodes:
        ss_dict = {
            'name': x.xpath('u:source', namespaces=USER_NAMESPACE)[0].text.strip(),
            'timestamp': x.xpath('u:date', namespaces=USER_NAMESPACE)[0].text.strip()
        }
        # Django can't handle '0001-01-01T00:00:00'; in the future we will clean these up
        if ss_dict['timestamp'] == '0001-01-01T00:00:00':
            ss_dict['timestamp'] = '0001-01-02T00:00:00'
        d['source_signups'].append(ss_dict)


def map_fields(doc):
    p = {}

    p['email'] = extract_element("email", doc)
    p['email_hash'] = extract_element("emailHash", doc)
    p['omeda_id'] = extract_element("omedaId", doc)

    if 'no-sailthru-ids' not in sys.argv:
        p['sailthru_id'] = extract_element("sailthruId", doc, optional=True)

    p['vars'] = {}
    for demo_var in demographic_var_names:
        add_var(demo_var, p['vars'], doc)

    add_legacy_vars(p['vars'], doc)

    # for MarkLogic users with omeda IDs as fake email addresses, we are making the
    # email addresses in this case null
    if p['email'] and p['email'].strip() and p['email'].strip().isdigit():
        assert p['email'] == p['omeda_id']
        p['email'] = None

    add_source_signups(p, doc)

    return p


def get_subscriptions(doc):
    s = {}

    for node in doc.xpath('/u:user/u:subscriptions/u:subscription', namespaces=USER_NAMESPACE):
        assert len(node.xpath('u:list[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)) == 1
        assert len(node.xpath('u:enabled[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)) == 1
        assert node.xpath('u:enabled[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)[0].text.strip() in ('0', '1')
        nl_slug = node.xpath('u:list[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)[0].text.strip()
        assert nl_slug not in s
        s[nl_slug] = bool(int(node.xpath('u:enabled[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)[0].text.strip()))

    for node in doc.xpath('/u:user/u:listSubscriptions/u:listSubscription', namespaces=USER_NAMESPACE):
        assert len(node.xpath('u:list[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)) == 1
        assert len(node.xpath('u:optedOut[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)) == 1
        opted_out_val = node.xpath('u:optedOut[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)[0].text.strip()
        assert opted_out_val in ('false', 'true')
        list_slug = node.xpath('u:list[normalize-space(.) != ""]', namespaces=USER_NAMESPACE)[0].text.strip()
        assert list_slug not in s
        s[list_slug] = opted_out_val == 'false'

    return s


def add_product_actions(doc, user):
    ns = USER_NAMESPACE
    product_actions_endpoint = "{}{}/{}/product-actions".format(
        CONFIG['target_base_url'], CONFIG['audienceusers_endpoint'], user["id"]
    )

    for action_type in ('registered', 'consumed'):
        action_payloads = []
        action_nodes = (
            doc.xpath(
                "/u:user/u:products{}/u:product{}".format(
                    action_type.title(), action_type.title()
                ),
                namespaces=ns
            )
        )
        for action in action_nodes:
            payload = {}
            payload['type'] = action_type

            # we do not expect <promoRef> to have ever been used
            assert not action.xpath('u:promoRef[normalize-space(.) != ""]', namespaces=ns)

            # we do not expect <details> to have ever been used
            assert not action.xpath('u:details[normalize-space(.) != ""]', namespaces=ns)

            assert len(action.xpath('u:product[normalize-space() != ""]', namespaces=ns)) == 1
            product_uuid = action.xpath('u:product', namespaces=ns)[0].get('ref-uuid', '').strip()
            assert product_uuid.strip()
            product_slug = PRODUCT_LOOKUP.xpath(
                '//p:product/p:uuid[normalize-space(.) = "{}"]/following-sibling::p:nameSlug'.format(product_uuid),
                namespaces=PRODUCT_NAMESPACE
            )
            assert len(product_slug) == 1
            assert product_slug[0].text.strip()

            payload['product'] = product_slug[0].text.strip()

            if payload['product'] == 'tech+tequilaq1registrants':
                payload['product'] = 'techtequilaq1registrants'

            datetime_prefix = 'registration' if action_type == 'registered' else 'consumed'
            assert len(action.xpath('u:{}Datetime[normalize-space() != ""]'.format(datetime_prefix), namespaces=ns)) == 1
            assert not action.xpath('u:{}Datetime/*'.format(datetime_prefix), namespaces=ns)
            payload['timestamp'] = action.xpath('u:{}Datetime'.format(datetime_prefix), namespaces=ns)[0].text.strip()
            action_payloads.append(payload)

        for payload in sorted(action_payloads, key=lambda x: x['timestamp']):
            logger.info(
                'user %d - recording product action - %s - %s',
                user['id'], payload['product'], payload['type']
            )
            response = requests.post(
                product_actions_endpoint, json=payload, headers=CONFIG['api_req_headers']
            )
            response.raise_for_status()
            assert response.status_code in (200, 201)


def process_user_xml_doc(f):
    try:
        assert f.endswith('.xml')
        if 'get-user-xml-via-http' in sys.argv:
            logger.info('getting user via http: %s', 'uuid=' + f[:-4])
            user_req = requests.get(
                CONFIG['marklogic_users_endpoint'],
                params={'uuid': f[:-4]},
                auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1])
            )
            user_req.raise_for_status()
            doc = etree.parse(StringIO.StringIO(user_req.text))
        else:
            o = open(os.path.join(CONFIG['user_xml_dir'], f), 'rb')
            doc = etree.parse(o)
            o.close()
        payload = map_fields(doc)
    except Exception as e:
        logger.error("could not process %s", os.path.join(CONFIG['user_xml_dir'], f))
        logger.error(e)
        return
    marklogic_email_hash = payload['email_hash']
    del payload['email_hash']

    response = requests.post(
        CONFIG['target_base_url'] + CONFIG['audienceusers_endpoint'],
        json=payload,
        headers=CONFIG['api_req_headers']
    )

    if response.status_code != 201:
        logger.error(
            "%s %s %s %s", f, unicode(payload['email']),
            unicode(response.status_code), response.text
        )
        return

    user = response.json()
    user_pk = user['id']

    logger.info(
        "created user %d from %s %s (%s)",
        user['id'], f, unicode(payload['email']), unicode(response.status_code)
    )

    if user['email'] and user['email_hash'] != marklogic_email_hash:
        logger.warning("email hash mismtach for %s", user['email'])

    subscriptions_endpoint = "{}{}/{}/subscriptions".format(
        CONFIG['target_base_url'], CONFIG['audienceusers_endpoint'], user_pk
    )

    subscriptions = get_subscriptions(doc)

    for list_slug, active in subscriptions.iteritems():
        comment = "initial import from MarkLogic "
        if active:
            comment += "[subscribed]"
        else:
            comment += "[unsubscribed]"
        subscription_payload = {
            "list": list_slug,
            "active": active,
            "log_override": {
                "action": "update",
                "comment": comment
            }
        }
        logger.info('user %d - adding subscription - %s [%s]', user_pk, list_slug, active)
        subscriptions_response = requests.post(
            subscriptions_endpoint,
            json=subscription_payload,
            headers=CONFIG['api_req_headers']
        )
        if subscriptions_response.status_code != 201:
            raise Exception(subscriptions_response.text)

    add_product_actions(doc, user)

    if 'verify-users' in sys.argv:
        test_migrated_data.compare_user(int(user_pk))


def import_users():
    xml_files = sorted(os.listdir(CONFIG['user_xml_dir']))
    assert not [x for x in xml_files if not x.endswith('.xml')]


    start_at = [x for x in sys.argv if x.startswith('start-at-')]
    start_at_offset = 0
    if start_at:
        start_at_offset = int(start_at[0].split('-')[-1])
        xml_files = xml_files[start_at_offset:]

    limit = [x for x in sys.argv if x.startswith('limit-')]
    if limit:
        xml_files = xml_files[0:int(limit[0].split('-')[-1])]

    if 'no-multi' in sys.argv:
        for i, x in enumerate(xml_files):
            logger.info('processing xml file %d', (i + start_at_offset))
            process_user_xml_doc(x)
    elif [x for x in sys.argv if x.startswith('filename=')]:
        process_user_xml_doc(
            [x for x in sys.argv if x.startswith('filename=')][0].split('=')[-1]
        )
    else:
        logger.info('user xml input dir: %s', CONFIG['user_xml_dir'])
        logger.info('processing %d files', len(xml_files))

        pool = multiprocessing.Pool(processes=CONFIG['threads'])
        map_result = pool.map_async(process_user_xml_doc, xml_files)
        map_result.wait()
        pool.close()
        assert map_result.successful()


def import_lists():
    r = requests.get(
        CONFIG['marklogic_lists_endpoint'],
        params={"rows": 1000},
        auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1]),
    )
    r.raise_for_status()

    doc = etree.fromstring(r.text)
    assert len(doc.xpath('/l:list', namespaces=LIST_NAMESPACE)) == 1
    assert len(doc.xpath('/l:list/l:list', namespaces=LIST_NAMESPACE)) > 1
    assert (
        int(doc.xpath('/l:list/totalrecords', namespaces=LIST_NAMESPACE)[0].text.strip()) ==
        len(doc.xpath('/l:list/l:list', namespaces=LIST_NAMESPACE))
    )

    for list_ in doc.xpath('/l:list/l:list', namespaces=LIST_NAMESPACE):
        payload = {}
        payload['type'] = 'list'

        slug_node = list_.xpath('l:name', namespaces=LIST_NAMESPACE)
        assert len(slug_node) == 1
        assert not slug_node[0].xpath('*')
        payload['slug'] = slug_node[0].text.strip()

        name_node = list_.xpath('l:description', namespaces=LIST_NAMESPACE)
        assert len(name_node) == 1
        assert not name_node[0].xpath('*')
        if not name_node[0].text:
            payload['name'] = payload['slug']
        else:
            assert name_node[0].text.strip()
            payload['name'] = name_node[0].text.strip()

        logger.info('creating list %s', payload['slug'])

        response = requests.post(
            CONFIG['target_base_url'] + CONFIG['lists_endpoint'],
            json=payload,
            headers=CONFIG['api_req_headers']
        )
        response.raise_for_status()
        assert response.status_code == 201


def import_newsletters():
    r = requests.get(
        CONFIG['marklogic_newsletters_endpoint'],
        params={"rows": 1000},
        auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1]),
    )
    r.raise_for_status()

    doc = etree.fromstring(r.text)

    assert len(doc.xpath('/l:list', namespaces=LIST_NAMESPACE)) == 1
    assert len(doc.xpath('/l:list/l:newsletter', namespaces=LIST_NAMESPACE)) > 1
    assert (
        int(doc.xpath('/l:list/totalrecords', namespaces=LIST_NAMESPACE)[0].text.strip()) ==
        len(doc.xpath('/l:list/l:newsletter', namespaces=LIST_NAMESPACE))
    )

    for nl in doc.xpath('/l:list/l:newsletter', namespaces=LIST_NAMESPACE):
        payload = {}
        payload['type'] = 'newsletter'

        slug_node = nl.xpath('l:name', namespaces=LIST_NAMESPACE)
        assert len(slug_node) == 1
        assert not slug_node[0].xpath('*')
        payload['slug'] = slug_node[0].text.strip()

        name_node = nl.xpath('l:description', namespaces=LIST_NAMESPACE)
        assert len(name_node) == 1
        assert not name_node[0].xpath('*')
        payload['name'] = name_node[0].text.strip()

        enabled_node = nl.xpath('l:enabled', namespaces=LIST_NAMESPACE)
        assert len(enabled_node) == 1
        assert not enabled_node[0].xpath('*')
        assert enabled_node[0].text.strip() in ('true', 'false')
        if (enabled_node[0].text.strip() == 'false') or payload['slug'].startswith('archive_'):
            payload['archived'] = True
        else:
            payload['archived'] = False

        synchronized_node = nl.xpath('l:synchronized', namespaces=LIST_NAMESPACE)
        assert len(synchronized_node) == 1
        assert not synchronized_node[0].xpath('*')
        assert synchronized_node[0].text.strip() in ('true', 'false')
        payload['sync_externally'] = synchronized_node[0].text.strip() == 'true'

        logger.info('creating newsletter %s', payload['slug'])
        response = requests.post(
            CONFIG['target_base_url'] + CONFIG['lists_endpoint'],
            json=payload,
            headers=CONFIG['api_req_headers']
        )
        response.raise_for_status()
        assert response.status_code == 201


def _create_trigger(primary_list, related_list):
    logger.debug('GETting primary list %s', primary_list)
    r = requests.get(
        CONFIG['target_base_url'] + CONFIG['lists_endpoint'],
        params={"slug": primary_list},
        headers=CONFIG['api_req_headers']
    )
    r.raise_for_status()
    assert len(r.json()['results']) == 1
    assert r.json()['results'][0]['slug'] == primary_list
    primary_id = r.json()['results'][0]['id']

    logger.debug('GETting related list %s', related_list)
    r = requests.get(
        CONFIG['target_base_url'] + CONFIG['lists_endpoint'],
        params={"slug": related_list},
        headers=CONFIG['api_req_headers']
        )
    r.raise_for_status()
    assert len(r.json()['results']) == 1
    assert r.json()['results'][0]['slug'] == related_list

    logger.info('adding subscriptiontrigger %s -> %s', primary_list, related_list)
    subscription_triggers_endpoint = "{}{}/{}/subscription-triggers".format(
        CONFIG['target_base_url'], CONFIG['lists_endpoint'], primary_id
    )
    r = requests.post(
        subscription_triggers_endpoint,
        json={"related_list_slug": related_list, "override_previous_unsubscribes": False},
        headers=CONFIG['api_req_headers']
    )
    r.raise_for_status()
    assert r.status_code == 201


def create_subscription_triggers():
    r = requests.get(
        CONFIG['marklogic_newsletterlistsignups_endpoint'],
        params={"rows": 1000},
        auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1]),
    )
    r.raise_for_status()

    doc = etree.fromstring(r.text)

    assert len(doc.xpath('/l:list', namespaces=LIST_NAMESPACE)) == 1
    assert len(doc.xpath('/l:list/l:newsletterListSignup', namespaces=LIST_NAMESPACE)) > 1
    assert (
        int(doc.xpath('/l:list/totalrecords', namespaces=LIST_NAMESPACE)[0].text.strip()) ==
        len(doc.xpath('/l:list/l:newsletterListSignup', namespaces=LIST_NAMESPACE))
    )

    signups = {}
    for n in doc.xpath('/l:list/l:newsletterListSignup', namespaces=LIST_NAMESPACE):
        assert len(n.xpath('l:newsletter[normalize-space(.) != ""]', namespaces=LIST_NAMESPACE)) == 1
        assert len(n.xpath('l:list[normalize-space(.) != ""]', namespaces=LIST_NAMESPACE)) == 1
        nl_slug = n.xpath('l:newsletter[normalize-space(.) != ""]', namespaces=LIST_NAMESPACE)[0].text.strip()
        list_slug = n.xpath('l:list[normalize-space(.) != ""]', namespaces=LIST_NAMESPACE)[0].text.strip()
        if nl_slug not in signups:
            signups[nl_slug] = [list_slug]
        else:
            signups[nl_slug] = signups[nl_slug] + [list_slug]

    for nl_slug, list_slugs in signups.iteritems():
        for list_slug in list(set(list_slugs)):
            _create_trigger(nl_slug, list_slug)

    logger.info('adding extra subscriptiontriggers')
    for primary_slug, related_slugs in EXTRA_SUBSCRIPTION_TRIGGERS_TO_CREATE.iteritems():
        assert isinstance(related_slugs, type([]))
        for related_slug in related_slugs:
            _create_trigger(primary_slug, related_slug)


def import_product_subtypes():
    r = requests.get(
        CONFIG['marklogic_product_subtypes_endpoint'],
        params={"rows": 1000},
        auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1]),
    )
    r.raise_for_status()

    doc = etree.fromstring(r.text)

    ns = PRODUCT_NAMESPACE

    assert len(doc.xpath('/p:list', namespaces=ns)) == 1
    assert len(doc.xpath('/p:list/p:productSubtype', namespaces=ns)) > 1
    assert (
        int(doc.xpath('/p:list/totalrecords', namespaces=ns)[0].text.strip()) ==
        len(doc.xpath('/p:list/p:productSubtype', namespaces=ns))
    )

    for pst in doc.xpath('/p:list/p:productSubtype', namespaces=ns):
        payload = {}

        pst_name = pst.xpath('p:name[normalize-space(.) != ""]', namespaces=ns)
        assert len(pst_name) == 1
        assert not pst_name[0].xpath('*')
        payload['name'] = pst_name[0].text.strip()

        logger.info('creating product subtype %s', payload['name'])

        response = requests.post(
            CONFIG['target_base_url'] + CONFIG['product_subtypes_endpoint'],
            json=payload,
            headers=CONFIG['api_req_headers']
        )
        response.raise_for_status()
        assert response.status_code == 201


def import_product_topics():
    r = requests.get(
        CONFIG['marklogic_product_topics_endpoint'],
        params={"rows": 1000},
        auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1]),
    )
    r.raise_for_status()

    doc = etree.fromstring(r.text)

    ns = PRODUCT_NAMESPACE

    assert len(doc.xpath('/p:list', namespaces=ns)) == 1
    assert len(doc.xpath('/p:list/p:productTopic', namespaces=ns)) > 1
    assert (
        int(doc.xpath('/p:list/totalrecords', namespaces=ns)[0].text.strip()) ==
        len(doc.xpath('/p:list/p:productTopic', namespaces=ns))
    )

    for pt in doc.xpath('/p:list/p:productTopic', namespaces=ns):
        payload = {}

        pt_name = pt.xpath('p:name[normalize-space(.) != ""]', namespaces=ns)
        assert len(pt_name) == 1
        assert not pt_name[0].xpath('*')
        payload['name'] = pt_name[0].text.strip()

        logger.info('creating product topic %s', payload['name'])

        response = requests.post(
            CONFIG['target_base_url'] + CONFIG['product_topics_endpoint'],
            json=payload,
            headers=CONFIG['api_req_headers']
        )
        response.raise_for_status()
        assert response.status_code == 201


def import_products():
    r = requests.get(
        CONFIG['marklogic_products_endpoint'],
        params={"rows": 1000},
        auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1]),
    )
    r.raise_for_status()

    doc = etree.fromstring(r.text)

    ns = PRODUCT_NAMESPACE

    assert len(doc.xpath('/p:list', namespaces=ns)) == 1
    assert len(doc.xpath('/p:list/p:product', namespaces=ns)) > 1
    assert (
        int(doc.xpath('/p:list/totalrecords', namespaces=ns)[0].text.strip()) ==
        len(doc.xpath('/p:list/p:product', namespaces=ns))
    )

    for product in doc.xpath('/p:list/p:product', namespaces=ns):
        payload = {}

        field_mappings = {
            'name': 'name',
            'nameSlug': 'slug',
            'brand': 'brand',
            'type': 'type',
        }

        for ml_field, new_field in field_mappings.items():
            node = product.xpath(
                'p:{}[normalize-space(.) != ""]'.format(ml_field), namespaces=ns
            )
            assert len(node) == 1
            assert not node[0].xpath('*')
            payload[new_field] = node[0].text.strip()

        payload['subtypes'] = []
        for subtype in product.xpath('p:subtypes/p:subtype', namespaces=ns):
            assert subtype.text is not None
            assert subtype.text.strip()
            assert not subtype.xpath('*')
            payload['subtypes'].append({'name': subtype.text.strip()})

        payload['topics'] = []
        for topic in product.xpath('p:topics/p:topic', namespaces=ns):
            assert topic.text is not None
            assert topic.text.strip()
            assert not topic.xpath('*')
            payload['topics'].append({'name': topic.text.strip()})

        if payload['slug'] == 'tech+tequilaq1registrants':
            payload['slug'] = 'techtequilaq1registrants'

        logger.info('creating product %s', payload['name'])
        response = requests.post(
            CONFIG['target_base_url'] + CONFIG['products_endpoint'],
            json=payload,
            headers=CONFIG['api_req_headers']
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            if 'products-expect-existing' in sys.argv:
                assert response.json().get("name") == ['Product with this name already exists.']
            else:
                raise
        else:
            assert response.status_code == 201


def import_lists_and_newsletters():
    logger.info("importing lists")
    import_lists()
    logger.info("importing newsletters")
    import_newsletters()
    logger.info("importing newsletterlistsignups as subscriptiontriggers")
    create_subscription_triggers()


def create_vars():
    vars_endpoint = "{}{}".format(CONFIG['target_base_url'], CONFIG['vars_endpoint'])

    for k in [var_name_transform_mapping[x] for x in demographic_var_names]:
        logger.info('creating "official" user var: %s', k)
        payload = {'key': k.strip(), 'type': 'official', 'sync_with_sailthru': True}
        response = requests.post(vars_endpoint, json=payload, headers=CONFIG['api_req_headers'])
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.error(unicode(response.text))
            raise
        assert response.status_code == 201

    for k in CUSTOM_VARS_TO_CREATE:
        logger.info('creating "custom" user var: %s', k)
        payload = {'key': k.strip(), 'type': 'other', 'sync_with_sailthru': False}
        response = requests.post(vars_endpoint, json=payload, headers=CONFIG['api_req_headers'])
        response.raise_for_status()
        assert response.status_code == 201

    for k in LEGACY_VARS_TO_CREATE:
        logger.info('creating "legacy" user var: %s', k)
        payload = {'key': k.strip(), 'type': 'other', 'sync_with_sailthru': False}
        response = requests.post(vars_endpoint, json=payload, headers=CONFIG['api_req_headers'])
        response.raise_for_status()
        assert response.status_code == 201


def main():
    logger.info('targeting %s', CONFIG['target_base_url'])

    if 'lists' in sys.argv or 'all' in sys.argv:
        import_lists_and_newsletters()

    if 'products' in sys.argv or 'all' in sys.argv:
        logger.info("import product subtypes")
        import_product_subtypes()
        logger.info("import product topics")
        import_product_topics()
        logger.info("import products")
        import_products()

    if 'vars' in sys.argv or 'all' in sys.argv:
        create_vars()

    if 'users' in sys.argv or 'all' in sys.argv:
        import_users()


if __name__ == "__main__":
    if 'verify-users' in sys.argv:
        import test_migrated_data
        test_migrated_data.logger = logger

    main()
