#!/usr/bin/env python

""" import vanilla unicode and run lda"""

__author__ = 'kln-courses'

## import unicode vanilla
import io, os, re, unicodedata

# sort on integer
num = re.compile(r'(\d+)')
def numericalsort(value):
    parts = num.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts

# normalize: punctuation, numeric, character
def vanilla_folder(datapath):
    docs = []
    regex = re.compile('^[a-zA-Z]')
    files = sorted(os.listdir(datapath), key = numericalsort)
    os.chdir(datapath)
    for file in files:
        print "file import: " + file
        with io.open(file,'r',encoding = 'utf8') as f:
            text = f.read()
            text = unicodedata.normalize('NFKD', text).encode('ascii','ignore')
            docs.append(regex.sub('', text))
    return docs

## tokenize
# normalize: case folding
def vanilla_tokenize(docs):
    unigrams = [[w for w in doc.lower().split()] for doc in docs]
    return unigrams

## chunk tokenized documents in n chunks
from gensim.utils import chunkize
def vanilla_chunk(unigrams,n):
    chunks = []
    for doc in unigrams:
        clen = len(doc)/n
        for chunk in chunkize(doc,clen):
            chunks.append(chunk)
    return chunks

## prune top percentile and bottom percentile
from collections import defaultdict
import numpy as np
def vanilla_prune(unigrams,mxper,mnper):
    frequency = defaultdict(int)
    for doc in unigrams:
        for unigram in doc:
            frequency[unigram] += 1
    freqs = [val for val in frequency.values()]
    mx = np.percentile(freqs, mxper)
    mn = np.percentile(freqs, mnper)
    unigrams_prune = [[unigram for unigram in doc if frequency[unigram] > mn and frequency[unigram] <= mx] for doc in unigrams]
    return unigrams_prune

## lemmatize with NLTK & POS tags from WordNet
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
# change from treebank to wordnet POS tags
def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN
# lemmatize
def vanilla_lemmatizer(unigrams):
    wordnet_lemmatizer = WordNetLemmatizer()
    unigrams_lemma = unigrams
    for i, _ in enumerate(unigrams):
        tmp = pos_tag(unigrams[i])
        for ii, _ in enumerate(tmp):
            unigrams_lemma[i][ii] = wordnet_lemmatizer.lemmatize(tmp[ii][0],get_wordnet_pos(tmp[ii][1]))
    return unigrams_lemma

## build corpus
datapath = "/home/kln/corpora/dabiq/dabiq_vanilla"
os.listdir(datapath)

texts = vanilla_folder(datapath)

tokens = vanilla_tokenize(texts)
chunks100 = vanilla_chunk(tokens,100)
prune98 = vanilla_prune(chunks100,98,0)
lemmanoun = vanilla_lemmatizer(prune98)

## train LDA model
from gensim import corpora, models
# bag-of-words
dictionary = corpora.Dictionary(lemmanoun)
corpus = [dictionary.doc2bow(chunk) for chunk in lemmanoun]
# for reproducibility
fixed_seed = 1234
np.random.seed(fixed_seed)
# train model on k topics
k = 20
mdl = models.LdaModel(corpus, id2word=dictionary, num_topics=k)

print 'Z:'
for i in range(k):
    print mdl.show_topic(i)
    print '----------'

print 'Theta:'
for i in range(k):
    print lemmanoun[i][0:19]
    print mdl.get_document_topics(corpus[i])
    print '----------'
    
    
### export theta
import numpy as np
docdist = []    
for d in corpus:
    doc = mdl.get_document_topics(d, minimum_probability = 0)
    for t in doc:
        docdist.append(t[1])
dim = (len(docdist)/k,k) 
docmat = np.asarray(docdist).reshape(dim)

# dump matrix to csv
os.chdir('/home/kln')
np.savetxt("data/theta.csv", docmat, delimiter=",")




