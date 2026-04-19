from autogen import AssistantAgent, UserProxyAgent , GroupChat, GroupChatManager
import json
from AUTO_FILL_ANSWER import get_QA
import openai
from time import sleep
import re
from get_personality_score import fulfill_answers
import concurrent.futures


# 配置 api key
URL = "https://www.16personalities.com/free-personality-test"
config_path= "OAI_CONFIG_LIST"
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)
"""
分数的取值为[100,80,65,35,20,0]
Energy:score>50时代表E,score<50时代表I
Mind:score>50时代表N,score<50时代表S
Nature:score>50时代表T,score<50时代表F
Tactics:score>50时代表J,score<50时代表P
Identity:score>50时代表A,score<50时代表T
"""

"""参数设置"""
Temperature = 1
need_QA_shuffled =  True
test_times = 5

"""填写你配置中的模型名"""
model_list = config["your model name"]
model_name = "your model name"

model_config = {
"config_list":[model_list],
"temperature": Temperature,
}

"""
全人格类型["ENFJA","ENFPA","ENTJA","ENTPA","ESFJA","ESFPA","ESTJA","ESTPA","INFJA","INFPA","INTJA","INTPA","ISFJA","ISFPA","ISTJA","ISTPA"]

人格测试选择
"""
personality_list = ["choose personality"]



def get_answer(prompt:str , question:str ,sample:str, need_sample:bool,task_id:int )-> str:
    max_retries = 5
    retry_delay = 20
    request_delay = 3
    User_proxy = UserProxyAgent(
        name=f"User_proxy_{task_id}",  # 动态命名，避免多线程下名称冲突
        code_execution_config=False,
        human_input_mode="NEVER"
    )

    for retry in range(max_retries):
        try:
            sleep(request_delay)

            # 关键优化2：动态创建Answer_assistant（每个任务/重试都新建，避免状态污染）
            Answer_assistant = AssistantAgent(
                name=f"Answer{task_id + 1}_assistant_retry{retry}",  # 加重试次数，名称唯一
                description=f"You are a helpful assistant." ,
                llm_config=model,  # 使用传入的配置，不依赖全局变量
            )

            # 构造消息（简化if-else逻辑，避免重复代码）
            if need_sample:
                content = f"\n{prompt}\nYou can answer these questions by the sample.\n{sample}\n【quesions】\n{question}\n"
            else:
                content = f"\n{prompt}\n【quesions】\n{question}\n"
            answer_msg = [{"role": "user", "content": content}]

            # 生成回复
            answer = Answer_assistant.generate_reply(messages=answer_msg, sender=User_proxy)  # 补充sender，AutoGen推荐参数

            # 关键优化3：统一返回字符串格式（避免后续解析TypeError）
            if answer is None:
                raise ValueError(f"任务 {task_id} 重试{retry}次：模型返回空答案")
            # 若返回是列表/元组，拼接成字符串；否则直接转字符串
            if isinstance(answer, (list, tuple)):
                answer_str = " ".join(str(item) for item in answer)
            else:
                answer_str = str(answer).strip()

            return task_id, answer_str  # 返回统一格式的字符串

        # 扩展异常捕获：包含AutoGen包装的错误，避免漏捕
        except openai.RateLimitError as e:
            error_msg = str(e).lower()
            if "rate_limit" in error_msg or "concurrency" in error_msg or "429" in error_msg:
                if retry < max_retries - 1:
                    print(f"⚠️  任务 {task_id}：触发并发限制（第{retry + 1}次重试），{retry_delay}秒后继续...")
                    sleep(retry_delay)
                    continue
                raise Exception(f"❌ 任务 {task_id}：重试{max_retries}次后仍失败（并发限制）") from e
            else:
                # 其他API错误（如无效密钥、模型不存在），直接抛出
                raise Exception(f"❌ 任务 {task_id}：API错误（非并发限制）") from e

        # 捕获其他错误（如空答案、格式错误）
        except Exception as e:
            if retry < max_retries - 1:
                print(f"⚠️  任务 {task_id}：出现错误（{str(e)}），{retry_delay}秒后第{retry + 1}次重试...")
                sleep(retry_delay)
                continue
            raise Exception(f"❌ 任务 {task_id}：重试{max_retries}次后仍失败") from e


    return task_id ,answer


