from multiprocessing import Value
import fitz  # PyMuPDF
import re
import pandas as pd

slaves_token = "Slaves:"
slaves_token_len = len(slaves_token)

def initialize_dict():
   # List of keys
  keyList = ["household_number", "source", "provenance", "declarant_name", "declarant_name_parsed", "declarant_id", "name_of_family_members", "name_of_non_family_members", "slaves", "declarant_occupation", "verif_photo", "discussion"]
  # initialize dictionary
  d = {}
  for i in keyList:
    if i == "slaves" or i == "name_of_family_members" or i == "name_of_non_family_members" or i == "declarant_name_parsed" or i == "declarant_id":
      d[i] = []
    else:    
      d[i] = None
  return d


def extract_info_from_pdf(pdf_path):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)

    data = []
    current_household = initialize_dict()
    last_read_variable = ""
    household_counter = 0
    # Loop through each page in the document
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text = page.get_text("text")

        # Split text into lines for easier processing
        lines = text.split('\n')
    
        for line in lines[2:]:
            # Check if line contains specific information and extract it
            print(line)
            if line == '':
              continue
            if line.startswith("HOUSEHOLD NO.:"):
                if current_household and household_counter != 0 :
                    # Save previous household information
                    data.append(current_household)
                    current_household = initialize_dict()
                    last_read_variable = ""
                current_household['household_number'] = line.split(":")[1].strip()
                household_counter = household_counter + 1
                if "131-He-2" in current_household['household_number']:
                   print("Remove this line this is just for debugging")
            elif line.startswith("Source:") or line[1:].startswith("Source:") or line.startswith("*Source:"):
                current_household['source'] = line.split("Source:")[1].strip()
            elif line.startswith("Prov., Date:"):
                current_household['provenance'] = line.split(":")[1].strip()
            elif line.startswith("Declarant:") or line.startswith("Declarants:"):
                last_read_variable = 'declarant_name'
                current_household['declarant_name'] = line.split(":")[1].strip()
                #current_household['declarant_id'] = generate_unique_id(current_household['household_number'])  # Assume you have a function to generate a unique ID
            elif line.startswith("Family members:") or line.startswith("Family members, free non-kin:") or line.startswith("Family members, free non-kin, slaves:"):
                last_read_variable = 'name_of_family_members'
                member = get_members(line)
                if (member):
                    current_household['name_of_family_members'].append(member)
            elif line.startswith("Free non-kin, slaves:") or line.startswith("Free non-kin:"):
                last_read_variable = 'name_of_non_family_members'
                non_member = get_members(line)
                if (non_member):
                  current_household['name_of_non_family_members'].append(non_member)
                else:
                    index = line.find(":") + 1
                    sl_value = line[index:].strip()
                    if (sl_value and not sl_value.startswith('None') and sl_value != 'No names survive' and sl_value != 'No name survive'):
                      current_household['name_of_non_family_members'].append(sl_value)
                    
            elif line.startswith("Slaves:"):
                last_read_variable = 'slaves'
                value_str = get_members(line)
                if (value_str):
                    current_household['slaves'].append(value_str)
                else: 
                    index = line.find(slaves_token) + slaves_token_len
                    sl_value = line[index:].strip()
                    if (sl_value and sl_value != 'None'):
                      current_household['slaves'].append(sl_value) 
            elif line.startswith("Verif./photo:"):
                #print(current_household['name_of_non_family_members'])
                last_read_variable = 'verif_photo'
                current_household['verif_photo'] = line.split("Verif./photo:")[1].strip()
            elif line.startswith("Discussion:"):
                last_read_variable = 'Discussion'
                current_household['discussion'] = line.split(":")[1].strip()
                #discussion_text.append(line)
            elif line.startswith('Cambridge Books') or line.startswith('https://') or line.startswith('Catalogue of census declarations'):
                continue
            else: 
                if last_read_variable == 'name_of_family_members':
                    member = get_members(line)
                    if (member):
                        current_household['name_of_family_members'].append(member)
                    else:
                        idx = len(current_household['name_of_family_members']) 
                        if idx == 0:
                            current_household['name_of_family_members'].append(" " + line)
                        else:    
                            idx -= 1
                            current_household['name_of_family_members'][idx] += " " + line
                if last_read_variable == 'name_of_non_family_members':
                    member = get_members(line)
                    if (member):
                        current_household['name_of_non_family_members'].append(member)
                    else:
                        idx = len(current_household['name_of_non_family_members'])
                        if idx == 0:
                            current_household['name_of_non_family_members'].append(" " + line)
                        else:   
                            idx -= 1
                            current_household['name_of_non_family_members'][idx] +=  " " + line
                if last_read_variable == 'slaves':
                    member = get_members(line)
                    if (member):
                        current_household['slaves'].append(member)
                    else:
                        idx = len(current_household['slaves'])
                        if idx == 0:
                            current_household['slaves'].append(" " + line)
                        else:
                            idx -= 1
                            current_household['slaves'][idx] += " " + line
                if last_read_variable == 'declarant_name':
                    current_household['declarant_name'] += " " + line
                if last_read_variable == 'Discussion':
                    #discussion_text.append(line)
                    current_household['discussion'] += " " + line
                    

    # Save the last household information
    if current_household:
        #current_household['discussion'] = ' '.join(discussion_text).strip()
        data.append(current_household)

    return data

