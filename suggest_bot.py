#!/usr/bin/python
# suggest_bot.py
# Saito 2017

"""This creates robot assisted poems!


"""
import argparse
import random
import sys

import geo_converter
import editor
import geosearchclass
import ngrams
import utils
import write


def create_poem(g=None, default_words=None, ngram=None):
    """ This creates a poem with user input by suggesting from the words supplied.

    A user can use the word, decline the word, or add their own input.
    g is for geosearchclass. It is none by default.
    default_words is a list of words that can be enabled by default.
    """
    words = []
    formatted_poem = ''''''
    # for no, yes and finish (print poem)
    options = ['y', 'n', 's', 'd', 'r', 'e', 'f', '\n']
    keep_adding = True
    added_default = False
    use_phrases = False
    random_word = False
    print "\n\n\n"
    print """

        This robot poet will present a series of suggestions. You can
        either use these suggestions, edit them, or type your own
        input.  You may also add more words from geolocated tweets to
        your word corpus. The words you choose or add will be
        succeessively added to a poem, which will be printed and saved
        to an output file. To add a new line, type '\\n'. To finish
        writing type f (for finish).

        y: yes use this word
        n: no, skip this and give me a new phrase
        s: search: add more geolocated terms from twitter
        d: default words added to corpus
        r: get random word, when running markov model
        e: edit the text
        \\n: enter line
        f: finish

    """

    if ngram:
        print "Populating seed words from markov chain ngram"
        values = sum(ngram.values(), [])
        words.extend(values)
    chosen = ""
    while keep_adding:
        if len(words) == 0:
            print "Nothing in corpus. Type d for default words or s to search\
twitter"
        if ngram and formatted_poem and not random_word:
            tokens = utils.tokenize_normal_words(formatted_poem)
            num = random.random()
            potential_word = ""
            if len(tokens) > 0:
                #  This is for trigrams
                if num > 0.66 and len(tokens) > 1:  # 50% of time get trigram
                    potential_word = tokens_to_word(tokens, ngram, 2)
                    if potential_word:
                        chosen = potential_word
                    else:
                        potential_word = tokens_to_word(tokens, ngram, 1)
                        if potential_word:
                            chosen = potential_word
                        else:
                            chosen = random.choice(words)
                elif num > 0.33:  # 30% of time get bigram
                    potential_word = tokens_to_word(tokens, ngram, 1)
                    if potential_word:
                        chosen = potential_word
                    else:
                        chosen = random.choice(words)
                else:  # 20% of time get random word
                    chosen = random.choice(words)
            else:
                chosen = random.choice(words)
        elif words:
            chosen = random.choice(words)
            random_word = False
        else:
            pass
        if chosen:
            print chosen,
        response_string = "     " + str(options) + " or your own :"
        response = raw_input(response_string)
        # include the chosen word:
        if response == "y":
            if len(words) == 0:
                continue
            formatted_poem = formatted_poem + ''' ''' + chosen
            print
            print formatted_poem
            continue
        elif response == "n":
            continue
        elif response == "r":
            random_word = True
        elif response == "s":
            print "Searching geo-located tweets to add to vocab"
            print "This can only be used once every 5 seconds"
            if g is None:
                g = geosearchclass.GeoSearchClass()
            search_results = g.search()

            phrase_response = ""
            while phrase_response not in ["y", "n"]:
                phrase_response = raw_input("\nWould you like to use phrases (\
(otherwise, just words)? [y/n]: ")
                if phrase_response == "y":
                    list_of_info_dicts = write.parse_tweets(search_results)
                    filtered_words = []
                    if len(list_of_info_dicts) < 1:
                        filtered_words = utils.tokenize_and_filter(
                            search_results)
                    else:
                        for d in list_of_info_dicts:
                            filtered_words.append(d['phrase'])
                elif phrase_response == "n":
                    filtered_words = utils.tokenize_and_filter(search_results)
                else:
                    continue
            print "\n\n\nAdding these Twitter words: "
            print filtered_words
            print "\n"
            words.extend(filtered_words)
            continue
        elif response == "d":
            if not added_default:
                print "\nadding in these words to corpus:"
                print default_words
                print "\n\n\n"
                words.extend(default_words)
                options.remove('d')
                added_default = True
        elif response == "e":
            formatted_poem = editor.create_editor(formatted_poem)
            print formatted_poem
        elif response not in options:
            response = response.replace('\\n', '\n')
            formatted_poem = formatted_poem + ''' ''' + response
            print
            print formatted_poem
            continue
        elif response == "f":
            print
            print formatted_poem
            keep_adding = False
    return formatted_poem


def tokens_to_word(tokens, ngram, n):
    seed = tokens[-n:]
    t = tuple(seed)
    word = ngrams.generate(ngram, t)
    return word


