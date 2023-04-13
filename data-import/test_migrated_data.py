# [SublimeLinter pylint-@python:2]

import datetime
import multiprocessing
import re
import sys

from django.utils.timezone import localtime
import isodate
import lxml.etree
import pytz
import requests
import xmltodict



CONFIG = {
    'threads': 6,

    'audb_base_url': 'http://localhost:7979',
    'audb_api_req_headers': {'Authorization': 'Token f776aecc3d48dc6c1db211c0b93206c0fbaeb32e'},
    'audb_audienceusers_endpoint': '/api/audience-users',

    'marklogic_http_credentials': ('acrewdson', '60ACCRETEDabstractions'),  # it's ok, it's only my MarkLogic password
    'marklogic_users_endpoint': 'http://marklogic1.geprod.amc:9400/users/get.xml',

}


_product_lookup_request = requests.get(
    'http://marklogic1.geprod.amc:9400/products/list.xml',
    params={"rows": 1000},
    auth=('acrewdson', '60ACCRETEDabstractions'),
)
_product_lookup_request.raise_for_status()
PRODUCT_LOOKUP = lxml.etree.fromstring(_product_lookup_request.text)



def product_uuid_to_slug(uuid):
    return PRODUCT_LOOKUP.xpath(
        '//p:product/p:uuid[normalize-space(.) = "{}"]/../p:nameSlug'.format(uuid),
        namespaces={'p': "http://www.govexec.com/product"}
    )[0].text.strip()


def get_audb_user(pk):
    response = requests.get(
        CONFIG['audb_base_url'] + CONFIG['audb_audienceusers_endpoint'] + '/{}'.format(str(pk)),
        headers=CONFIG['audb_api_req_headers']
    )
    response.raise_for_status()
    return response.json()


def _get_user_xml(email):
    response = requests.get(
        CONFIG['marklogic_users_endpoint'],
        params={"email": email.strip()},
        auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1]),
    )
    try:
        response.raise_for_status()
        return response
    except:
        if email.strip() not in ['rickytomlin@hotmail.com', 'milesa@mail.nih.gov', 'rathna.ramani@gmail.com', 'sh44094@gmail.com', 'virginia.wiggins@mda.mil', 'zeigler.steve@epa.gov', 'cmillersierraps@gmail.com', 'sherri.carpenter@ssa.gov', 'lhidalgo10@yahoo.com', 'sokolow50@yahoo.com', 'braxtonbernard@deloitte.com', 'karen.a.gelling@irs.gov', 'mueller.garret@westside66.net', 'thomas.spann@asg.com', 'williams.joan@epa.gov', 'opawlyk@airforcetimes.com', 'jay.mcconville@lmco.com', 'dennis.arinello@dyn-intl.com', 'priscilla.neves@fda.hhs.gov', 'chang.li3@treasury.gov', 'julie.a.hamilton@us.army.mil', 'elizabeth.a.comer8.civ@mail.mil', 'donald.e.cowles2.civ@mail.mil', 'agluck@chp-sf.org', 'clo@younggov.org', 'sartaj.alag@cfpb.gov', 'dandjschulz@hotmail.com']:
            raise
        response = requests.get(
            CONFIG['marklogic_users_endpoint'],
            params={"email": email.strip() + ' '},
            auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1]),
        )
        try:
            response.raise_for_status()
            return response
        except:
            response = requests.get(
                CONFIG['marklogic_users_endpoint'],
                params={"email": ' ' + email.strip()},
                auth=(CONFIG['marklogic_http_credentials'][0], CONFIG['marklogic_http_credentials'][1]),
            )
            response.raise_for_status()
            return response


