import pandas as pd
import requests
from bs4 import BeautifulSoup
import bs4, re
response = requests.get('https://gbbo.fandom.com/wiki/Series_1')
html = response.text
goodsoup = BeautifulSoup(html,'html5lib')

main_body = goodsoup.find('div', class_ = 'mw-parser-output')

# its the same for all series - little list of coloured boxes and keys of their values
# make into a table for reference with shorthand to use in tables
colour_keys = main_body.dl 

def create_colour_key_table(colour_keys: bs4.element.Tag) -> None:
    # get all background colours and corresponding descriptions in lists
    colour_dict = {}
    colour_list = []
    description_list = []
    for dd in colour_keys.select('dd'):
        colour = dd.span['style'].split(';')[0]
        colour_list.append(colour.split(':')[1])
        description = dd.span.next_sibling.string
        description = description.replace('– ','').replace('- ','')
        description_list.append(description)
    # add lists to dictionary
    colour_dict['Colour'] = colour_list
    colour_dict['Description'] = description_list
    # make dictionary into dataframe
    colour_df = pd.DataFrame(colour_dict, dtype='string')
    # add shorthand made up 
    shorthand = ['star','moves','out','dislike','like','winner','ill']
    colour_df['Shorthand'] = shorthand
    # add the missing colour "silver"
    colour_df.loc[len(colour_df)] = ['silver','Baker is no longer participating','done']
    # save to tsv file
    colour_df.to_csv('progress_colour_key.tsv',sep='\t',encoding='utf-8',index=False)


def get_html_tables(main_body:bs4.element.Tag, series:str)-> None:
    tables = main_body.select("table") # list of two tables on the page 
    contestants_table = tables[0] # first one is contestants info table
    with open(f'contestants_{series}.html','w',encoding='utf-8') as outfile:
        outfile.write(str(contestants_table.prettify()))
    progress_table = tables[1] # second one is progress table
    with open(f'progress_{series}.html','w',encoding='utf-8') as outfile:
        outfile.write(str(progress_table.prettify()))

def modify_colour_cells(table_path)-> None:
    with open(table_path,'r',encoding='utf-8') as infile:
        html = infile.read()
    progress = BeautifulSoup(html,'html5lib')
    table_colour = progress.find_all(style=re.compile('background')) # all cells with background colour specified
    for item in table_colour:
        item.append(item['style']) # append the colour as str for later
    with open(table_path,'w',encoding='utf-8') as outfile:
        outfile.write(str(progress.prettify()))

def add_missing_cells(table_path)-> None:
    with open(table_path,'r',encoding='utf-8') as infile:
        html = infile.read()
    progress = BeautifulSoup(html,'html5lib')
    table_colspan = progress.find_all(colspan=True)
    for item in table_colspan:
        colspan = int(item["colspan"]) # get number of cells a colour spans
        colspan -= 1
        for i in range(colspan): # add the missing cells made by colspan
            new_tag = progress.new_tag("td")
            new_tag.string = item.string
            item.next_sibling.insert_before(new_tag)
    with open(table_path,'w',encoding='utf-8') as outfile:
        outfile.write(str(progress.prettify()))

def create_progress_table(path: str, series: str) -> None:
    '''
    '''
    with open(path,'r',encoding='utf-8') as infile:
        html = infile.read()
    progress = BeautifulSoup(html,'html5lib')
    # header of the table
    header_list = []
    for header in progress.select('th'):
        text = header.string
        text = text.strip()
        if text == '':
            text = 'contestant'
        header_list.append(text)
    # datacells of the table stored in list (table) of lists (rows)
    table_list = []
    for i, row in enumerate(progress.select('tr')): # loop through rows
        if i != 0: # skip header
            row_list = []
            for td in row.select('td'): # loop through datacells of ith row
                text = td.string
                if text == None: # more than one string then
                    text_l = [t for t in td.stripped_strings]
                    text = ' '.join(text_l)
                text = text.strip()
                if '\n' in text: # in the multiple strings
                    text = text.split('\n')[0]
                if 'background' in text: # remove the prefix and leave only the colour name/HEX code
                    text = text.split(':')[1]
                row_list.append(text)
            table_list.append(row_list)
    # convert to a dataframe & save to TSV file
    table_df = pd.DataFrame(table_list,dtype=str,columns = header_list)
    table_df.to_csv(f'progress_df_{series}.tsv',sep='\t',index=False)

def replace_colours_with_shorthand(progress_path:str,key_path:str,series:str)-> None:
    '''
    '''
    colour_df = pd.read_csv(key_path,sep='\t',dtype=str)
    table_df = pd.read_csv(progress_path,sep='\t',dtype=str)
    weeks = table_df.columns.difference(['contestant'])
    table_df[weeks] = table_df[weeks].apply(lambda x: x.str.strip(';').str.lower())
    for week in weeks:
        table_df[week] = table_df[week].map(colour_df.set_index('Colour')['Shorthand'])
    table_df.to_csv(f'progress_df_{series}.tsv',sep='\t',index=False)

