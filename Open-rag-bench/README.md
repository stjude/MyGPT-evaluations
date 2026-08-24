# Open-rag-bench Dataset

## Overview

Open-rag-bench is a retrieval-augmented generation benchmark dataset used to evaluate the MyGPT system's performance on open-domain question answering with context retrieval.

## Folder Structure

```
Open-rag-bench/
├── inputs/
│   └── text_queries_170.csv         # Input queries
├── outputs/
│   ├── contexts/                    # Generated context data
│   │   └── context_open-rag-bench-4.json
│   └── answers/                     # Generated answers and scores
│       ├── answers-gpt-oss-20b-open-rag-bench-4.json
│       ├── answers-gpt-oss-20b-open-rag-bench-4-full.csv
│       ├── answers-gpt-oss-20b-open-rag-bench-4.csv
│       └── answers-scores-open-rag-bench-4-gpt-oss:20b.csv
└── scripts/
    ├── collect_context.py           # Build context JSON
    ├── collect_answers.py           # Call LLM and store answers
    ├── save_answers.py              # Send answers to scoring API
    ├── format_answers.py            # Convert answer JSON to CSV
    └── combine_answers.py           # Combine all results
```

## Running the Pipeline

From the `scripts/` directory:

```bash
python3 collect_context.py
python3 collect_answers.py
python3 save_answers.py
python3 format_answers.py
python3 combine_answers.py
```

## Input Format

- **File**: `inputs/text_queries_170.csv`
- Contains 170 text queries for retrieval-augmented generation evaluation

## Output Files

- **Context**: `outputs/contexts/context_open-rag-bench-4.json` - Retrieved context for each query
- **Answers**: `outputs/answers/answers-gpt-oss-20b-open-rag-bench-4.json` - LLM responses
- **Formatted Answers**: `outputs/answers/answers-gpt-oss-20b-open-rag-bench-4.csv` - Answers in CSV format
- **Scores**: `outputs/answers/answers-scores-open-rag-bench-4-gpt-oss:20b.csv` - Evaluation scores

## Notes

- Ensure `.env` file is configured with appropriate credentials before running scripts
- See the main [README.md](../README.md) for environment setup instructions