def get_ml_user(email):

    try:
        response = _get_user_xml(email)
    except:
        return None

    # define this here just to avoid the possibility of thread unsafety with lxml
    NS_XSLT = lxml.etree.XSLT(lxml.etree.XML("""<?xml version="1.0"?>
    <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

        <xsl:output indent="yes" method="xml" encoding="utf-8" omit-xml-declaration="yes"/>

        <!-- Stylesheet to remove all namespaces from a document -->
        <!-- Nodes that cannot have a namespace are copied as such -->

        <!-- template to copy elements -->
        <xsl:template match="*">
            <xsl:element name="{local-name()}">
                <xsl:apply-templates select="@* | node()"/>
            </xsl:element>
        </xsl:template>

        <!-- template to copy attributes -->
        <xsl:template match="@*">
            <xsl:attribute name="{local-name()}">
                <xsl:value-of select="."/>
            </xsl:attribute>
        </xsl:template>

        <!-- template to copy the rest of the nodes -->
        <xsl:template match="comment() | text() | processing-instruction()">
            <xsl:copy/>
        </xsl:template>

    </xsl:stylesheet>
    """))

    input_doc = lxml.etree.fromstring(response.text)
    for e in input_doc.xpath('//*'):
        stripped_attribs = [re.compile(r'^\{.*?\}').sub('', x) for x in e.attrib.keys()]
        if len(stripped_attribs) != len(set(stripped_attribs)):
            logger.error('dupe attributes in xml doc, cannot continue')
            return

    try:
        user_dict = xmltodict.parse(lxml.etree.tostring(NS_XSLT(input_doc)))
    except:
        logger.error('failed to parse xml')
        return

    try:
        assert len(user_dict.keys()) == 1
        user = user_dict[user_dict.keys()[0]]
        assert not [x for x in user.keys() if x.startswith('user:')]
    except:
        logger.error('problem with keys')
        return

    return user


def nl_and_lists_comp(a, m):
    ml_lists = m.get('listSubscriptions', {}) or {}
    ml_lists = ml_lists.get('listSubscription', []) or []
    ml_lists = ml_lists if isinstance(ml_lists, type([])) else [ml_lists]
    ml_list_lookup = {}
    for x in ml_lists:
        try:
            assert x['list']['#text'] not in ml_list_lookup
        except AssertionError:
            logger.error('duplicate list info for %s', m['uuid'])
        assert x['optedOut'] in ('false', 'true')
        ml_list_lookup[x['list']['#text']] = x['optedOut'] == 'false'

    ml_subs = m.get('subscriptions', {}) or {}
    ml_subs = ml_subs.get('subscription', []) or []
    ml_subs = ml_subs if isinstance(ml_subs, type([])) else [ml_subs]
    ml_sub_lookup = {}
    for x in ml_subs:
        try:
            assert x['list']['#text'] not in ml_sub_lookup
        except AssertionError:
            logger.error('duplciate sub info for %s', m['uuid'])
        assert x['enabled'] in ('0', '1')
        ml_sub_lookup[x['list']['#text']] = bool(int(x['enabled']))

    a_list_lookup = {}
    for s in [x for x in a['subscriptions'] if x['list']['type'] == 'list']:
        assert s['list']['slug'] not in a_list_lookup
        a_list_lookup[s['list']['slug']] = s['active']

    a_subs_lookup = {}
    for s in [x for x in a['subscriptions'] if x['list']['type'] == 'newsletter']:
        assert s['list']['slug'] not in a_subs_lookup
        a_subs_lookup[s['list']['slug']] = s['active']

    assert not [x for x in a['subscriptions'] if x['list']['type'] not in ('list', 'newsletter')]

    if ml_list_lookup != a_list_lookup:
        logger.error('lists do not match for %s', m['uuid'])
    if ml_sub_lookup != a_subs_lookup:
        logger.error('newsletters do not match for %s', m['uuid'])

