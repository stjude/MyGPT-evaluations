import os
import json
import time
import requests
import pandas as pd
from dotenv import load_dotenv

## Load environment variables
load_dotenv('../../.env')

# Set start time for execution time measurement.
start_time = time.time()

#############
# Variables #
#############

LIBRARY_NAME = 'Kinase-literature'
EMBEDDING_MODEL = 'nomic'
PUBMED_KINASES_PAIRS = '../inputs/kinase_pubmed_pairs.csv'

##############

# Define API endpoints
CONTEXT_API = 'http://localhost:8000/api/get_context/'
DATASET_API = 'http://localhost:8000/api/get_documents/'

# get synonums for all the kinases
SYNONYM_DOC = pd.read_csv('../inputs/human_kinome_synonyms.csv').dropna()
KINASES_NAMES_LIST = SYNONYM_DOC['kinase_ID'].tolist()
SYNONYM_LIST = SYNONYM_DOC['synonyms'].tolist()

# Load evaluation documents and questions
EVAL_DOC = pd.read_csv('../inputs/questions.csv', encoding='ISO-8859-1').dropna()
QUESTION_LIST = EVAL_DOC['question'].tolist()

LIB_LIST = [LIBRARY_NAME] * len(QUESTION_LIST)

EMBED_SHORTHANDS = [EMBEDDING_MODEL]
DATASETS = [LIBRARY_NAME]

# Get bearer token for backend API calls
def get_jwt_token():
    # get jwt token
    response = requests.post('http://localhost:8000/token/', json={
        'username': os.environ.get('API_USERNAME'),
        'password': os.environ.get('API_PASSWORD')
    })
    if response.status_code == 200:
        token = response.json().get('access')
    else:
        token = ''
    return token
 
TOKEN = get_jwt_token()
print(TOKEN)

