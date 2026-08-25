import os
import json
import time
import requests
import pandas as pd
import re
from dotenv import load_dotenv

load_dotenv('../../.env')
start_time = time.time()

#############
# Variables #
#############

LIBRARY_NAME = 'global-french-bge-no-rerank'
EMBEDDING_MODEL = 'bge-m3:latest'
MODELS = [
    'gpt-oss:20b'
]

##############

# Define API endpoints
ANSWER_API = 'http://localhost:11434/api/generate/'
DATASET_API = 'http://localhost:8000/api/get_documents/'

# Load evaluation documents and questions
EVAL_DOC = pd.read_csv('../inputs/global_questions.csv', encoding='ISO-8859-1').dropna()
QUESTION_LIST = EVAL_DOC['question'].tolist()

# List of models and embeddings to evaluate
EMBED_SHORTHANDS = [EMBEDDING_MODEL]
COLLECTED = []  # Example: [('llama3:latest', 'mini-l6')]

# Get bearer token for backend API calls
def get_jwt_token():
    response = requests.post('http://localhost:8000/token/', json={
        'username': os.environ.get('API_USERNAME'),
        'password': os.environ.get('API_PASSWORD')
    })
    if response.status_code == 200:
        return response.json().get('access')
    return ''

TOKEN = get_jwt_token()
print(f"Token: {TOKEN[:20]}..." if TOKEN else "No token")

def query_api(url, payload, use_auth=False):
    """Query the API with the given payload and measure time taken."""
    headers = {'Content-Type': 'application/json'}
    if use_auth and TOKEN:
        headers['Authorization'] = f'Bearer {TOKEN}'
    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    end_time = time.time()
    print(f"API call to {url} took {end_time - start_time:.2f} seconds.")
    if response.status_code == 200:
        return response.json()
    print(f"Error: {response.text}")
    print(response.reason)
    return None

# Get all documents from the library
def get_library_documents(library_name):
    """Fetch all documents from the specified library."""
    payload = {
        'dataset': library_name,
        'user_email': os.environ.get('USER_EMAIL', ''),
        'user_group': os.environ.get('USER_GROUP', '')
    }
    print(f"\nFetching documents from '{library_name}'...")
    response = query_api(DATASET_API, payload, use_auth=True)
    if response and 'documents' in response:
        docs = response['documents']
        print(f"Found {len(docs)} documents")
        return docs
    print("No documents found or API error")
    return []

# Fetch all documents from the library
all_documents = get_library_documents(LIBRARY_NAME)
DOCUMENTS = [doc['paper_title'] for doc in all_documents]


def answer_already_exists(result_file_path, document, question_id):
    """Check if answer already exists for this combination."""
    if not os.path.exists(result_file_path):
        return False
    
    try:
        with open(result_file_path, 'r', encoding='utf-8') as result_file:
            result_data = json.load(result_file)
            for item in result_data:
                if (item.get('document') == document and 
                    item.get('question_number') == question_id):
                    # Check if answer is not empty
                    if item.get('answer') and len(item.get('answer', '').strip()) > 0:
                        return True
                    # Found the entry but answer is empty, need to reprocess
                    return False
        return False
    except (json.JSONDecodeError, KeyError):
        return False


