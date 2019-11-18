# how to run the code
# python3 tokenizer_for_file.py --input Input --output Output
# works at folder and file levels
# lang = 0 for languages ['hi', 'or', 'mn', 'as', 'bn', 'pa'], purna biram as sentence end marker
# lang = 1 for Urdu '۔' sentence end marker
# lang = 2 for languages ['en', 'gu', 'mr', 'ml', 'kn', 'te', 'ta'] '.' sentence end marker
import re
import argparse
import os
from string import punctuation


token_specification = [
    ('datemonth',
     r'^(0?[1-9]|1[012])[-\/\.](0?[1-9]|[12][0-9]|3[01])[-\/\.](1|2)\d\d\d$'),
    ('monthdate',
     r'^(0?[1-9]|[12][0-9]|3[01])[-\/\.](0?[1-9]|1[012])[-\/\.](1|2)\d\d\d$'),
    ('yearmonth',
     r'^((1|2)\d\d\d)[-\/\.](0?[1-9]|1[012])[-\/\.](0?[1-9]|[12][0-9]|3[01])'),
    ('EMAIL1', r'([\w\.])+@(\w)+\.(com|org|co\.in)$'),
    ('url1', r'(www\.)([-a-z0-9]+\.)*([-a-z0-9]+.*)(\/[-a-z0-9]+)*/i'),
    ('url', r'/((?:https?\:\/\/|www\.)(?:[-a-z0-9]+\.)*[-a-z0-9]+.*)/i'),
    ('BRACKET', r'[\(\)\[\]\{\}]'),       # Brackets
    ('NUMBER', r'^(\d+)([,\.]\d+)*(\w)*'),  # Integer or decimal number
    ('ASSIGN', r'[~:]'),          # Assignment operator
    ('END', r'[;!_]'),           # Statement terminator
    ('EQUAL', r'='),   # Equals
    ('OP', r'[+*\/\-]'),    # Arithmetic operators
    ('QUOTES', r'[\"\'‘’“”]'),          # quotes
    ('Fullstop', r'(\.+)$'),
    ('ellips', r'\.(\.)+'),
    ('HYPHEN', r'[-+\|+]'),
    ('Slashes', r'[\\\/]'),
    ('COMMA12', r'[,%]'),
    ('hin_stop', r'।'),
    ('quotes_question', r'[”\?]'),
    ('hashtag', r'#')
]
tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
get_token = re.compile(tok_regex)
punctuations = punctuation + '\"\'‘’“”'


def tokenize(list_s):
    tkns = []
    for wrds in list_s:
        wrds_len = len(wrds)
        initial_pos = 0
        end_pos = 0
        while initial_pos <= (wrds_len - 1):
            mo = get_token.match(wrds, initial_pos)
            if mo is not None and len(mo.group(0)) == wrds_len:
                tkns.append(wrds)
                initial_pos = wrds_len
            else:
                match_out = get_token.search(wrds, initial_pos)
                if match_out is not None:
                    end_pos = match_out.end()
                    if match_out.lastgroup == "NUMBER":
                        aa = wrds[initial_pos:(end_pos)]
                    else:
                        aa = wrds[initial_pos:(end_pos - 1)]
                    if aa != '':
                        tkns.append(aa)
                    if match_out.lastgroup != "NUMBER":
                        tkns.append(match_out.group(0))
                    initial_pos = end_pos
                else:
                    tkns.append(wrds[initial_pos:])
                    initial_pos = wrds_len
    return tkns


def read_file_and_tokenize(input_file, lang_type=0):
        file_read = open(input_file, 'r', encoding='utf-8')
        text = file_read.read().strip()
        if lang_type == 0:
            sentences = re.findall('.*?।|.*?\n', text + '\n', re.UNICODE)
            endMarkers = ['?', '।', '!', '|']
        elif lang_type == 1:
            sentences = re.findall('.*?\n', text + '\n', re.UNICODE)
            endMarkers = ['؟', '!', '|', '۔']
        else:
            sentences = re.findall('.*?\n', text + '\n', re.UNICODE)
            endMarkers = ['?', '.', '!', '|']
        proper_sentences = list()
        print(endMarkers, lang_type)
        for index, sentence in enumerate(sentences):
            if sentence.strip() != '':
                list_tokens = tokenize(sentence.split())
                end_sentence_markers = [index + 1 for index, token in enumerate(list_tokens) if token in endMarkers]
                if len(end_sentence_markers) > 0:
                    if end_sentence_markers[-1] != len(list_tokens):
                        end_sentence_markers += [len(list_tokens)]
                    end_sentence_markers_with_sentence_end_positions = [0] + end_sentence_markers
                    sentence_boundaries = list(zip(end_sentence_markers_with_sentence_end_positions, end_sentence_markers_with_sentence_end_positions[1:]))
                    for start, end in sentence_boundaries:
                        individual_sentence = list_tokens[start: end]
                        proper_sentences.append(' '.join(individual_sentence))
                else:
                    proper_sentences.append(' '.join(list_tokens))
                if index < len(sentences) - 1:
                    nextSentence = sentences[index + 1]
                    nextTokens = tokenize(nextSentence.split())
                    punctFlag = True
                    for token in nextTokens:
                        punctFlag &= token in punctuations
                    if punctFlag:
                        print(nextTokens)
                        if proper_sentences:
                            proper_sentences[-1] += ' ' + ' '.join(nextTokens)
                            sentences[index + 1] = ''
        return proper_sentences


def write_list_to_file(output_file, data_list):
    with open(output_file, 'w', encoding='utf-8') as file_write:
        file_write.write('\n'.join(data_list) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input', dest='inp', help="enter the input file path")
    parser.add_argument(
        '--output', dest='out', help="enter the output file path")
    args = parser.parse_args()
    if os.path.isdir(args.inp) and not os.path.isdir(args.out):
        os.mkdir(args.out)
    if not os.path.isdir(args.inp):
        langCode = args.inp[args.inp.find('.') + 1:][: 2]
        if langCode in ['hi', 'or', 'mn', 'as', 'bn', 'pa']:
            lang = 0
        elif langCode == 'ur':
            lang = 1
        elif langCode in ['en', 'gu', 'mr', 'ml', 'kn', 'te', 'ta']:
            lang = 2
        sentences = read_file_and_tokenize(args.inp, lang)
        write_list_to_file(args.out, sentences)
    else:
        for root, dirs, files in os.walk(args.inp):
            for fl in files:
                inputFilePath = os.path.join(root, fl)
                langCode = args.input[fl.find('.') + 1:][: 2]
                if langCode in ['hi', 'or', 'mn', 'as', 'bn', 'pa']:
                    lang = 0
                elif langCode == 'ur':
                    lang = 1
                elif langCode in ['en', 'gu', 'mr', 'ml', 'kn', 'te', 'ta']:
                    lang = 2
                sentences = read_file_and_tokenize(inputFilePath, lang)
                outputFilePath = os.path.join(args.out, fl)
                write_list_to_file(outputFilePath, sentences)
