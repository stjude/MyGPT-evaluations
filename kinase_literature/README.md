# Kinase Literature Dataset

## Overview

Kinase Literature evaluates MyGPT on kinase-specific biomedical literature extraction. The pipeline retrieves contexts from PubMed-linked papers, generates answers for kinase assay questions, scores the answers, and combines results for analysis.

## Folder Structure

```
kinase_literature/
├── inputs/
│   ├── questions.csv                 # Kinase extraction questions
│   ├── kinase_pubmed_pairs.csv       # PubMed/kinase pairs used by the pipeline
│   └── human_kinome_synonyms.csv     # Kinase synonym lookup table
├── outputs/                          # Generated contexts and answers
└── scripts/
    ├── get_dois.py                   # Add DOI values for PubMed IDs
    ├── collect_context.py            # Retrieve contexts from the MyGPT library
    ├── collect_answers.py            # Generate answers from retrieved contexts
    ├── save_answers.py               # Send answers to scoring API
    ├── format_answers.py             # Convert answer JSON to CSV
    └── combine_answers.py            # Combine answers, scores, and contexts
```

## MyGPT Library Setup

Before running the retrieval and answer scripts, create a MyGPT library named:

```text
Kinase-literature
```

Upload or index the kinase literature PDFs into that library. The context and answer scripts use `kinase_pubmed_pairs.csv` to pair papers with kinase names, and the full pipeline expects the paper identifiers in that file to match documents available in the MyGPT library.

## Running the Pipeline

From the `scripts/` directory:

```bash
python3 get_dois.py
python3 collect_context.py
python3 collect_answers.py
python3 save_answers.py
python3 format_answers.py
python3 combine_answers.py
```

`get_dois.py` is optional for retrieval, but useful for enriching `inputs/kinase_pubmed_pairs.csv` with DOI metadata. By default it writes `inputs/kinase_pubmed_pairs_with_doi.csv`.

## Input Format

- **Questions**: `inputs/questions.csv`
- **Kinase/PubMed pairs**: `inputs/kinase_pubmed_pairs.csv`
- **Synonyms**: `inputs/human_kinome_synonyms.csv`

The answer-generation script also reads `inputs/expression_systems_list.csv`; make sure that file is present before running `collect_answers.py`.

## Output Files

The scripts write generated files under `outputs/` when they run:

- **Contexts**: `outputs/contexts/eval_context_Kinase-literature.json`
- **Answers**: `outputs/answers/answers-gpt-oss-20b-Kinase-literature.json`
- **Formatted Answers**: `outputs/answers/answers-gpt-oss-20b-Kinase-literature.csv`
- **Scores**: `outputs/answers/answers-scores-Kinase-literature-gpt-oss:20b.csv`
- **Combined CSV**: `outputs/answers/answers-gpt-oss-20b-Kinase-literature.csv`

## Notes

- Ensure `.env` is configured with `API_USERNAME` and `API_PASSWORD` before running scripts that call MyGPT.
- `get_dois.py` can use optional `NCBI_API_KEY` and `NCBI_EMAIL` environment variables for PubMed E-utilities requests.
- Check the hardcoded `LIBRARY_NAME`, model, and input filenames in the scripts before running a new library variant.