import re
import pandas as pd
import ast
import traceback
import sys


def get_name(data):
    name_pattern = r"^\s*[\(\d+\)]*\s*(.*?)(?=\s*,\s*)"
    rel_pattern = r"(\?d\.|\?s\.|s\.|d\.|mother of|ss\.|son of| daughter of|brother of|father of|slave of|child of|wife of|child of|female|male|wife|freed|offspring of)"
    pattern = r'^\s*[\(\d+\)]*\s*(.*?)(?=\s+[\?d\.|\?s\.|s\.|d\.|mother of|ss\.|son of| daughter of|brother of|father of|slave of|child of|wife of|male|female|wife|freed|offspring of]+)'
    pattern2 = r"^\s*[\(\d+\)]*\s*(.*)(?=\s*\W\s*(\?d\.|\?s\.|s\.|d\.|mother of|ss\.|son of| daughter of|brother of|father of|slave of|child of|wife of|male|female|wife|freed|offspring of))"
    decalarant_pattern = r"(\[declarant]| \[declarant\] |(\[declarant) |\[declarant)"
    if isinstance(data, str):
        match = re.search(name_pattern, data, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if re.search(rel_pattern, name, re.IGNORECASE) is not None:
                name_found = re.search(pattern, data)
                if name_found:
                    name = name_found.group(1).strip()
                    if len(name) == 0:
                        name_found = re.search(pattern2, data, re.IGNORECASE)
                        if name_found:
                            name = name_found.group(1).strip()
                else:
                    name_found = re.search(pattern2, data, re.IGNORECASE)
                    if name_found:
                        name = name_found.group(1).strip()
            else:
                match = re.search(name_pattern, data, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
        else:
            return None

        name = re.sub(decalarant_pattern, ' ', name)
        name = name.replace("(s.", "")
        name = name.replace("(d.", "")
    else:
        name = ''

    return name.strip()

def remove_starting_number(data):
    number_pattern = r"^\s*\(\d+\)\s*"
    return re.sub(number_pattern,'',data)


def get_sex(data, type):
    data = remove_starting_number(data)
    parts = data.split(" ")
    sex = None
    if data.__contains__("s. (or d.?)"):
        sex = 'male or female'
    else:
        for part in parts:
            if type == 'F' or type == 'K':
                if part == "s./d.":
                    sex = 'male or female'
                    break

                if part == "d." or \
                        part == "?d." or \
                        part == "(d." or \
                        part == "daughter" or \
                        part == "wife" or \
                        part == "sister" or \
                        part.__contains__("mother") or \
                        part.__contains__("female") or \
                        part == "freedw.":
                    if sex is None:
                        sex = 'female'
                        if part.__contains__('?'):
                            sex = 'possible ' + sex

                    else:
                        sex = sex + 'or female'
                    break

                if part == "s." or \
                        part == "?s." or \
                        part == "s.?" or \
                        part == "son" or \
                        part == "(s." or \
                        part == "brother" or \
                        part.__contains__("father") or \
                        part.__contains__("male"):
                    sex = 'male'
                    if part.__contains__('?'):
                        sex = 'possible ' + sex
                    break
            elif type == 'S':
                if part.__contains__("female"):
                    sex = 'female'
                    break
                if part.__contains__("male"):
                    sex = 'male'
                    break

    return sex


def get_age(data):
    age = ''
    data = remove_starting_number(data)
    if data.__contains__('age lost'):
        age = 'age lost'

    if data.__contains__('age not given'):
        age = 'age not given'

    if age is None:
        probably_age_pattern = r"(\(probably\s+.*)|(probably\s+.*)|\?.*probable.*"
        age_pattern = r"(?<=;\s|,\s)([\[\.\]]*\d+.*)"
        age_search = re.findall(age_pattern, data, re.IGNORECASE)
        if age_search:
            age = ' or '.join(match.strip() for match in age_search)
            if age == "2nd certain)":
                age_search = re.search(probably_age_pattern, data, re.IGNORECASE)
                if age_search:
                    age = age_search.group(0).strip()
        else:
            age_search = re.search(probably_age_pattern, data, re.IGNORECASE)
            if age_search:
                age = age_search.group(0).strip()

    return age

def get_role(type):
    role = None
    if type == 'F':
        role = 'family member'
    if type == 'K':
        role = 'free non-kin'
    if type == 'S':
        role = 'slave'

    return role

def get_type(role):
    type = None
    if role == 'family member':
        type = 'FM'
    if role == 'free non-kin':
        type = 'NK'
    if role == 'slave':
        type = 'S'

    return type


def get_occupation(line):
    occupation_list = ['public farmer and priest', 'public farmer', 'farmer', 'priest', 'mason',
                       'discharged solder', 'workman', 'idiotes', 'former gym- nasiarch', 'metallikos',
                       'discharged veteran', 'hyperetes', 'hierotek- ton', 'tax-exempt hieronikes',
                       'nekrotaphos', 'woolwasher', 'linenweaver', 'sitometrosakkophoros',
                       'former exegetai', 'member of the hiera synodos',
                       'councillor', 'taurotrophos', 'fisherman', 'weaver', 'scribe', 'doctor','lathe turner'
                       ,'stonecutter','tailor', 'cloth-beater']
    ret_str = ""
    if line is None:
        return ret_str
    for occupation in occupation_list:
        ret_str = occupation
        if occupation in line:
            if 'priest' in occupation:
                splitted_Line = line.split("priest of ")
                if len(splitted_Line) == 2:
                    ret_str += " of "
                    if "," in splitted_Line[1]:
                        ret_str += splitted_Line[1].split(",")[0]
                    else:
                        ret_str += splitted_Line[1]
            return ret_str
    return ""



def get_parents(data):
    parents = data
    parent_pattern = r"(?:\?d\.|\?s\.|s\.|d\.|ss\.|son of| daughter of|father of|child of)([—\s+\w+\(.?[\]))]+)"
    parent_match = re.search(parent_pattern,data, re.IGNORECASE)
    if parent_match:
        parents = parent_match.group(1).strip()

    return parents
def get_father(data):

    #father_pattern = "(\w+)(?:\s+\(\w+\s+\w+\)|\s+\[no.\s*\d+\]|\s+\[no.l\])"
    father_and_pattern = r"(?: s\. \(or d\.\?\) of | s\. \(\?\) of | s\.\/d\. | d\. \(\?\) of |\?d\.|\?s\.| s\.\? of | s\.|d\.|ss\.|son of| daughter of|father of|child of|born to)(.*?)(?:and)"
    father_pattern = r"(?: s\. \(or d\.\?\) of | s\. \(\?\) of | d\. \(\?\) of |\?d\.|\?s\.| s\.\? of | s\.|d\.|ss\.|son of| daughter of|father of|child of|born to)([—\s+\w+.?[\]))]+)"
    pattern_to_use = None
    father = None
    if data.__contains__(" and "):
        pattern_to_use = father_and_pattern
    else:
        pattern_to_use = father_pattern

    match = re.search(pattern_to_use,data,re.IGNORECASE)
    if match:
        father = match.group(1).strip()

    if father is not None:
        if father.__contains__("declarant"):
            father = ""
        else:
            father = re.search(r"\b(\w+)\b",father,re.IGNORECASE).group(1)
            father.strip()

    return father

def get_mother(data):
    mother_pattern = r"(?:\D\s+and\s+)([—\s+\w+\(.?[\]))]+)"
    #mother_pattern = r"(?: s\. \(or d.\?\) of .*| s\.\/d\. .*|\?d\..*|\?s\..*| s\..*| d\..*|ss\..*| son of.*| daughter of.*| father of.*| child of.*|\s+s\.\/d\..*)(?:\s+and\s+)([—\s+\w+\(.?[\]))]+)"
    mother = None

    match = re.search(mother_pattern,data,re.IGNORECASE)
    if match:
        mother = match.group(1).strip()

    if mother is not None and mother.__contains__("wife"):
        mother = None

    if mother is not None:
        mother = mother.split(" ")[0]
    return mother


def get_paternal_grand_father(data, household_id=""):
    p_grand_father = None
    if household_id != "117-Ar-2":
        pattern1 = r"\(s\. ([\w+\s+.\[\]]+)\)"

        match = re.search(pattern1, data, re.IGNORECASE)
        if match:
            p_grand_father = match.group(1).strip()

        if p_grand_father is not None:
            p_grand_father = p_grand_father.split(" ")[0]

    return p_grand_father

def get_maternal_grand_father(data, household_id=""):
    m_grand_father = None
    if household_id != "117-Ar-2":
        pattern = r"\(d\. ([\w+\s+.\[\]]+)\)"

        match = re.search(pattern, data, re.IGNORECASE)
        if match:
            m_grand_father = match.group(1).strip()

    return m_grand_father


def get_spouses(data):
    husband_pattern = r"(?<!divorced |deceased )(?:husband of )([\w\s.[\]]+)"
    wife_pattern = r"(?<!divorced |deceased )(?:wife of |wife and full sister of |wife and sister of )([\w\s.[\]]+)"
    match = re.search(husband_pattern, data, re.IGNORECASE)
    spouse = None
    if match:
        spouse = match.group(1).strip()
    else:
        match = re.search(wife_pattern, data, re.IGNORECASE)
        if match:
            spouse = match.group(1).strip()
            if spouse.__contains__("s."):
                spouse = spouse.split(" ")[0]


    return spouse


def get_siblings(data):
    brother_pattern = re.compile(r"(?:, |,)(?:brother of |br\. of|br\. )([\w\s.[\]]+)", re.IGNORECASE)
    sister_pattern = re.compile(r"(?:, |,)(?:sister of |sister and former wife of |sister and wife of |sister and divorced wife of |sister )([\w\s.[\]']+)", re.IGNORECASE)

    brothers = brother_pattern.findall(data)
    sisters = sister_pattern.findall(data)

    siblings = [match.strip() for match in brothers + sisters]

    return siblings if siblings else []


def get_relation_to_declarant(data, household_id=""):
    relation = None
    relation_pattern = "(?:, |,|\()(perhaps wife and sister|probably wife |full sister and wife|wife and sister|sister and wife|sister and divorced wife|wife|sister|brother of the father|husband|brother|relative|son|daughter|child|mother)(?:[\s+\w+\s+]+)\[*declarant\]*\)*"
    relation_pattern1 = r"(?:, |,|\()(perhaps wife and sister|probably wife |full sister and wife|wife and sister|sister and wife|sister and divorced wife|wife|sister|brother of the father|husband|brother|relative|son|daughter|child|mother)(?:[\s+\w+\s+]+).*\[*declarant\]*\)*"
    son_daughter_pattern = r"(s\. or gs\.|s\.\/d\.|s\.|d\.).*?(\[declarant\]|\[declarant,|\[of declarant\]*)"
    match = re.search(relation_pattern, data, re.IGNORECASE)
    if match:
        relation = match.group(1).lower()
    else:
        match = re.search(relation_pattern1, data, re.IGNORECASE)
        if match:
            relation = match.group(1).lower()
        else:
            match = re.search(son_daughter_pattern, data, re.IGNORECASE)
            if match:
                value = match.group(1).lower()
                if value == "s. or gs.":
                    relation = 'self'
                if value == 's.':
                    relation = 'son'
                elif value == 'd.':
                    relation = 'daughter'
                elif value.__contains__("s") and value.__contains__("d"):
                    relation = 'son or daughter'

    if relation is None:
        self_pattern = r"^(?!.*(?:s\.|d\.).*?\[declarant\]).*\[declarant\]|^(?!.*(?:s\.|d\.).*?\[declarant\]).*\(declarant\)"
        match = re.search(self_pattern, data, re.IGNORECASE)
        if match:
            relation = 'self'

    return relation


def contain_members(data):
    pattern = r"\(*\d+\)"
    parseable = False
    match = re.search(pattern, data, re.IGNORECASE)
    if match:
        parseable = True

    return parseable

def get_slave_mother(data):
    pattern = r"(?:offspring of )(.*?),"
    match = re.search(pattern, data, re.IGNORECASE)
    mother = None
    if match:
        mother = match.group(1).strip()

    return mother

def get_owner(data):
    pattern = r"(?:slave[ \(\w\)]* of )(.*?),"
    match = re.search(pattern, data, re.IGNORECASE)
    mother = None
    if match:
        mother = match.group(1).strip()

    return mother


def parse_person(household_id, fm_data, type):
    members = []

    for data in fm_data:
        member = {}
        if contain_members(data):
            member['household_id'] = household_id
            member['name'] = get_name(data)
            member['sex'] = get_sex(data, type)
            member['age'] = get_age(data)
            if type == 'F' or  type == 'K':
                member['occupation'] = get_occupation(data)
                member['father'] = get_father(data)
                member['mother'] = get_mother(data)
                member['paternal_grandfather'] = get_paternal_grand_father(data, household_id)
                member['maternal_grandfather'] = get_maternal_grand_father(data, household_id)
                member['spouse'] = get_spouses(data)
                member['siblings'] = get_siblings(data)
                member['children'] = []
                member['relation_to_declarant'] = get_relation_to_declarant(data)
                member['owner'] = None
            else:
                member['father'] = None
                member['mother'] = get_slave_mother(data)
                member['occupation'] = None
                member['paternal_grandfather'] = None
                member['maternal_grandfather'] = None
                member['relation_to_declarant'] = None
                member['spouse'] = None
                member['siblings'] = []
                member['children'] = []
                member['owner'] = get_owner(data)

            member['role'] = get_role(type)
            member['data'] = data
            members.append(member)

    return members



def set_personal_ids(houshold_id, declarant_ids, declarant_names, persons):
    id_index = 1
    for person in persons:
        if person['relation_to_declarant'] == 'self' and person.get('id') is None:
            person_name_to_compare = person['name']
            for index, dec_name in enumerate(declarant_names):
                dec_name_to_compare = dec_name.strip()
                if dec_name_to_compare.__contains__("Aurelius"):
                    dec_name_to_compare = dec_name_to_compare.replace("Aurelius", "Aur.")

                if person_name_to_compare.__contains__("Aurelius"):
                    person_name_to_compare = person_name_to_compare.replace("Aurelius", "Aur.")

                if person_name_to_compare.startswith(dec_name_to_compare) or dec_name_to_compare.startswith(person_name_to_compare) \
                        or person_name_to_compare.__contains__(dec_name_to_compare) or dec_name_to_compare.__contains__(person['name']):
                    person['id'] = declarant_ids[index]
                    break
            if person.get('id') is None:
                person['id'] = houshold_id + "-" + get_type(person['role']) + str(id_index)
                id_index += 1
        else:
            person['id'] = houshold_id + "-" + get_type(person['role']) + str(id_index)
            id_index += 1


def find_person(relation, persons):
    persons_found = []
    for person in persons:
        if person['relation_to_declarant']:
            if person['relation_to_declarant'].__contains__(relation):
                persons_found.append(person)

    return persons_found

    # return [person for person in persons if person.get('relation_to_declarant') == relation]

def check_existence(value, array):
    for ele in array:
        if ele.__contains__(value):
            return True

    return False

def filter_siblings(existing_siblings, sibling_ids):
    for ex in existing_siblings:
        if ex in sibling_ids:
            sibling_ids.remove(ex)

def update_ids(person, related_person, relationship, question_mark=False):

    related_person_id = related_person[0]['id']
    person_id = person['id']
    if question_mark:
        related_person_id += "?"
        person_id += "?"

    if relationship == 'father':
        person['father'] = related_person_id
        related_person[0]['children'].append(person_id)
    if relationship == 'mother':
        person['mother'] = related_person_id
        related_person[0]['children'].append(person_id)
    if relationship == 'spouse':
        person['spouse'] = related_person_id
        related_person[0]['spouse'] = person_id
    if relationship == 'siblings':
        sibling_ids = [person["id"] for person in related_person]
        filter_siblings(person['siblings'], sibling_ids)
        if question_mark:
            sibling_ids = [sib_id + "?" for sib_id in sibling_ids]
        person['siblings'].extend(sibling_ids)
        for sib in related_person:
            sib['siblings'].append(person_id)

    if relationship == 'children':
        for child in related_person:
            # if child['father'] == person['name'] or child['mother'] == person['name']:
            child_id = child['id']
            if question_mark:
                child_id += "?"
            person['children'].append(child_id)

            if person['sex'] == 'male':
                child['father'] = person_id
            if person['sex'] == 'female':
                child['mother'] = person_id
            if person['sex'] is None: #Assumption is that person is father
                child['father'] = person_id


def set_relationship_ids_based_on_declarant(persons):
    declarants = find_person('self', persons)
    for declarant in declarants:
        father = find_person('father', persons)
        if father:
            update_ids(declarant, father, 'father')

        mother = find_person('mother', persons)
        if mother:
            update_ids(declarant, mother, 'mother')

        wife = find_person('wife', persons)
        if wife:
            if wife[0]['relation_to_declarant'].__contains__("probably"):
                update_ids(declarant, wife, 'spouse', True)
            else:
                update_ids(declarant, wife, 'spouse', False)

        husband = find_person('husband', persons)
        if husband:
            update_ids(declarant, husband, 'spouse')

        siblings = find_person('brother', persons)
        siblings.extend(find_person('sister', persons))
        if len(siblings) > 0:
            update_ids(declarant, siblings, 'siblings')
            remove_declarant_entry(siblings, 'siblings')

        children = find_person('son', persons)
        children.extend(find_person('daughter', persons))
        children.extend(find_person('son or daughter', persons))
        if len(children) > 0:
            update_ids(declarant, children, 'children')
            remove_declarant_entry(children, 'children')

def remove_declarant_entry(referenced_by_persons, key):
    for person in referenced_by_persons:
        for item in person[key]:
            if item.__contains__("declarant"):
                person[key].remove(item)

def set_specific_relation(referenced_person, referenced_by_person, relation, referenced_index, question_mark=False):
    if relation == 'wife and sister' \
            or relation == 'sister and wife' \
            or relation == 'wife and full sister' \
            or relation == 'sister and divorced wife' \
            or relation == 'wife her brother' \
            or relation == 'full sister and wife':
        update_ids(referenced_person, [referenced_by_person], 'spouse', question_mark)
        update_ids(referenced_person, [referenced_by_person], 'siblings')
        remove_reference_num_entry(referenced_person, referenced_by_person,referenced_index,'siblings')
    elif relation == 'wife' or relation == 'husband' or relation == "wife (?)":
        update_ids(referenced_person, [referenced_by_person], 'spouse', question_mark)
    elif relation == 'sister' or relation == 'brother' or relation == 'br.':
        update_ids(referenced_person, [referenced_by_person], 'siblings')
        remove_reference_num_entry(referenced_person, referenced_by_person,referenced_index,'siblings')
    elif relation == 'son' or relation == 'daughter' or relation == 'child':
        update_ids(referenced_person, [referenced_by_person], 'children', question_mark)
        remove_reference_num_entry(referenced_person, referenced_by_person,referenced_index,'children')
    elif relation == 'mother' or relation == 'father':
        update_ids(referenced_person, [referenced_by_person], relation, question_mark)


def set_relations(referenced_person, referenced_by_person, referenced_index, question_mark=False):
    relation_pattern = r",\s*(wife \(\?\)|full sister and wife|wife and sister|sister and wife|wife and full sister|sister and divorced wife|wife|sister|brother of the father|husband|brother|relative|son|daughter|child|mother|br\.)\s*of\s*[^\[]*\[*\s*nos*\.\s*(?:{})\s*\]\?*(.*brother)*"
    relation_pattern1 = r",*\s*(wife \(\?\)|full sister and wife|wife and sister|sister and wife|wife and full sister|sister and divorced wife|wife|sister|brother of the father|husband|brother|relative|son|daughter|child|mother|br\.)\s*of\s*[^\[]*\[*\s*nos*\.\s*(?:{})\s*\]\?*(.*brother)*"
    relation_pattern2 = r",\s*(wife \(\?\)|full sister and wife|wife and sister|sister and wife|wife and full sister|sister and divorced wife|wife|sister|brother of the father|husband|brother|relative|son|daughter|child|mother|br\.)\s*of\s*[^\[]*\(*\s*nos*\.\s*(?:{})\s*\)\?*(.*brother)*"
    relation_pattern3 = r",*\s*(wife \(\?\)|full sister and wife|wife and sister|sister and wife|wife and full sister|sister and divorced wife|wife|sister|brother of the father|husband|brother|relative|son|daughter|child|mother|br\.)\s*of\s*[^\[]*\(*\s*nos*\.\s*(?:{})\s*\)\?*(.*brother)*"
    relation_pattern4 = ",\s*(wife \(\?\)|full sister and wife|wife and sister|sister and wife|wife and full sister|sister and divorced wife|wife|sister|brother of the father|husband|brother|relative|son|daughter|child|mother|br\.)\s*of\s*[^\[]*no\.[{}]\?*(.*brother)*"
    relation_pattern_with_nos = r"[,]\s*(full sister and wife|wife and sister|sister and wife|wife and full sister|sister and divorced wife|wife|sister|brother of the father|husband|brother|relative|son|daughter|child|mother|br\.)\s*of\s*[^\[]*nos\. [{}]\?*"
    relation_pattern_with_nos_and = r"[,]\s*(full sister and wife|wife and sister|sister and wife|wife and full sister|sister and divorced wife|wife|sister|brother of the father|husband|brother|relative|son|daughter|child|mother|br\.)\s*of\s*[^\[]*nos\. [[\d|l]\?* and]* [{}]\?*"
    relation_pattern_father_mother1 = r"(s\.\/d\.|s\.|d\.|daughter|child|son).*?\[*\s*nos*\.\s*(?:{})\s*\]\?*"
    relation_pattern_father_mother2 = r"(s\.\/d\.|s\.|d\.|daughter|child|son).*?\(*\s*nos*\.\s*(?:{})\s*\)\?*"
    if referenced_index == 1:
        relation_pattern = relation_pattern.format("1|l")
        relation_pattern1 = relation_pattern1.format("1|l")
        relation_pattern2 = relation_pattern2.format("1|l")
        relation_pattern3 = relation_pattern3.format("1|l")
        relation_pattern4 = relation_pattern4.format("1|l")
        relation_pattern_with_nos = relation_pattern_with_nos.format("1|l")
        relation_pattern_father_mother1 = relation_pattern_father_mother1.format("1|l")
        relation_pattern_father_mother2 = relation_pattern_father_mother2.format("1|l")
        relation_pattern_with_nos_and = relation_pattern_with_nos_and.format("1|l")
    else:
        relation_pattern = relation_pattern.format(referenced_index)
        relation_pattern1 = relation_pattern1.format(referenced_index)
        relation_pattern2 = relation_pattern2.format(referenced_index)
        relation_pattern3 = relation_pattern3.format(referenced_index)
        relation_pattern4 = relation_pattern4.format(referenced_index)
        relation_pattern_with_nos = relation_pattern_with_nos.format(referenced_index)
        relation_pattern_father_mother1 = relation_pattern_father_mother1.format(referenced_index)
        relation_pattern_father_mother2 = relation_pattern_father_mother2.format(referenced_index)
        relation_pattern_with_nos_and = relation_pattern_with_nos_and.format(referenced_index)
    match = re.search(relation_pattern, referenced_by_person['data'], re.IGNORECASE)
    if match:
        relation = match.group(1)
        if relation:
            if len(match.groups()) > 1:
                if match.group(2):
                    relation += match.group(2).lower()
            set_specific_relation(referenced_person, referenced_by_person, relation, referenced_index, question_mark)
    else:
        match = re.search(relation_pattern1, referenced_by_person['data'], re.IGNORECASE)
        if match:
            relation = match.group(1)
            if relation:
                set_specific_relation(referenced_person, referenced_by_person, relation, referenced_index, question_mark)
        else:
            match = re.search(relation_pattern2, referenced_by_person['data'], re.IGNORECASE)
            if match:
                relation = match.group(1)
                if relation:
                    set_specific_relation(referenced_person, referenced_by_person, relation, referenced_index, question_mark)
            else:
                match = re.search(relation_pattern3, referenced_by_person['data'], re.IGNORECASE)
                if match:
                    relation = match.group(1)
                    if relation:
                        set_specific_relation(referenced_person, referenced_by_person, relation, referenced_index, question_mark)
                else:
                    match = re.search(relation_pattern4, referenced_by_person['data'], re.IGNORECASE)
                    if match:
                        relation = match.group(1)
                        if relation:
                            set_specific_relation(referenced_person, referenced_by_person, relation, referenced_index, question_mark)
                    else:
                        match = re.search(relation_pattern_with_nos, referenced_by_person['data'], re.IGNORECASE)
                        if match:
                            relation = match.group(1).lower()
                            set_specific_relation(referenced_person, referenced_by_person, relation, referenced_index, question_mark)
                        else:
                            match = re.search(relation_pattern_with_nos_and, referenced_by_person['data'], re.IGNORECASE)
                            if match:
                                relation = match.group(1).lower()
                                set_specific_relation(referenced_person, referenced_by_person, relation, referenced_index, question_mark)
                            else:
                                match = re.search(relation_pattern_father_mother1, referenced_by_person['data'], re.IGNORECASE)
                                if match:
                                    relation = match.group(1).lower()
                                    if relation.startswith("s"):
                                        set_specific_relation(referenced_person, referenced_by_person, 'son', referenced_index, question_mark)
                                    if relation.startswith("d"):
                                        set_specific_relation(referenced_person, referenced_by_person, 'daughter', referenced_index, question_mark)
                                    if relation.startswith("child"):
                                        set_specific_relation(referenced_person, referenced_by_person, 'daughter', referenced_index, question_mark)
                                else:
                                    match = re.search(relation_pattern_father_mother2, referenced_by_person['data'], re.IGNORECASE)
                                    if match:
                                        relation = match.group(1).lower()
                                        if relation.startswith("s"):
                                            set_specific_relation(referenced_person, referenced_by_person, 'son', referenced_index, question_mark)
                                        if relation.startswith("d"):
                                            set_specific_relation(referenced_person, referenced_by_person, 'daughter', referenced_index, question_mark)
                                        if relation.startswith("child"):
                                            set_specific_relation(referenced_person, referenced_by_person, 'daughter', referenced_index, question_mark)


def find_declarant_reference(persons):
    indexes = []
    declarant_pattern = r"(\[declarant]| \[declarant\] |(\[declarant) |\[declarant)"

    for index, person in enumerate(persons):
        if person['relation_to_declarant'] != 'self':
            match = re.search(declarant_pattern, person['data'], re.IGNORECASE)
            if match:
                indexes.append(index+1)

    return indexes

def remove_reference_num_entry(referenced_person, referenced_by_person, referenced_index, key):
    number_and_pattern = r"(?:nos\. )(\d and \d)"
    number_pattern = r"(nos\. [\d|l]|\[no\. *[\d|l]\?*\])"
    for item in referenced_by_person[key]:
        match = re.search(number_and_pattern, item, re.IGNORECASE)
        if match:
            values = match.group(1).strip().split(" and ")
            if str(referenced_index) in values:
                referenced_by_person[key].remove(item)
        else:
            matches = re.findall(number_pattern, item, re.IGNORECASE)
            for match in matches:
                value = match.strip()
                if referenced_index == 1:
                    if value.__contains__("1") or value.__contains__("l"):
                        referenced_by_person[key].remove(item)
                else:
                    if value.__contains__(str(referenced_index)):
                        referenced_by_person[key].remove(item)


def set_relationship_ids(persons):

    set_relationship_ids_based_on_declarant(persons)

    for index, person in enumerate(persons):
        referenced_indexes = find_number_reference(index + 1, persons)
        for index1 in referenced_indexes:
            question_mark = False
            if isinstance(index1, str):
                val = index1.rstrip("?")
                val = int(val)
                question_mark = True
            else:
                val = index1
            set_relations(person, persons[val - 1], index + 1, question_mark)

    # for index, person in enumerate(persons):
    #     dec_referenced_indexes = find_declarant_reference(persons)
    #     for index2 in dec_referenced_indexes:
    #         set_relations(person, persons[index2 - 1], index + 1)


def find_number_reference(ref_no, persons):
    indexes = []
    number_and_pattern = r"(?:nos\. )(\d\?* and \d\?*)"
    #number_pattern = r"no\.[{}]\?*|nos\. [{}]\?*|\[no\. *[{}]\?*\]\?*"
    number_pattern = r"\[*\s*nos*\.\s*({})\s*\]\?*|\(*\s*nos*\.\s*({})\s*\)\?*|no\.({}\?*)"
    if ref_no == 1:
        number_pattern = number_pattern.format(str(ref_no)+"|l", str(ref_no)+"|l", str(ref_no)+"|l")
    else:
        number_pattern = number_pattern.format(ref_no, ref_no, ref_no)

    for index, person in enumerate(persons):
        match = re.search(number_and_pattern, person['data'], re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            values = value.split(" and ")
            for val in values:
                if str(ref_no) == val:
                    indexes.append(index+1)
        else:
            match = re.search(number_pattern, person['data'], re.IGNORECASE)
            if match:
                value = match.group(1)
                if value is None:
                    value = match.group(2)
                    if value is None:
                        value = match.group(3)

                if value.startswith("l"):
                    value = "1"

                if value == str(ref_no):
                    value = index+1
                    if match.group(0).__contains__("?"):
                        value = str(value) + "?"

                    indexes.append(value)

    return indexes


def add_declarant_as_person(household_id, dec_line, declarant_names, declarant_ids, persons):

    declarant_added = False
    if len(find_person('self', persons)) == 0:
        if isinstance(dec_line, str):
            lines = dec_line.split(";")
            for index, dec_name in enumerate(declarant_names):
                if index < len(lines):
                    line = lines[index]
                    line = line.lstrip("and")
                else:
                    line = dec_line
                person = {
                    'household_id': household_id,
                    'id': declarant_ids[index],
                    'name': dec_name,
                    'age': get_age(line),
                    'sex': get_sex(line, 'F'),
                    'occupation': get_occupation(line),
                    'father': get_father(line),
                    'mother': get_mother(line),
                    'paternal_grandfather': get_paternal_grand_father(line),
                    'maternal_grandfather': get_maternal_grand_father(line),
                    'spouse': get_spouses(line),
                    'siblings': get_siblings(line),
                    'children': [],
                    'role': 'family member',
                    'relation_to_declarant': 'self',
                    'owner': None,
                    'data': dec_line
                }
                if len(persons) > 0:
                    persons.insert(0, person)
                else:
                    persons.append(person)

                declarant_added = True

    return declarant_added
def start():

    household_id = ''
    try:
        df = pd.read_csv('output_csv_1.csv', encoding="utf-8")
        persons = []
        df['name_of_family_members'] = df['name_of_family_members'].apply(ast.literal_eval)
        df['name_of_non_family_members'] = df['name_of_non_family_members'].apply(ast.literal_eval)
        df['slaves'] = df['slaves'].apply(ast.literal_eval)
        df['declarant_name_parsed'] = df['declarant_name_parsed'].apply(ast.literal_eval)
        df['declarant_id'] = df['declarant_id'].apply(ast.literal_eval)

        # df = df.loc[51:51]
        for index, row in df.iterrows():
            household_id = row['household_number']
            family_members = parse_person(household_id, row['name_of_family_members'], 'F')
            set_personal_ids(row['household_number'], row['declarant_id'], row['declarant_name_parsed'], family_members)
            set_relationship_ids(family_members)
            added = add_declarant_as_person(household_id, row['declarant_name'], row['declarant_name_parsed'], row['declarant_id'], family_members)
            if added:
                set_relationship_ids_based_on_declarant(family_members)
            persons.extend(family_members)

            non_kin_members = parse_person(household_id, row['name_of_non_family_members'], 'K')
            set_personal_ids(row['household_number'], row['declarant_id'], row['declarant_name_parsed'], non_kin_members)
            set_relationship_ids(non_kin_members)
            persons.extend(non_kin_members)

            slaves = parse_person(household_id, row['slaves'], 'S')
            set_personal_ids(row['household_number'], row['declarant_id'], row['declarant_name_parsed'], slaves)
            persons.extend(slaves)

        df = pd.DataFrame(persons)
        df = df[['household_id','id', 'name', 'sex', 'age', 'occupation', 'father', 'mother', 'paternal_grandfather','maternal_grandfather','spouse','siblings','children','relation_to_declarant', 'role', "owner"]]
        df.to_csv('persons.csv')
        print(df.to_markdown())
    except:
        traceback.print_exception(*sys.exc_info())
        print("Error for household_id: {}".format(household_id))

if __name__ == "__main__":

    start()


