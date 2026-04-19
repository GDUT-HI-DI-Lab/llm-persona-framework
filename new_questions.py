from autogen import AssistantAgent, UserProxyAgent , GroupChat, GroupChatManager
import json
from openai import OpenAI
from autogen.oai.client import OpenAIWrapper


# set api key
config_path= "OAI_CONFIG_LIST"
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)
deepseek_list = config["deepseek_chat"]
qwen_list = config["qwen"]

deepseek_config = {
"config_list":[deepseek_list],
"temperature": 0.5,
}

qwen_config = {
"config_list":[qwen_list],
"temperature": 0.5,
}


question_path= "PIF-IndSet/mbti_questions.txt"
with open(question_path, "r", encoding="utf-8") as q:
    question = q.read()




# create user proxy agent, Generator_assistant, Compare_assistant 
user_proxy = UserProxyAgent(
    name="User_proxy",
    code_execution_config = False,
    system_message="You act as the user who initiates a question request. Based on the feedback from the review assistant, determine whether the revised question meets the requirements. If it does not, continue revising; if it does, stop and provide the result.",
    human_input_mode = "NEVER",
    llm_config=deepseek_config,
)

Generator_assistant = AssistantAgent(
    name="Generator_assistant",
    description="You are a professional rewriting assistant who excels at generating new versions of original questions without altering their core meaning, while ensuring other large language models cannot identify them as identical tasks. If revision suggestions are provided, you shall modify the questions accordingly.",
    system_message= "You are a professional rewriting assistant. You need to change the wording and expressions of the content provided to you so that other large models cannot recognize it, without altering the core content. Express both the original content and the revised content in English and output them in one-to-one correspondence.",
    llm_config=deepseek_config,
)

Compare_assistant= AssistantAgent(
    name="Compare_assistant",
    description="You are a professional review assistant who is skilled at comparing whether two questions are identical in nature.",
    system_message="You are a professional review assistant responsible for comparing the two sets of questions sent to you, identifying which ones are identical and which are not. List the questions that are recognized as the same. Provide revision suggestions for those that are the same question; no suggestions are needed for those that are not.",
    llm_config=qwen_config,
)


work_agents = [Generator_assistant, Compare_assistant]
# Create Group Chat（Set maximum rounds, speaking order, etc.)
groupchat = GroupChat(
    agents=work_agents,
    messages=[],
    max_round=6,  
    speaker_selection_method="round_robin"  
)
# Create Group Manager (Coordinate Agent Interactions)
manager = GroupChatManager(
    groupchat=groupchat,
    llm_config=deepseek_config,  
    code_execution_config=False
)

# Initiate a multi-agent collaboration task
result = user_proxy.initiate_chat(
    manager,  
    message="Rewrite these questions in English without changing their original meaning. Alter the vocabulary and expressions to ensure that readers cannot recognize them as the original questions. If any question is identified as the original one, revise it until it is unrecognizable."+f"\n\n【refer to the text file】\n{question}\nGenerate new questions based on the content of this file."
)

with open (f'PIF-IndSet/new_questions.txt', 'w') as f:
    json.dump(result, f)