import csv
from pprint import pprint as p



counter = 0

with open('/Users/acrewdson/audb_cleanup/23_march_sailthru_full.csv', 'rb') as o:
    reader = csv.DictReader(o, strict=True)
    for row in reader:
        """
        if row['external_source'] and row['external_source'].strip():
            print row['Email']
            assert row['Lists'] != 'SUPPRESS Villanova eblast'
        """

        if row['Lists'] != "SUPPRESS Villanova eblast":
            if row['Email']:
                print row['Email']
        """
            continue
        if not row['Email']:
            continue  # TODO take a look at these
        if not row.get('Profile Id', None):
            raise Exception(u'no profile id: {}'.format(unicode(row)))
        if row['modified_time']:
            print row['Email']
        """