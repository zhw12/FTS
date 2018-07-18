import sys
import logging
import re
from gensim.models import word2vec
import gensim

# e.g. file = '../data/segmented_text.txt_phraseAsWord'
if len(sys.argv) > 1:
    file = sys.argv[1]

file_wordvec = file+'.wordvec'
if len(sys.argv) > 2:
    file_wordvec = sys.argv[2]


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger('log')
logger.addHandler(logging.FileHandler(__file__+'.log'))
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

logger.debug('==================================')
logger.debug('for file %s' % file)

short_word = re.compile(
    r"^\w{,1}$"
)
doesnt_contain_vowel = re.compile(
    r"^[^aeiou]*$"
)


def notMeaningfulWord(word):
    return short_word.match(word)


square_brackets_enclosed = re.compile(
    r"<phrase>(?P<phrase>[^<]*)</phrase>"
)


def trim_rule(word, count, min_count):
    if square_brackets_enclosed.match(word):
        return gensim.utils.RULE_KEEP
    if notMeaningfulWord(word):
        return gensim.utils.RULE_DISCARD
    return gensim.utils.RULE_DEFAULT


if __name__ == '__main__':
    with open(file) as fin:
        model = word2vec.Word2Vec(word2vec.LineSentence(file), size=200,  workers=8, max_vocab_size=None, trim_rule=trim_rule, sg=1)
        model.save(file_wordvec)