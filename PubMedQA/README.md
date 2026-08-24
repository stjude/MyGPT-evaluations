# PubMedQA Dataset

## Overview

PubMedQA is a biomedical question answering dataset from PubMed abstracts used to evaluate the MyGPT system's performance on scientific QA tasks with entity re-ranking.

## Folder Structure

```
PubMedQA/
├── inputs/
│   └── questions.csv                # Input questions
├── outputs/
│   ├── contexts/                    # Generated context data
│   │   └── context_PubMedQA-nomic-rerank-2.json
│   └── answers/                     # Generated answers and scores
│       ├── answers-gpt-oss-20b-PubMedQA-nomic-rerank.json
│       ├── answers-gpt-oss-20b-PubMedQA-nomic-rerank-full.csv
│       ├── answers-gpt-oss-20b-PubMedQA-nomic-rerank.csv
│       └── answers-scores-PubMedQA-nomic-rerank-gpt-oss:20b.csv
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

- **File**: `inputs/questions.csv`
- Contains PubMed-based biomedical questions for evaluation

## Output Files

- **Context**: `outputs/contexts/context_PubMedQA-nomic-rerank-2.json` - Context data with nomic entity re-ranking
- **Answers**: `outputs/answers/answers-gpt-oss-20b-PubMedQA-nomic-rerank.json` - LLM responses
- **Formatted Answers**: `outputs/answers/answers-gpt-oss-20b-PubMedQA-nomic-rerank.csv` - Answers in CSV format
- **Scores**: `outputs/answers/answers-scores-PubMedQA-nomic-rerank-gpt-oss:20b.csv` - Evaluation scores

## Notes

- This dataset uses Nomic entity re-ranking for improved context selection
- Ensure `.env` file is configured with appropriate credentials before running scripts
- See the main [README.md](../README.md) for environment setup instructions
