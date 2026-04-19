from selenium import webdriver
from pyquery import PyQuery as pq
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import json
import random
import re

"""此URL为mbti测试网站 由于没有拿到mbti测试的分数计算规则 所以分数靠爬取获得"""
URL = "https://www.16personalities.com/free-personality-test"
input_PATH = ""
output_PATH = ""

def extract_personality_results(browser):
    """提取人格类型和占比信息"""
    results = {
        'personality_type': '',
        'dimensions': {},
        'traits': {}
    }

    try:
        # 提取人格类型（支持5个维度，如INFP-T）
        html_content = browser.page_source

        # 方法1：使用正则表达式匹配人格类型（4或5个字符，如INFP或INFP-T）
        type_pattern = r'[IE][NS][TF][PJ][\-]?[AT]?'
        type_matches = re.findall(type_pattern, html_content, re.IGNORECASE)

        if type_matches:
            # 取最长的一个匹配（通常是完整的人格类型）
            results['personality_type'] = max(type_matches, key=len).upper()
            #print(f"🎉 发现人格类型: {results['personality_type']}")

        # 提取人格维度占比 - 专门针对您提供的HTML结构
        #print("正在提取人格维度占比...")

        # 方法1: 查找特质框中的百分比
        try:
            trait_boxes = browser.find_elements(By.CSS_SELECTOR, ".traitbox")
            #print(f"找到 {len(trait_boxes)} 个特质框")

            for box in trait_boxes:
                try:
                    # 查找特质标签
                    label_elem = box.find_element(By.CSS_SELECTOR, ".traitbox__label")
                    label_text = label_elem.text.strip().replace("：", "")  # 移除冒号

                    # 查找百分比
                    percentage_elem = box.find_element(By.CSS_SELECTOR, ".traitbox__value")
                    percentage_text = percentage_elem.text.strip()

                    # 提取百分比数字
                    percentage_match = re.search(r'(\d+)%', percentage_text)
                    if percentage_match:
                        percentage = int(percentage_match.group(1))
                        results['dimensions'][label_text] = percentage
                        #print(f"发现维度: {label_text} - {percentage}%")

                        # 同时提取特质描述（如"内向"）
                        try:
                            # 查找特质值文本
                            trait_value = box.find_element(By.CSS_SELECTOR, ".traitbox_value")
                            full_text = trait_value.text.strip()
                            # 移除百分比部分，获取特质描述
                            trait_desc = re.search(r'"(\w)"', percentage_text)
                            if trait_desc and trait_desc != label_text:
                                results['traits'][label_text] = trait_desc
                                #print(f"  特质描述: {trait_desc}")
                        except:
                            pass

                except Exception as e:
                    print(f"没有找到特质标签和百分比:{e}")
        except Exception as e:
            print(f"通过特质框提取失败: {e}")
    except Exception as e:
        print(f"提取人格结果时出错: {e}")
    return results


def fulfill_answers(url, answers):
    edge_options = webdriver.EdgeOptions()
    settings = {
        "appState": {
            "recentDestinations": [{
                "id": "Save as PDF",
                "origin": "local",
                "account": "",
            }],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        }
    }
    prefs = {'printing.print_preview_sticky_settings': json.dumps(settings)}
    edge_options.add_experimental_option('prefs', prefs)
    edge_options.add_argument('--kiosk-printing')
    #browser = webdriver.Chrome(options=chrome_options)
    browser = webdriver.Edge(options=edge_options)
    wait = WebDriverWait(browser, 18)
    browser.get(url)

    # ================================
    # 🔥 加速版：填写问题（保留你的逻辑，但极限加速）
    # ================================
    idx = 0

    for page_idx in range(10):
        #print(f"正在填写第 {page_idx + 1} 页...")

        # 等待页面加载问题
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-question]")))
        questions = browser.find_elements(By.CSS_SELECTOR, "[data-question]")

        for q_idx, question in enumerate(questions):
            if idx >= len(answers):
                break

            # 原逻辑：答案转换
            try:
                answer_value = -int(answers[idx])
            except Exception:
                answer_value = 0

            option_idx = answer_value + 3

            # 点击选项（加速版）
            try:
                radio_buttons = question.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                if option_idx < len(radio_buttons):
                    browser.execute_script("arguments[0].click();", radio_buttons[option_idx])
                    #print(f"问题 {idx + 1}: 选择 {option_idx} (值 {answer_value})")
                else:
                    print(f"警告: 问题 {idx+1} 找不到选项 {option_idx}")
            except Exception as e:
                print(f"错误: 无法选择问题 {idx + 1} 的选项: {e}")

            idx += 1
            sleep(0.02)  # 🚀 超短等待即可，应对动态渲染

        # 下一页（加速版）
        if page_idx < 9 and idx < len(answers):
            try:
                next_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Next')]"))
                )
                browser.execute_script("arguments[0].click();", next_button)
                #print("点击下一页")
                sleep(0.3)  # 🚀 极限加速
            except Exception as e:
                print(f"无法点击下一页: {e}")
                break

    # 选择性别和提交
    try:
        clickable_selectors = ["span", "div"]
        for selector in clickable_selectors:
            elements = browser.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                text = element.text.strip().lower()
                if any(keyword in text for keyword in ["other", "prefer not", "not say", "another"]):
                    if element.is_displayed():
                        browser.execute_script("arguments[0].click();", element)
                        break
    except Exception as e:
        print(f"性别选择失败: {e}")

    sleep(1)

    # 提交测试
    print("尝试提交测试...")
    try:

        submit_buttons = browser.find_elements(By.XPATH, "//button[contains(@class, 'button--action')]")
        for button in submit_buttons:
            if button.is_displayed() and button.is_enabled():
                browser.execute_script("arguments[0].click();", button)
                submitted = True
                break
    except Exception as e:
        print(f"提交测试失败: {e}")

    # 等待结果生成
    print("等待结果生成...")
    sleep(8)



    # 提取人格类型和占比
    print("正在提取人格测试结果...")
    personality_results = extract_personality_results(browser)



    # 打印结果摘要
    print("\n" + "=" * 50)
    print("人格测试结果摘要:")
    print("=" * 50)
    if personality_results['personality_type']:
        print(f"人格类型: {personality_results['personality_type']}")
    else:
        print("人格类型: 未找到")

    if personality_results['dimensions']:
        print("\n人格维度占比:")
        for dimension, percentage in personality_results['dimensions'].items():
            print(f"  {dimension} {percentage}%")
    else:
        print("\n人格维度占比: 未找到")

    print("=" * 50)


    sleep(2)
    browser.quit()
    print("测试完成！")
    return personality_results

if __name__ == '__main__':
    with open(input_PATH, "r") as f:
        answers = json.load(f)

    answers = list(answers.values())
    print(f"总共 {len(answers)} 个答案")

    data=fulfill_answers(URL, answers)

    results_filename = output_PATH
    with open(results_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"人格结果已保存到: {results_filename}")