def query_api(url, payload):
    """Query the API with the given payload and measure time taken."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {TOKEN}'
    }
    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    end_time = time.time()
    print(f"API call to {url} took {end_time - start_time:.2f} seconds.")
    if response.status_code == 200:
        return response.json()
    print(f"Error: {response.status_code}")
    print(response.reason)
    return None

def get_documents():
    """Load documents and kinases from the input CSV."""
    df = pd.read_csv(PUBMED_KINASES_PAIRS)
    documents = df['pdf_name'].astype(str).tolist()
    kinases = df['kinase_name'].tolist()
    return documents, kinases

[DOCUMENTS, KINASES] = get_documents()

# Main processing loop
for shorthand in EMBED_SHORTHANDS:
    print(f'Processing with embedding: {shorthand}')
    for dataset in DATASETS:
        print(f'Processing dataset: {dataset}')
        proper_dataset = f'{dataset}'
        result_file_path = f'../outputs/contexts/eval_context_{proper_dataset}.json'
        
        # Load existing results to check what's already collected
        existing_results = []
        if os.path.exists(result_file_path):
            with open(result_file_path, 'r', encoding='utf-8') as result_file:
                existing_results = json.load(result_file)
            print(f'Found {len(existing_results)} existing entries. Will skip already collected contexts.')
        
        for i, (document, kinase) in enumerate(zip(DOCUMENTS, KINASES)):
            question_id = 0
            for j, (question, library) in enumerate(zip(QUESTION_LIST, LIB_LIST)):
                question_id = j + 1
                # skip Q8 and Q26 as they will be handled separately
                # question_to_skip = [i for i in range(1, 35) if i not in [11, 12, 13, 15, 16, 17]]
                question_to_skip = [i for i in range(1, 35) if i not in [11, 15, 16]]
                if question_id in question_to_skip:
                    continue
                if library == dataset:
                    # Check for existing entries with this combination
                    matching_entries = [
                        result for result in existing_results
                        if (result['document'] == document and 
                            result['kinase'] == kinase and 
                            result['question_id'] == question_id)
                    ]
                    
                    # Get entries with valid (non-empty) contexts
                    valid_entries = [e for e in matching_entries if len(e.get('contexts', [])) > 0]
                    
                    if valid_entries:
                        # Already have at least one valid entry, skip this entry
                        print(f'Skipping already collected: Question {question_id}, kinase {kinase}, document {document}')
                        
                        # Remove ALL matching entries and keep only one valid entry (deduplicate)
                        existing_results = [
                            result for result in existing_results
                            if not (result['document'] == document and 
                                    result['kinase'] == kinase and 
                                    result['question_id'] == question_id)
                        ]
                        # Add back just one valid entry
                        existing_results.append(valid_entries[0])
                        continue
                    
                    # Remove any existing entries (all are empty) before collecting new data
                    existing_results = [
                        result for result in existing_results
                        if not (result['document'] == document and 
                                result['kinase'] == kinase and 
                                result['question_id'] == question_id)
                    ]
                    
                    if matching_entries:
                        print(f'Re-collecting empty contexts: Question {question_id}, kinase {kinase}, document {document}')
                    
                    print('\n')
                    print(f'DATASET: {proper_dataset}; EMBEDDING: {shorthand};')
                    print(f'Loading Question {str(j+1)}...')
                   
                    kinase_id_idx = KINASES_NAMES_LIST.index(kinase)
                    question = question.replace('[kinase name]', kinase) + ' The kinase ' + kinase + ' is a also known as ' + SYNONYM_LIST[kinase_id_idx] + '.'
                    context_payload = {
                        "text": question,
                        "model_type": "gpt-oss:20b",
                        "focused_document_titles": [document],
                        "maximum_chunks_count": 5,
                        "no_cutoff": False,
                        "use_default_qrs": True,
                        "dataset": proper_dataset,
                        "new_conversation": True,
                        "related_query": False,
                        "previous_query": "",
                        "no_context": False,
                        "question_best_distance": 0.2,
                        "question_worst_distance": 1.7,
                        "skip_highlight": True
                    }
                    context_raw = query_api(CONTEXT_API, context_payload)
                    if context_raw:
                        contexts = [source['context'] for source in context_raw.get('sources', [])]
                        document_titles = [source['document'] for source in context_raw.get('sources', [])]
                        pages = [source['page'] for source in context_raw.get('sources', [])]
                        vector_distances = [source['vector_distance_raw'] for source in context_raw.get('sources', [])]
                        vector_scores = [source['vector_score'] for source in context_raw.get('sources', [])]
                        bm25_scores_raw = [source['bm25_score_raw'] for source in context_raw.get('sources', [])]
                        bm25_scores = [source['bm25_score'] for source in context_raw.get('sources', [])]
                        ranks = [source['rank'] for source in context_raw.get('sources', [])]
                        reranked_score = [source['reranked_score'] for source in context_raw.get('sources', [])]
                        relevance_score = context_raw.get('relevance_score', [])
                        question_id = j + 1
                    else:
                        contexts = []
                        document_titles = []
                        pages = []
                        vector_distances = []
                        vector_scores = []
                        bm25_scores_raw = []
                        bm25_scores = []
                        ranks = []
                        reranked_score = []
                        relevance_score = []
                        question_id = j + 1

                    full_contexts = [
                        f'Page {page} - {document_title}:  {context}'
                        for document_title, page, context in zip(document_titles, pages, contexts)
                    ]

                    qa_result = {
                        'question': question,
                        'relevance_score': relevance_score,
                        'contexts': full_contexts,
                        'dataset': dataset,
                        'question_id': question_id,
                        'document': document,
                        'kinase': kinase,
                        'vector_distances': vector_distances,
                        'vector_scores': vector_scores,
                        'bm25_scores_raw': bm25_scores_raw,
                        'bm25_scores': bm25_scores,
                        'reranked_score': reranked_score,
                        'ranks': ranks
                    }
                    print(f'Writing to {result_file_path}...')

                    # Append to existing results and write
                    existing_results.append(qa_result)
                    with open(result_file_path, 'w', encoding='utf-8') as result_file:
                        json.dump(existing_results, result_file, indent=4)
                    print(f'Saved. Total entries: {len(existing_results)}')
                    
                print(f'Finished processing question {j+1} for document {i+1} ({document})')

end_time = time.time()

elapsed_time = (end_time - start_time)/60
print(f"\n\nExecution time: {elapsed_time} min\n\n")