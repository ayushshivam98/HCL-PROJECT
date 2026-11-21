"""Clean the raw Denmark cancer dataset, run data-quality checks and add new columns.
Run from the project root:  python scripts/clean_data.py"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
raw = pd.read_csv(ROOT / 'data/raw/cancer_data_denmark.csv')
df = raw.drop_duplicates().copy()

# 1. Remove rows with any missing value (no filling)
before = len(df)
df = df.dropna()
print(f'Rows removed because of missing values: {before - len(df)}')

# 2. Tidy text, fix types
cat_cols = ['Gender','Cancer_Type','Stage','Treatment_Type','Smoking_Status',
            'Family_History','Relapse','Occupation','Income_Level']
for c in cat_cols:
    df[c] = df[c].str.strip()
for c in ['Diagnosis_Date','Treatment_Start_Date','Treatment_End_Date','Followup_Date']:
    df[c] = pd.to_datetime(df[c], format='%d-%m-%Y')
df['Lymph_Nodes_Examined'] = df['Lymph_Nodes_Examined'].astype(int)

# 3. New columns
df['Age_Group'] = pd.cut(df['Age'], [17,30,45,60,75,120], labels=['18-30','31-45','46-60','61-75','76+'])
df['BMI_Category'] = pd.cut(df['BMI'], [0,18.5,25,30,100], right=False,
                            labels=['Underweight','Normal','Overweight','Obese'])
df['Survival_Category'] = pd.cut(df['Survival_Months'], [0,24,60,1000], right=False,
                                 labels=['Short','Medium','Long'])
df['Treatment_Delay_Days'] = (df['Treatment_Start_Date'] - df['Diagnosis_Date']).dt.days
df['Treatment_Duration_Days'] = (df['Treatment_End_Date'] - df['Treatment_Start_Date']).dt.days
df['Diagnosis_Year'] = df['Diagnosis_Date'].dt.year
df['Relapse_Flag'] = (df['Relapse'] == 'Yes').astype(int)

# 4. Data-quality checks (fail loudly if the data does not make sense)
assert (df['Treatment_Delay_Days'] >= 0).all(), 'Treatment starts before diagnosis'
assert (df['Treatment_Duration_Days'] >= 0).all(), 'Treatment ends before it starts'
assert df['Age'].between(18, 100).all() and df['BMI'].between(10, 60).all(), 'Out-of-range values'
gap = (df['Followup_Date'] - df['Diagnosis_Date']).dt.days / 30.44
print('Warning - survival longer than follow-up window:', int((gap < df['Survival_Months']).sum()), 'patients')

out = ROOT / 'data/processed/cancer_data_denmark_clean.csv'
df.to_csv(out, index=False)
print('Saved', out.name, df.shape)
