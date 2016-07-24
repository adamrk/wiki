#!/usr/bin/python

from math import log

def get_num_sentences(file_name):
    """ Reads the number of sentences from file_name + 'pid' """

    pid_file = open(file_name + 'pid', 'r')
    first_line = pid_file.readline()
    return int(first_line.replace('Number of sentences: ', ''))

def calc_tfidf(num_cite, num_non_cite, num_sentences):
    idf = log(float(num_sentences) / float(num_cite + num_non_cite))
    return num_cite * idf

def get_tfidf_list(file_name):
    words_file = open(file_name, 'r')
    lines = words_file.readlines()
    num_sentences = get_num_sentences(file_name)

    tfidf_list = []
    for line in lines:
        entries = line.split(' ')
        word = entries[0]
        num_cite = int(entries[1])
        num_non_cite = int(entries[2])
        cite_tfidf = calc_tfidf(num_cite, num_non_cite, num_sentences)
        noncite_tfidf = calc_tfidf(num_non_cite, num_cite, num_sentences)
        tfidf_list.append((word, cite_tfidf, noncite_tfidf, cite_tfidf - noncite_tfidf))

    tfidf_list.sort(key = lambda x: x[1], reverse = True)
    return tfidf_list


