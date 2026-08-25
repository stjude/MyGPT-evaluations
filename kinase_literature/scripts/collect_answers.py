import os
import json
import time
import requests
import pandas as pd
import re

start_time = time.time()

#############
# Variables #
#############

LIBRARY_NAME = 'Kinase-literature'
EMBEDDING_MODEL = 'nomic'
MODELS = [
    'gpt-oss:20b'
]
PUBMED_KINASES_PAIRS = '../inputs/kinase_pubmed_pairs.csv'
##############

# Define API endpoints
ANSWER_API = 'http://localhost:11434/api/generate/'

# get synonums for all the kinases
SYNONYM_DOC = pd.read_csv('../inputs/human_kinome_synonyms.csv').dropna()
KINASES_NAMES_LIST = SYNONYM_DOC['kinase_ID'].tolist()
SYNONYM_LIST = SYNONYM_DOC['synonyms'].tolist()

# Load evaluation documents and questions
EVAL_DOC = pd.read_csv('../inputs/questions.csv', encoding='ISO-8859-1').dropna()
QUESTION_LIST = EVAL_DOC['question'].tolist()
QUESTION_IDS = EVAL_DOC['question_id'].tolist()

EXPRESSION_SYSTEM_DOC = pd.read_csv('../inputs/expression_systems_list.csv').dropna()
EXPRESSION_SYSTEM_LIST = EXPRESSION_SYSTEM_DOC['expression_system_name'].tolist()

# LIB_LIST = [LIBRARY_NAME] * len(QUESTION_LIST)

# List of models and embeddings to evaluate
EMBED_SHORTHANDS = [EMBEDDING_MODEL]
COLLECTED = []  # Example: [('llama3:latest', 'mini-l6')]

def get_documents():
    """Load documents and kinases from the input CSV."""
    df = pd.read_csv(PUBMED_KINASES_PAIRS)
    documents = df['pdf_name'].astype(str).tolist()
    kinases = df['kinase_name'].tolist()
    return documents, kinases

DOCUMENTS, KINASES = get_documents()

def query_api(url, payload):
    """Query the API with the given payload and measure time taken."""
    headers = {'Content-Type': 'application/json'}
    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload, verify=False)
    end_time = time.time()
    print(f"API call to {url} took {end_time - start_time:.2f} seconds.")
    if response.status_code == 200:
        return response.json()
    print(f"Error: {response.text}")
    print(response.reason)
    return None

