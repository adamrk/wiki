#!/usr/bin/python

import wikipedia
import bs4
import nltk.data
import re
import nltk.tokenize
import random
import multiprocessing
import threading
import pdb
import time
import sys
from sendemail import send_email

sentence_detector = nltk.data.load('tokenizers/punkt/english.pickle')

def get_content(title):
    #print title
    try:
        pg = wikipedia.page(title)
    except wikipedia.DisambiguationError as e:
        newtitle = random.sample(e.options, 1)
        pg = wikipedia.page(newtitle)
    pgsoup = bs4.BeautifulSoup(pg.html(), 'html.parser')
    start = pgsoup.get_text().find('[edit]')
    end = pgsoup.get_text().find('References[edit]')
    return pgsoup.get_text()[start:end], pg.revision_id

def tokenize_text(text):
    """ Splits text into a list of sentences. """
    return sentence_detector.tokenize(text.strip())

def label_citations(sentences):
    """ Takes an array of strings and returns an array of the same length
        with strings including citations marked 1 and others marked 0. A
        citation is a number or 'citation needed' in brackets:

        >>> label_citations(["This fact[1] is cited.", "This one isn't"])
        [1, 0]

        If a string begins with a citation, the previous string is marked if
        it exists:

        >>> label_citations(["Blah blah $1 million dollars", "[citation needed] Something else."])
        [1, 0]
    """
    regex = re.compile('\[\d+\]|\[citation needed\]')
    cite_ind = [0 for x in sentences] # this will be returned after canging some 0's to 1's
    for i in xrange(len(sentences)):
        matches = regex.finditer(sentences[i])
        try:
            first = matches.next().start() # location of first citation
        except:
            first = -1 # if no citations
        try:
            second = matches.next().start() # location of second citation
        except:
            second = -1 # no second citation
        if (first > 0) or (second > 0): # this sentence has a citation
            cite_ind[i] = 1
        if (first == 0) and (i > 0): # the previous sentence had a citation
            cite_ind[i-1] = 1

    return cite_ind

def get_words(sentence):
    """ Returns the words in a sentence as a list (removing citations, numbers and characters):

        >>> get_words("Hi, I think you owe[citation needed] me $1.53 for the book 'Lord of the Flies'.")
        ['Hi', 'I', 'think', 'you', 'owe', 'me', 'for', 'the', 'book', 'Lord', 'of', 'the', 'Flies']
    """
    regex = re.compile('\[d+\]|\[citation needed\]') # remove citations
    sentence = regex.sub('', sentence) # replace matches with ''
    specialregex = re.compile('[^a-zA-Z\s\-]') # remove non letters
    sentence = specialregex.sub('', sentence)
    spaceregex = re.compile('\s') # matches whitespace
    words = spaceregex.split(sentence)
    while(True): # remove all blank words
        try:
            words.remove('')
        except:
            break
    return words

def cat_words_sentence(sentence, label):
    """ Returns list of tuples (word, citation, noncitation) """
    return [(word, label, 1 - label) for word in set(get_words(sentence))]

def cat_words_text(text):
    """ Returns list of tuples (word, citation, noncitation) for entire text """
    sentences = tokenize_text(text)
    labels = label_citations(sentences)
    words = []
    for i in range(len(sentences)):
        words += cat_words_sentence(sentences[i], labels[i])
    return words

def reduce_words(words):
    """ Reduces a list of (word, cite, noncite) tuples by summing over each word """
    current_word = None
    current_cite = 0
    current_noncite = 0
    results = []

    for word, cite, noncite in words:
        if word == current_word:
            current_cite += cite
            current_noncite += noncite
        else:
            if current_word != None:
                results.append((current_word, current_cite, current_noncite))
            current_word = word
            current_cite = cite
            current_noncite = noncite

    return results

def thread_get_content( queue_in, queue_out ):
    while True:
        title = queue_in.get()
        if title == None:
            break
        try:
            text, rev_id = get_content(title)
            all_words = cat_words_text(text)
            all_words.sort()
            num_sentences = len(tokenize_text(text))
            queue_out.put((reduce_words(all_words), rev_id, num_sentences))
        except:
            print "Disambiguation Error with %s" % title
            #queue_out.put(('error', 1))
    return 0

def aggregate_words(titles, number_threads):
    """ returns reduced list of (word, cite, noncite) tuples for a list of titles """
    all_words = []
    all_ids = []
    total_num_sentences = 0
    queue_in = multiprocessing.Queue(len(titles) + number_threads)
    queue_out = multiprocessing.Queue(len(titles))
    threads = []
    for i in range(number_threads):
        threads.append(threading.Thread(target = thread_get_content, args = (queue_in, queue_out)))
        threads[i].start()
    for title in titles:
        #print title
        queue_in.put(title)
    for i in range(number_threads):
        queue_in.put(None)

    for i in range(number_threads):
        threads[i].join()
    while queue_out.qsize() > 0:
        #pdb.set_trace()
        words, rev_id, num_sentences = queue_out.get()
        all_words += words
        all_ids.append(rev_id)
        total_num_sentences += num_sentences

    all_words.sort()
    return reduce_words(all_words), all_ids, total_num_sentences

def gen_word_file( num_titles, file_name, number_threads ):
    """ Writes word count results to words/file_name as csv with row format:

        word, (count in cited sentence), (count in uncited sentence)

        Writes page ids and the total number of sentences to words/file_namepid as:

        Number of sentences: (number of sentences)
        pid1
        pid2 ...

        Also emails summary: requires environ vars EMAIL_ADDRESS, EMAIL_PASSWORD, TO_EMAIL
    """
    start_time = time.time()
    titles = []
    for n in range(num_titles/500):
        titles += wikipedia.random(500)
    if num_titles % 500:
        if num_titles % 500 == 1:
            titles += [wikipedia.random(1)] # doesn't return a list for one title
        else:
            titles += wikipedia.random(num_titles % 500)

    # get word counts
    words, ids, tot_num_sentences = aggregate_words(titles, number_threads)
    wordfile = open('words/' + file_name, 'w')
    for (word, cite, noncite) in words:
        wordfile.write("%s %s %s\n" % (word, str(cite), str(noncite)))
    wordfile.close()
    idfile = open('words/' + file_name + 'pid', 'w')
    idfile.write("Number of sentences: %d\n" % tot_num_sentences)
    for rev_id in ids:
        idfile.write("%s\n" % str(rev_id))
    idfile.close()
    end_time = time.time()
    send_email("Finished Aggregating Words\nSearching %d titles in %d threads\nTotal Time: %f minutes\nsaved in %s" \
            % (num_titles, number_threads, (end_time - start_time) / 60, file_name))

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "Usage: ./minewords number_titles file_name number_threads"
        raise SystemExit(1)
    elif not sys.argv[1].isdigit:
        print "First argument must be numeric (number of titles)"
        raise SystemExit(1)
    elif not sys.argv[3].isdigit:
        print "Third argument must be numeric (number of threads)"
        raise SystemExit(1)
    else:
        gen_word_file(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]))
