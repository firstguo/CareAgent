"""
Streamlit前端 - 集成Chat Service REST API和定时任务管理
"""
import streamlit as st
import json
import time
import base64
import requests
from streamlit_lottie import st_lottie

# 页面配置
st.set_page_config(
    page_title="CareAgent - 智能看护助手",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 CareAgent 智能看护助手")

# ============================================
# 初始化Session State
# ============================================

if 'chat_client' not in st.session_state:
    st.session_state.chat_client = None

if 'schedule_manager' not in st.session_state:
    st.session_state.schedule_manager = None

if 'task_history' not in st.session_state:
    st.session_state.task_history = []

# ============================================
# 注入JavaScript代码
# ============================================

js_code = """
<script>
// 等待页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化ScheduleManager
    if (typeof ScheduleManager !== 'undefined') {
        window.scheduleManager = new ScheduleManager();
        console.log('[Streamlit] ScheduleManager已初始化');
    }
    
    // 请求通知权限
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});
</script>
"""

# 注入JavaScript
st.components.v1.html(js_code, height=0)

# 加载JavaScript文件
with open('js/schedule_manager.js', 'r', encoding='utf-8') as f:
    schedule_js = f.read()
    
with open('js/chat_service_client.js', 'r', encoding='utf-8') as f:
    client_js = f.read()

st.components.v1.html(f"""
<script>
{schedule_js}
{client_js}
</script>
""", height=0)

# ============================================
# 侧边栏 - 配置
# ============================================

with st.sidebar:
    st.header("⚙️ 配置")
    
    # 检测是否在Docker环境中
    import os
    in_docker = os.path.exists('/.dockerenv')
    
    # 根据环境设置默认API地址
    default_api_url = "http://chat-service:8007" if in_docker else "http://localhost:8007"
    
    api_url = st.text_input("Chat Service API地址", value=default_api_url)
    user_id = st.text_input("用户ID", value="user_001")
    
    # 初始化客户端
    if api_url and user_id:
        st.session_state.chat_client = api_url
        st.success(f"✅ API地址: {api_url}")
    
    st.divider()
    
    # 定时任务管理
    st.header("⏰ 定时任务")
    
    schedule_count = st.empty()
    schedule_count.info("正在加载定时任务...")

# ============================================
# 主界面 - 标签页
# ============================================

tab1, tab2, tab3 = st.tabs(["💬 对话", "📋 任务历史", "⏰ 定时任务管理"])

# ============================================
# Tab 1: 对话
# ============================================

with tab1:
    st.header("💬 多模态对话")
    
    # 输入方式选择
    input_type = st.radio(
        "选择输入方式",
        ["文本", "语音", "视频"],
        horizontal=True
    )
    
    if input_type == "文本":
        user_input = st.text_area("输入消息", placeholder="例如：今天天气怎么样？")
        
        if st.button("发送", type="primary"):
            if user_input:
                with st.spinner("处理中..."):
                    try:
                        # 调用后端API提交对话（同步响应）
                        response = requests.post(
                            f"{api_url}/api_planning",
                            json={
                                "user_id": user_id,
                                "trigger_type": "user_initiated",
                                "input": {
                                    "type": "text",
                                    "text": user_input
                                }
                            }
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            # 检测响应模式：conversation 或 task
                            if result.get("mode") == "conversation":
                                # 同步对话响应（新格式）
                                st.success(f"✅ 会话: {result.get('session_id', 'unknown')}")
                                
                                # 显示文本回复
                                text_response = result.get("response", "")
                                if text_response:
                                    st.subheader("💬 AI回复")
                                    st.write(text_response)
                                
                                # 播放确认语音（audio_confirm）
                                audio_confirm = result.get("audio_confirm")
                                if audio_confirm:
                                    st.subheader("🔊 确认语音")
                                    audio_bytes = base64.b64decode(audio_confirm)
                                    st.audio(audio_bytes, format="audio/wav")
                                
                                # 如果有定时任务，显示提醒语音（audio_reminder）
                                schedule = result.get("schedule")
                                audio_reminder = result.get("audio_reminder")
                                if schedule and audio_reminder:
                                    st.subheader("⏰ 定时任务已设置")
                                    st.info(f"Cron: {schedule.get('cron')}")
                                    st.info(f"提醒内容: {schedule.get('message')}")
                                    
                                    st.subheader("🔔 提醒语音（定时播放）")
                                    reminder_bytes = base64.b64decode(audio_reminder)
                                    st.audio(reminder_bytes, format="audio/wav")
                                
                                # 保存任务历史
                                st.session_state.task_history.append(result)
                                
                            else:
                                # 异步任务响应（旧格式，保持兼容）
                                task_id = result.get("task_id")
                                st.success(f"✅ 任务已提交: {task_id}")
                                
                                # 轮询任务状态
                                with st.spinner("等待回复..."):
                                    progress_bar = st.progress(0)
                                    
                                    for i in range(30):
                                        time.sleep(2)
                                        progress_bar.progress((i + 1) / 30)
                                        
                                        status_response = requests.get(
                                            f"{api_url}/api_task_status/{task_id}"
                                        )
                                        status = status_response.json()
                                        
                                        if status["status"] == "completed":
                                            final_response = status["result"].get("final_response", "")
                                            if final_response:
                                                st.subheader("💬 AI回复")
                                                st.write(final_response)
                                            
                                            audio_response = status["result"].get("audio_response")
                                            if audio_response:
                                                st.subheader("🔊 语音回复")
                                                audio_bytes = base64.b64decode(audio_response)
                                                st.audio(audio_bytes, format="audio/wav")
                                            
                                            st.session_state.task_history.append(status)
                                            progress_bar.empty()
                                            break
                                        elif status["status"] == "failed":
                                            st.error(f"❌ 任务失败: {status.get('error', 'Unknown error')}")
                                            progress_bar.empty()
                                            break
                                    else:
                                        st.warning("⏰ 超时，请稍后手动查询结果")
                                        progress_bar.empty()
                        else:
                            st.error(f"❌ 请求失败: {response.status_code} - {response.text}")
                    
                    except Exception as e:
                        st.error(f"请求失败: {str(e)}")
    
    elif input_type == "语音":
        st.info("🎤 语音输入将被转换为文字，然后走对话流程")
        st.info("💡 语音识别使用阿里云 Fun-ASR，识别后等同于文字输入")
        
        uploaded_audio = st.file_uploader("上传语音文件", type=["wav", "mp3"])
        
        if uploaded_audio:
            st.audio(uploaded_audio, format="audio/wav")
            
            audio_bytes = uploaded_audio.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            if st.button("发送语音", type="primary"):
                with st.spinner("正在识别语音..."):
                    try:
                        response = requests.post(
                            f"{api_url}/api_planning",
                            json={
                                "user_id": user_id,
                                "trigger_type": "user_initiated",
                                "input": {
                                    "type": "voice",
                                    "audio_data": audio_base64
                                }
                            }
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            # 处理对话响应（同文本输入）
                            if result.get("mode") == "conversation":
                                st.success(f"✅ 会话: {result.get('session_id')}")
                                
                                text_response = result.get("response", "")
                                if text_response:
                                    st.subheader("💬 AI回复")
                                    st.write(text_response)
                                
                                audio_confirm = result.get("audio_confirm")
                                if audio_confirm:
                                    st.subheader("🔊 确认语音")
                                    audio_bytes = base64.b64decode(audio_confirm)
                                    st.audio(audio_bytes, format="audio/wav")
                                
                                st.session_state.task_history.append(result)
                        else:
                            st.error(f"❌ 请求失败: {response.status_code}")
                    
                    except Exception as e:
                        st.error(f"请求失败: {str(e)}")


# ============================================
# Tab 2: 任务历史
# ============================================

with tab2:
    st.header("📋 任务历史")
    
    if st.session_state.task_history:
        for task in reversed(st.session_state.task_history):
            with st.expander(f"Task: {task.get('task_id', 'unknown')} - {task.get('status', 'unknown')}"):
                st.json(task)
    else:
        st.info("暂无任务历史")

# ============================================
# Tab 3: 定时任务管理
# ============================================

with tab3:
    st.header("⏰ 定时任务管理")
    
    st.info("💡 定时任务由前端JavaScript管理，保存在浏览器localStorage中")
    
    # 添加定时任务表单
    with st.form("add_schedule"):
        st.subheader("添加定时任务")
        
        schedule_type = st.selectbox(
            "任务类型",
            ["medication_reminder", "care_check", "meal_reminder", "custom"]
        )
        
        cron_expr = st.text_input("Cron表达式", placeholder="0 8 * * * (每天8点)", value="0 8 * * *")
        message = st.text_input("提醒内容", placeholder="提醒吃药")
        
        st.caption("Cron格式: 分 时 日 月 星期")
        st.caption("示例: 0 8 * * * = 每天早上8点")
        
        submitted = st.form_submit_button("添加定时任务", type="primary")
        
        if submitted:
            st.code(f"""
// 添加定时任务示例
const scheduleManager = new ScheduleManager();

const schedule = scheduleManager.addSchedule({{
    type: '{schedule_type}',
    cron: '{cron_expr}',
    message: '{message}',
    context: {{
        user_id: '{user_id}'
    }}
}});

console.log('Schedule added:', schedule.id);
console.log('Total schedules:', scheduleManager.getCount());
            """, language="javascript")
            
            st.success("✅ 定时任务已添加到前端（需在浏览器中执行JavaScript）")
    
    st.divider()
    
    # 查看定时任务
    st.subheader("查看定时任务")
    st.code("""
// 查看所有定时任务
const schedules = scheduleManager.getAllSchedules();
console.log('Schedules:', schedules);

// 删除定时任务
scheduleManager.removeSchedule('schedule_id');

// 清空所有定时任务
scheduleManager.clearAll();
    """, language="javascript")

# ============================================
# 底部 - 重要提示
# ============================================

st.divider()
st.warning("⚠️ **重要提示**: 定时任务需要保持页面打开才能正常触发。关闭浏览器或标签页将导致定时任务失效。")

st.info("""
📱 **手机端使用建议**:
1. 将网站添加到主屏幕（虽然不做PWA，但可以创建快捷方式）
2. 保持浏览器后台运行
3. 定期检查任务执行状态
""")

# ============================================
# 帮助信息
# ============================================

with st.expander("📖 API文档"):
    st.markdown("""
    ### Chat Service REST API
    
    #### POST /api_planning
    提交任务（支持多模态输入）
    
    **文本/语音输入（同步对话）**:
    ```json
    {
        "user_id": "user_001",
        "trigger_type": "user_initiated",
        "input": {
            "type": "text",
            "text": "每天早上8点提醒吃药"
        }
    }
    ```
    
    响应（新格式 - 对话模式）:
    ```json
    {
        "mode": "conversation",
        "session_id": "sess_xxx",
        "response": "好的，已设置每天早上8点提醒你吃药",
        "audio_confirm": "base64...",
        "audio_reminder": "base64...",
        "is_new_session": true,
        "message_count": 2,
        "schedule": {
            "cron": "0 8 * * *",
            "message": "提醒吃药",
            "type": "medication_reminder",
            "audio_reminder": "base64..."
        }
    }
    ```
    
    **视频输入（同步）**:
    ```json
    {
        "user_id": "user_001",
        "trigger_type": "event_driven",
        "input": {
            "type": "video",
            "video_data": "base64..."
        }
    }
    ```
    
    响应（非危险）:
    ```json
    {
        "mode": "ignored",
        "status": "ignored",
        "reason": "no_risk_detected",
        "result": {
            "risk_level": "normal",
            "confidence": 0.9
        }
    }
    ```
    
    响应（危险）:
    ```json
    {
        "mode": "conversation",
        "session_id": "sess_xxx",
        "response": "🚨 检测到摔倒！建议立即...",
        "audio_confirm": "base64...",
        "schedule": {...}
    }
    ```
    
    **注意**: 图像输入暂不支持，将返回 400 错误。
    """)

# ============================================
# 视频摔倒检测测试页面
# ============================================

st.header("🎥 视频摔倒检测测试")
st.info("上传一段视频（建议5-10秒），系统将分析是否发生摔倒")

# 使用侧边栏配置的api_url
api_url = st.session_state.get('chat_client', 'http://localhost:8007')

uploaded_video = st.file_uploader(
    "选择视频文件",
    type=["webm", "mp4", "mov", "avi"],
    help="支持WebM、MP4、MOV、AVI格式"
)

if uploaded_video:
    # 显示视频预览
    st.video(uploaded_video)
    
    # 读取视频数据
    video_bytes = uploaded_video.read()
    video_base64 = base64.b64encode(video_bytes).decode('utf-8')
    
    st.write(f"📊 视频大小: {len(video_bytes) / 1024:.1f} KB")
    
    if st.button("🔍 分析视频", type="primary"):
        with st.spinner("正在分析视频...（预计 5-10 秒）"):
            try:
                # 调用后端API - 统一同步接口
                response = requests.post(
                    f"{api_url}/api_planning",
                    json={
                        "user_id": "test_user_001",
                        "trigger_type": "event_driven",
                        "input": {
                            "type": "video",
                            "video_data": video_base64
                        }
                    },
                    timeout=60  # 60 秒超时
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 处理不同模式
                    if result.get("mode") == "ignored":
                        # 非危险视频，快速返回
                        st.success("✅ 视频分析完成：状态正常")
                        
                        detection_result = result.get("result", {})
                        risk_level = detection_result.get("risk_level", "unknown")
                        confidence = detection_result.get("confidence", 0)
                        
                        st.info(f"风险等级: {risk_level}，置信度: {confidence:.0%}")
                        
                        # 保存历史记录
                        st.session_state.task_history.append(result)
                    
                    elif result.get("mode") == "conversation":
                        # 危险视频，走对话流程
                        st.warning("⚠️ 检测到潜在风险！")
                        
                        # 显示文本回复
                        text_response = result.get("response", "")
                        if text_response:
                            st.subheader("💬 AI建议")
                            st.write(text_response)
                        
                        # 播放确认语音
                        audio_confirm = result.get("audio_confirm")
                        if audio_confirm:
                            st.subheader("🔊 语音提醒")
                            audio_bytes = base64.b64decode(audio_confirm)
                            st.audio(audio_bytes, format="audio/wav")
                        
                        # 如果有定时任务，显示提醒语音
                        schedule = result.get("schedule")
                        audio_reminder = result.get("audio_reminder")
                        if schedule and audio_reminder:
                            st.subheader("⏰ 后续跟进任务")
                            st.info(f"Cron: {schedule.get('cron')}")
                            st.info(f"提醒内容: {schedule.get('message')}")
                            
                            st.subheader("🔔 提醒语音（定时播放）")
                            reminder_bytes = base64.b64decode(audio_reminder)
                            st.audio(reminder_bytes, format="audio/wav")
                        
                        # 保存历史记录
                        st.session_state.task_history.append(result)
                    
                    else:
                        st.error(f"❌ 未知响应模式: {result.get('mode')}")
                else:
                    st.error(f"❌ 请求失败: {response.status_code} - {response.text}")
            
            except requests.exceptions.Timeout:
                st.error("❌ 请求超时，视频分析耗时过长")
            except Exception as e:
                st.error(f"请求失败: {str(e)}")
