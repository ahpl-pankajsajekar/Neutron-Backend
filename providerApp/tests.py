import pandas as pd

# create dictionries in list ( Create a list of dictionaries )

# url for formate data https://codebeautify.org/python-formatter-beautifier#
def CreateDictsinList():
    df = pd.read_excel('C://Users/pankaj.sajekar/Desktop/Standard_Test_Names_Correct_Nomenclature_Loin_Code_Final_Submission.xlsx', sheet_name='Sheet1', usecols=['Standard_Description', 'Standard_Code', 'Alias', 'Type_of_Code', 'Final_Code', 'Description_of_Code', 'Correct_Nomenclature'] )

    data_list = []
    i = 0
    for index, row in df.iterrows():
        if row['Final_Code']:
            data_list.append({'item_Standard_Code': int(row['Standard_Code']), 
                            'item_Standard_Description': str(row['Standard_Description']),
                            'item_Alias': bool(row['Alias']),
                            'item_Type_of_Code': str(row['Type_of_Code']),
                            'item_Final_Code': str(row['Final_Code']),
                            'item_Description_of_Code': str(row['Description_of_Code']),
                            'item_Correct_Nomenclature': str(row['Correct_Nomenclature']),
                            })
        else:
            i = i + 1

    return  data_list



# comment import in providerapp view.py test file and CreateDictsinList function