def products_comp(a, m):
    ml_prod_reg = m.get('productsRegistered', {}) or {}
    ml_prod_reg = ml_prod_reg.get('productRegistered', []) or []
    ml_prod_reg = ml_prod_reg if isinstance(ml_prod_reg, type([])) else [ml_prod_reg]
    ml_prod_reg = list(reversed(sorted(ml_prod_reg, key=lambda x: isodate.parse_datetime(x['registrationDatetime']))))
    collapsed_ml_prod_reg = {}
    for mlpr in ml_prod_reg:
        assert not mlpr.get('details', None)
        assert not mlpr.get('promoRef', None)
        collapsed_ml_prod_reg[product_uuid_to_slug(mlpr['product']['@ref-uuid'])] = mlpr['registrationDatetime']
    ml_prod_reg = sorted(collapsed_ml_prod_reg.items(), key=lambda x: (isodate.parse_datetime(x[1]), x[0]))

    a_prod_reg = sorted([x for x in a.get('product_actions', []) if x['type'] == 'registered'], key=lambda x: (isodate.parse_datetime(x['timestamp']), x['product']['slug']))

    product_reg_problem = False
    for mpr, apr in zip(ml_prod_reg, a_prod_reg):
        assert not apr.get('details', None)
        if apr['product']['slug'] != mpr[0]:
            product_reg_problem = True
        if localtime(isodate.parse_datetime(apr['timestamp']), timezone=pytz.timezone("America/New_York")).replace(tzinfo=None) != isodate.parse_datetime(mpr[1]):
            product_reg_problem = True

    if len(a_prod_reg) != len(ml_prod_reg):
        product_reg_problem = True
    if product_reg_problem:
        logger.error('prod reg problems for %s', m.get('uuid', ''))

    ml_prod_cons = m.get('productsConsumed', {}) or {}
    ml_prod_cons = ml_prod_cons.get('productConsumed', []) or []
    ml_prod_cons = ml_prod_cons if isinstance(ml_prod_cons, type([])) else [ml_prod_cons]
    ml_prod_cons = list(reversed(sorted(ml_prod_cons, key=lambda x: isodate.parse_datetime(x['consumedDatetime']))))
    collapsed_ml_prod_cons = {}
    for mlpc in ml_prod_cons:
        assert not mlpc.get('details', None)
        collapsed_ml_prod_cons[product_uuid_to_slug(mlpc['product']['@ref-uuid'])] = mlpc['consumedDatetime']
    ml_prod_cons = sorted(collapsed_ml_prod_cons.items(), key=lambda x: (isodate.parse_datetime(x[1]), x[0]))

    a_prod_cons = sorted([x for x in a.get('product_actions', []) if x['type'] == 'consumed'], key=lambda x: (isodate.parse_datetime(x['timestamp']), x['product']['slug']))

    product_cons_problem = False
    for mpr, apr in zip(ml_prod_cons, a_prod_cons):
        assert not apr.get('details', None)
        if apr['product']['slug'] != mpr[0]:
            product_cons_problem = True
        if localtime(isodate.parse_datetime(apr['timestamp']), timezone=pytz.timezone("America/New_York")).replace(tzinfo=None) != isodate.parse_datetime(mpr[1]):
            product_cons_problem = True

    if len(a_prod_cons) != len(ml_prod_cons):
        product_cons_problem = True
    if product_cons_problem:
        logger.error('prod consumed problems for %s', m.get('uuid', ''))


