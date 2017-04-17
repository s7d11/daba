#!/usr/bin/python
# -*- coding: utf-8 -*-

# Auteur : Elvis Mboning, Stagiaire 2016, INALCO
# Auteur : Damien Nouvel, MCF, INALCO

# Le principale rôle de ce script est de créer des modèles de données pour l'apprentissage automatique avec CRFTagger.
# Le CRF implémenté provient du module tag de NLTK inspiré de CRFSuite (http://www.nltk.org/api/nltk.tag.html#module-nltk.tag.crf).
# Trois modèles sont possibles : les POS, les tons, les gloses

import sys, re, codecs, random, glob,  time, random
import argparse
import formats,  grammar
from ntgloss import Gloss
from nltk.tag.crf import CRFTagger
from differential_tone_coding import differential_encode

import codecs, sys
sys.stdin = codecs.getreader('utf8')(sys.stdin)
sys.stdout = codecs.getwriter('utf8')(sys.stdout)

def main():

	# déclaration d'une interface en ligne de commande
	aparser = argparse.ArgumentParser(description='Daba disambiguator')
	aparser.add_argument('-l', '--learn', help='Learn model from data (and save as F if provided)', default=None)
	aparser.add_argument('-p', '--pos', help='Prediction for POS', default=False, action='store_true')
	aparser.add_argument('-t', '--tone', help='Prediction for tones', default=False, action='store_true')
	aparser.add_argument('-g', '--gloss', help='Prediction for gloses', default=False, action='store_true')
	aparser.add_argument('-e', '--evalsize', help='Percent of randomized data to use for evaluation (default 10)', default=10)
	aparser.add_argument('-v', '--verbose', help='Verbose output', default=False, action='store_true')

	aparser.add_argument('-d', '--disambiguate', help='Use model F to disambiguate data', default=None)

	# ToDO :
	# aparser.add_argument('-i', '--infile', help='Input file (.html)', default="sys.stdin")
	# aparser.add_argument('-o', '--outfile', help='Output file (.html)', default="sys.stdout")

	args = aparser.parse_args()
	print args

	if args.learn:

		if not (args.pos or args.tone or args.gloss) :
			print 'Choose pos, tone, gloss or combination of them'
			exit(0)

		print 'Make list of files'
		files1 = glob.iglob("../corbama/*/*.dis.html")
		files2 = glob.iglob("../corbama/*.dis.html")
		allfiles = ""
		for file1, file2 in zip(files1, files2):
			allfiles += file1+','+file2+','
		allsents = []

		# verbose :
		if args.tone :
			cnt_non_encodable_tone = 0
			cnt_encodable_tone = 0

		print 'Open files and find features / supervision tags'
		for infile in allfiles.split(','):
			if(len(infile)) :
				print '-', infile
				sent = []
				in_handler = formats.HtmlReader(infile, compatibility_mode=False)
				for token in in_handler:
					tag = ''
					if token.type == 'w' or token.type == 'c':
						tags = ''
						if args.pos:
							for ps in token.gloss.ps:
								tags += ps
						if args.tone:

							# representation différentielle de la tonalisation
							lists_of_equivalence = [{u'e',u'ɛ',u'a'}, {u'o',u'ɔ'}]
							# lists_of_equivalence = []
							[tone_coded, validity] = differential_encode(token.token, \
												    token.gloss.form, \
												 lists_of_equivalence)
							if validity :
								# debogage
								"""
								if cnt_encodable_tone % 5 == 4 : str = "\n"
								else : str = " "
								sys.stdout.write(u"'{}' - '{}' = '{}'\t{}".format(token.gloss.form,token.token,tone_coded,str))
								"""
								tags += tone_coded.encode('raw_unicode_escape')
								cnt_encodable_tone += 1
							else :
								# print token.token, token.gloss.form
								# tags += token.gloss.form.encode('utf-8')
								cnt_non_encodable_tone += 1
						if args.gloss:
							tags += token.gloss.gloss.encode('utf-8')
						sent.append((token.token, tags))
					if token.type == 'c' and token.token in ['.', '?', '!']:
						if len(sent) > 1:
							allsents.append(sent)
						sent = []

		if args.verbose and args.tone :
			print ""
			print  'number of tokens encodables     :', cnt_encodable_tone
        	        print  'number of tokens non-encodables :', cnt_non_encodable_tone
			print u'taux des tons non-codés         :', cnt_non_encodable_tone / float(cnt_encodable_tone)

		datalength = len(allsents)
		p = (1-args.evalsize/100.0)
		print 'Randomize and split the data in train (', int(p*datalength),' sentences) / test (', int(datalength-p*datalength),' sentences)'
		random.seed(123456)
		random.shuffle(allsents)
		train_set = allsents[:int(p*datalength)]
		test_set = allsents[int(p*datalength):datalength]

		if args.verbose and args.tone :
			print train_set;

		print 'Building classifier (CRF/NLTK)'
		tagger = CRFTagger(verbose = args.verbose, training_opt = {'feature.minfreq' : 10})
		t1 = time.time()
		tagger.train(train_set, args.learn)
		t2 = time.time()
		texec = t2-t1
		print "... done in",  time.strftime('%H %M %S', time.localtime(texec))

		print 'Evaluating classifier'
		print tagger.evaluate(test_set)

		if args.verbose:
			print 'Compute detailed output'

	else:
		print 'USE...'
		aparser.print_help()

	exit(0)

if __name__ == '__main__':
	main()

