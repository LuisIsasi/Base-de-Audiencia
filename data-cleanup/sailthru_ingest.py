import multiprocessing
import logging
import rethinkdb


import requests
requests.packages.urllib3.disable_warnings()


from sailthru.sailthru_client import SailthruClient


logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(levelname)s/%(processName)s] [%(asctime)s] %(message)s')
logger.handlers[0].setFormatter(formatter)


THREADS = 7

SAILTHRU_API_KEY = 'a0015d6172f59c1a789e6071711e4a25'  # PROD
SAILTHRU_SECRET = 'e64123f793d67e3177b0cb476d08f89b'   # PROD


def ingest_st_user(email_address):
    try:
        sailthru_client = SailthruClient(SAILTHRU_API_KEY, SAILTHRU_SECRET)
        response = sailthru_client.api_get("user", {"id": email_address})
    except:
        logger.error('failure talking to sailthru for %s', email_address)
        return
    if not response.is_ok():
        logger.error(
            'Sailthru error response for %s : %s', email_address, unicode(response.get_error().get_message())
        )
        return

    try:
        data = response.get_body()
        data['email'] = data['keys']['email']
        data['sid'] = data['keys']['sid']
        del data['keys']
    except:
        logger.error('failure munging data for %s', email_address)

    try:
        conn = rethinkdb.connect("localhost", 28015, db="audb")
        logger.info('rethink / inserting %s', email_address)
        result = rethinkdb.table("sailthru").insert(data).run(conn)
        assert result['inserted'] == 1
    except:
        logger.error('rethink insert error for %s', email_address)
        raise


def main():
    conn = rethinkdb.connect("localhost", 28015, db="audb")
    logger.info("dropping rethinkdb 'sailthru' table")
    rethinkdb.db('audb').table_drop("sailthru").run(conn)
    rethinkdb.db('audb').table_create("sailthru").run(conn)
    rethinkdb.db('audb').table("sailthru").index_create('email').run(conn)
    logger.info("done")

    with open('/Users/acrewdson/audb/data-cleanup/emails_not_in_villanova.txt', 'rb') as o:
        emails = sorted(o.read().split('\n'))

    logger.info('processing %d emails', len(emails))

    pool = multiprocessing.Pool(processes=THREADS)
    map_result = pool.map_async(ingest_st_user, emails)
    map_result.wait()
    pool.close()
    assert map_result.successful()


if __name__ == "__main__":
    main()
