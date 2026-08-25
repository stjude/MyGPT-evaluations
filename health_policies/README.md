# Health Policies Dataset

## Overview

Health Policies evaluates MyGPT retrieval and answer generation on national and regional health policy PDFs. The current scripts are configured for French policy documents and pediatric/global health policy questions.

## Folder Structure

```
health_policies/
├── inputs/
│   ├── global_questions.csv          # Evaluation questions
│   ├── French_10_pdfs/               # French policy PDFs
│   └── Spanish_10_pdfs/              # Spanish policy PDFs
└── scripts/
    ├── collect_context.py            # Retrieve contexts from the MyGPT library
    ├── collect_answers.py            # Generate answers from retrieved contexts
    ├── save_answers.py               # Send answers to scoring API
    └── combine_answers.py            # Combine scores and contexts into final CSV
```

## MyGPT Library Setup

Before running the scripts, create a MyGPT library for the policy PDFs. The current scripts use this library name:

```text
global-french-bge-no-rerank
```

Upload or index the PDFs from `inputs/French_10_pdfs/` into that library before running `collect_context.py`.

For Spanish policy PDFs, create a separate library and update the `LIBRARY_NAME` constants and output suffixes in the scripts before running the pipeline.

## Running the Pipeline

From the `scripts/` directory:

```bash
python3 collect_context.py
python3 collect_answers.py
python3 save_answers.py
python3 combine_answers.py
```

## Input Format

- **Questions**: `inputs/global_questions.csv`
- Required question columns include `qid`, `domain`, `question_key`, `question`, and `for_testing`.
- Policy PDFs are stored under language-specific folders in `inputs/`.

## Output Files

The scripts write generated files under `outputs/` when they run:

- **Contexts**: `outputs/contexts/eval_contexts_global-french-bge-no-rerank-fr.json`
- **Answers**: `outputs/answers/answers-gpt-oss-20b-global-french-bge-no-rerank-fr.json`
- **Scores**: `outputs/answers/answers-scores-global-french-bge-no-rerank-gpt-oss-20b.csv`
- **Combined CSV**: written by `combine_answers.py` based on the library/model constants in that script

## Notes

- Ensure `.env` is configured with `API_USERNAME` and `API_PASSWORD` before running the scripts.
- The scripts currently call the local MyGPT backend at `http://localhost:8000` and Ollama at `http://localhost:11434`.
- Check the hardcoded `LIBRARY_NAME`, model, and output filenames in each script before running a new language or library variant.