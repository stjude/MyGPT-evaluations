# BioASQ Dataset

## Overview

BioASQ is a biomedical question answering dataset used to evaluate the MyGPT system's performance on domain-specific QA tasks.

## Folder Structure

```
BioASQ/
├── inputs/
│   └── questions_final.csv          # Input questions
├── outputs/
│   ├── contexts/                    # Generated context data
│   │   └── context_Bioasq.json
│   └── answers/                     # Generated answers and scores
│       ├── answers-gpt-oss-20b-Bioasq.json
│       └── answers-scores-Bioasq-gpt-oss-20b.csv
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

- **File**: `inputs/questions_final.csv`
- Contains the biomedical questions to be evaluated

## Output Files

- **Context**: `outputs/contexts/context_Bioasq.json` - Context data used for answering
- **Answers**: `outputs/answers/answers-gpt-oss-20b-Bioasq.json` - LLM responses
- **Scores**: `outputs/answers/answers-scores-Bioasq-gpt-oss-20b.csv` - Evaluation scores

## Notes

- Ensure `.env` file is configured with appropriate credentials before running scripts
- See the main [README.md](../README.md) for environment setup instructions