def collect_answers():
    """Main function to collect answers from the API."""
    for shorthand in EMBED_SHORTHANDS:
        with open('../outputs/contexts/eval_context_' + LIBRARY_NAME + '.json', encoding='utf-8') as file:
            context_lists = pd.DataFrame.from_dict(json.load(file))['contexts'].tolist()
        for model in MODELS:
            if (model, shorthand) in COLLECTED:
                continue
            
            # Load existing answers to check what's already generated
            model_name = model.removesuffix(":latest").replace(":", "-")
            result_file_path = f'../outputs/answers/answers-{model_name}-{LIBRARY_NAME}.json'
            existing_answers = []
            if os.path.exists(result_file_path):
                with open(result_file_path, 'r', encoding='utf-8') as result_file:
                    existing_answers = json.load(result_file)
                print(f'Found {len(existing_answers)} existing answers for {model_name}. Will skip already generated answers.')
            
            for i, (document, kinase) in enumerate(zip(DOCUMENTS, KINASES)):
                for j, question in enumerate(QUESTION_LIST):
                    question_id = j + 1
                    
                    # Only process questions 11, 15, 16
                    questions_to_process = [11, 15, 16]
                    if question_id not in questions_to_process:
                        continue
                    
                    # Check if answer already exists for this combination
                    matching_answers = [
                        ans for ans in existing_answers
                        if (ans.get('document') == document and 
                            ans.get('kinase') == kinase and 
                            ans.get('question_number') == question_id)
                    ]
                    
                    if matching_answers:
                        print(f'Skipping already generated: Question {question_id}, kinase {kinase}, document {document}')
                        continue
                    
                    # Map question_id to context index (0-5)
                    question_idx = questions_to_process.index(question_id)
                    
                    # Get contexts: 3 questions per document
                    contexts_full = context_lists[(i * 3) + question_idx]
                    # contexts_full = context_lists[(i * 3) + question_idx]
                    contexts = []
                    #  remove this kind of strings from the beginning of the context 'Page 4 - 38252844:  '
                    contexts_regex = r'Page \d+ - \d+:  '
                    for index, context in enumerate(contexts_full):
                        if re.match(contexts_regex, context):
                            # remove the string from the context
                            context = re.sub(contexts_regex, '', context)
                            contexts.append(context)
                    print('\n')
                    print(f'MODEL: {model}; EMBEDDING: {shorthand};')
                    print(f'Loading Question {question_id}... For Kinase: {kinase}')

                    system_prompt = ''
                    kinase_id_idx = KINASES_NAMES_LIST.index(kinase)
                    question = question.replace('[kinase name]', kinase) + ' The kinase ' + kinase + ' is a also known as ' + SYNONYM_LIST[kinase_id_idx] + '.'

                    # Q11
                    if question_id == 11:
                      system_prompt = '  Use following information to answer the question in less than 50 words, and with minimal amount of words, try not to use anything else. Answer the expression system and avoid other text. If there are no expression system in these experiments, answer with "no answer". Use one of these choices for expression system: [' + ', '.join(EXPRESSION_SYSTEM_LIST) +'] Format it as an javascript array with a single value of expression system, no other text: ' + str(contexts)
                    
                   # Q15
                    elif  question_id == 15:
                        system_prompt = 'Use the following information to answer the question in less than 50 words, with minimal text. If no information is available, respond with "no match." If information is available, list the assay methods used to detect substrate phosphorylation, kinase activity, or catalytic activity, ensuring that mentioned kinase was the enzyme in the experiment. Only list the method names as a JavaScript array, with no additional text: ' + str(contexts)
                    
                    # Q16
                    elif question_id == 16:
                        system_prompt = 'Use following information to answer the question in less than 50 words, and with minimal amount of words, try not to use anything else. List the figures or tables separated by comma and avoid other text. If there are no figures or tables in these experiments, answer with "no answer". Format it as an javascript array of figures and tables, no other text: ' + str(contexts)
                    
                    answer_prompt = {
                        "model": model,
                        "prompt": question,
                        "stream": False,
                        "system": system_prompt,
                        "think": "medium",
                        "options": {
                            "temperature": 0.4,
                            "top_k": 20,
                            "top_p": 0.7
                        }
                    }
                    
                    try:
                        response = query_api(ANSWER_API, answer_prompt)
                        if response and response.get('response'):
                            answer = response.get('response', '')
                            qa_result = {
                                'question': question,
                                'context': contexts_full,
                                'answer': answer,
                                "question_number": question_id,
                                'model': model,
                                'document': document,
                                "kinase": kinase
                            }
                            print(f'Finished processing question {j+1} for document {i+1} ({document})')
                            
                            # Append to existing answers and write
                            existing_answers.append(qa_result)
                            with open(result_file_path, 'w', encoding='utf-8') as result_file:
                                json.dump(existing_answers, result_file, indent=4)
                            print(f'Saved. Total answers: {len(existing_answers)}')
                        else:
                            print(f'WARNING: No response for Q{question_id}, kinase {kinase}, document {document} - will retry on next run')
                    except Exception as e:
                        print(f'ERROR processing Q{question_id}, kinase {kinase}, document {document}: {e}')
                        print(f'Continuing with next question...')
                        continue

collect_answers()

end_time = time.time()

elapsed_time = (end_time - start_time)/60
print(f"\n\nExecution time: {elapsed_time} min\n\n")
# qa-cos, topic 1, gemma3:12b, papers skipped: 6, 74, 100