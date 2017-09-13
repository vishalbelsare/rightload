from datetime import datetime
import feedgenerator
from functools import reduce  # forward compatibility for Python 3
import operator
import re
from time import mktime


def feed2XML(parsed_feed):
    'takes a parsed feed and generates an xml feed'

    def feedFactory(version):
        if version.upper().find('RSS') != -1:
            return feedgenerator.Rss201rev2Feed
        else:
            return feedgenerator.Atom1Feed

    pf = parsed_feed.feed
    pf['title'] = pf.get('title', u'')
    pf['link'] = pf.get('link', u'')
    feed = feedFactory(parsed_feed.version)(
        description=pf.get('description', u''),
        **dict(zip(map(str, pf.keys()), pf.values())))
    for e in parsed_feed.entries:
        add_args = map_entry_structure(field_map, e)
        if e.has_key('published_parsed'):
            add_args['pubdate'] = datetime.fromtimestamp(
                mktime(e['published_parsed']))
        if e.has_key('updated_parsed'):
            add_args['updateddate'] = datetime.fromtimestamp(
                mktime(e['updated_parsed']))
        feed.add_item(**add_args)
    return feed.writeString(parsed_feed.encoding)


# this dict contains an entry for each entry.add_item unicode argument (dates
# are treated separately). Each value is a tuple with a list of paths and a
# default value for the argument. Each path is a tuple of keys used to access
# the nested dict-like structure created by feedparser from the root down. The
# first path to return a falseish value is used, converted to unicode. I've
# found a great variety of fields within the so called RSS and Atom standards.
# This mapping is the result of trial and error and will most likely have to be
# updated to support more feeds.

field_map = dict(
    title=(['title'], u''),
    link=(['link'], u''),
    description=(["description", ('content', 'value'), "summary"], u''),
    author_email=([('author_detail', 'email')], None),
    author_name=(['author', ('author_detail', 'name')], None),
    author_link=([('author_link', 'href')], None),
    comments=(None, None),
    unique_id=([("id")], None),
    enclosure=(None, None),
    categories=(None, ()),
    item_copyright=(None, None),
    ttl=(None, None),
    content=(None, None))


def get_nested(nested_dict, path):
    if isinstance(path, str):
        path = (path, )
    return reduce(lambda x, y: x.get(y, {}), path, nested_dict)


def map_entry_structure(fmap, entry):
    return {
        arg: reduce(lambda x, y: x or unicode(get_nested(entry, y)) or default,
                    paths, u'')
        for arg, (paths, default) in fmap.iteritems() if paths is not None
    }
