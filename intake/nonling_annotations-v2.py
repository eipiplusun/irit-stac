#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Automatically adds annotations for non-linguistic events in a game of "Settlers of Catan"

This 'v2' version uses the educe API and not only the python base libraries.
But for now it only works for units annotations, so it's better to use the first version of the script.

NB : this version of the script is not up to date, since a few rules of annotations have been changed.
So if you want to use this specific version, you should compare with the first version and make some changes.

Command line :
python nonling_annotations-v2.py <path to the game>

Example :
python nonling_annotations-v2.py ../../data/pilotnonling/test/
"""


from __future__ import print_function
from collections import namedtuple

import xml.etree.ElementTree as ET
import re
import argparse
import codecs
import sys
import os
import math
import itertools

import educe.stac as STAC
import educe.annotation as ANNO
import educe.glozz as GLOZZ

from csvtoglozz import append_unit, init_mk_id, mk_id
from educe.stac.util.prettifyxml import prettify



# ---------------------------------------------------------------------
# "Units" annotations
# ---------------------------------------------------------------------


def add_units_annotations(doc):
    """
    Add units annotations for non-linguistical event
    
    Parameters
    ----------
    doc :
        document (.aa file) to annotate
    text : string
        raw text extracted from the .ac file

    Returns
    -------
    root :
        modified XML tree with units annotations for non-linguistical event
    """

    OfferRegEx = re.compile(r'(.+) made an offer to trade (\d+) (clay|ore|sheep|wheat|wood) for (\d+) (clay|ore|sheep|wheat|wood)\.')
    #OfferRegEx = re.compile(r'(.+) made an offer to trade (\d+) (clay|ore|sheep|wheat|wood)(, (\d+) (clay|ore|sheep|wheat|wood))* for (\d+) (clay|ore|sheep|wheat|wood)(, (\d+) (clay|ore|sheep|wheat|wood))*\.')
    #TODO this new regex for offer works for discourse annotations
    #but for units, how do we fetch the data ???
    TradeRegEx = re.compile(r'(.+) traded (\d+) (clay|ore|sheep|wheat|wood) for (\d+) (clay|ore|sheep|wheat|wood) from (.+)\.')
    #TradeRegEx = re.compile(r'(.+) traded (\d+) (clay|ore|sheep|wheat|wood)(, (\d+) (clay|ore|sheep|wheat|wood))* for (\d+) (clay|ore|sheep|wheat|wood)(, (\d+) (clay|ore|sheep|wheat|wood))* from (.+)\.')
    #TODO same as offers : it is complicated to fetch the data properly...
    RejectRegEx = re.compile(r'(.+) rejected trade offer\.')

    GetRegEx = re.compile(r'(.+) gets (\d+) (clay|ore|sheep|wheat|wood)\.')
    Get2RegEx = re.compile(r'(.+) gets (\d+) (clay|ore|sheep|wheat|wood), (\d+) (clay|ore|sheep|wheat|wood)\.')

    MonopolyRegEx = re.compile(r'(.+) monopolized (clay|ore|sheep|wheat|wood)\.')

    NewPartialUnits = []

    for anno in doc.units:
        if anno.type == 'NonplayerSegment':
            start = anno.span.char_start
            end = anno.span.char_end
            event = doc.text(anno.text_span())

            if OfferRegEx.search(event) != None: #<X> made an offer to trade <M> <R1> for <N> <R2>.
                mo = OfferRegEx.search(event)
                X = mo.group(1)
                M = mo.group(2)
                R1 = mo.group(3)
                N = mo.group(4)
                R2 = mo.group(5)

                anno.type = 'Offer'
                anno.features['Surface_act'] = 'Question'
                anno.features['Addresse'] = '?'

                left1 = start + len(X) + 24
                right1 = left1 + len(M) + 1 + len(R1)
                spanR1 = ANNO.Span(left1, right1)
                featsR1 = {'Status': 'Givable', 'Quantity': M, 'Correctness': 'True', 'Kind': R1}
                #Res1 = ANNO.Unit(unit_id, spanR1, 'Resource', featsR1, metadata, origin) #comment initialiser unit_id, metadata, et origin ?
                Res1 = STAC.PartialUnit(spanR1, 'Resource', featsR1)
                NewPartialUnits.append(Res1)
                
                right2 = end - 1
                left2 = right2 - len(R2) - 1 - len(N)
                spanR2 = ANNO.Span(left2, right2)
                featsR2 = {'Status': 'Receivable', 'Quantity': N, 'Correctness': 'True', 'Kind': R2}
                #Res2 = ANNO.Unit(unit_id, spanR2, 'Resource', featsR2, metadata, origin)
                Res2 = STAC.PartialUnit(spanR2, 'Resource', featsR2)
                NewPartialUnits.append(Res2)
                continue


            elif TradeRegEx.search(event) != None: #<X> traded <M> <R1> for <N> <R2> from <Y>.
                mo = TradeRegEx.search(event)
                X = mo.group(1)
                M = mo.group(2)
                R1 = mo.group(3)
                N = mo.group(4)
                R2 = mo.group(5)
                Y = mo.group(6)

                anno.type = 'Accept'
                anno.features['Surface_act'] = 'Assertion'
                anno.features['Addresse'] = Y


                """
                Les units de type "Resource" sont tout en bas du fichier XML,
                donc je suppose qu'on peut simplement faire un append et les
                ajouter à la fin. Mais du coup toutes les Resource ne sont pas
                dans l'ordre (d'abord les ressources utilisateurs, ensuite les
                ressources serveur). Je ne sais pas si ça pose problème.
                """

                left1 = start + len(X) + 8
                right1 = left1 + len(M) + 1 + len(R1)
                spanR1 = ANNO.Span(left1, right1)
                featsR1 = {'Status': '?', 'Quantity': M, 'Correctness': 'True', 'Kind': R1}
                #Res1 = ANNO.Unit(unit_id, spanR1, 'Resource', featsR1, metadata, origin)
                Res1 = STAC.PartialUnit(spanR1, 'Resource', featsR1)
                NewPartialUnits.append(Res1)
                
                left2 = right1 + 5
                right2 = left2 + len(N) + 1 + len(R2)
                spanR2 = ANNO.Span(left2, right2)
                featsR2 = {'Status': 'Possessed', 'Quantity': N, 'Correctness': 'True', 'Kind': R2}
                #Res2 = ANNO.Unit(unit_id, spanR2, 'Resource', featsR2, metadata, origin)
                Res2 = STAC.PartialUnit(spanR2, 'Resource', featsR2)
                NewPartialUnits.append(Res2)
                continue


            elif RejectRegEx.search(event) != None: #<Y> rejected trade offer.
                mo = RejectRegEx.search(event)
                Y = mo.group(1)

                anno.type = 'Reject'
                anno.features['Surface_act'] = 'Assertion'
                anno.features['Addresse'] = 'All'
                continue


            elif GetRegEx.search(event) != None: #<Y> gets <N> <R>.
                mo = GetRegEx.search(event)
                Y = mo.group(1)
                N = mo.group(2)
                R = mo.group(3)

                anno.type = 'Other'
                anno.features['Surface_act'] = 'Assertion'
                anno.features['Addresse'] = 'All'

                left = start + len(Y) + 6
                right = end - 1
                spanR = ANNO.Span(left, right)
                featsR = {'Status': 'Possessed', 'Quantity': N, 'Correctness': 'True', 'Kind': R}
                #Res = ANNO.Unit(unit_id, spanR, 'Resource', featsR, metadata, origin)
                Res = STAC.PartialUnit(spanR, 'Resource', featsR)
                NewPartialUnits.append(Res)
                continue

            elif Get2RegEx.search(event) != None: #<Y> gets <N1> <R1>, <N2> <R2>.
                mo = Get2RegEx.search(event)
                Y = mo.group(1)
                N1 = mo.group(2)
                R1 = mo.group(3)
                N2 = mo.group(2)
                R2 = mo.group(3)

                anno.type = 'Other'
                anno.features['Surface_act'] = 'Assertion'
                anno.features['Addresse'] = 'All'

                left1 = start + len(Y) + 6
                right1 = left1 + len(N1) + 1 + len(R1)
                spanR1 = ANNO.Span(left1, right1)
                featsR1 = {'Status': 'Possessed', 'Quantity': N1, 'Correctness': 'True', 'Kind': R1}
                #Res1 = ANNO.Unit(unit_id, spanR1, 'Resource', featsR1, metadata, origin)
                Res1 = STAC.PartialUnit(spanR1, 'Resource', featsR1)
                NewPartialUnits.append(Res1)

                left2 = right1 + 2
                right2 = left2 + len(N2) + 1 + len(R2)
                spanR2 = ANNO.Span(left2, right2)
                featsR2 = {'Status': 'Possessed', 'Quantity': N2, 'Correctness': 'True', 'Kind': R2}
                #Res2 = ANNO.Unit(unit_id, spanR2, 'Resource', featsR2, metadata, origin)
                Res2 = STAC.PartialUnit(spanR2, 'Resource', featsR2)
                NewPartialUnits.append(Res2)
                continue


            elif MonopolyRegEx.search(event) != None: #<X> monopolized <R>.
                mo = MonopolyRegEx.search(event)
                X = mo.group(1)
                R = mo.group(2)

                anno.type = 'Other'
                anno.features['Surface_act'] = 'Assertion'
                anno.features['Addresse'] = 'All'

                right = end - 1
                left = right - len(R)
                spanR = ANNO.Span(left, right)
                featsR = {'Status': 'Possessed', 'Quantity': '?', 'Correctness': 'True', 'Kind': R}
                #Res = ANNO.Unit(unit_id, spanR, 'Resource', featsR, metadata, origin)
                Res = STAC.PartialUnit(spanR, 'Resource', featsR)
                NewPartialUnits.append(Res)
                continue

            else:
                anno.type = 'Other'
                anno.features['Surface_act'] = 'Assertion'
                anno.features['Addresse'] = 'All'
                continue

    NewUnits = STAC.create_units('', doc, 'stac', NewPartialUnits)
    doc.units.extend(NewUnits)

    return doc



# ---------------------------------------------------------------------
# "Discourse" annotations
# ---------------------------------------------------------------------



class PartialRelation(namedtuple("PartialRelation", "span type")):
    """
    Partially instantiated relation, for use when you want to programmatically
    insert annotations into a document

    A partially instantiated relation does not have any metadata (creation date,
    etc); as these will be derived automatically
    """
    pass

def create_relations(_, doc, author, partial_relations):
    """Create a collection of relations from their partial specification.

    Parameters
    ----------
    _: anything
        Anonymous parameter whose value is ignored. It was apparently
        supposed to contain a FileId. I suppose the intention was to
        follow a signature similar to other functions.
    doc: Document
        Containing document.
    author: string
        Author for the new relations.
    partial_relations: iterable of `PartialRelation`
        Partial specification of the new relations.

    Returns
    -------
    res: list of Relations
        Collection of instantiated new relation objects.

    Notes
    -----
    As of 2016-05-11, this function does not seem to be used anymore
    in the codebase.
    It used to be called in `irit-stac/segmentation/glozz-segment`,
    which was deleted 2015-06-08 (commit e2373c03) because it was not
    used.
    """
    # It seems like Glozz uses the creation-date metadata field to
    # identify units (symptom: units that have different ids, but
    # same date don't appear in UI).
    #
    # Also, other tools in the STAC pipeline seem to use the convention
    # of negative numbers for fields where the notion of a creation date
    # isn't very appropriate (automatically derived annotations)
    #
    # So we take the smallest negative date (largest absolute value)
    # and subtract from there.
    #
    # For readability, we'll jump up a couple powers of 10
    creation_dates = [int(u.metadata['creation-date']) for u in doc.units]
    smallest_neg_date = min(creation_dates)
    if smallest_neg_date >= 0:
        smallest_neg_date = -1  # don't use 0 because log10(0)
    # next two power of 10
    id_base = 10 ** (int(math.log10(abs(smallest_neg_date))) + 2)

    def mk_creation_date(counter):
        "from counter to string for next available creation date"
        return str(0 - (id_base + counter))

    def mk_relation(partial, counter):
        "from PartialUnit and counter to Unit"

        # Note that Glozz seems to identify items by the pair of author and
        # creation date, ignoring the unit ID altogether (assumed to be
        # author_date)
        creation_date = mk_creation_date(counter)
        metadata = {'author': author,
                    'creation-date': creation_date,
                    'lastModifier': 'n/a',
                    'lastModificationDate': '0'}
        features = {'Comments': 'Please write in remarks...',
                    'Argument_scope': 'Please choose...'}
        relation_id = '_'.join([author, str(counter)])
        return ANNO.Relation(relation_id,
                    partial.span,
                    partial.type,
                    features,
                    metadata)

    return [mk_relation(x, i) for x, i in
            itertools.izip(partial_relations, itertools.count(0))]





def add_discourse_annotations(doc):
    """
    Add discourse annotations for non-linguistical event
    
    Parameters
    ----------
    doc :
        document (.aa file) to annotate
    text : string
        raw text extracted from the .ac file

    Returns
    -------
    root :
        modified XML tree with discourse annotations for non-linguistical events
    """

    JoinEvents = dict()
    StartEvent = ""
    DiceEvent = []
    RobberEvent = []
    TradeEvent = ""
    MonopolyEvent = ""


    JoinRegEx = re.compile(r'(.+) joined the game\.')
    SitDownRegEx = re.compile(r'(.+) sat down at seat (\d)\.')

    DiceRegEx = re.compile(r'(.+) rolled a (\d) and a (\d)\.')
    GetRegEx = re.compile(r'(.+) gets (\d+) (clay|ore|sheep|wheat|wood)\.')
    Get2RegEx = re.compile(r'(.+) gets (\d+) (clay|ore|sheep|wheat|wood), (\d+) (clay|ore|sheep|wheat|wood)\.')
    NoGetRegEx = re.compile(r'No player gets anything\.')

    SoldierRegEx = re.compile(r'(.+) played a Soldier card\.')
    Discard1RegEx = re.compile(r'(.+) needs to discard\.')
    Discard2RegEx = re.compile(r'(.+) discarded (\d+) resources\.')
    Robber1RegEx = re.compile(r'(.+) will move the robber\.')
    Robber2RegEx = re.compile(r'(.+) moved the robber\.')
    Robber3RegEx = re.compile(r'(.+) moved the robber, must choose a victim\.')
    StoleRegEx = re.compile(r'(.+) stole a resource from (.+)')

    OfferRegEx = re.compile(r'(.+) made an offer to trade (\d+) (clay|ore|sheep|wheat|wood)(, (\d+) (clay|ore|sheep|wheat|wood))* for (\d+) (clay|ore|sheep|wheat|wood)(, (\d+) (clay|ore|sheep|wheat|wood))*( from the bank or a port)?\.')

    CantRegEx = re.compile(r"You can't make that trade\.")
    TradeRegEx = re.compile(r'(.+) traded (\d+) (clay|ore|sheep|wheat|wood)(, (\d+) (clay|ore|sheep|wheat|wood))* for (\d+) (clay|ore|sheep|wheat|wood)(, (\d+) (clay|ore|sheep|wheat|wood))* from (.+)\.')
    RejectRegEx = re.compile(r'(.+) rejected trade offer\.')
    CardRegEx = re.compile(r'(.+) played a Monopoly card\.')
    MonopolyRegEx = re.compile(r'(.+) monopolized (clay|ore|sheep|wheat|wood)\.')


    NewPartialRelations = []

    for anno in doc.units:
        if anno.type == 'NonplayerSegment':
            start = anno.span.char_start
            end = anno.span.char_end
            event = doc.text(anno.text_span())

            # Join / sit down events

            if JoinRegEx.search(event) != None: #<X> joined the game.
                mo = JoinRegEx.search(event)
                X = mo.group(1)
                JoinEvents[X] = anno._anno_id
                continue

            elif SitDownRegEx.search(event) != None: #<X> sat down at seat <N>.
                mo = SitDownRegEx.search(event)
                X = mo.group(1)
                rspan = ANNO.RelSpan(JoinEvents[X], anno._anno_id)
                #rel = ANNO.Relation(rel_id, rspan, 'Sequence', features, metadata)
                rel = PartialRelation(rspan, 'Sequence')
                NewPartialRelations.append(rel)
                del JoinEvents[X]
                continue

            # Game started / Board layout set events

            elif event == "Game started.":
                StartEvent = anno._anno_id
                continue

            elif event == "Board layout set.":
                rspan = ANNO.RelSpan(StartEvent, anno._anno_id)
                #rel = ANNO.Relation(rel_id, rspan, 'Sequence', features, metadata)
                rel = PartialRelation(rspan, 'Sequence')
                NewPartialRelations.append(rel)
                continue
                

            # Resource distribution events

            elif DiceRegEx.search(event) != None: #<X> rolled a <M1> and a <M2>.
                mo = DiceRegEx.search(event)
                M1 = int(mo.group(2))
                M2 = int(mo.group(3))
                if M1 + M2 != 7: # Resource distribution event
                    if len(DiceEvent) > 0:
                        if len(DiceEvent) == 2: # Resource distribution : 1 player
                            rspan = ANNO.RelSpan(DiceEvent[0], DiceEvent[1])
                            #rel = ANNO.Relation(rel_id, rspan, 'Sequence', features, metadata)
                            rel = PartialRelation(rspan, 'Sequence')
                            NewPartialRelations.append(rel)
                        else: # Resource Distribution : 2 or more players
                            #cdu = ANNO.Schema(rel_id, DiceEvent[1:], relations, schemas, 'Complex_discourse_unit', features, metadata)
                            #rspan = ANNO.RelSpan(DiceEvent[0], cdu._anno_id)
                            #rel = ANNO.Relation(rel_id, rspan, 'Result', features, metadata)
                            #rel = PartialRelation(rspan, 'Result')
                            #NewPartialRelations.append(rel)
                            for i in range(1,len(DiceEvent)-1):
                                rspan = ANNO.RelSpan(DiceEvent[i], DiceEvent[i+1])
                                #rel = ANNO.Relation(rel_id, rspan, 'Continuation', features, metadata)
                                rel = PartialRelation(rspan, 'Continuation')
                                NewPartialRelations.append(rel)
                        DiceEvent[:] = []
                    DiceEvent.append(anno._anno_id)
                else: # M1 + M2 == 7 : Robber event
                    if RobberEvent != []:
                        raise Exception("add_discourse_annotations : la liste RobberEvent n'a pas été vidée!")
                    RobberEvent.append(anno._anno_id)
                continue

            elif GetRegEx.search(event) != None: #<Y> gets <N> <R>.
                DiceEvent.append(anno._anno_id)
                continue

            elif Get2RegEx.search(event) != None: #<Y> gets <N1> <R1>, <N2> <R2>.
                DiceEvent.append(anno._anno_id)
                continue

            elif NoGetRegEx.search(event) != None: #No player gets anything.
                rspan = ANNO.RelSpan(DiceEvent[0], anno._anno_id)
                #rel = ANNO.Relation(rel_id, rspan, 'Result', features, metadata)
                rel = PartialRelation(rspan, 'Result')
                NewPartialRelations.append(rel)
                DiceEvent[:] = []
                continue

            # Robber events

            elif SoldierRegEx.search(event) != None: #<X> played a Soldier card.
                if RobberEvent != []:
                    raise Exception("add_discourse_annotations : la liste RobberEvent n'a pas été vidée!")
                RobberEvent.append(anno._anno_id)
                continue

            elif Discard1RegEx.search(event) != None: #<Y> needs to discard.
                RobberEvent.append(anno._anno_id)
                continue

            elif Discard2RegEx.search(event) != None: #<Y> discarded <N> resources.
                RobberEvent.append(anno._anno_id)
                continue

            elif Robber1RegEx.search(event) != None: #<X> will move the robber.
                RobberEvent.append(anno._anno_id)
                continue

            elif Robber2RegEx.search(event) != None: #<X> moved the robber.
                RobberEvent.append(anno._anno_id)
                #cdu = ANNO.Schema(rel_id, RobberEvent[1:], relations, schemas, 'Complex_discourse_unit', features, metadata)
                #rspan = ANNO.RelSpan(RobberEvent[0], cdu._anno_id)
                #rel = ANNO.Relation(rel_id, rspan, 'Result', features, metadata)
                #rel = PartialRelation(rspan, 'Result')
                #NewPartialRelations.append(rel)
                for i in range(1,len(RobberEvent)-1):
                    rspan = ANNO.RelSpan(RobberEvent[i], RobberEvent[i+1])
                    #rel = ANNO.Relation(rel_id, rspan, 'Sequence', features, metadata)
                    rel = PartialRelation(rspan, 'Sequence')
                    NewPartialRelations.append(rel)
                RobberEvent[:] = []
                continue

            elif Robber3RegEx.search(event) != None: #<X> moved the robber, must choose a victim.
                RobberEvent.append(anno._anno_id)
                continue

            elif StoleRegEx.search(event) != None: #<X> stole a resource from <Z>.
                RobberEvent.append(anno._anno_id)
                #cdu = ANNO.Schema(rel_id, RobberEvent[1:], relations, schemas, 'Complex_discourse_unit', features, metadata)
                #rspan = ANNO.RelSpan(RobberEvent[0], cdu._anno_id)
                for i in range(1,len(RobberEvent)-1):
                    rspan = ANNO.RelSpan(RobberEvent[i], RobberEvent[i+1])
                    #rel = ANNO.Relation(rel_id, rspan, 'Sequence', features, metadata)
                    rel = PartialRelation(rspan, 'Sequence')
                    NewPartialRelations.append(rel)
                RobberEvent[:] = []
                continue

            # Trade events
            # HYPOTHESIS : only one offer can be made at a time (not sure if true, needs in/confirmation)

            elif OfferRegEx.search(event) != None: #<X> made an offer to trade <M> <R1> for <N> <R2>.
                TradeEvent = anno._anno_id
                continue

            elif CantRegEx.search(event) != None: #You can't make that trade.
                rspan = ANNO.RelSpan(TradeEvent, anno._anno_id)
                #rel = ANNO.Relation(rel_id, rspan, 'Question-answer_pair', features, metadata)
                rel = PartialRelation(rspan, 'Question-answer_pair')
                NewPartialRelations.append(rel)
                continue

            elif TradeRegEx.search(event) != None: #<X> traded <M> <R1> for <N> <R2> from <Y>.
                rspan = ANNO.RelSpan(TradeEvent, anno._anno_id)
                #rel = ANNO.Relation(rel_id, rspan, 'Question-answer_pair', features, metadata)
                rel = PartialRelation(rspan, 'Question-answer_pair')
                NewPartialRelations.append(rel)
                continue

            elif RejectRegEx.search(event) != None: #<Y> rejected trade offer.
                rspan = ANNO.RelSpan(TradeEvent, anno._anno_id)
                #rel = ANNO.Relation(rel_id, rspan, 'Question-answer_pair', features, metadata)
                rel = PartialRelation(rspan, 'Question-answer_pair')
                NewPartialRelations.append(rel)
                continue

            # Monopoly events

            elif CardRegEx.search(event) != None: #<X> played a Monopoly card.
                if MonopolyEvent != "":
                    raise Exception("add_discourse_annotations : la chaîne MonopolyEvent n'a pas été vidée!")
                MonopolyEvent = anno._anno_id
                continue

            elif MonopolyRegEx.search(event) != None: #<X> monopolized <R>.
                rspan = ANNO.RelSpan(MonopolyEvent, anno._anno_id)
                #rel = ANNO.Relation(rel_id, rspan, 'Sequence', features, metadata)
                rel = PartialRelation(rspan, 'Sequence')
                NewPartialRelations.append(rel)
                MonopolyEvent = ""
                continue


    """
    For resources distributions, we complete the XML tree and empty the list at the next dice roll.
    So for the last turn we may have forgotten to annotate some events.
    """
    if len(DiceEvent) > 0:
        if len(DiceEvent) == 2: # Resource distribution : 1 player
            rspan = ANNO.RelSpan(DiceEvent[0], DiceEvent[1])
            #rel = ANNO.Relation(rel_id, rspan, 'Result', features, metadata)
            rel = PartialRelation(rspan, 'Result')
            NewPartialRelations.append(rel)
        else: # Resource Distribution : 2 or more players
            #cdu = ANNO.Schema(rel_id, RobberEvent[1:], relations, schemas, 'Complex_discourse_unit', features, metadata)
            #rspan = ANNO.RelSpan(DiceEvent[0], cdu._anno_id)
            #rel = ANNO.Relation(rel_id, rspan, 'Result', features, metadata)
            #rel = PartialRelation(rspan, 'Result')
            #NewPartialRelations.append(rel)
            for i in range(1,len(DiceEvent)-1):
                rspan = ANNO.RelSpan(DiceEvent[i], DiceEvent[i+1])
                #rel = ANNO.Relation(rel_id, rspan, 'Continuation', features, metadata)
                rel = PartialRelation(rspan, 'Continuation')
                NewPartialRelations.append(rel)
        DiceEvent[:] = []



    NewUnits = create_relations('', doc, 'stac', NewPartialRelations)
    doc.relations.extend(NewUnits)
    return doc




# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------



def main():

    #ligne de commande : python nonling_annotations-v2.py ../../data/pilotnonling/test/

    def to_annotate(fileId):
        stage = fileId.stage
        return stage == 'units' or stage == 'discourse'

    parser = argparse.ArgumentParser()
    parser.add_argument('Directory', help = 'directory where the files to annotate are')
    args = parser.parse_args()
    Directory = args.Directory

    reader = STAC.Reader(Directory)
    subset = reader.filter(reader.files(), lambda k: to_annotate(k))
    corpus= reader.slurp(subset, verbose=True)

    for key in corpus.keys():
        doc = corpus[key]
        data = str(key).split(' ')
        game = data[0]
        part = data[1][1:-1] #the integer that interests us is between brackets
        stage = data[2]
        metal = data[3]
        path = Directory + game + '/' + stage + '/' + metal + '/'
        print(game, part, stage, metal)
        if stage == 'units':
            newdoc = add_units_annotations(doc)
            GLOZZ.write_annotation_file(path + game + '_' + part + '.aa', newdoc)
            continue
        elif stage == 'discourse':
            newdoc = add_discourse_annotations(doc)
            GLOZZ.write_annotation_file(path + game + '_' + part + '.aa', newdoc)
            continue
        else:
            raise Exception("main : you shouldn't be here!")
            continue


if __name__ == '__main__':
    main()
