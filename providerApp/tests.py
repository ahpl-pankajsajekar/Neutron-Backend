import pandas as pd
df = pd.read_excel('C://Users/pankaj.sajekar/Desktop/Standard_Test_Names.xlsx' ,sheet_name='Sheet2', usecols=['Standard_Description', 'Standard_Code'] )
# print(df)
# Create a dictionary from the DataFrame
# data_dict = df.set_index('Standard_Description')['Standard_Code'].to_dict()
# Print the dictionary

# Create a list of dictionaries
data_list = []
for index, row in df.iterrows():
    data_list.append({'item_value': int(row['Standard_Code']), 'item_text': str(row['Standard_Description'])})

# Print the list of dictionaries
print(data_list)