def collect_answers():
    """Main function to collect answers from the API."""
    for shorthand in EMBED_SHORTHANDS:
        # Load all contexts
        with open('../outputs/contexts/eval_contexts_' + LIBRARY_NAME + '-fr.json', encoding='utf-8') as file:
            all_contexts = json.load(file)
        
        for model in MODELS:
            if (model, shorthand) in COLLECTED:
                continue
            
            model_name = model.removesuffix(":latest").replace(":", "-")
            result_file_path = f'../outputs/answers/answers-{model_name}-{LIBRARY_NAME}-fr.json'
            os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
            
            # Initialize or load existing results
            existing_results = []
            if os.path.exists(result_file_path):
                with open(result_file_path, 'r', encoding='utf-8') as result_file:
                    existing_results = json.load(result_file)
                print(f'Loaded {len(existing_results)} existing results.')
            
            # Process each document
            for doc_idx, document in enumerate(DOCUMENTS):
                print(f"\n[{doc_idx + 1}/{len(DOCUMENTS)}] Processing document: {document}")
                
                # Process each question for this document
                for question_idx, question in enumerate(QUESTION_LIST):
                    question_id = question_idx + 1
                    # for modified questions, only process Q3 and Q8
                    # if question_id != 3 and question_id != 8:
                    #     continue
                    
                    # Check if already processed
                    if answer_already_exists(result_file_path, document, question_id):
                        print(f'  Q{question_id}: Already has answer, skipping')
                        continue
                    
                    # Find the context for this document and question
                    contexts_full = []
                    for ctx_item in all_contexts:
                        if (ctx_item.get('document') == document and 
                            ctx_item.get('qid') == question_id):
                            contexts_full = ctx_item.get('contexts', [])
                            break
                    
                    # # If the question has no context, save empty answer
                    # if not contexts_full:
                    #     print(f'  Q{question_id}: No context found, saving with empty answer')
                    #     # Save entry with empty answer
                    #     qa_result = {
                    #         'question': question,
                    #         'context': [],
                    #         'answer': '',
                    #         'question_number': question_id,
                    #         'model': model,
                    #         'document': document
                    #     }
                        
                        # Update or append result
                        # entry_updated = False
                        # for idx, existing_item in enumerate(existing_results):
                        #     if (existing_item.get('document') == document and 
                        #         existing_item.get('question_number') == question_id):
                        #         existing_results[idx] = qa_result
                        #         entry_updated = True
                        #         break
                        
                        # if not entry_updated:
                        #     existing_results.append(qa_result)
                        
                        # with open(result_file_path, 'w', encoding='utf-8') as result_file:
                        #     json.dump(existing_results, result_file, indent=4)
                        # print(f'    Saved. Total: {len(existing_results)}')
                        # continue
                    
                    # Clean contexts
                    contexts = []
                    contexts_regex = r'Page \d+ - .+?:  '
                    for context in contexts_full:
                        if re.match(contexts_regex, context):
                            context = re.sub(contexts_regex, '', context)
                        contexts.append(context)

                    if len(contexts) == 0:
                        contexts = ["### IMPORTANT: No relevant context found. Please answer 'No'. ###"]
                    
                    print(f'  Q{question_id}: {question[:60]}...')
                    
                    system_prompt = 'Use following information to answer the question in less than 100 words, and with minimal amount of words, try not to use anything else. Always start the answer with "Yes,", "No," and then answer the question:  ' + str(contexts)
                    
                    answer_prompt = {
                        "model": model,
                        "prompt": question,
                        "stream": False,
                        "system": system_prompt,
                        "options": {
                            "temperature": 0.4,
                            "top_k": 20,
                            "top_p": 0.7
                        }
                    }
                    
                    response = query_api(ANSWER_API, answer_prompt)
                    answer = response.get('response', '') if response else ''
                    
                    if answer:
                        qa_result = {
                            'question': question,
                            'context': contexts_full,
                            'answer': answer,
                            'question_number': question_id,
                            'model': model,
                            'document': document
                        }
                        
                        # Update or append result
                        entry_updated = False
                        for idx, existing_item in enumerate(existing_results):
                            if (existing_item.get('document') == document and 
                                existing_item.get('question_number') == question_id):
                                existing_results[idx] = qa_result
                                entry_updated = True
                                break
                        
                        if not entry_updated:
                            existing_results.append(qa_result)
                        
                        with open(result_file_path, 'w', encoding='utf-8') as result_file:
                            json.dump(existing_results, result_file, indent=4)
                        print(f'    Saved. Total: {len(existing_results)}')
                    
                    # Add delay between requests
                    time.sleep(1)

collect_answers()

end_time = time.time()

elapsed_time = (end_time - start_time)/60
print(f"\n\nExecution time: {elapsed_time} min\n\n")

