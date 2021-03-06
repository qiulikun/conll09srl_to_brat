from argparse import ArgumentParser
import re
from nltk.tokenize.moses import MosesDetokenizer
detokenizer = MosesDetokenizer()


def conll09srl_to_brat(srl, ann=None):

    if ann:
        # split annotation information line by line and make table
        ann_list = ann.split('\n')
        ann_table =[]
        for ann_line_tmp in ann_list:
            if ann_line_tmp:
                if ann_line_tmp[0] == 'T' and ';' in ann_line_tmp:
                    # Term-boundary (separated word case!)
                    line_tmp1 = re.split(r'\t', ann_line_tmp)
                    line_tmp2 = re.split(r'\s|;', line_tmp1[1])
                    ann_table.append(
                        [line_tmp1[0], line_tmp2[0], line_tmp2[1] + ' ' + line_tmp2[2], line_tmp2[3] + ' ' + line_tmp2[4],
                         line_tmp1[2]])
                elif ann_line_tmp[0] == 'T':
                    # Term - boundary(single or continuous word(s))
                    line_tmp1 = re.split(r'\t', ann_line_tmp)
                    line_tmp2 = re.split(r'\s|;', line_tmp1[1])
                    ann_table.append(
                        [line_tmp1[0], line_tmp2[0], line_tmp2[1], line_tmp2[2], line_tmp1[2]])
                elif ann_line_tmp[0] == 'E' or ann_line_tmp[0] == 'R':
                    # Relation, Event
                    ann_table.append(re.split(r'\t|\s|:', ann_line_tmp))

        # find max R and T annotation numbers
        t_ann_list = list(filter(lambda x: x[0][0] == 'T', ann_table))
        r_ann_list = list(filter(lambda x: x[0][0] == 'R', ann_table))
        t_max = max(list(map(lambda x: int(x[0][1:]), t_ann_list)))
        r_max = max(list(map(lambda x: int(x[0][1:]), r_ann_list)))
    else:
        ann_table = []
        t_max = 0
        r_max = 0

    t_now = t_max
    r_now = r_max

    def ann_table_append_T(term_type, start, end, phrase):
        nonlocal ann_table, t_now

        t_ann_list_now = list(filter(lambda x: x[0][0] == 'T', ann_table))
        tid_term_type = set(map(lambda x: x[0], filter(lambda x: x[1] == term_type, t_ann_list_now)))
        tid_starts = set(map(lambda x: x[0], filter(lambda x: x[2] == str(start), t_ann_list_now)))
        tid_ends = set(map(lambda x: x[0], filter(lambda x: x[3] == str(end), t_ann_list_now)))
        tid_phrases = set(map(lambda x: x[0], filter(lambda x: x[4] == phrase, t_ann_list_now)))
        matched_tid = list(tid_phrases & tid_starts & tid_ends & tid_term_type)

        if not matched_tid:
            t_now = t_now + 1
            ann_table.append(['T' + str(t_now), term_type, str(start), str(end), phrase])
            return 'T' + str(t_now)
        else:
            return matched_tid[0]

    def ann_table_append_R(relation, arg1, arg2):
        nonlocal ann_table, r_now

        r_ann_list_now = list(filter(lambda x: x[0][0] == 'R', ann_table))
        rid_relation = set(map(lambda x: x[0], filter(lambda x: x[1] == relation, r_ann_list_now)))
        rid_arg1 = set(map(lambda x: x[0], filter(lambda x: x[3] == arg1, r_ann_list_now)))
        rid_arg2 = set(map(lambda x: x[0], filter(lambda x: x[5] == arg2, r_ann_list_now)))
        matched_rid = list(rid_relation & rid_arg1 & rid_arg2)

        if not matched_rid:
            r_now = r_now + 1
            ann_table.append(['R' + str(r_now), relation, 'Arg1', arg1, 'Arg2', arg2])
            return 'R' + str(r_now)
        else:
            return matched_rid[0]

    # split semantic role label information line by line, and make dictionaries
    srl_list = srl.split('\n')
    srl_all_dicts = []
    srl_dict_tmp = {}
    srl_line_count = 0
    srl_list_len = len(srl_list)
    for srl_line in srl_list:
        srl_elements = re.split(r'\t|\s', srl_line)

        if srl_line:
            srl_dict_tmp[str(srl_elements[0])] = srl_elements[1:]

            # if it is the end of a sentence or the next line is empty, move values to a dictionary
            if srl_line_count + 1 < srl_list_len:
                is_next_line_empty = srl_list[srl_line_count + 1] == ''
            else:
                is_next_line_empty = False

            if srl_elements[1] == '.' or is_next_line_empty:
                srl_all_dicts.append(srl_dict_tmp)
                srl_dict_tmp = {}

        if not srl_line:
            srl_all_dicts.append({})
            srl_dict_tmp = {}
        srl_line_count = srl_line_count + 1

    def print_dict_in_order(src_dict):
        keys_in_order = list(map(lambda x: int(x), src_dict.keys()))
        keys_in_order.sort()
        if keys_in_order:
            for num in keys_in_order:
                print(str(num) + ' ' + str(src_dict[str(num)]))
        else:
            print("*** Dict is empty. ***")

    def token2string(tokens):
        detokens = detokenizer.detokenize(tokens, return_str=False)
        detokens_joint = " ".join(detokens)
        detokens_joint = detokens_joint.replace(" -- ", "–")
        detokens_joint = detokens_joint.replace("( ", "(")
        # detokens_joint = detokens_joint.replace("'", "’")  # for special case
        detokens_joint = detokens_joint.replace("-", "-")  # for special case
        return detokens_joint

    def count_dict_characters_as_sentences(src_dict, start=None, end=None):
        if not start:
            start = min(map(lambda x: int(x), list(src_dict.keys())))
            end = max(map(lambda x: int(x), list(src_dict.keys())))
        if start == end:
            end = int(start)
        keys_in_order = list(range(int(start), int(end)+1))

        words = []
        for num in keys_in_order:
            words.append(src_dict[str(num)][0])
        character_count = len(token2string(words))

        return character_count

    word_count_paragraph = 0
    parsed_verb_number = 0

    srl_pattern = re.compile(r'.*A.*')

    for srl_dict in srl_all_dicts:

        if srl_dict:

            # find semantic role label related words (verbs)
            srl_verb_keys = []
            for k, v in srl_dict.items():
                if v[12] != '_':  # all semantic role label roots have something other than '_' (like 'make.01')
                    srl_verb_keys.append(k)
            srl_verb_keys = list(map(lambda x: int(x), srl_verb_keys))
            srl_verb_keys.sort()
            srl_verb_keys = list(map(lambda x: str(x), srl_verb_keys))  # sort verb list

            for srl_verb_key in srl_verb_keys:

                def startpos_endpos_phrase(phrase_numbers, srl_dict):
                    if not isinstance(phrase_numbers, list):
                        phrase_numbers = [phrase_numbers]

                    min_phrase_numbers = min(list(map(lambda x: int(x), phrase_numbers)))
                    max_phrase_numbers = max(list(map(lambda x: int(x), phrase_numbers)))
                    start_dict_numbers = min(list(map(lambda x: int(x), srl_dict.keys())))
                    if min_phrase_numbers > start_dict_numbers:
                        start_position = count_dict_characters_as_sentences(srl_dict, start_dict_numbers, min_phrase_numbers - 1)
                        if srl_dict[str(min_phrase_numbers - 1)][0] == '(' or srl_dict[str(min_phrase_numbers)][0] == '%':
                            pass
                        else:
                            start_position = start_position + 1  # counting a space
                    else:
                        start_position = 0  # no space

                    end_position = start_position + count_dict_characters_as_sentences(srl_dict, min_phrase_numbers, max_phrase_numbers)

                    phrase = []
                    for num in phrase_numbers:
                        phrase.append(srl_dict[num][0])

                    content = [start_position, end_position, token2string(phrase)]
                    return content

                def find_phrase_keys(ax_key, srl_dict):

                    def find_parent_keys(src_keys, src_dict):
                        result = []
                        for src_key in src_keys:
                            for k, v in src_dict.items():
                                if v[7] == src_key:
                                    result.append(k)
                        return result

                    result_keys = [ax_key]

                    current_keys = [ax_key]
                    parent_keys = [ax_key]
                    while parent_keys:
                        parent_keys = find_parent_keys(current_keys, srl_dict)  # key that has ax_key at srl_dict.values()[7]
                        for k in parent_keys:
                            result_keys.append(k)
                        current_keys = parent_keys

                    # remove preposition
                    result_keys = list(map(lambda x: int(x), result_keys))
                    result_keys.sort()
                    if srl_dict[str(result_keys[0])][3] == "IN":
                        result_keys = result_keys[1:]
                    result_keys = list(map(lambda x: str(x), result_keys))

                    return result_keys

                def remove_verb_phrase_from_keys(target_keys, verb_key, srl_dict):
                    if verb_key not in target_keys:
                        return target_keys
                    else:
                        verb_keys = find_phrase_keys(verb_key, srl_dict)
                        removal_pos_list = ["TO", "MD", "VBG", "VBZ", "WDT"]
                        verb_key_previous = str(int(verb_key) - 1)
                        while True:
                            if verb_key_previous in srl_dict.keys():
                                verb_parent_pos = srl_dict[verb_key_previous][4]
                                if verb_parent_pos in removal_pos_list:
                                    verb_keys.append(verb_key_previous)
                                    verb_key_previous = str(int(verb_key_previous) - 1)
                                else:
                                    break
                            else:
                                break
                        for vk in verb_keys:
                            if vk in target_keys:
                                target_keys.remove(vk)
                        return target_keys

                def abandon_fragment(target_keys):
                    if target_keys:
                        min_key_int = min(list(map(lambda x: int(x), target_keys)))
                        max_key_int = max(list(map(lambda x: int(x), target_keys)))
                        if len(target_keys) != max_key_int - min_key_int + 1:
                            return None
                        else:
                            return target_keys
                    else:
                        return None


                [start, end, phrase] = startpos_endpos_phrase(srl_verb_key, srl_dict)

                tid_root = ann_table_append_T('P:' + srl_dict[srl_verb_key][12], start + word_count_paragraph, end + word_count_paragraph, phrase)

                for srl_key, srl_val in srl_dict.items():
                    srl_cell = srl_val[13 + srl_verb_keys.index(srl_verb_key) + parsed_verb_number]
                    if srl_pattern.match(srl_cell):
                        target_keys = find_phrase_keys(srl_key, srl_dict)
                        target_keys = remove_verb_phrase_from_keys(target_keys, srl_verb_key, srl_dict)
                        target_keys = abandon_fragment(target_keys)
                        if target_keys:
                            [start, end, phrase] = startpos_endpos_phrase(target_keys, srl_dict)
                            tid_ax = ann_table_append_T('Argument', start + word_count_paragraph, end + word_count_paragraph, phrase)
                            ann_table_append_R(srl_cell, tid_root, tid_ax)

            word_count_paragraph = word_count_paragraph + count_dict_characters_as_sentences(srl_dict) + 1
            parsed_verb_number = parsed_verb_number + len(srl_verb_keys)

        else:
            word_count_paragraph = word_count_paragraph + 1
            parsed_verb_number = 0

    ann_string_list = []
    for ann_line in list(filter(lambda x: x[0][0] != 'R', ann_table)):
        if ann_line[0][0] == 'T':
            if ' ' not in ann_line[2]:
                ann_string_list.append(ann_line[0] + "\t" + ann_line[1] + " " + ann_line[2] + " " + ann_line[3] + "\t" + ann_line[4])
            else:
                ann_string_list.append(
                    ann_line[0] + "\t" + ann_line[1] + " " + ann_line[2] + ";" + ann_line[3] + "\t" + ann_line[4])
        elif ann_line[0][0] == 'E':
            ann_string_list.append(ann_line[0] + "\t" + ann_line[1] + ":" + ann_line[2])
    for ann_line in list(filter(lambda x: x[0][0] == 'R', ann_table)):
        ann_string_list.append(ann_line[0] + "\t" + ann_line[1] + " " + ann_line[2] + ":" + ann_line[3] + " " + ann_line[4] + ":" + ann_line[5])

    return "\n".join(ann_string_list)


if __name__ == '__main__':
    usage = 'Usage: python3 {} FILE [--annotation] [--output]'.format(__file__)
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument('srl_file_name', type=str,
                           help='Input File Name (CoNLL2009 Format with Semantic Role Labels)')
    argparser.add_argument('-a', '--annotation', type=str,
                           action='store',
                           dest='input_annotation_file',
                           help='Input File Name to Add SRL Annotation (Brat Annotation Format))',
                           )
    argparser.add_argument('-o', '--output', type=str,
                           action='store',
                           dest='output_file',
                           help='Output File Name (Brat Annotation Format)')
    args = argparser.parse_args()

    if args.input_annotation_file:
        with open(args.input_annotation_file, 'r') as f:
            ann = f.read()
    else:
        ann = None

    with open(args.srl_file_name, 'r') as f:
        srl = f.read()

    brat_annotation = conll09srl_to_brat(srl, ann)

    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(brat_annotation)
    else:
        print(brat_annotation)
