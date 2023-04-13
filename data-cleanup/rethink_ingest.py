import multiprocessing
import logging
import os
import re

import lxml.etree
import rethinkdb
import xmltodict


logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(levelname)s/%(processName)s] [%(asctime)s] %(message)s')
logger.handlers[0].setFormatter(formatter)


THREADS = 7
INPUT_XML_DIR = "/Users/acrewdson/ml_prod_dump/23_march/users"


def ingest_users(xml_filename):

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

    input_doc = lxml.etree.parse(os.path.join(INPUT_XML_DIR, xml_filename))
    for e in input_doc.xpath('//*'):
        stripped_attribs = [re.compile(r'^\{.*?\}').sub('', x) for x in e.attrib.keys()]
        if len(stripped_attribs) != len(set(stripped_attribs)):
            logger.error('dupe attributes %s', xml_filename)
            return

    try:
        user_dict = xmltodict.parse(lxml.etree.tostring(NS_XSLT(input_doc)))
    except:
        logger.error('failed to parse %s', xml_filename)
        return

    try:
        assert len(user_dict.keys()) == 1
        user = user_dict[user_dict.keys()[0]]
        assert not [x for x in user.keys() if x.startswith('user:')]
        #user = cleaned_user(user)
    except:
        logger.error('problem with keys for %s', xml_filename)
        return

    #logger.info('parsed doc into dict %s', xml_filename)

    try:
        conn = rethinkdb.connect("localhost", 28015, db="audb")
        #logger.info('rethink / inserting %s', user['uuid'])
        result = rethinkdb.table("users").insert(user).run(conn)
        assert result['inserted'] == 1
        conn.close()
    except:
        logger.error('rethink insert error for %s', xml_filename)
        return


def main():
    logger.info("dropping rethinkdb 'users' table")
    conn = rethinkdb.connect("localhost", 28015, db="audb")
    rethinkdb.db('audb').table_drop("users").run(conn)
    rethinkdb.db('audb').table_create("users").run(conn)
    rethinkdb.db('audb').table("users").index_create('email').run(conn)
    logger.info("done")

    pool = multiprocessing.Pool(processes=THREADS)
    pool.map(ingest_users, sorted(os.listdir(INPUT_XML_DIR)))
    pool.close()


if __name__ == "__main__":
    main()
