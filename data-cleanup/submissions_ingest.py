import sys
import json
import multiprocessing
import logging
import rethinkdb


logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(levelname)s/%(processName)s] [%(asctime)s] %(message)s')
logger.handlers[0].setFormatter(formatter)


THREADS = int(sys.argv[1])


def ingest_submission(submission):

    fields = submission['fields']
    fields['pk'] = submission['pk']

    for json_field in ('newsletters_string', 'user_vars_string', 'lists_string', 'products_string'):
        json_field_ = fields.get(json_field, None) or None
        json_field_ = json_field_.strip() if json_field_ is not None else None
        json_field_ = json_field_ if json_field_ else None
        if json_field_:
            try:
                json_field_parsed = json.loads(json_field_)
            except:
                json_field_parsed = None
                logger.error('%s could not parse %s', fields['email'], json_field)
            fields[json_field] = json_field_parsed
        else:
            if json_field == 'products_string':
                fields[json_field] = []
            else:
                fields[json_field] = {}

    try:
        conn = rethinkdb.connect("localhost", 28015, db="audb")
        result = rethinkdb.table("submissions").insert(fields).run(conn)
        assert result['inserted'] == 1
    except:
        logger.error('rethink insert error for %s', fields['pk'])
        raise


def main():
    conn = rethinkdb.connect("localhost", 28015, db="audb")
    try:
        logger.info("dropping rethinkdb 'submissions' table if it exists")
        rethinkdb.db('audb').table_drop("submissions").run(conn)
    except rethinkdb.errors.ReqlOpFailedError:
        pass
    rethinkdb.db('audb').table_create("submissions").run(conn)
    rethinkdb.db('audb').table("submissions").index_create('email').run(conn)
    rethinkdb.db('audb').table("submissions").index_create('pk').run(conn)

    logger.info("starting ingest")

    with open('submissions.json', 'rb') as o:
        submissions = list(reversed(json.load(o)))

    pool = multiprocessing.Pool(processes=THREADS)
    map_result = pool.map_async(ingest_submission, submissions)
    map_result.wait()
    pool.close()
    assert map_result.successful()


if __name__ == "__main__":
    main()
