import os
import random

Energy_pos=[0,10,15,30,35,42,52]
Energy_neg=[5,20,25,40,50]
Mind_pos=[1,16,18,29,36,41,56]
Mind_neg=[11,21,31,45,51]
Nature_pos=[12,22,24,27,37]
Nature_neg=[2,7,17,32,47,53,57]
Tactics_pos=[3,6,8,23,38,43,55]
Tactics_neg=[13,28,33,48,58]
Identity_pos=[4,14,34,39,59]
Identity_neg=[9,19,26,44,46,49,54]

# 答案映射（保持原配置不变）
ANSWER_MAP = {
    3: "strongly agree",
    2: "agree",
    1: "tend to agree",
    0: "unsure",
    -1: "tend to disagree",
    -2: "disagree",
    -3: "strongly disagree"
}


def get_dimension_config(score):
    """
    五个维度统一配置：分数段对称设计
    格式说明：每个配置项为 (分数区间, 总题数, 分数分配规则)
    分数分配规则：[(目标分数, 该分数的题目数量), ...]
    """
    configs = [
        # -------------------------- 高分区（100~60分）--------------------------
        ((99, 100), 12, [(3, 12)]),  # 100分：12题全3分（strongly agree）
        ((90, 98), 12, [(3, 6), (2, 6)]),  # 90-98分：6题3分 + 6题2分（随机）
        ((80, 89), 12, [(2, 12)]),  # 80-89分：12题2分 （随机）
        ((70, 79), 12, [(2, 6), (1, 6)]),  # 70-79分：6题2分 + 6题1分（随机）
        ((60, 69), 12, [(1, 12)]),  # 60-69分：12题全1分（tend to agree）

        # -------------------------- 中间区（50分）--------------------------
        ((50, 50), 12, [(0, 12)]),  # 50分专属：12题全0分（unsure）

        # -------------------------- 低分区（49~0分）：与高分区对称 --------------------------
        ((40, 49), 12, [(-1, 12)]),  # 40-49分：12题全-1分（tend to agree）
        ((30, 39), 12, [(-2, 6), (-1, 6)]),  # 30-39分：6题-2分 + 6题-1分（随机）
        ((10, 29), 12, [(-2, 12)]),  # 10-29分：12题-2分 （随机）→ 对应90-98分镜像
        ((1, 9), 12, [(-3, 6), (-2, 6)]),  # 1-9分：6题-3分 + 6题-2分（随机）→ 补充对称区间
        ((0, 0), 12, [(-3, 12)])  # 0分：12题全-3分（strongly disagree）→ 对应100分镜像
    ]

    # 匹配当前分数对应的配置
    for (min_score, max_score), total_count, score_dist in configs:
        if min_score <= score <= max_score:
            # 验证分数分配总和是否等于总题数（避免配置错误）
            dist_total = sum(count for _, count in score_dist)
            if dist_total != total_count:
                print(
                    f"⚠️  警告：{min_score}-{max_score} 分的分数分配总和({dist_total})不等于总题数({total_count})，自动修正为全0级")
                return total_count, [(0, total_count)]
            return total_count, score_dist

    # 无匹配分数段时默认配置（12题全0级）
    return 12, [(0, 12)]


