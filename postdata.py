import os
import hug
from subprocess import check_output, call
from logging import getLogger, StreamHandler, DEBUG, INFO
from hug_middleware_cors import CORSMiddleware
from elasticsearch import Elasticsearch

log = getLogger(__name__)
log.setLevel(INFO)
handler = StreamHandler()
handler.setLevel(INFO)
log.addHandler(handler)

api = hug.API(__name__)
api.http.add_middleware(CORSMiddleware(api))

es = Elasticsearch()


def generate_thumbnail(path: str):
    """ background job """
    call('python tasks.py GenerateThumbnail --ppt-path={}'.format(path),
         shell=True, universal_newlines=True)


def parse_text(path: str):
    call('python tasks.py parseTxt --ppt-path={}'.format(path),
         shell=True, universal_newlines=True)


def post_upload(path: str):
    log.info('post_upload: {}'.format(path))
    parse_text(path)
    generate_thumbnail(path)


@hug.post('/upload')
def upload_file(user: hug.directives.user, name, upload_file):
    """Converts multipart form data into native Python objects
    URLを返す
    """

    outdir = './upload'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outfile = os.path.join(outdir, name.decode('utf-8'))

    with open(outfile, 'wb') as f:
        f.write(upload_file)

    post_upload(path=outfile)

    return {'url': outfile, 'name': name, 'length': len(upload_file)}


@hug.get('/search')
def search():
    res = es.search(
        index="example",
        filter_path=['hits.hits._source', 'hits.hits._score', 'hits.count'],
        body={"query": {"match_all": {}}})

    return res
