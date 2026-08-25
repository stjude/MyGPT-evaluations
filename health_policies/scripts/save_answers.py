import json
import requests
import time
import pandas as pd
import re
import os
import csv
from dotenv import load_dotenv

load_dotenv('../../.env')
start_time = time.time()

#############
# Variables #
#############

MODELS = [
     'gpt-oss:20b'
]

TRASNLATE_MODELS = [
    'translategemma:latest'
]
language_from_full = 'English'
language_from = 'en'
# language_to_full = 'Spanish'
# language_to = 'es'
language_to_full = 'French'
language_to = 'fr'
ANSWER_API = 'http://localhost:11434/api/generate/'

LIBRARY_NAME = 'global-french-bge-no-rerank'
EMBEDDING_MODEL = 'bge'
EMBED_SHORTHANDS = [EMBEDDING_MODEL]

##############

### APIs ###
answer_api = 'http://localhost:8000/api/get_distance_between_answers/'
save_answer_api = 'http://localhost:8000/api/save_answer/'

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
 
token = get_jwt_token()
print(token)

dataset_questions_api = 'http://localhost:8000/api/get_conversation_history/?dataset='
question_detail_api = 'http://localhost:8000/api/get_question_details/?question_id='

CSV_HEADERS = [
    'qid',
    'question',
    'answer',
    'document',
    'dataset',
    'mean_distance_a',
    'relevance_score',
    'hallucination_index_by_equation',
    'hallucination_index_by_ml',
    'vector_distances',
    'vector_scores',
    'bm25_score_raws',
    'bm25_scores',
    'rerank_sentiments',
    'answer_semantic_score',
    'answer_keyword_score',
]


def _is_completed_row(row):
    # A row is considered completed if a numeric score was saved.
    value = str(row.get('mean_distance_a', '')).strip().lower()
    return value not in ('', 'n/a', 'nan', 'none')


