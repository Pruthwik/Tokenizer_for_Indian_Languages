"""Tokenization for all Indian languages in raw format."""
# how to run the code
# python3 tokenize_in_raw_format_with_sentence_tokenization.py --input Input --output Output --lang lang
# works at folder and file levels
# lang = 0 for languages ['hi', 'or', 'mn', 'as', 'bn', 'pa'], purna biram as sentence end marker
# lang = 1 for Urdu and Kashmiri '۔' sentence end marker
# lang = 2 for languages ['en', 'gu', 'mr', 'ml', 'kn', 'te', 'ta'] '.' sentence end marker
# the mapping of languages and ISO code
# Hindi: hi, Odia: or, Manipuri: mn, Assamese: as, Bengali: bn, Punjabi: pa
# Urdu: ur, Kashmiri: ks
# English: en, Gujarati: gu, Marathi: mr, Malayalam: ml, Kannada: kn, Telugu: te, Tamil: ta
import re
import argparse
import os
from string import punctuation
from transformers import pipeline


# The below model automatically identifies the language of the input text with ISO 639-1 codes and classifies it into one of the 25 Indian languages. The model is trained on the ILID dataset and is based on the MURIL architecture. The model can be used to identify the language of the input text and then the appropriate tokenization can be applied based on the identified language.
pipe = pipeline("text-classification", model="pruthwik/ilid-muril-model", tokenizer="google/muril-base-cased")
# The below mapping is used to convert the predicted language index from the model into the corresponding language code, which can then be used to determine the appropriate tokenization rules for that language.
index_to_lang = {0: 'asm', 1: 'ben', 2: 'brx', 3: 'doi', 4: 'eng', 5: 'gom', 6: 'guj', 7: 'hin', 8: 'kan', 9: 'kas', 10: 'mai', 11: 'mal', 12: 'mar', 13: 'mni_Beng', 14: 'mni_Mtei', 15: 'npi', 16: 'ory', 17: 'pan', 18: 'san', 19: 'sat', 20: 'snd_Arab', 21: 'snd_Deva', 22: 'tam', 23: 'tel', 24: 'urd'}


# the below code defines different kinds of regular expressions
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
    ('urdu_year', r'^(ء)(\d{4,4})'),
    ('bullets', r'(\d+\.)$'), # Bullets
    ('NUMBER', r'^(\d+)([,\.٫٬]\d+)*(\S)*'),  # Integer or decimal number
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
    ('urdu_stop', r'۔'),
    ('urdu_comma', r'،'),
    ('urdu_semicolon', r'؛'),
    ('urdu_question_mark', r'؟'),
    ('urdu_percent', r'٪'),
    ('quotes_question', r'[”\?]'),
    ('hashtag', r'#'),
    ('join', r'–')
]
# the below code converts the above expression into a python regex
tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
get_token = re.compile(tok_regex, re.U)
punctuations = punctuation + '\"\'‘’“”'


def find_language(text):
    """Identify the language of the input text using the pre-trained model."""
    label = pipe(text[: 300])[0]['label'].split("_")[-1]
    lang_name = index_to_lang[int(label)]
    return lang_name


def tokenize(list_s):
    """Tokenize a list of tokens."""
    tkns = []
    for wrds in list_s:
        wrds_len = len(wrds)
        initial_pos = 0
        end_pos = 0
        while initial_pos <= (wrds_len - 1):
            mo = get_token.match(wrds, initial_pos)
            if mo is not None and len(mo.group(0)) == wrds_len:
                if mo.lastgroup == 'urdu_year':
                    tkns.append(wrds[: -4])
                    tkns.append(wrds[-4:])
                else:
                    tkns.append(wrds)
                initial_pos = wrds_len
            else:
                match_out = get_token.search(wrds, initial_pos)
                if match_out is not None:
                    end_pos = match_out.end()
                    if match_out.lastgroup in ["NUMBER", "bullets"]:
                        aa = wrds[initial_pos:(end_pos)]
                    else:
                        aa = wrds[initial_pos:(end_pos - 1)]
                    if aa != '':
                        tkns.append(aa)
                    if match_out.lastgroup not in ["NUMBER", "bullets"]:
                        tkns.append(match_out.group(0))
                    initial_pos = end_pos
                else:
                    tkns.append(wrds[initial_pos:])
                    initial_pos = wrds_len
    return tkns