def get_occupation(line):
    occupation_list = ['public farmer and priest', 'public farmer', 'farmer', 'priest', 'mason', 
                       'discharged solder', 'workman', 'idiotes', 'former gym- nasiarch', 'metallikos',
                       'discharged veteran', 'hyperetes', 'hierotek- ton', 'tax-exempt hieronikes',
                       'nekrotaphos', 'woolwasher', 'linenweaver', 'sitometrosakkophoros',
                       'former exegetai', 'member of the hiera synodos',
                       'councillor', 'taurotrophos', 'fisherman', 'weaver','donkey driver', 'goldsmith', 'spinner', 'salaried linen-weaver',
                       'lathe turner']  
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
                       
    
    
def generate_unique_id(household_number, declarants_list):
    declarant_ids = []
    if household_number and declarants_list and len(declarants_list) > 0:
      counter = 1
      for item in declarants_list:
          declarant_ids.append(household_number + "-d" + str(counter))
          counter = counter + 1
    return declarant_ids

def get_members(line):
    str = extract_numbered_substring(line)
    #print(str)
    return str

def extract_numbered_substring(s):
    # Regular expression pattern to match numbers between 1 and 30 enclosed in parentheses
    pattern = r'\((1[0-9]|2[0-9]|30|[1-9])\).*'
    match = re.search(pattern, s)
    if match:
        return match.group(0)
    return None

def contains_number_in_parentheses(s):
    # Regular expression pattern to match numbers between 1 and 30 enclosed in parentheses
    pattern = r'\((1[0-9]|2[0-9]|30|[1-9])\)'
    return bool(re.search(pattern, s))

def calculate_num(str):
    if str:
        return len(str.split(";;"))
  
def check_discussion_indicates_broken(str):
    if str: 
      if "Broken" in str or "broken" in str:
         return "Yes"
    return "No"    
 
def split_on_key(input_list, key):
    # Find the indices where the key appears
    indices = [i for i, item in enumerate(input_list) if item.startswith(key)]
    
    # Add the end of the list to the indices to handle the last sublist
    indices.append(len(input_list))
    
    # Create sublists based on the indices
    result = [input_list[indices[i]:indices[i+1]] for i in range(len(indices)-1)]
    
    return result

def split_household_number(household_number) :
    modified_household_number = household_number.strip().replace(' ', '-')
    splitted_household_number = modified_household_number.split("-")
    if len(splitted_household_number) == 2:
       splitted_household_number.append('') 
    return splitted_household_number

def split_provenance(provenance) :
    splitted_provenance = provenance.split(",")
    if len(splitted_provenance) == 1:
       splitted_provenance.append('') 
    return splitted_provenance        

