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

    emails = set()

    for res in results:
        email, info = res.items()[0]
        if 'no_sailthru_data_found' in info:
            emails.add(email)

    for e in sorted(emails):
        print e


if __name__ == "__main__":
    main()
