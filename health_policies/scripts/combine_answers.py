import pandas as pd
import json

def combine_context_with_answers(
	answers_csv,
	contexts_json,
	output_csv
):
	"""
	Combines answer, score, context, and ground truth files, and adds a correctness column from label studio JSON.
	"""
	# Load answer and score CSVs
	df1 = pd.read_csv(answers_csv)

	# Rename relevance_score to ARS if present
	if 'relevance_score' in df1.columns:
		df1.rename(columns={'relevance_score': 'ARS'}, inplace=True)

	# Load contexts JSON
	with open(contexts_json, 'r', encoding='utf-8') as f:
		data = json.load(f)
	extracted_data = []
	import re
	page_number_pattern = re.compile(r"Page (\d+) - ")
	for item in data:
		contexts = item.get('contexts', {})
		# Extract page numbers using regex from each context string
		page_numbers = []
		for context in contexts:
			match = page_number_pattern.search(context)
			if match:
				page_numbers.append(int(match.group(1)))
			else:
				page_numbers.append(None)
		extracted_data.append({
			'question_id': item.get('question_id'),
			'question': item.get('question'),
			'relevance_score': item.get('relevance_score'),
			'vector_distances': item.get('vector_distances'),
			'vector_scores': item.get('vector_scores'),
			'bm25_scores_raw': item.get('bm25_scores_raw'),
			'bm25_scores': item.get('bm25_scores'),
			'reranked_score': item.get('reranked_score'),
			'ranks': item.get('ranks'),
			'page_numbers': page_numbers
		})
	df_contexts = pd.DataFrame(extracted_data)
	
	# Reset index to ensure both DataFrames have matching indices
	df1.reset_index(drop=True, inplace=True)
	df_contexts.reset_index(drop=True, inplace=True)
	
	# Handle duplicate columns before concatenating
	duplicate_cols = set(df1.columns) & set(df_contexts.columns)
	if duplicate_cols:
		# Rename duplicate columns in df_contexts
		rename_dict = {col: f"{col}_context" for col in duplicate_cols}
		df_contexts = df_contexts.rename(columns=rename_dict)
	
	# Merge using index by concatenating along axis=1
	final_combined = pd.concat([df1, df_contexts], axis=1)
	
	if 'relevance_score' in final_combined.columns:
		final_combined.rename(columns={'relevance_score': 'QRS'}, inplace=True)

	# Remove rows with no contexts
	if all(col in final_combined.columns for col in ['mean_distance_a', 'ARS', 'hallucination_index']):
		mask = (
			(final_combined['mean_distance_a'] == 500.0) &
			(final_combined['ARS'] == 500.0) &
			(final_combined['hallucination_index'] == 100.0)
		)
		final_combined = final_combined[~mask]
		final_combined.to_csv(output_csv, index=False)

if __name__ == "__main__":
	library_name = 'global-french-nomic-no-rerank'
	answers_csv = f"../outputs/answers/answers-scores-{library_name}-gpt-oss-120b.csv"
	contexts_json = f'../outputs/contexts/eval_contexts_{library_name}.json'
	output_csv = f"../outputs/answers/answers-gpt-oss-120b-{library_name}-full.csv"

	combine_context_with_answers(
		answers_csv,
		contexts_json,
		output_csv
	)