def prepare_first_csv(extracted_data):
  # List of keys
  keyList = ["household_number_year", "household_number_location", "household_number_order", "source", "provenance", "provenance_place", "provenance_year", "declarant_1", "declarant_2", "declarant_3", "declarant_4", "declarant_5", "declarant_ids", "declarant_occupation", "number_of_family_members", "number_of_non_family_members", "number_of_slaves", "verif_photo", "discussion_text", "discussion_indicates_substantive_record_brokenness" ]
  # initialize dictionary
  final_data = {}
  # iterating through the elements of list
  for i in keyList:
    final_data[i] = None
  
  final_data_list = []  
  for entry in extracted_data:
      final_data = {}
      splitted_household_number = split_household_number(entry.get('household_number'))
      final_data["household_number_year"] = splitted_household_number[0]
      final_data["household_number_location"] = splitted_household_number[1]
      final_data["household_number_order"] = splitted_household_number[2]
      
      final_data["source"] = entry.get('source')
      
      final_data["provenance"] = entry.get('provenance')
      splitted_provenance = split_provenance(entry.get('provenance'))
      final_data["provenance_place"] = splitted_provenance[0]
      final_data["provenance_year"] = splitted_provenance[1]
      
      declarants_list = entry.get('declarant_name_parsed')
      declarant_column_key = "declarant"
      #for item in declarants_list:
      
      i = 0
      while i < 5:
          if declarants_list and len(declarants_list) > i :
            final_data["declarant_name_"+str(i+1)] = declarants_list[i]  
          else:    
            final_data["declarant_name_"+str(i+1)] = ''
          i = i + 1
          
      #for idx, declarant in enumerate(declarants_list):
      #  print(idx, declarant)
      #  final_data["declarant_name_"+str(idx+1)] = declarant
        
      #final_data["declarant_name"] = entry.get('declarant_name_parsed')
      
      final_data["declarant_ids"] = entry.get('declarant_id')
      final_data["declarant_occupation"] = entry.get('declarant_occupation')
      final_data["number_of_family_members"] = len(entry.get('name_of_family_members'))
      final_data["number_of_non_family_members"] = len(entry.get('name_of_non_family_members'))
      final_data["number_of_slaves"] = len(entry.get('slaves'))
      final_data["verif_photo"] = entry.get('verif_photo')
      final_data["discussion_text"] = entry.get('discussion')
      final_data["discussion_indicates_substantive_record_brokenness"] = check_discussion_indicates_broken(entry.get('discussion'))
      final_data_list.append(final_data)
      
  return final_data_list

def get_parsed_declarants(declarant_line):
    
    declarants = []
    
    if declarant_line is None:
        return declarants
    if declarant_line.startswith("Name") or declarant_line.startswith("Not"):
      declarants.append(declarant_line)
      return declarants
    
    if declarant_line.startswith("[") :
        declarant_line = declarant_line[1:]

    # Regular expression to match the declarant names
    #below regex works mostly
    #regex = r"^([A-Za-z]+(?: and [A-Za-z]+)*)\b"
    regex = r"^([A-Za-z\s.]+?)(?=\s+s\.)|([A-Za-z\s.]+?)(?=\s+d\.)|([A-Za-z]+(?: and [A-Za-z]+)*)\b"

    segments = declarant_line.split(';')
    matches = None
    for segment in segments:
        segment = segment.strip()
        if segment.lower().startswith("and "):
            # Remove the leading "and"
            segment = segment[4:].strip()
        match = re.match(regex, segment)
        if match:
          matches = match.group(1) or match.group(2) or match.group(3)
        if matches:
          if "d." in matches:
              matches = matches.split("d.")[0]
          declarants.append(matches)

    #print(f"Declarants: {declarants}")

    if len(declarants) == 0:
        if "s." in declarant_line:
            declarants.append(declarant_line.split("s.")[0])
        if "d." in declarant_line:
            declarants.append(declarant_line.split("d.")[0]) 
        elif "]tion" in declarant_line:
            declarants.append(declarant_line)      

    if "(s. Lykos)" in declarant_line or "s. Petos," in declarant_line :
        pattern = r"(?<!\()\b(\w+)\b (?=[sd]\.)"
        matches = re.findall(pattern, declarant_line)
        declarants.clear()
        declarants.extend(matches)
    elif "archos s. Apollonios" in declarant_line:
        declarants.clear()
        declarants.append(declarant_line.split("s.")[0].strip())
    elif " and his children " in declarant_line:
        declarants.append(declarant_line.split(" and his children ")[1])
    elif ", all three sons of " in declarant_line:
        declarants.clear()
        splitted_tmp = declarant_line.split(", all three sons of ")[0]
        splitted_tmp = splitted_tmp.split(", and")
        declarants.append(splitted_tmp[0].split(",")[0].strip())
        declarants.append(splitted_tmp[0].split(",")[1].strip())
        declarants.append(splitted_tmp[1].strip())
        #declarants.append(declarant_line.split(", all three sons of ")[0])
    elif ("(nios?)" in declarant_line):
         declarants.clear()
         declarants.append(declarant_line.split(", sons of ")[0])
    elif "alias" in declarant_line and " sons of " in declarant_line:
          if "," in declarant_line:
            specific_case_splitted = declarant_line.split(",")
            declarants.clear()
            declarants.append(specific_case_splitted[0]) 
            declarants.append(specific_case_splitted[2].split("s.")[0].split("and ")[1])
            declarants.append(specific_case_splitted[3].split(" both sons of")[0].split("and ")[1])
            #print(specific_case_splitted[3].split(" both sons of")[0].split("and "))
            declarants.append(specific_case_splitted[3].split(" both sons of")[0].split("and ")[2])
          else:
            declarants.clear()
            declarants.append(declarant_line.split(" sons of ")[0])    
    elif ", and " in declarant_line and " both sons of " in declarant_line:
        declarants.append(declarant_line.split(" both sons of ")[0].split(", and ")[1])
    elif " his sister, and " in declarant_line:
        declarants.append(declarant_line.split(" his sister, and ")[0].split(", ")[1])
        declarants.append(declarant_line.split(" his sister, and ")[1].split(" daughters of")[0])
    elif " and her children " in declarant_line:
        children_str = declarant_line.split(" and her children ")[1]
        children_str = children_str.split(", through their father ")
        declarants.append(children_str[0])
        declarants.append(children_str[1])
    
    new_list_declarants = []
    for item in declarants:
        # Check if 'and' is in the item
        if 'and' in item or ',' in item:
            if 'and' in item:
                # Split the item by 'and' and extend the new_list with the split items
                new_list_declarants.extend(item.split(' and '))
            else:    
                splitted_str = item.split(',')
                if splitted_str[1].strip() != "":
                    new_list_declarants.extend(item.split(','))
                else:    
                    new_list_declarants.append(splitted_str[0]) 
        else:
            # If 'and' is not in the item, just append it to the new_list
            new_list_declarants.append(item)
    
    stripped_list = [s.strip() for s in new_list_declarants]
    return stripped_list

    

