import requests, json


uuids = []


for uuid in uuids:

    req = requests.get(
        'http://marklogic1.geprod.amc:9400/users/get.json',
        params={"uuid": uuid},
        auth=('acrewdson', '60ACCRETEDabstractions'),
    )
    print req.url
    req.raise_for_status()

    req2 = requests.get(
        'http://marklogic1.geprod.amc:9400/users/get.json',
        params={"email": req.json()['email']},
        auth=('acrewdson', '60ACCRETEDabstractions'),
    )
    print req2.url
    req2.raise_for_status()
    assert req2.json()['email'] == req.json()['email']

    req3 = requests.post(
        'http://marklogic1.geprod.amc:9400/users/put.json',
        data=json.dumps({'email': req.json()['email']}),
        headers={"content-type": "application/json"},
        auth=('acrewdson', '60ACCRETEDabstractions'),
    )
    print req3.url
    req3.raise_for_status()
    print '------'

