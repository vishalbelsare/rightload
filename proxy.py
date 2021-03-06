"""Proxy logic."""
import copy
from embedUI import embedUI
from datastores import feed_db
from feed2XML import feed2XML
import feedcache
from flask import request, redirect
import logging as log
from ml import score_feed
from werkzeug.http import is_hop_by_hop_header


def proxy(url):
    log.info("Processing %s?%s", url, request.query_string)
    if request.method == 'GET':
        parsed_feed = feedcache.Cache(feed_db()).fetch(
            '?'.join(filter(None, [url, request.query_string])),
            force_update=False
        )  # defaults: force_update = False, offline = False
        # return content
        status = parsed_feed.get('status', 404)
        if status >= 400:  # deal with errors
            response = ("External error", status, {})
        elif status >= 300:  # deal with redirects
            if status == 301:
                log.warn("Permanent redirect from %s to %s", url,
                         parsed_feed.href)
            return redirect("/feed/{reurl}".format(reurl=parsed_feed.href))
        else:
            etag = request.headers.get('IF_NONE_MATCH')
            modified = request.headers.get('IF_MODIFIED_SINCE')
            if False:
                pass
            if (etag and etag == parsed_feed.get('etag')) or (
                    modified and modified == parsed_feed.get('modified')):
                response = ("", 304, {})
            else:
                if not parsed_feed['bozo']:
                    parsed_feed = copy.deepcopy(
                        parsed_feed
                    )  # if it's bozo copy fails and copy is not cached,
                    # so we skip
                    # deepcopy needed to avoid side effects on cache
                response = (_process(parsed_feed), 200, {})
        if 'headers' in parsed_feed:  # some header rinsing
            for k, v in parsed_feed.headers.iteritems():
                # TODO: seems to work with all the hop by hop  headers unset
                # or to default values, need to look into this
                if not is_hop_by_hop_header(
                        k
                ) and k != 'content-length' and k != 'content-encoding':
                    # let django deal with these headers
                    response[2][k] = v
        return response
    else:
        return ("POST not allowed for feeds", 405, {})


def _process(parsed_feed):
    score = score_feed(parsed_feed) if (len(parsed_feed.entries) > 0) else []
    return feed2XML(embedUI(parsed_feed, score))