# Path to your PDF file
pdf_path = 'input_pdf\\catalogue-of-census-declarations.pdf'
extracted_data = extract_info_from_pdf(pdf_path)

pdf_path = 'input_pdf\\catalogue-of-census-declarations-supplement.pdf'
extracted_data_pdf2 = extract_info_from_pdf(pdf_path)

extracted_data.extend(extracted_data_pdf2)

# Print the extracted information
#print(extracted_data)
for entry in extracted_data:
    #print("Occupation: " + get_occupation(entry.get('declarant_name')))
    entry.update({'declarant_occupation':  get_occupation(entry.get('declarant_name'))})
    entry.update({'declarant_name_parsed':  get_parsed_declarants(entry.get('declarant_name'))})
    entry.update({'declarant_id': generate_unique_id(entry.get('household_number'), entry.get('declarant_name_parsed'))})
    #print(entry)
    if len(entry.get('name_of_family_members')) == 0 :
        if len(entry.get('slaves')) > 0:
            print("Household Number: " + str(entry.get('household_number')) + " requires enrichment")
            key = '(1)'
            splitted_data = split_on_key(entry.get('slaves'), key)
            if len(splitted_data) >= 3:
                entry.update({'name_of_family_members':  splitted_data[0]})
                entry.update({'name_of_non_family_members':  splitted_data[1]})
                entry.update({'slaves': splitted_data[2]})
            elif len(splitted_data) >= 2:
                entry.update({'name_of_family_members': splitted_data[0]})
                entry.update({'slaves': splitted_data[1]})
    
    if "187-Ar-4" in str(entry.get('household_number')):
        key = '(1)'
        splitted_data = split_on_key(entry.get('name_of_family_members'), key)
        entry.update({'name_of_family_members':  splitted_data[0]})
        entry.update({'name_of_non_family_members':  splitted_data[1]})
    
    # this data is not read by libray in line-by-line reading    
    if "131-He-2" in str(entry.get('household_number')):
        entry['provenance'] = 'Ankyronpolis (Herakleopolite), 133'
        
first_csv_data = prepare_first_csv(extracted_data)
df = pd.DataFrame(first_csv_data)
df.to_csv('household_data_csv_1.csv')


df = pd.DataFrame(extracted_data)
df.to_csv('input_csv\\persons_input.csv')



with open("myfile.txt", 'w') as f:  
    for entry in extracted_data:
      for key, value in entry.items():  
        f.write('%s: %s\n' % (key, value))
        if key == 'discussion':
            f.write('\n')   

#for entry in extracted_data:
#    #print(entry)
#    print("Household Number: " + str(entry.get('household_number')))
#    print("Source: " + str(entry.get('source')))
#    print("Provenance: " + str(entry.get('provenance')))
#    print("Declarant Name: " + str(entry.get('declarant_name')))
#    print("Declarant ID: " + str(entry.get('declarant_id')))
#    print("Name of Family Members: " + str(entry.get('name_of_family_members')))
#    if (entry.get('slaves')) : 
#        print("Name of Non-Family Members: " + str(entry.get('name_of_non_family_members')) + "," + str(entry.get('slaves')) )
#    else: 
#        print("Name of Non-Family Members: " + str(entry.get('name_of_non_family_members'))  )
#    print("Discussion: " + str(entry.get('discussion')))
#    print("\n-----------------------------\n")    
