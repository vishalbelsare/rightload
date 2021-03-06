from content_extraction import get_text
from InferSent.encoder import models as im
from joblib import Memory
from nltk.data import load as nltk_load
import torch


_sent_detector = nltk_load("tokenizers/punkt/english.pickle")

# alternate infersent load method based on
# https://stackoverflow.com/questions/42703500/best-way-to-save-a-trained-model-in-pytorch
# as chdir doesn't work in flask
_config = dict(
    bsize=64,
    word_emb_dim=300,
    enc_lstm_dim=2048,
    pool_type="max",
    dpout_model=0.0,
    use_cuda=False,
)
# copied from loaded object
_infersent = im.BLSTMEncoder(_config)
_infersent.load_state_dict(
    torch.load(
        "InferSent/encoder/infersent.allnli.state.pickle",
        map_location=lambda storage, loc: storage,
    )
)
# saved with torch.save(
# _infersent.state_dict(), "InferSent/encoder/infersent.allnli.state.pickle")
_infersent.set_glove_path("InferSent/dataset/GloVe/glove.840B.300d.txt")
_infersent.build_vocab_k_words(K=1)

_memory = Memory(cachedir="feature-cache", verbose=1, bytes_limit=10 ** 9)
_memory.reduce_size()


@_memory.cache(ignore=["entry"])
def entry2mat(entry, url):
    return _text2mat(get_text(entry=entry, url=url))


def url2mat(url):
    return entry2mat(None, url)


def text2sentences(text, max_sentences=300):  # limit to cap latency
    return _sent_detector.tokenize(text.strip())[:max_sentences]


def _text2mat(text):
    sentences = text2sentences(text)
    if len(sentences) == 0:
        raise FailedExtraction

    _infersent.update_vocab(sentences, tokenize=True)
    if sentences:
        return _infersent.encode(sentences, tokenize=True)
    else:
        raise FailedExtraction


class FailedExtraction(Exception):
    pass