def get_QA(E_score, M_score, N_score, T_score, I_score):
    """
    分数的取值为[100,80,65,50,35,20,0]
    Energy: score>50时代表E, score<50时代表I
    Mind: score>50时代表N, score<50时代表S
    Nature: score>50时代表T, score<50时代表F
    Tactics: score>50时代表J, score<50时代表P
    Identity: score>50时代表A, score<50时代表T
    核心规则：pos题使用配置的基础分数，neg题使用基础分数的相反数（-base_key）
    """
    # 计算人格类型
    personality = ''
    personality += "E" if E_score > 50 else "I"
    personality += "N" if M_score > 50 else "S"
    personality += "T" if N_score > 50 else "F"
    personality += "J" if T_score > 50 else "P"
    personality += "T" if I_score < 50 else "A"

    # 结果文件路径（确保目录存在）

    result_path = f"PIF-IndSet/Q&A/{personality}_score_{E_score}_{M_score}_{N_score}_{T_score}_{I_score}_Q&A.txt"

    # 加载题目（校验文件存在性）
    if not os.path.exists("PIF-IndSet/new_questions.txt"):
        print("❌ 错误：未找到题目文件 new_questions.txt，请确保文件在当前目录")
        return personality
    with open("PIF-IndSet/new_questions.txt", 'r', encoding='utf-8') as f:
        new_questions = [line.strip() for line in f if line.strip()]
    if len(new_questions) == 0:
        print("❌ 错误：题目文件 new_questions.txt 内容为空")
        return personality

    # 维度配置总表（五个维度统一规则）
    dimension_configs = [
        {
            "name": "Energy",  # 第一维度
            "score": E_score,
            "pos_idx": Energy_pos,
            "neg_idx": Energy_neg
        },
        {
            "name": "Mind",  # 第二维度
            "score": M_score,
            "pos_idx": Mind_pos,
            "neg_idx": Mind_neg
        },
        {
            "name": "Nature",  # 第三维度
            "score": N_score,
            "pos_idx": Nature_pos,
            "neg_idx": Nature_neg
        },
        {
            "name": "Tactics",  # 第四维度
            "score": T_score,
            "pos_idx": Tactics_pos,
            "neg_idx": Tactics_neg
        },
        {
            "name": "Identity",  # 第五维度
            "score": I_score,
            "pos_idx": Identity_pos,
            "neg_idx": Identity_neg
        }
    ]

    # 预处理：为每个维度分配题目和基础分数（随机挑选+分数分配）
    dimension_qa_config = {}  # {维度名: {"selected_idx": [选中题索引], "base_scores": [对应基础分数]}}
    for config in dimension_configs:
        dim_name = config["name"]
        dim_score = config["score"]
        pos_idx = config["pos_idx"]
        neg_idx = config["neg_idx"]

        # 1. 获取当前维度的配置（总题数+基础分数分配）
        total_questions, score_distribution = get_dimension_config(dim_score)

        # 2. 获取该维度的所有题目索引（去重，避免重复选）
        all_dim_idx = list(set(pos_idx + neg_idx))
        # 若可用题目数不足，自动适配（避免报错）
        if len(all_dim_idx) < total_questions:
            print(f"  ⚠️  警告：{dim_name}维度可用题目数({len(all_dim_idx)})不足{total_questions}题，自动使用所有题目")
            total_questions = len(all_dim_idx)

        # 3. 随机选择题目索引（无重复）
        selected_idx = random.sample(all_dim_idx, total_questions)

        # 4. 按配置分配基础分数，并打乱顺序（随机分布）
        base_scores = []
        for target_score, count in score_distribution:
            base_scores.extend([target_score] * count)
        random.shuffle(base_scores)  # 打乱基础分数顺序，避免集中

        # 5. 存储该维度的最终配置（索引+基础分数）
        dimension_qa_config[dim_name] = {
            "selected_idx": selected_idx,
            "base_scores": base_scores
        }

    # 生成最终Q&A结果（核心：pos题用基础分数，neg题用基础分数的相反数）
    result = []
    for q_idx, question in enumerate(new_questions):
        q_formatted = f"Q:{question}"
        current_answer = "unsure"  # 默认答案
        matched_dim = None
        base_key = 0
        final_score = 0

        # 查找当前题目属于哪个维度，并获取基础分数
        for dim_name, dim_config in dimension_qa_config.items():
            if q_idx in dim_config["selected_idx"]:
                matched_dim = dim_name
                # 找到该题目在选中列表中的索引，获取基础分数（base_key）
                score_idx = dim_config["selected_idx"].index(q_idx)
                base_key = dim_config["base_scores"][score_idx]

                # 判断题目类型：pos题用基础分数，neg题用基础分数的相反数（-base_key）
                is_pos = q_idx in dimension_configs[[d["name"] for d in dimension_configs].index(dim_name)]["pos_idx"]
                final_score = base_key if is_pos else -base_key
                current_answer = ANSWER_MAP.get(final_score, "unsure")
                break

        # 拼接Q&A（标注维度、题目类型、基础分数、最终分数，方便核对）
        qa_pair = f"{q_formatted}\nA:I {current_answer}"
        if matched_dim:
            question_type = "pos题" if (
                        q_idx in dimension_configs[[d["name"] for d in dimension_configs].index(matched_dim)][
                    "pos_idx"]) else "neg题"
        result.append(qa_pair)

    # 保存结果到文件（每个Q&A之间空两行，更易读）
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(result))
    print(f"\n✅ 问题与答案已保存至：\n{result_path}")

    return personality


# -------------------------- 测试调用（验证对称规则+neg题反向）-------------------------