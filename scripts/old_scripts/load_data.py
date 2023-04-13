import itertools
import json

from django.conf import settings

import core.models as m


# this must be run using the django 'runscript' extension, like:
#    manage runscript load_data --script-args filename.json


# TODO probably we should add subscription triggers if we start using this much


def run(*args):
    assert 'geprod' not in settings.DATABASES['default']['HOST']

    with open(args[0], 'r') as o:
        data = json.load(o)

    products, lists, vars_ = data['products'], data['lists'], data['vars']

    print('! clearing out products, lists, vars')
    [x.delete() for x in m.Product.objects.all()]
    [x.delete() for x in m.ProductSubtype.objects.all()]
    [x.delete() for x in m.ProductTopic.objects.all()]
    [x.delete() for x in m.List.objects.all()]
    [x.delete() for x in m.VarKey.objects.all()]

    product_topics = set([
        x['name'] for x in
        itertools.chain.from_iterable([x['topics'] for x in products])
    ])
    product_subtypes = set([
        x['name'] for x in
        itertools.chain.from_iterable([x['subtypes'] for x in products])
    ])

    for pt in product_topics:
        print('creating product topic: {}'.format(pt))
        m.ProductTopic.objects.validate_and_create(name=pt)
    for ps in product_subtypes:
        print('creating product subtype: {}'.format(ps))
        m.ProductSubtype.objects.validate_and_create(name=ps)

    for p in products:
        print('creating product {}'.format(p['slug']))
        prod = m.Product.objects.validate_and_create(
            name=p['name'],
            slug=p['slug'],
            brand=p['brand'],
            type=p['type']
        )
        for subtype_name in [x['name'] for x in p['subtypes']]:
            prod.subtypes.add(m.ProductSubtype.objects.get(name=subtype_name))
        for topic_name in [x['name'] for x in p['topics']]:
            prod.topics.add(m.ProductTopic.objects.get(name=topic_name))

    for list_ in data['lists']:
        print('creating list {}'.format(list_['slug']))
        new_list = m.List.objects.validate_and_create(
            name=list_['name'],
            slug=list_['slug'],
            archived=list_['archived'],
            sync_externally=list_['sync_externally'],
            type=list_['type']
        )

    for var in data['vars']:
        print('creating var: {}'.format(var['key']))
        m.VarKey.objects.validate_and_create(
            key=var['key'], type=var['type'], sync_with_sailthru=var['sync_with_sailthru']
        )
