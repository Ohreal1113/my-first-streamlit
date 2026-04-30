import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="AI 技能解鎖打卡 App", page_icon="🎯", layout="centered")

if 'plan' not in st.session_state:
    st.session_state.plan = []
if 'topic' not in st.session_state:
    st.session_state.topic = ""

st.sidebar.title("⚙️ 系統設定")
st.sidebar.write("請輸入你的 Google Gemini API Key 來啟動 AI 規劃師。")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
st.sidebar.markdown("[👉 點此免費申請 API Key](https://aistudio.google.com/)")


def generate_plan(topic, days, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_prompt = f"""
    你是一個專業的學習規劃師。使用者想學習「{topic}」。
    請幫他規劃「{days}天」的入門學習計畫。
    【重要指示】
    1. 你的回應「必須」是一個純 JSON 陣列，絕對不能有 Markdown 標記 (如 ```json) 或是問候語。
    2. JSON 格式必須精確如下：
    [
      {{
        "day": 1,
        "title": "今日任務主要標題",
        "detail": "具體要看什麼資料、做什麼練習或了解什麼觀念",
        "source": "推薦的免費線上教學影片或網站"
        "completed": false
      }}
    ]
    """
    
    payload = {
        "contents": [{"parts": [{"text": f"請幫我生成學習 {topic} 的 {days} 天計畫"}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"responseMimeType": "application/json"} # 強制回傳 JSON
    }
    
    response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
    
    if response.status_code == 200:
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        clean_text = result_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    else:
        st.error(f"API 呼叫失敗！狀態碼: {response.status_code}")
        return None


st.title("🎯 AI 學習計畫打卡小幫手")
st.write("輸入你想學習的技能，AI 會幫你拆解成每天的破關任務！")

if not st.session_state.plan:
    with st.form("input_form"):
        topic_input = st.text_input("我想學習...", placeholder="例如：Python 網路爬蟲、日文 N5 文法...")
        days_input = st.selectbox("預計花費天數", [3, 5, 7, 14], index=1)
        submit_button = st.form_submit_button("✨ 生成你的專屬學習計畫", type="primary", use_container_width=True)
        
        if submit_button:
            if not api_key:
                st.warning("⚠️ 請先在左側邊欄輸入你的 Gemini API Key！")
            elif not topic_input:
                st.warning("⚠️ 請輸入你想學習的主題！")
            else:
                with st.spinner("AI 正在為你客製化課表，請稍候..."):
                    new_plan = generate_plan(topic_input, days_input, api_key)
                    if new_plan:
                        st.session_state.plan = new_plan
                        st.session_state.topic = topic_input
                        st.rerun() # 重整


if st.session_state.plan:
    
    total_task = len(st.session_state.plan)
    completed_tasks = sum(1 for task in st.session_state.plan if task['completed'])
    progress_pct = completed_tasks / total_task
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📚 目標：{st.session_state.topic}")
    with col2:
        st.subheader(f"**進度：{completed_tasks} / {total_task}**")
    
    st.progress(progress_pct)
    
    if progress_pct == 1.0:
        st.success("🎉 太棒了！你已經完成了所有的學習任務！")
        st.balloons() 
    
    st.write("### 每日任務清單")
     
    for i, task in enumerate(st.session_state.plan):
        
        with st.container():
            checked = st.checkbox(
                f"**Day {task['day']} : {task['title']}**", 
                value=task['completed'], 
                key=f"task_{i}"
            )
            st.info(task['detail'])
            st.info(task['source'])
          
            if checked != task['completed']:
                st.session_state.plan[i]['completed'] = checked
                st.rerun()

    st.divider()
    
    if st.button("🔁 放棄當前計畫，重新設定", type="secondary"):
        st.session_state.plan = []
        st.session_state.topic = ""
        st.rerun()
