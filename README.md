# PIF - Personality Induction Framework

PIF (Personality Induction Framework) is an automated personality induction system based on MBTI personality tests. It can generate test answers that conform to specific personality types through multi-agent collaboration and verify their accuracy.

## Project Overview

The system is mainly used for:
- **Automated Personality Testing**: Automatically fill MBTI test questions and obtain personality types and dimension scores
- **Personality Induction Verification**: Generate answers conforming to specific personality types through LLM and verify their accuracy
- **Question Rewriting**: Use multi-agent collaboration to rewrite MBTI test questions, maintaining original meaning while changing expressions
- **Answer Generation and Shuffling**: Automatically generate corresponding answers based on personality dimension scores and shuffle the order

## Project Structure

```
PIF/
├── AUTO_FILL_ANSWER.py          # Automatically generate answers based on personality scores
├── get_personality_score.py     # Scrape MBTI test results
├── new_questions.py            # Multi-agent question rewriting
├── Personality assessment.py   # Main test file
├── Q&A_shuffled.py            # Shuffle answer order
├── OAI_CONFIG_LIST             # API configuration file
├── PIF-IndSet/                 # Data storage directory
│   ├── prompt/                # Personality induction prompts
│   ├── Q&A/                   # Generated Q&A pairs
│   ├── Q&A_shuffled/          # Shuffled Q&A pairs
│   ├── mbti_questions.txt     # Original MBTI questions
│   └── new_questions.txt      # Rewritten questions
└── test_result/               # Test results
    ├── model_answer/          # Model-generated answers
    └── personlity_score/      # Personality test scores
```

## Core Features

### 1. Personality Test Scraping (`get_personality_score.py`)
- Automated MBTI test completion
- Scrape test results (personality types and dimension percentages)
- Edge browser automation support

### 2. Automatic Answer Generation (`AUTO_FILL_ANSWER.py`)
- Automatically generate corresponding answers based on 5 dimension scores
- Support score mapping: 100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0
- Intelligent allocation of positive/negative question answers

### 3. Multi-Agent Question Rewriting (`new_questions.py`)
- Uses AutoGen framework
- Generator Agent: Rewrites questions, maintaining meaning while changing expression
- Compare Agent: Compares rewriting effectiveness, ensuring questions aren't recognized as originals
- Supports multi-round iterative optimization

### 4. Personality Induction Testing (`Personality assessment.py`)
- Main test flow control
- Multi-threaded concurrent testing
- Personality type to score mapping
- Result saving and verification

### 5. Answer Shuffling (`Q&A_shuffled.py`)
- Maintains Q&A pairing relationships
- Randomly shuffles question order
- Supports answer generation for different personality types

## Personality Dimensions

The system is based on MBTI's 5 dimensions:
- **Energy (E/I)**: Extraversion/Introversion
- **Mind (N/S)**: Intuition/Sensing
- **Nature (T/F)**: Thinking/Feeling
- **Tactics (J/P)**: Judging/Perceiving
- **Identity (A/T)**: Assertive/Turbulent

Scoring Rules:
- Score > 50: Represents the first letter (e.g., E, N, T, J, A)
- Score < 50: Represents the second letter (e.g., I, S, F, P, T)
- Score = 50: Neutral state

## Usage Process

1. **Configure API**: Set up LLM API keys in `OAI_CONFIG_LIST`
2. **Set Parameters**: Configure test parameters in `Personality assessment.py`
3. **Run Tests**: Execute the main file for personality induction testing
4. **View Results**: Check test results in the `test_result` directory

## Dependencies

Please refer to the `requirements.txt` file for necessary dependency packages.

## Important Notes

- Valid LLM API keys must be configured
- Microsoft Edge browser driver needs to be installed
- The browser will automatically open during testing
- Recommended to run in a stable network environment

## Output Description

- **Personality Type**: e.g., ENFJ-A, INTP-T, etc.
- **Dimension Scores**: Percentage scores for each dimension
- **Test Results**: Complete test data in JSON format