def comp(a, m):
    a_id = a['id']

    if a['email']:
        try:
            assert a['email'].strip() == m['email'].strip()
        except AssertionError:
            logger.error('emails do not match for pk %d', a_id)
    else:
        try:
            assert a['omeda_id'].strip() == m['omedaId']
        except AssertionError:
            logger.error('omeda id mismtach for pk %d', a_id)

    simple_comp_keys = (
        ('sailthru_id', 'sailthruId'),
        ('email_hash', 'emailHash'),
    )

    for a_k, m_k in simple_comp_keys:
        if a_k == 'email_hash' and m.get('email', '') == m.get('omedaId', ''):
            continue
        a_val = a.get(a_k, "") or ""
        m_val = m.get(m_k, '') or ''
        if a_val != m_val:
            logger.error('%s mismatch for %d', a_k, a_id)

    # =========================================================================

    ml_other_omeda_ids = m.get('otherOmedaIds', {}) or {}
    ml_other_omeda_ids = ml_other_omeda_ids.get('otherOmedaId', []) or []
    ml_other_omeda_ids = ml_other_omeda_ids if isinstance(ml_other_omeda_ids, type([])) else [ml_other_omeda_ids]
    ml_other_omeda_ids = [x for x in ml_other_omeda_ids if x != m.get('omedaId', None)]

    a_other_omeda_ids = a.get('vars', {}).get('legacy_otherOmedaIds', '') or ''
    a_other_omeda_ids = [x for x in a_other_omeda_ids.split('::') if x]

    if sorted(ml_other_omeda_ids) != sorted(a_other_omeda_ids):
        logger.error('otherOmedaIds mismatch for %d', a_id)

    # =========================================================================

    var_pairs = (
        ('firstName', 'first_name'),
        ('lastName', 'last_name'),
        ('address1', 'postal_address'),
        ('address2', 'postal_address2'),
        ('city', 'postal_city'),
        ('state', 'postal_state'),
        ('postalCode', 'postal_code'),
        ('country', 'country'),
        ('locale', 'locale'),
        ('workPhone', 'phone'),
        ('homePhone', 'home_phone'),
        ('mobilePhone', 'mobile_phone'),
        ('fax', 'fax'),
        ('timezone', 'timezone'),
        ('gender', 'gender'),
        ('birthDate', 'birth_date'),
        ('marital', 'martial'),
        ('income', 'income'),
        ('educationLevel', 'education_level'),
        ('industry', 'industry'),
        ('jobTitle', 'job_title'),
        ('jobFunction', 'job_function'),
        ('jobSector', 'job_sector'),
        ('jobSectorType', 'job_sector_type'),
        ('employer', 'employer'),
        ('companySize', 'company_size'),
        ('agencyDepartment', 'agency_department'),
        ('gradeRank', 'grade_rank'),
        ('procurementSubject', 'procurement_subject'),
        ('procurementLevel', 'procurement_level'),
        ('procurementArea', 'procurement_area'),
        ('procurementRole', 'procurement_role'),
        ('procurementIntent', 'procurement_intent'),
        ('appInterestRouteFifty', 'rf_app_interest'),

        ('company', 'legacy_company'),
        ('topicalInterest', 'legacy_topicalInterest'),
    )
    a_vars = a.get('vars', {}) or {}
    for m_var, a_var in var_pairs:
        a_val = a_vars.get(a_var, '') or ''
        m_val = m.get(m_var, '') or ''
        if isinstance(m_val, type([])):
            m_val = '::'.join(m_val)
        if a_val != m_val:
            logger.error('%s mismatch for %d', a_var, a_id)

    unaccounted_for_vars = [
        y for y in a_vars.keys() if y not in [x[1] for x in var_pairs] and y != 'legacy_otherOmedaIds'
    ]
    if unaccounted_for_vars:
        logger.error('unaccounted for vars in %d: %s', a_id, str(unaccounted_for_vars))

    # =========================================================================

    ml_ss = m.get('sourceSignups', {}) or {}
    ml_ss = ml_ss.get('sourceSignup', []) or []
    ml_ss = ml_ss if isinstance(ml_ss, type([])) else [ml_ss]
    ml_ss = sorted([(x['source'], isodate.parse_datetime(x['date'])) for x in ml_ss], key=lambda x: (x[0], x[1]))

    a_ss = a.get('source_signups', []) or []
    a_ss = sorted([
        (x['name'], localtime(isodate.parse_datetime(x['timestamp']), timezone=pytz.timezone("America/New_York")).replace(tzinfo=None))
        for x in a_ss
    ], key=lambda x: (x[0], x[1]))

    source_signup_probs = False
    for ml_s, a_s in zip(ml_ss, a_ss):
        ml_ss_name, ml_ss_date = ml_s
        a_ss_name, a_ss_date = a_s
        if ml_ss_date.year == 1 and ml_ss_date.month == 1 and ml_ss_date.day == 1:
            ml_ss_date = ml_ss_date + datetime.timedelta(days=1)
        if ml_ss_name != a_ss_name or ml_ss_date != a_ss_date:
            source_signup_probs = True
    if source_signup_probs:
        logger.error('source signups mismtach for %s', m.get('uuid', ''))

    # =========================================================================

    nl_and_lists_comp(a, m)
    products_comp(a, m)

    # =========================================================================

    ml_uuid = m.get('uuid', '')

    if 'source' in m.keys():
        try:
            assert not m['source']
        except AssertionError:
            logger.error('not empty source field for %s', ml_uuid)

    del_keys = ['@type', 'create-user', 'uuid', 'created', 'modified', 'source']
    for dk in del_keys:
        if dk in m.keys():
            del m[dk]

    do_not_care = ['emailOptOut', 'engagement', 'researchOptIn', 'synchronized']

    examined_vars = do_not_care + [x[0] for x in var_pairs] + ['email', 'omedaId', 'emailHash', 'sailthruId']
    examined_vars.extend([
        'sourceSignups', 'subscriptions', 'listSubscriptions', 'productsConsumed',
        'productsRegistered', 'otherOmedaIds'
    ])

    for k in [x for x in m.keys() if x not in examined_vars]:
        logger.error('missed field "%s" in doc %s', k, ml_uuid)


def compare_user(pk):
    audb_user = get_audb_user(pk)

    ml_lookup_email = audb_user['email'] if audb_user['email'] else audb_user['omeda_id']
    if not ml_lookup_email or not ml_lookup_email.strip():
        logger.warning('could not get email or omeda id for %s', str(pk))
        return

    ml_user = get_ml_user(ml_lookup_email)
    if not ml_user:
        logger.error('could not get xml for user')
        return

    comp(audb_user, ml_user)


def main():
    user_pks = range(int(sys.argv[1]), int(sys.argv[2]) + 1)

    if 'no-multi' in sys.argv:
        for k in user_pks:
            compare_user(k)
    else:
        pool = multiprocessing.Pool(processes=CONFIG['threads'])
        map_result = pool.map_async(compare_user, user_pks)
        map_result.wait()
        pool.close()
        assert map_result.successful()


if __name__ == "__main__":
    import logging
    logger = multiprocessing.log_to_stderr()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s/%(processName)s] %(message)s')
    logger.handlers[0].setFormatter(formatter)

    main()