def mbti_to_fixed_scores(mbti_type: str) -> dict:
    """
    将 MBTI 五字母人格类型（如 ENTJA、ENTJ-A）转换为固定分数字典

    规则：
    - Energy（E/I）: E→80，I→20
    - Mind（N/S）: N→80，S→20
    - Nature（T/F）: T→80，F→20
    - Tactics（J/P）: J→80，P→20
    - Identity: 固定 50（忽略输入的第五位字母）

    参数：
        mbti_type: str - MBTI 人格类型（支持 5 字母，带或不带分隔符，如 "ENTJA"、"ENTJ-A"）

    返回：
        dict - 包含 5 个维度分数的字典，格式：{"Energy": 80, "Mind": 80, ..., "Identity": 50}

    异常：
        ValueError - 输入格式无效（非 5 字母人格类型）
    """
    # 步骤1：清理和标准化输入（去除分隔符、转大写、去空格）
    cleaned_mbti = mbti_type.replace("-", "").replace(" ", "").upper()

    # 步骤2：验证输入有效性（必须是 5 字母）
    if len(cleaned_mbti) != 5:
        raise ValueError(
            f"无效的 MBTI 类型：{mbti_type}！请输入 5 字母人格类型（如 ENTJA、ENTJ-A）"
        )

    # 步骤3：定义各维度的映射规则
    dimension_rules = {
        "E_score": {"E": 90, "I": 10},  # 第1位字母（E/I）
        "M_score": {"N": 90, "S": 10},  # 第2位字母（N/S）
        "N_score": {"T": 90, "F": 10},  # 第3位字母（T/F）
        "T_score": {"J": 90, "P": 10}  # 第4位字母（J/P）
    }

    # 步骤4：提取前 4 位核心字母（按顺序对应 4 个维度）
    core_letters = cleaned_mbti[:4]  # 取前4位（如 ENTJA → ENTJ，ENTJ-A → ENTJ）

    # 步骤5：生成各维度分数（按规则映射）
    scores = {}
    for idx, (dimension, letter_map) in enumerate(dimension_rules.items()):
        letter = core_letters[idx]
        if letter not in letter_map:
            valid_letters = "/".join(letter_map.keys())
            raise ValueError(
                f"无效的 {dimension} 维度字母：{letter}！该维度仅支持 {valid_letters}"
            )
        scores[dimension] = letter_map[letter]

    # 步骤6：添加 Identity 固定分数（忽略输入的第五位字母）
    scores["I_score"] = 50

    return scores