def get_parser():
    """ Creates a command line parser

    --doc -d
    --help -h
    --params -p
    --input -i
    --markov -m
    --output -o
    --address -a

    This automatically grabs arguments from sys.argv[]
    """

    parser = argparse.ArgumentParser(
        description='Create a robot assisted poem.')

    parser.add_argument(
        '-d', '--doc', action='store_true',
        help='print module documentation and exit')
    parser.add_argument(
        '-m', '--markov',
        help='''specify a TEXT file to mimic. This will\
 Train a markov chain word predictor\
 using this text. This will basically create a robotic poet!''')
    parser.add_argument(
        '-p', '--params',
        help='''specify a PARAMS file to use as the parameter file.
        If not specified, will use 'params.txt' for searches.''')
    parser.add_argument(
        '-i', '--input',
        help='''specify an input file to use as word seed file.
        ''')
    parser.add_argument(
        '-o', '--output',
        help='''specify an OUTPUT file to write to.
        Default is output.txt''')
    parser.add_argument(
        '-a',
        '--address',
        help='''give an ADDRESS to get geocoordinates for.''')

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.doc:
        print __doc__
        sys.exit()

    g = geosearchclass.GeoSearchClass()

    if args.params:
        print 'Using parameters from ' + str(args.params)
        # turn parameter file into dictionary
        g.set_params_from_file(args.params)
        
    if args.address:
        print "Finding geocoordates for address:\n{}".format(args.address)
        coords = geo_converter.get_geocoords_from_address(args.address)
        if coords:
            g.latitude = coords[0]
            print "Found this latitude:"
            print g.latitude
            g.longitude = coords[1]
            print "Found this longitude:"
            print g.longitude
        else:
            print "Failed to find coordinates. Exiting."
            sys.exit()

    if args.input:
        text = utils.load_file(args.input)
        tokens = utils.tokenize_normal_words(text)
        for_poem = utils.filter_words(tokens)
    else:
        for_poem = get_default_words()

    if args.markov:
        if args.input:
            raise StandardError("Can only input a single text file. \
use --markov <your_text_file.txt>")
        else:
            text = utils.load_file(args.markov)
            # ngram = ngrams.make_ngram(text, 2)
            ngram = ngrams.make_bigram_trigram_dictionary(text)
            formatted_poem = create_poem(g, for_poem, ngram)
    else:
        formatted_poem = create_poem(g, for_poem)

    if args.output:
        print '\nwriting formatted poem to ' + str(args.output)
        output_file = args.output
    else:
        print "\nwriting formatted poem to poem.txt"
        output_file = "poem.txt"

    utils.save_file(output_file, formatted_poem)

    
