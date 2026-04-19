import random
from AUTO_FILL_ANSWER import get_QA

"""
分数的取值为[100,80,65,35,20,0]
Energy:score>50时代表E,score<50时代表I
Mind:score>50时代表N,score<50时代表S
Nature:score>50时代表T,score<50时代表F
Tactics:score>50时代表J,score<50时代表P
Identity:score>50时代表A,score<50时代表T
"""
# -------------------------- 配置参数（可根据实际情况修改）--------------------------
E_score=20
M_score=80
N_score=20
T_score=20
I_score=80  # 打乱后的结果输出文件路径（可选）
# ----------------------------------------------------------------------------------

def load_qa_from_file(file_path, separator):
    """从文件加载 Q&A 数据，返回绑定后的 Q&A 列表"""
    qa_pairs = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()  # 读取所有行
            for i  in range(0, len(lines), 2):
                line1 = lines[i].strip("Q:")
                line2 = lines[i + 1].strip("A:")   # 处理最后一行可能缺失的情况
                qa_unit = f"Q:{line1}A:I {line2}"
                qa_pairs.append(qa_unit)

        if not qa_pairs:
            raise ValueError("输入文件中未找到有效 Q&A 数据")
        print(f"成功从文件加载 {len(qa_pairs)} 组 Q&A 数据\n")
        return qa_pairs
    except FileNotFoundError:
        print(f"错误：未找到文件 {file_path}，请检查文件路径是否正确")
        exit(1)
    except Exception as e:
        print(f"错误：读取文件时发生异常 - {str(e)}")
        exit(1)

def shuffle_qa(qa_pairs):
    """打乱 Q&A 顺序（保持每组 Q&A 绑定）"""
    random.shuffle(qa_pairs)  # 原地打乱，不拆分 Q&A 单元
    return qa_pairs

def save_qa_to_file(qa_pairs, file_path):
    """将打乱后的 Q&A 保存到文件"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for idx, qa in enumerate(qa_pairs, 1):
                f.write(f"{qa}")  # 按编号写入，每组之间空行分隔
        print(f"打乱后的结果已保存到：{file_path}\n")
    except Exception as e:
        print(f"警告：保存文件时发生异常 - {str(e)}，将仅在控制台输出结果")



# -------------------------- 主流程执行 --------------------------

def get_shuffled(E_score,M_score,N_score,T_score,I_score):
    personality = get_QA(E_score, M_score, N_score, T_score, I_score)
    INPUT_FILE_PATH = f"PIF-IndSet/Q&A/{personality}_score_{E_score}_{M_score}_{N_score}_{T_score}_{I_score}_Q&A.txt"  # 输入文件路径（相对路径/绝对路径均可）
    SEPARATOR = "\n"  # Q 和 A 的分隔符（需与输入文件一致）
    OUTPUT_FILE_PATH = f"PIF-IndSet/Q&A_shuffled/{personality}_score_{E_score}_{M_score}_{N_score}_{T_score}_{I_score}.txt"
    # 1. 从文件加载 Q&A
    qa_list = load_qa_from_file(INPUT_FILE_PATH, SEPARATOR)
    # 2. 打乱顺序
    shuffled_qa = shuffle_qa(qa_list)
    # 3. 保存到文件（可选）
    save_qa_to_file(shuffled_qa, OUTPUT_FILE_PATH)
    # 4. 控制台打印结果