def read_lines_from_file(file_path):
    """Read lines from a file."""
    with open(file_path, 'r', encoding='utf-8') as file_read:
        return [line.strip() for line in file_read.readlines() if line.strip()]


def proper_bullet_creation(text, pattern):
    """Create proper bullet points after removing spaces between them."""
    text = re.sub('\\s{2,}', ' ', text)
    updated_text = ''
    bullet_patterns = re.finditer(pattern, text)
    bullet_patterns = list(bullet_patterns)
    if not bullet_patterns:
        updated_text = text
    else:
        prev_end = -100000
        for bullet_pattern in bullet_patterns:
            start, end = bullet_pattern.start(), bullet_pattern.end()
            if start == prev_end:
                updated_text = updated_text.strip()
                updated_text += bullet_pattern.group(1)
            else:
                updated_text += text[prev_end: start]
                updated_text += bullet_pattern.group(1)
            prev_end = end
        if end != len(text):
            updated_text += text[end:]
    return updated_text


def read_file_and_tokenize(input_file):
    """Read a file and tokenize its content by specifying the input file path and language type."""
    lines = read_lines_from_file(input_file)
    pattern = '(\\d+\\.\\s?)'
    lines = [proper_bullet_creation(line, pattern) for line in lines]
    text = '\n'.join(lines)
    lang_name = find_language(text)
    if lang_name in ['hin', 'ory', 'mni_Beng', 'mni_Mtei', 'asm', 'ben', 'pan', 'snd_Deva', 'sat', 'san', 'doi', 'brx', 'gom', 'mai']:
        lang_type = 0
    elif lang_name in ['ur', 'ks', 'snd_Arab']:
        lang_type = 1
    elif lang_name in ['eng', 'guj', 'mar', 'mal', 'kan', 'tel', 'tam']:
        lang_type = 2
    if lang_type == 0:
        sentences = re.findall('.*?।|.*?\n', text + '\n', re.UNICODE)
        end_markers = ['?', '।', '!', '|']
    elif lang_type == 1:
        sentences = re.findall('.*?\n', text + '\n', re.UNICODE)
        end_markers = ['؟', '!', '|', '۔']
    else:
        sentences = re.findall('.*?\n', text + '\n', re.UNICODE)
        end_markers = ['?', '.', '!', '|']
    proper_sentences = list()
    for index, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if sentence != '':
            list_tokens = tokenize(sentence.split())
            end_sentence_markers = [index + 1 for index, token in enumerate(list_tokens) if token in end_markers]
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
                next_sentence = sentences[index + 1]
                next_tokens = tokenize(next_sentence.split())
                punct_flag = True
                for token in next_tokens:
                    punct_flag &= token in punctuations
                if punct_flag:
                    if proper_sentences:
                        proper_sentences[-1] += ' ' + ' '.join(next_tokens)
                        sentences[index + 1] = ''
    return proper_sentences


def write_list_to_file(output_file, data_list):
    """Write a list to a file."""
    with open(output_file, 'w', encoding='utf-8') as file_write:
        file_write.write('\n'.join(data_list) + '\n')


def main():
    """Pass arguments and call functions here."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input', dest='inp', help="enter the input file path")
    parser.add_argument(
        '--output', dest='out', help="enter the output file path")
    args = parser.parse_args()
    if os.path.isdir(args.inp) and not os.path.isdir(args.out):
        os.mkdir(args.out)
    if not os.path.isdir(args.inp):
        sentences = read_file_and_tokenize(args.inp)
        write_list_to_file(args.out, sentences)
    else:
        for root, dirs, files in os.walk(args.inp):
            for fl in files:
                input_file_path = os.path.join(root, fl)
                lang = 0
                sentences = read_file_and_tokenize(input_file_path)
                output_file_path = os.path.join(args.out, fl)
                write_list_to_file(output_file_path, sentences)


if __name__ == '__main__':
    main()
