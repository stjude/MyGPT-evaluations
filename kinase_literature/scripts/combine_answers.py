'''this script combines answer data, scores, questions data, and ground truth into a single CSV file'''

import pandas as pd
import re
import json

library_name = 'Kinase-literature'


# Load first two CSV files (answers and scores)
df1 = pd.read_csv(f"../outputs/answers/answers-gpt-oss-20b-{library_name}.csv")
df2 = pd.read_csv(f"../outputs/answers/answers-scores-{library_name}-gpt-oss:20b.csv")

# Extract first word (yes, no, or maybe) from answer column
def extract_short_answer(answer):
    if pd.isna(answer):
        return None
    match = re.match(r'^\s*(\w+)', str(answer))
    if match:
        first_word = match.group(1).lower()
        if first_word in ['yes', 'no', 'maybe']:
            return first_word
    return None

# df1['short_answer'] = df1['answer'].apply(extract_short_answer)

# Combine first two dataframes

# Combine first two dataframes
combined = pd.concat([df1, df2], axis=1)

# Remove duplicate pubmed_id columns if present
for col in ['pubmed_id']:
    cols = [c for c in combined.columns if c == col]
    if len(cols) > 1:
        # Keep only the first occurrence
        combined = combined.loc[:,~combined.columns.duplicated()]

# Create unique key in combined dataframe using the first occurrence
if 'pubmed_id' in combined.columns:
    combined['unique_key'] = combined['pubmed_id'].astype(str) + '_' + combined['document'].astype(str) + '_' + combined['kinase'].astype(str)

# Rename relevance_score to ARS in the combined dataframe
if 'relevance_score' in combined.columns:
    combined.rename(columns={'relevance_score': 'ARS'}, inplace=True)

# Load the contexts JSON file
with open(f'../outputs/contexts/eval_context_{library_name}.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract only the specified columns from contexts
extracted_data = []
for item in data:
    extracted_data.append({
        'document': item.get('document'),
        'question': item.get('question'),
        'relevance_score': item.get('relevance_score'),
        'vector_distances': item.get('vector_distances'),
        'vector_scores': item.get('vector_scores'),
        'bm25_scores_raw': item.get('bm25_scores_raw'),
        'bm25_scores': item.get('bm25_scores'),
        'reranked_score': item.get('reranked_score'),
        'ranks': item.get('ranks'),
        'unique_key': str(item.get('pubmed_id')) + '_' + str(item.get('document') ) + '_' + str(item.get('kinase'))
    })

# Convert to DataFrame

df_contexts = pd.DataFrame(extracted_data)

# Merge with the combined dataframe on 'unique_key'
final_combined = pd.merge(combined, df_contexts, on=['unique_key'], how='left', suffixes=('', '_question'))

# save to CSV
final_combined.to_csv(f"../outputs/answers/answers-gpt-oss-20b-{library_name}.csv", index=False)

print(f"Combined {len(final_combined)} records")
print(f"Output saved to: ../outputs/answers/answers-gpt-oss-20b-{library_name}.csv")