def _load_completed_pairs(output_path):
    completed_pairs = set()
    if not os.path.exists(output_path):
        return completed_pairs

    try:
        with open(output_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row:
                    continue

                qid_raw = str(row.get('qid', '')).strip()
                document = str(row.get('document', '')).strip()
                if not qid_raw or not document:
                    continue

                try:
                    qid = int(float(qid_raw))
                except ValueError:
                    continue

                if _is_completed_row(row):
                    completed_pairs.add((qid, document))
    except Exception as e:
        print(f"Could not parse existing output for resume: {e}.", flush=True)

    return completed_pairs


def _append_output_row(output_path, row_values):
    with open(output_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row_values)
        f.flush()
 
def get_context_distances(input_contexts, input_answers):
        with open(input_contexts, encoding='utf-8') as file:
            json_data = pd.DataFrame.from_dict(json.load(file))
            question_list = json_data['question'].tolist()
            dataset_list = json_data['dataset_name'].tolist()

        with open(input_answers, encoding='utf-8') as file:
            json_data = pd.DataFrame.from_dict(json.load(file))
            context_lists = json_data['context'].tolist()
            answers_list = json_data['answer'].tolist()
            document_list = json_data['document'].tolist()
            
        for model in MODELS:
            # if (model, shorthand) in COLLECTED:
            #     continue
            for shorthand in EMBED_SHORTHANDS:
                output = f'../outputs/answers/answers-scores-{LIBRARY_NAME}-{model.replace(":", "-")}.csv'

            # Load completed rows so re-runs skip only successfully saved questions.
            completed_pairs = _load_completed_pairs(output)
            if completed_pairs:
                print(f"Found {len(completed_pairs)} completed question-document pairs. Resuming...", flush=True)

            # Write header if starting fresh
            if not os.path.exists(output) or os.stat(output).st_size == 0:
                with open(output, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(CSV_HEADERS)
            
            for j, (question, answer, contexts_full, document, dataset) in enumerate(zip(question_list, answers_list, context_lists, document_list, dataset_list)):
                question_idx = j + 1
                # Skip if this qid-document pair was previously completed.
                if (question_idx, document) in completed_pairs:
                    print(f'Q{question_idx} ({document}) - Already completed, skipping...', flush=True)
                    continue
                
                print(f'\nMODEL: {model}; EMBEDDING: {shorthand};')
                print(f'Loading Question {j + 1}...', flush=True)

                translated_answer = translate_answer(answer)
                safe_question = question.replace('"', '“')

                if contexts_full == []:
                    _append_output_row(output, [
                        question_idx,
                        safe_question,
                        translated_answer,
                        document,
                        dataset,
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a'
                    ])
                    continue

                try:
                    response = requests.post(save_answer_api, json={
                        'question_text': question,
                        'answer_text': translated_answer,
                        'answer_no_context_text': 'n/a',
                        'model_type': 'gpt-oss:20b',
                        'dataset': dataset,
                        'no_context': False,
                        'use_default_ars': True,
                        'answer_best_distance':27.328,
                        'answer_worst_distance':153.758,
                        'use_default_hi': True,
                        'a_hi':1,
                        'b_hi':0.33,
                        'c_hi':0.66,
                        'temperature':0.4,
                        'top_k':20,
                        'top_p':0.7
                    },
                    headers={'Authorization': f'Bearer {token}'}, timeout=30)

                    if response.status_code == 200:
                        response_data = response.json()
                        mean_distance_a = response_data.get('mean_distance_a', 'n/a')
                        relevance_score = response_data.get('relevance_score', 'n/a')
                        semantic_score = response_data.get('semantic_score', 'n/a')
                        keyword_score = response_data.get('keyword_score', 'n/a')
                        hallucination_index_by_equation = response_data.get('hallucination_index_by_equation', 'n/a')
                        hallucination_index_by_ml = response_data.get('hallucination_index_by_ml', 'n/a')
                        sources = response_data.get('sources', [])
                        
                        if sources:
                            vector_distances = [source.get('answer_vector_distance_raw', 0) for source in sources]
                            vector_scores = [source.get('answer_vector_score', 0) for source in sources]
                            bm25_score_raws = [source.get('bm25_score_raw', 0) for source in sources]
                            bm25_scores = [source.get('answer_bm25_score', 0) for source in sources]
                            rerank_sentiments = [source.get('rerank_sentiment', 0) for source in sources]
                        else:
                            vector_distances = vector_scores = bm25_score_raws = bm25_scores = rerank_sentiments = answer_semantic_scores = answer_keyword_scores = []

                        # Write to CSV after each successful request.
                        _append_output_row(output, [
                            question_idx,
                            safe_question,
                            answer,
                            document,
                            dataset,
                            mean_distance_a,
                            relevance_score,
                            hallucination_index_by_equation,
                            hallucination_index_by_ml,
                            semantic_score,
                            keyword_score,
                            vector_distances,
                            vector_scores,
                            bm25_score_raws,
                            bm25_scores,
                            rerank_sentiments,

                        ])
                        completed_pairs.add((question_idx, document))
                        print(f"Q{question_idx} - Success", flush=True)
                    else:
                        print(f"Q{question_idx} - Error: Status {response.status_code}", flush=True)
                        _append_output_row(output, [
                            question_idx,
                            safe_question,
                            answer,
                            document,
                            dataset,
                            'n/a',
                            'n/a',
                            'n/a',
                            'n/a',
                            'n/a',
                            'n/a',
                            'n/a',
                            'n/a',
                            'n/a',
                            'n/a',
                            'n/a'

                        ])
                        
                except Exception as e:
                    print(f"Q{question_idx} - Exception: {str(e)}", flush=True)
                    _append_output_row(output, [
                        question_idx,
                        safe_question,
                        answer,
                        document,
                        dataset,
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a',
                        'n/a'
                    ])
                
                # Small delay between requests
                time.sleep(0.5)

def calculate_context_answers_distance():
    input_contexts = f'../outputs/contexts/eval_contexts_{LIBRARY_NAME}-fr.json'
    input_answers = f'../outputs/answers/answers-{MODELS[0].replace(":","-")}-{LIBRARY_NAME}-fr.json'
    get_context_distances(input_contexts, input_answers)

def query_api(url, payload):
    """Query the API with the given payload and measure time taken."""
    headers = {'Content-Type': 'application/json'}
    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload)
    end_time = time.time()
    print(f"API call to {url} took {end_time - start_time:.2f} seconds.")
    if response.status_code == 200:
        return response.json()
    print(f"Error: {response.text}")
    print(response.reason)
    return None

def translate_answer(answer):
    """
    Translates a given answer using the specified model.

    Args:
        answer (str): The answer text to translate.
    """
    
    system_prompt = f'You are a professional {language_from_full} ({language_from}) to {language_to_full} ({language_to}) translator. Your goal is to accurately convey the meaning and nuances of the original {language_from_full} text while adhering to {language_to_full} grammar, vocabulary, and cultural sensitivities. Produce only the {language_to_full} translation, without any additional explanations or commentary. Please translate the following {language_from_full} text into {language_to_full}:  '
                
    answer_prompt = {
        "model": TRASNLATE_MODELS[0],
        "prompt": answer,
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

    return answer
 
calculate_context_answers_distance()

end_time = time.time()

elapsed_time = (end_time - start_time)/60
print(f"\n\nExecution time: {elapsed_time} min\n\n")