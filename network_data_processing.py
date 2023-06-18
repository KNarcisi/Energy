

import pandas as pd

# load csv file and select wanted columns
df=pd.read_csv("/content/nw_dissolved.csv")
df=df[['network','boro','tier_2_2023']]
df.info()

# sorting netorks into alphabetical order
df2 = df.sort_values("network")
df2.head(10)

# using for loop to create new column by creating new list
dlm_priority = []
for row in df['network']:
  if row =='Ridgewood' : dlm_priority.append('Yes')
  elif row == 'Richmond Hill - BK': dlm_priority.append('Yes')
  elif row == 'Richmond Hill - QN':  dlm_priority.append('Yes')
  elif row == 'Crown Heights':  dlm_priority.append('Yes')
  else:           dlm_priority.append('No')

# calling created list into dataframe
df['dlm_priority'] = dlm_priority
print(df)

# creating function 
def myfunc(tier_2_2023,dlm_priority):
    if tier_2_2023=='Yes' and dlm_priority=='Yes':
        sum='Yes'
    else:
        sum='No'
    return sum

# calling function to create new column
df['sum'] = df.apply(lambda x: myfunc(x['tier_2_2023'], x['dlm_priority']), axis=1)
df.head(60)

# replacing values in dataset
df.replace(['Yes', 'No',], [1, 0]).to_csv('networks.csv')