#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import optparse
import argparse
import formats
from orthography import detone

INFLECTION = [
    'PROG',
    'PFV.INTR',
    'PL',
    'PTCP.PRIV',
    'PTCP.POT',
    'RES'
    ]

def print_token(token, args):
    gt = formats.GlossToken(token)
    print u"{0}\t".format(gt.token).encode('utf-8'),
    if gt.type == 'w':
        if args.tonal:
            get_lemma = lambda x: ''.join(c for c in x if c not in '.')
        elif args.nullify:
            nullify_dict={u'ɔ': 'o', u'ɛ': 'e', u'ɲ': 'ny'}
            def get_lemma(x):
                x = detone(''.join(c for c in x if c not in '.'))
                for source, target in nullify_dict.items():
                    x = x.replace(source, target)
                return x
        else:
            get_lemma = lambda x: detone(''.join(c for c in x if c not in '.'))

        lemmas = []
        tags = set([])
        glosses = []
        for g in gt.glosslist:
            tags = tags.union(g.ps)
            glosses.append(g.gloss)
            if g.morphemes:
                #HACK: if we have no gloss on the top, make up lemma from morphemes
                # targeted at inflected forms analyzed by the parser
                if not g.gloss:
                    stem = ''.join([m.form for m in g.morphemes if m.gloss not in INFLECTION])
                    lemmas.append(get_lemma(stem))
                for m in g.morphemes:
                    glosses.append(m.gloss)
                    if 'mrph' not in m.ps:
                        lemmas.append(get_lemma(m.form))
            else:
                lemmas.append(get_lemma(g.form))
        
        if args.unique:
            print u"\t".join([u'|'.join(filter(None, set(s))) for s in [lemmas, tags, glosses]]).encode('utf-8')
        else:
            print u"\t".join([u'|'.join(filter(None, s)) for s in [lemmas, tags, glosses]]).encode('utf-8')
    else:
        print u"\t".join([gt.token, gt.type, gt.token]).encode('utf-8')

def main():
    oparser = argparse.ArgumentParser(description='Native Daba format to vertical format converter')
    oparser.add_argument('infile', help='Input file (.html)')
    oparser.add_argument("-t", "--tonal", action="store_true", help="Make tonal lemmas")
    oparser.add_argument("-u", "--unique", action="store_true", help="Print only unique lemmas and glosses")
    oparser.add_argument("-n", "--nullify", action="store_true", help="Transliterate all non-ascii characters")
    oparser.add_argument("-v", "--variants", action="store_true", help="Treat all variants in given dictionary as alternative lemmas")
    args = oparser.parse_args()

    reader = formats.HtmlReader(args.infile)

    print "<doc ",
    print u'id="{0}"'.format(os.path.basename(args.infile)).encode('utf-8'),
    metad = dict(reader.metadata)
    try:
        genres = metad['text:genre'].split(';')
        hgenres = [g.split(' : ')[0] for g in genres] + genres
        hgenres.sort()
        metad['text:genre'] = u';'.join(hgenres)
        print u'text_genre="{0}"'.format(metad['text:genre']).encode('utf-8'),
    except (KeyError):
        print 'text_genre="UNDEF"',
    try:
        print u'text_title="{0}"'.format(metad['text:title']).encode('utf-8'),
    except (KeyError):
        print 'text_title="UNDEF"',
    print ">"

    for par in reader.glosses:
        print "<p>"
        for sent,annot in par:
            print "<s>"
            for token in annot:
                print_token(token, args)
            print "</s>"
        print "</p>"

    print "</doc>"

if __name__ == '__main__':
    main()


