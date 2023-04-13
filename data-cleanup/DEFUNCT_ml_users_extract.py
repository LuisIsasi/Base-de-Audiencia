import json
import multiprocessing
import logging
import os

import lxml.etree
import requests
import rethinkdb
import xmltodict


logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(levelname)s/%(processName)s] [%(asctime)s] %(message)s')
logger.handlers[0].setFormatter(formatter)


OUT_DIR = "/Users/acrewdson/audb_cleanup/raw_xml"
PAGES = 2460
ROWS_PER_PAGE = 200
THREADS = 4


def extract_and_ingest_users(page):
    logger.info('GETting page %d', page)
    params = {
        "page": unicode(page),
        "rows": unicode(ROWS_PER_PAGE),
    }
    r = requests.get(
        "http://marklogic1.geprod.amc:9400/users/list.xml",
        auth=("acrewdson", "60ACCRETEDabstractions"),
        headers={"content-type": "application/json"},
        params=params
    )
    try:
        r.raise_for_status()
    except:
        logger.error('failed on page %d', page)
        return

    out_file = os.path.join(OUT_DIR, 'page_' + str(page) + '.xml')

    logger.info('writing %s', out_file)
    o = open(out_file, 'wb')
    o.write(r.text)
    o.close()

    logger.info('parsing %s', out_file)
    try:
        page_doc = lxml.etree.parse(out_file)
    except:
        logger.error("could not parse %s', out_file")
        return
    try:
        assert page_doc.xpath('//*[local-name() = "user"]')
    except:
        logger.error("could not find <user> elements in %s', out_file")
        return

    o = open(out_file, 'rb')
    page_dict_users = xmltodict.parse(o)['list']['user']
    o.close()

    conn = rethinkdb.connect("localhost", 28015, db="audb")
    for ml_uuid in [x['uuid'] for x in page_dict_users]:
        try:
            logger.info('getting user %s', ml_uuid)
            r = requests.get(
                "http://marklogic1.geprod.amc:9400/users/get.xml",
                auth=("acrewdson", "60ACCRETEDabstractions"),
                headers={"content-type": "application/json"},
                params={'uuid': ml_uuid.strip()}
            )
            r.raise_for_status()
        except:
            logger.error('failed to get user doc for uuid %s', ml_uuid)
            return
        try:
            user_out_file = os.path.join(OUT_DIR, 'user_' + ml_uuid)
            user_out_file_o = open(user_out_file, 'wb')
            user_out_file_o.write(r.text)
            user_out_file_o.close()
        except:
            logger.error('could not write out user xml for %s', ml_uuid)
            return
        try:
            o = open(user_out_file, 'rb')
            user_json = xmltodict.parse(o)['user']
            o.close()
        except:
            logger.error('could not parse xml to dict for %s', ml_uuid)
        try:
            logger.info('rethink / inserting %s', user_json['uuid'])
            assert user_json['uuid'] == ml_uuid
            result = rethinkdb.table("users").insert(user_json).run(conn)
            assert result['inserted'] == 1
        except:
            logger.error('could not do rethink insert %s', ml_uuid)


def main():
    logger.info("clearing rethinkdb 'users' table")
    conn = rethinkdb.connect("localhost", 28015, db="audb")
    rethinkdb.table("users").delete().run(conn)

    logger.info('removing existing files from %s', OUT_DIR)
    for f in os.listdir(OUT_DIR):
        os.unlink(os.path.join(OUT_DIR, f))

    pool = multiprocessing.Pool(processes=THREADS)
    map_result = pool.map_async(extract_and_ingest_users, range(1, PAGES))
    map_result.wait()
    pool.close()
    assert map_result.successful()


if __name__ == "__main__":
    main()
