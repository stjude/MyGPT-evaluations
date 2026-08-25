import os
import json
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv('../../.env')
start_time = time.time()

#############
# Variables #
#############

LIBRARY_NAME = 'global-french-bge-no-rerank'
EMBEDDING_MODEL = 'bge-m3:latest'
model = 'gpt-oss:20b'

##############

# Define API endpoints
CONTEXT_API = 'http://localhost:8000/api/get_context/'
DATASET_API = 'http://localhost:8000/api/get_documents/'


# Load evaluation documents and questions
EVAL_DOC = pd.read_csv('../inputs/global_questions.csv', encoding='ISO-8859-1').dropna()
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

def query_api(url, payload, max_retries=2):
    """Query the API with retry logic and exponential backoff."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {TOKEN}'
    }
    
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            end_time = time.time()
            print(f"API call to {url} took {end_time - start_time:.2f} seconds.")
            
            if response.status_code == 200:
                return response.json()
            
            print(f"Error: {response.status_code} - {response.reason}")
            
            # Retry on 500 errors
            if response.status_code == 500 and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"Retrying in {wait_time}s... (attempt {attempt + 2}/{max_retries})")
                time.sleep(wait_time)
                continue
            
            return None
        except requests.exceptions.Timeout:
            print(f"Request timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                return None
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    return None

# Get all documents from the library
def get_library_documents(library_name):
    """Fetch all documents from the specified library."""
    payload = {
        'dataset': library_name,
        'user_email': '',
        'user_group': ''
    }
    print(f"\nFetching documents from '{library_name}'...")
    print(f"Using user_email: {payload['user_email']}")
    response = query_api(DATASET_API, payload)
    if response and 'documents' in response:
        docs = response['documents']
        print(f"Found {len(docs)} documents")
        return docs
    print("No documents found or API error")
    return []

# Fetch all documents from the library
all_documents = get_library_documents(LIBRARY_NAME)

def context_already_exists(result_file_path, document, question_id):
    """Check if context already exists for this combination."""
    if not os.path.exists(result_file_path):
        return False
    
    try:
        with open(result_file_path, 'r', encoding='utf-8') as result_file:
            result_data = json.load(result_file)
            for item in result_data:
                if (item.get('document') == document and 
                    item.get('qid') == question_id):
                    # Check if contexts list is not empty
                    if item.get('contexts') and len(item.get('contexts', [])) > 0:
                        return True
                    # Found the entry but contexts are empty, need to reprocess
                    return False
        return False
    except (json.JSONDecodeError, KeyError):
        return False

# Main processing loop
for shorthand in EMBED_SHORTHANDS:
    print(f'Processing embedding model: {shorthand}')
    for dataset in DATASETS:
        print(f'Processing dataset: {dataset}')
        proper_dataset = f'{dataset}'
        result_file_path = f'../outputs/contexts/eval_contexts_{proper_dataset}-fr.json'
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
        
        # Initialize or load existing results
        existing_results = []
        if os.path.exists(result_file_path):
            with open(result_file_path, 'r', encoding='utf-8') as result_file:
                existing_results = json.load(result_file)
            print(f'Loaded {len(existing_results)} existing results.')
        
        # Process each document individually
        for doc_idx, document in enumerate(all_documents):
            document_title = document.get('paper_title', 'Unknown')
            print(f"\n[{doc_idx + 1}/{len(all_documents)}] Processing document: {document_title}")
            
            # Process each question for this document
            for question_idx, question in enumerate(QUESTION_LIST):
                question_id = question_idx + 1
                # for modified questions, only process Q3 and Q8
                # if question_id != 3 and question_id != 8:
                #     continue
                
                # Check if already processed for this document
                if context_already_exists(result_file_path, document_title, question_id):
                    print(f'  Q{question_id}: Already has context, skipping')
                    continue
                
                # Delay between requests to avoid overwhelming server
                time.sleep(2)
                
                # Query this specific document
                context_payload = {
                    "text": question,
                    "model_type": model,
                    "document_title": document_title,  
                    "maximum_chunks_count": 10,
                    "no_cutoff": False,
                    "use_default_qrs": True,
                    "dataset": proper_dataset,
                    "new_conversation": True,
                    "related_query": False,
                    "previous_query": "",
                    "no_context": False,
                    "question_best_distance": 0.2,
                    "question_worst_distance": 1.7,
                    "skip_highlight": True,
                    "language_of_docs": "french"
                }
                
                print(f"  Q{question_id}: {question[:60]}...")
                context_raw = query_api(CONTEXT_API, context_payload)
                if context_raw:
                    contexts = [source['context'] for source in context_raw.get('sources', [])]
                    doc_titles = [source['document'] for source in context_raw.get('sources', [])]
                    pages = [source['page'] for source in context_raw.get('sources', [])]
                    vector_distances = [source.get('vector_distance_raw', 0) for source in context_raw.get('sources', [])]
                    vector_scores = [source.get('vector_score', 0) for source in context_raw.get('sources', [])]
                    bm25_scores_raw = [source.get('bm25_score_raw', 0) for source in context_raw.get('sources', [])]
                    bm25_scores = [source.get('bm25_score', 0) for source in context_raw.get('sources', [])]
                    ranks = [source.get('rank', 0) for source in context_raw.get('sources', [])]
                    reranked_scores = [source['reranked_score'] for source in context_raw.get('sources', [])]
                    relevance_score = context_raw.get('relevance_score', [])
                    semantic_score = context_raw.get('semantic_score', [])
                    keyword_score = context_raw.get('keyword_score', [])
                    rerank_score = context_raw.get('rerank_score', [])
                else:
                    contexts = []
                    doc_titles = []
                    pages = []
                    vector_distances = []
                    vector_scores = []
                    bm25_scores_raw = []
                    bm25_scores = []
                    ranks = []
                    reranked_scores = []
                    relevance_score = []
                    semantic_score = []
                    keyword_score = []
                    rerank_score = []

                full_contexts = [
                    f'Page {page} - {doc_title}:  {context}'
                    for doc_title, page, context in zip(doc_titles, pages, contexts)
                ]

                qa_result = {
                    'qid': question_id,
                    'question': question,
                    'document': document_title,
                    'relevance_score': relevance_score,
                    'contexts': full_contexts,
                    'dataset_name': dataset,
                    'vector_distances': vector_distances,
                    'vector_scores': vector_scores,
                    'bm25_scores_raw': bm25_scores_raw,
                    'bm25_scores': bm25_scores,
                    'reranked_scores': reranked_scores,
                    'question_semantic_score': semantic_score,
                    'question_keyword_score': keyword_score,
                    'question_rerank_score': rerank_score,
                    'ranks': ranks
                }

                # Update or append result
                entry_updated = False
                for idx, existing_item in enumerate(existing_results):
                    if (existing_item.get('document') == document_title and 
                        existing_item.get('qid') == question_id):
                        # Update the existing entry
                        existing_results[idx] = qa_result
                        entry_updated = True
                        break
                
                if not entry_updated:
                    # Append new result
                    existing_results.append(qa_result)
                
                with open(result_file_path, 'w', encoding='utf-8') as result_file:
                    json.dump(existing_results, result_file, indent=4)
                print(f"    Saved. Total: {len(existing_results)}")

        print(f'\nFinished processing all documents for dataset: {dataset}')

end_time = time.time()

elapsed_time = (end_time - start_time)/60
print(f"\n\nExecution time: {elapsed_time} min\n\n")

