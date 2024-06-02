from openai import OpenAI
from decouple import config


def gptInit(messages: list):
    client= OpenAI(api_key=config("OPENAI_API_KEY"))
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
    temperature=0.7,
    max_tokens=256,
    top_p=0.9,
    n=2,
    stop=None,
    frequency_penalty=0.9,
    presence_penalty=0.9
    )
    # Extract the generated text from the response
    response_text = response.choices[0].message.content.strip()

    return response_text


# For Module No. 2     Introduction Page
def getIntroPageNote(starting: str, family_name:str, tone:str, chatacters_list:str):

    # Define your prompt
    prompt= f"""
    Write an introductory memo of 200 words for {family_name} family.The intended tone for this communication is {tone} and character traits would you encourage family {chatacters_list}.Avoid explicitly mentioning "memo," and refrain from including greetings or subject lines. Instead, introduce the concept of a family handbook initiated by a parent, outlining its aims, objectives, and the benefits it offers in fostering unity and upholding core values. This handbook is envisioned as a guiding document for future reference, encapsulating the family's mission and vision.
    Begin the letter with {starting} and ensure the absence of questions, build points, or post-scripts. Please structure the content in paragraphs, emphasizing clarity and coherence.
    """
    messages = [
        {"role": "system", "content": "You are the most helpful assistant."}, # provides high-level instructions or context-setting messages
        {"role": "user", "content": prompt}, # user” role represents the messages or queries from the user
        ]
    
    response_text= gptInit(messages=messages)

    return response_text


# def writting_assis_IntroPage(note: str, starting: str, tone:str, chatacters_list:str):
#     prompt = f""" Rewrite and Rephase the below introductory memo in 200 words in the formal way for family.The intended tone for this communication is {tone} and character traits would you encourage family {chatacters_list}.Avoid explicitly mentioning "memo," and refrain from including greetings or subject lines. Instead, introduce the concept of a family handbook initiated by a parent, outlining its aims, objectives, and the benefits it offers in fostering unity and upholding core values. This handbook is envisioned as a guiding document for future reference, encapsulating the family's mission and vision.
#     Begin the letter with {starting} and ensure the absence of questions, build points, or post-scripts. Please structure the content in paragraphs, emphasizing clarity and coherence.\n REPAHASE This according to above instruction:\n {note}"""
#     messages = [
#         {"role": "system", "content": "You are the most helpful assistant."}, # provides high-level instructions or context-setting messages
#         {"role": "user", "content": prompt}, # user” role represents the messages or queries from the user
#         ]
#     print(prompt)
#     response_text= gptInit(messages=messages)

#     return response_text


def writting_assis_IntroPage(note: str):
    prompt = f""" Rewrite and Rephase the below introductory memo in 200 words in the formal way:\n {note}"""
    messages = [
        {"role": "system", "content": "You are the most helpful assistant."}, # provides high-level instructions or context-setting messages
        {"role": "user", "content": prompt}, # user” role represents the messages or queries from the user
        ]
    response_text= gptInit(messages=messages)

    return response_text


# For Module No. 04      Core Value Statement
def getCoreValueStatement(selected_words: str):
    statements = """
        Our family's dedication lies in living out these values every day as we engage with one another and our community, striving to uphold their guiding principles.\n
        Our commitment is to embody these values daily as we interact with each other and our community, endeavoring to maintain their guiding principles.\n
        These values are the cornerstones of our family and we will strive to choose them each day that we walk together serving each other and our community.
    """
    prompt = f""" Generate a 14-16 word family core value statement incorporating key elements are {selected_words} and statement don't have to used all key elements and should be using two or more key elements to generate more generic statement like: \n {statements}."""
    messages = [
        {"role": "system", "content": "You are the most helpful assistant."}, # provides high-level instructions or context-setting messages
        {"role": "user", "content": prompt}, # user” role represents the messages or queries from the user
        ]
    response_text= gptInit(messages=messages)

    return response_text

# For Module No. 05    Vision Statement
def vision_statement_with_core_values(selected_words: str, coreval_stat:str, statements:str):
    prompt = f"""Generate a 190 characters family vision statement for family, start with "Our Family" don't use family name, incorporating key elements {selected_words} and key statement {coreval_stat} and example mission statements  {statements}"""
    messages = [
        {"role": "system", "content": "You are the most helpful assistant."}, # provides high-level instructions or context-setting messages
        {"role": "user", "content": prompt}, # user” role represents the messages or queries from the user
        ]
    response_text= gptInit(messages=messages)

    return response_text


def simple_vision_statement(statements:str):
    prompt = f"""Generate a 190 characters family vision statement for family, start with "Our Family" don't use family name, incorporating key elements {statements}"""
    messages = [
        {"role": "system", "content": "You are the most helpful assistant."}, # provides high-level instructions or context-setting messages
        {"role": "user", "content": prompt}, # user” role represents the messages or queries from the user
        ]
    response_text= gptInit(messages=messages)

    return response_text


# For Module No. 6     Mission Statement
def mission_statement_with_core_values(selected_words: str, coreval_stat:str, statements:str):
    prompt = f"""Generate a 190 characters family mission statement for family, start with "Our Family" don't use family name, incorporating key elements {selected_words} and key statement {coreval_stat} and example mission statements  {statements}"""
    messages = [
        {"role": "system", "content": "You are the most helpful assistant."}, # provides high-level instructions or context-setting messages
        {"role": "user", "content": prompt}, # user” role represents the messages or queries from the user
        ]
    response_text= gptInit(messages=messages)

    return response_text


def simple_mission_statement(statements:str):
    prompt = f"""Generate a 190 characters family mission statement for family, start with "Our Family" don't use family name, incorporating key elements {statements}"""
    messages = [
        {"role": "system", "content": "You are the most helpful assistant."}, # provides high-level instructions or context-setting messages
        {"role": "user", "content": prompt}, # user” role represents the messages or queries from the user
        ]
    response_text= gptInit(messages=messages)

    return response_text