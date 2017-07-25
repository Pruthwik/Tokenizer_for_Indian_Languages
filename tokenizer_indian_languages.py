import re
import argparse
import codecs
import os
# from functools import reduce


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
    ('QUOTES', r'[\"\'`’]'),          # quotes
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


def tokenize(list_s):
    tkns = []
    for wrds in list_s:
        wrds_len = len(wrds)
        initial_pos = 0
        end_pos = 0
        while initial_pos <= (wrds_len-1):
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


def read_files_from_folder_and_tokenize(input_folder, output_folder, lang_type):
    if os.path.isdir(output_folder) is False:
        os.mkdir(output_folder)
    for root, dirs, files in os.walk(input_folder):
        files.sort()
#        files.sort(key=lambda x: int(re.search('(\d+)\-\d+', x).group(1)))
        for fl in files:
            string_sentences = ''
            file_read = codecs.open(os.path.join(root, fl), 'r', 'utf-8')
            if lang_type == 0:
                text = file_read.read().strip().replace('.\n', '।\n')
            else:
                text = file_read.read().strip()
            sentences = re.findall('.*?।|.*?\n', text, re.UNICODE)
            count_sentence = 1
            for index, sentence in enumerate(sentences):
                if sentence.strip() != '':
                    list_tokens = tokenize(sentence.split())
                    end_sentence_markers = [index + 1 for index, token in enumerate(list_tokens) if token in ['?', '.', '۔', '؟']]
                    if len(end_sentence_markers) > 0:
                        end_sentence_markers_with_sentence_end_positions = [0] + end_sentence_markers
                        sentence_boundaries = list(zip(end_sentence_markers_with_sentence_end_positions, end_sentence_markers_with_sentence_end_positions[1:]))
                        for start, end in sentence_boundaries:
                            individual_sentence = list_tokens[start: end]
                            string_sentences += '<Sentence id=\'' + \
                                str(count_sentence) + '\'>\n'
                            mapped_tokens = list(map(lambda token_index: str(
                                token_index[0] + 1) + '\t' + token_index[1].strip() + '\tunk', list(enumerate(individual_sentence))))
                            string_sentences += '\n'.join(mapped_tokens) + \
                                '\n</Sentence>\n\n'
                            count_sentence += 1
                    else:
                        string_sentences += '<Sentence id=\'' + \
                                str(count_sentence) + '\'>\n'
                        mapped_tokens = list(map(lambda token_index: str(
                            token_index[0] + 1) + '\t' + token_index[1].strip() + '\tunk', list(enumerate(list_tokens))))
                        string_sentences += '\n'.join(mapped_tokens) + \
                            '\n</Sentence>\n\n'
                        count_sentence += 1
                write_data_to_file(
                    os.path.join(output_folder, fl), string_sentences)


def write_data_to_file(output_file, data):
    with codecs.open(output_file, 'w', 'utf-8') as file_write:
        file_write.write(data + '\n')
        file_write.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input', dest='inp', help="enter the input folder path")
    parser.add_argument(
        '--output', dest='out', help="enter the output folder path")
    parser.add_argument(
        '--lang', dest='lang', help="enter the language: 0 for Hindi and 1 for Others", type=int, choices=[0, 1])
    args = parser.parse_args()
    if not os.path.isdir(args.out):
        os.mkdir(args.out)
    read_files_from_folder_and_tokenize(args.inp, args.out, args.lang)