def get_default_words():
    # These are some good default words used in the poem creator above
    for_poem = [  # emerging tech shit
        'Agricultural', 'ecological', 'systems', 'meat', 'genetically',
        'modified', 'precision', 'vertical', 'farming', 'printing', 'contour',
        'crafting', 'artificial', 'uterus', 'transplant', 'cryonics',
        'vitrification', 'suspended animation', 'de-extinction',
        'genetic engineering', 'gene therapy', 'life extension',
        'engineered negligible senescence',
        'nanomedicine', 'nanosensors', 'regenerative', 'medicine',
        'stem-cell', 'tissue engineering', 'robot assisted surgery',
        'synthetic biology', 'synthetic genomics', 'virus',
        'whole genome sequencing', 'bionic contact lens',
        'head-mounted display', 'virtual',
        'retinal', 'e-textiles', 'molecular', 'electronics', 'thermal',
        'copper', 'pillar', 'airborne wind turbine', 'artificial',
        'photosynthesis', 'biofuels', 'solar', 'power', 'fusion', 'fuel cell',
        'molten salt', 'photovoltaic', 'translation', 'machine vision',
        'speech recognition', 'fourth-generation', 'optical discs', 'storage',
        'holographic data', 'millipede', 'optical computing',
        'quantum computing', 'quantum cryptography', 'RFID', 'software-defined',
        'three-dimensional', 'integrated', 'circuit', 'artificial muscle',
        'superconductivity', 'superfluidity', 'metamaterials', 'cloaking',
        'metal', 'multi-function', 'superalloy', 'synthetic diamond',
        'weapon', 'laser', 'particle-beam', 'coilgun', 'plasma', 'stealth',
        'brain computer interface', 'retinal implant',
        'self reconfiguring modular robot', 'swarm robotics', 'pulse',
        'solar sail', 'backpack',
        'helicopter', 'delivery drone', 'detonation', 'engine', 'driverless\
        car', 'automated', 'vacuum', 'collection', 'cloak', 'immersive',
        'dilemma',
        # japanese shit
        'august', 'black', 'chinese', 'Gaugin', 'heaven', 'illusion',
        'island', 'Kibune', 'Michinoku', 'milky', 'Mogami', 'mother',
        'mount', 'mountain', 'Musashi', 'night', 'observe', 'October',
        'portrait', 'river', 'Roman', 'SUNSHINE', 'should', 'submit',
        'tangled', 'Tokiwa', 'washing', 'watching', 'world', 'Yoshino',
        'actual', 'admires', 'after', 'afterlife', 'again', 'against',
        'alive', 'almost', 'always', 'amidah', 'ancient', 'another',
        'armor', 'armored', 'arrayed', 'arrows', 'autumn', 'autumns',
        'awakening', 'bamboo', 'bathe', 'beads', 'become', 'becoming',
        'begins', 'behind', 'between', 'beyond', 'birth', 'blade',
        'blind', 'bloom', 'blooming', 'blossoms', 'break', 'breaks',
        'breeze', 'bridge', 'brings', 'brother', 'brush', 'buried',
        'burning', 'butterfly', 'calligraphy', 'calling', 'camellia',
        'cancer', 'candle', 'canyon', 'caress', 'carry', 'ceaseless',
        'cedars', 'center', 'certain', 'change', 'chanted', 'chases',
        'cherries', 'cherry', 'child', 'chill', 'chorus', 'chrysanthemum',
        'chrysanthemums', 'cicada', 'clock', 'closer', 'color', 'combing',
        'compare', 'completely', 'content', 'continent', 'corona',
        'could', 'crest', 'crossing', 'curve', 'dancers', 'darkens',
        'darkness', 'death', 'deepens', 'delusions', 'deserted',
        'destitute', 'distance', 'dream', 'dreaming', 'dreams', 'drips',
        'drops', 'drums', 'dying', 'early', 'eclipse', 'egret', 'ended',
        'entangling', 'escaped', 'evening', 'every', 'exhausted',
        'faintly', 'falling', 'falls', 'feeling', 'field', 'finished',
        'fireflies', 'firefly', 'fireworks', 'first', 'flash', 'flesh',
        'flies', 'float', 'flowers', 'flowing', 'flows', 'follow',
        'forever', 'forlorn', 'forth', 'fragile', 'frozen', 'garden',
        'gates', 'gauntlet', 'gauzy', 'gazing', 'geese', 'giant',
        'glances', 'going', 'grapes', 'grass', 'grasses', 'guards',
        'guided', 'gunshots', 'harbor', 'heart', 'heaven', 'hillside',
        'holding', 'horse', 'house', 'houses', 'hundred', 'hydrangea',
        'idling', 'image', 'insane', 'interrogation', 'invisible',
        'irrevocable', 'itself', 'journey', 'juice', 'karma', 'killed',
        'knotty', 'knowing', 'knowledge', 'later', 'leave', 'leaving',
        'letting', 'light', 'lightning', 'lilacs', 'limit', 'little',
        'lodging', 'longing', 'looks', 'loving', 'making', 'mantle',
        'marshes', 'memories', 'messengers', 'meteor', 'midnight',
        'might', 'mirror', 'mirrored', 'missed', 'month', 'moonlight',
        'mother', 'motorcycle', 'mouth', 'moving', 'myself', 'night',
        'nightingale', 'nights', 'north', 'nothing', 'nowhere', 'ocean',
        'octopus', 'opening', 'orchid', 'other', 'paradise', 'parting',
        'passes', 'passions', 'pattern', 'pealing', 'pears', 'people',
        'period', 'petal', 'place', 'plain', 'planters', 'playing',
        'poems', 'poppy', 'press', 'primal', 'primeval', 'purple',
        'quivered', 'rabbits', 'radiation', 'radio', 'rapids', 'reaches',
        'reality', 'really', 'recklessly', 'reconciled', 'relax',
        'remember', 'replies', 'returning', 'right', 'ripple', 'ripples',
        'rising', 'river', 'riverbank', 'rocky', 'rowing', 'running',
        'saying', 'seals', 'seeing', 'serpent', 'shadow', 'shall',
        'shaped', 'shattered', 'shell', 'shelves', 'shift', 'shining',
        'shore', 'short', 'shower', 'sided', 'silkworm', 'silkworms',
        'single', 'sleep', 'slept', 'slightest', 'slowly', 'smell',
        'snail', 'soiled', 'soldiers', 'solitary', 'somehow', 'something',
        'sometimes', 'sound', 'speak', 'spill', 'spilling', 'spray',
        'spreads', 'spring', 'squid', 'stable', 'stars', 'station',
        'steel', 'stirrups', 'stolen', 'stomach', 'stone', 'storm',
        'straighten', 'strands', 'strange', 'straw', 'streaming',
        'stripes', 'study', 'submit', 'summer', 'sunlight', 'sunrise',
        'sunset', 'sutra', 'sweet', 'swimsuit', 'tangled', 'taste',
        'temple', 'tethered', 'their', 'there', 'these', 'thighs',
        'thing', 'things', 'think', 'thought', 'thousand', 'throat',
        'through', 'throughout', 'tiger', 'tight', 'tossing', 'total',
        'toward', 'trace', 'transferred', 'traps', 'truth', 'turning',
        'turns', 'twilight', 'unborn', 'under', 'utterly', 'vanished',
        'village', 'visible', 'waiting', 'wandering', 'warrior',
        'warriors', 'washed', 'water', 'waves', 'weight', 'where',
        'which', 'whistling', 'white', 'whitecaps', 'willow', 'wings',
        'winter', 'wisteria', 'without', 'woman', 'world', 'yanking',
        'years', 'yesterday', 'yielded', 'young']
    return for_poem

if __name__ == '__main__':
    main()

