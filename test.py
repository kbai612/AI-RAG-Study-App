import json
import re

llm_response = """[
    {
        "question": "What is the formula for Euclidean distance between two points $(x_1, y_1)$ and $(x_2, y_2)$?",
        "options": [
            "$\\\\sqrt{(x_1 - y_1)^2 + (x_2 - y_2)^2}$",
            "$|x_1 - y_1| + |x_2 - y_2|$",
            "$\\\\max(|x_1 - y_1|, |x_2 - y_2|)$",
            "$\\\\sum_{i=1}^n |x_i - y_i|^p$"
        ],
        "answer": "$\\\\sqrt{(x_1 - y_1)^2 + (x_2 - y_2)^2}$",
        "type": "Mathematics"
    }
]"""
# match = re.search(r"```(?:json)?\s*(\[.*\])\s*```|(\[.*\])", llm_response, re.DOTALL | re.IGNORECASE)
# json_string_to_parse = match.group(1) if match.group(1) else match.group(2)
# print(json_string_to_parse)
# match = re.compile(r'\[.*\]', re.DOTALL)
# match2= match.search(llm_response)
# extracted_json = match2.group(0) if match2 else None
# # json_string_to_parse = match.group(1) if match.group(1) else match.group(2) 
# corrected_json = extracted_json.replace('\\', '\\\\')
# parsed_data = json.loads(corrected_json)

def parse_mcqs(llm_response_text):
    """
    Parses MCQs from LLM response, expecting a JSON list.
    Attempts to extract JSON from markdown code blocks if present.
    """
    llm_response_text = llm_response_text.strip()
    parsed_mcqs = []
    json_string_to_parse = llm_response_text.strip().replace("\n", " ").replace("\r", "")
    # Use greedy match '.*' instead of non-greedy '.*?' to capture the whole list
    match = re.search(r"```(?:json)?\s*(\[.*\])\s*```|(\[.*\])", llm_response_text, re.DOTALL | re.IGNORECASE)
    if match:
        # Correctly extract the captured group (either group 1 or group 2)
        json_string_to_parse = match.group(1) if match.group(1) else match.group(2)
        json_string_to_parse = json_string_to_parse.strip()
    else:
        if not (llm_response_text.startswith('[') and llm_response_text.endswith(']')) and \
           not (llm_response_text.startswith('{') and llm_response_text.endswith('}')):
             st.warning("Response does not appear to be a JSON list/object. Attempting direct parse.")
        else:
             st.info("No clear JSON block found via regex, attempting parse on the full response.")
    try:
        # Attempt direct JSON parsing
        parsed_data = json.loads(json_string_to_parse)

        return(parsed_data)
    except json.JSONDecodeError as e:
        return []

generated_mcqs = parse_mcqs(llm_response)
mcq = generated_mcqs[0]
print(mcq['answer'])