for personality in personality_list:
    print("目前人格为",personality)
    if need_QA_shuffled:
        scores=mbti_to_fixed_scores(personality)
        E_score = scores["E_score"]
        M_score = scores["M_score"]
        N_score = scores["N_score"]
        T_score = scores["T_score"]
        I_score = scores["I_score"]

    #导入问题、提示词
    prompt_path= f"PIF-IndSet/prompt/{personality}"

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()

    question_path= "PIF-IndSet/mbti_questions.txt"

    with open(question_path, "r", encoding="utf-8") as q:
        question = q.read()

    sample_path = f"PIF-IndSet/Q&A_shuffled/{personality}_score_{E_score}_{M_score}_{N_score}_{T_score}_{I_score}.txt"

    with open(sample_path, "r", encoding="utf-8") as f:
        sample = f.read()


    model = model_config
    with concurrent.futures.ThreadPoolExecutor(max_workers=test_times) as executor:
        # 提交所有任务（task_id用于区分结果顺序）
        future_to_task = {
            executor.submit(get_answer, prompt, question,sample,need_QA_shuffled, i): i
            for i in range(test_times)
        }

        for future in concurrent.futures.as_completed(future_to_task):
            task_id = future_to_task[future]  # 从future映射到任务ID（之前的i）
            try:
                # 注意：get_answer的返回值需是 (task_id, worker_result)，和提交时的参数对应
                i, worker_result = future.result()  # 获取任务结果
                result = {}

                # 关键修复1：修正正则表达式（匹配目标格式：-2, # Q1: 描述）
                # 格式1（目标格式）：数值, # Q序号: 描述（如 -2, # Q1: ...）
                pattern_target = r"(-?\d+)\s*(?:,)?\s*#\s*(Q\d+)\s*:"
                # 格式2（备用）：Q序号(数值)（如 Q1(-2)）
                pattern_backup1 = r"(Q\d+)\((-?\d+)\)"
                # 格式3（备用）：序号: 数值, # 描述（如 1: -2, # ...）
                pattern_backup2 = r"(\d+)\s*:\s*(-?\d+)\s*(?:,)?\s*#"

                # 步骤1：优先匹配目标格式（最可能命中）
                matches_target = re.findall(pattern_target, worker_result)
                if matches_target:
                    for q_val, q_key in matches_target:
                        result[q_key] = int(q_val)
                    print(f"目标格式匹配到 {len(matches_target)} 项")

                # 步骤2：若目标格式未凑够60项，用备用格式1补充（Qxx(数值)）
                if len(result) < 60:
                    matches_backup1 = re.findall(pattern_backup1, worker_result)
                    for q_key, q_val in matches_backup1:
                        if q_key not in result:  # 不覆盖已有的键
                            result[q_key] = int(q_val)
                    print(f"备用格式1补充 {len(matches_backup1)} 项，当前总计 {len(result)} 项")

                # 步骤3：若仍未凑够60项，用备用格式2补充（序号: 数值）
                if len(result) < 60:
                    matches_backup2 = re.findall(pattern_backup2, worker_result)
                    for seq, q_val in matches_backup2:
                        q_key = f"Q{seq}"  # 转换为 Q1 格式的键
                        if q_key not in result:
                            result[q_key] = int(q_val)
                    print(f"备用格式2补充 {len(matches_backup2)} 项，当前总计 {len(result)} 项")

                # 最终校验：是否凑够60项
                if len(result) == 60:
                    print(f"✅ 任务 {task_id} 成功匹配60项，结果完整！")
                    # 这里可以添加结果存储/后续处理逻辑（如存入列表、写入文件等）
                    # 示例：all_results[task_id] = result
                else:
                    print(f"❌ 任务 {task_id} 仅匹配到 {len(result)} 项，结果不完整！")

            except Exception as e:
                print(f"❌ 任务 {task_id} 执行失败：{str(e)}")



            with open(
                    f'test_result/model_answer/{model_name}_T_{Temperature}_sample_score_{E_score}_{M_score}_{N_score}_{T_score}_{I_score}_{personality}{i}',
                    "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            with open(
                    f'test_result/model_answer/{model_name}_T_{Temperature}_sample_score_{E_score}_{M_score}_{N_score}_{T_score}_{I_score}_{personality}{i}',
                    "r") as f:
                answers = json.load(f)
                answers = list(answers.values())
                print(f"总共 {len(answers)} 个答案")

            personality_results = fulfill_answers(URL, answers)
            sleep(1)
            results_filename = f'test_personality/personlity_score/{model_name}_T_{Temperature}_sample_score_{E_score}_{M_score}_{N_score}_{T_score}_{I_score}_{personality}{i}.json'
            with open(results_filename, "w", encoding="utf-8") as f:
                json.dump(personality_results, f, ensure_ascii=False, indent=2)
                print(f"人格结果已保存到: {results_filename}")

