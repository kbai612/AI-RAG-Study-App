# Cerebro AI
_A flexible, tailored study application built to help you learn better._

## Installation
```bash
# For all required libraries and packages 
pipx install -r requirements.txt
```
## Key Features
In the Cerebro homepage you are able to pull all documents in your google drive to be included in the knoweledge base through your Google Drive API. You are also able to manually add additional documents if you need extra context.This uses model BAAI/bge-base-en-v1.5 for embedding which runs locally on your machine and creates a vector store in memory.
![image](https://github.com/user-attachments/assets/5cc739bc-9ecf-45e3-be59-1d43b2943c2f)

You're also able to chat with Cerebro about your study documents. It will provide detailed responses and go in depth step by step for concepts that you want to learn. It utilizes Conversation Buffer Memory to create a memory object, automatically adding context after each interaction. It also formats mathimatical characters using LateX into easy to read equations.
![image](https://github.com/user-attachments/assets/2bd1cc38-6d0d-4c7e-8376-2a8cb1e07928)

In the Flashcards tab, you're able to create up to 50 flashcards on the material you've uploaded, highlighting key concepts and definitions. You can also star flashcards that you need to study more for later and go through them at the bottom.
![image](https://github.com/user-attachments/assets/5b0b1ad8-3aae-482f-adb9-2ad1683d2277)

In the MCQ Generator tab, you're able to generate multiple choice questions with a total of 4 choices. You can also generate up to 50 MC questions here and star them to review at the bottom
![image](https://github.com/user-attachments/assets/790b40df-7afe-46c0-bba7-8eac818ead73)



