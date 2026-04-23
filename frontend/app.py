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
    
    api_url = st.text_input("Chat Service API地址", value="http://localhost:8007")
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
        ["文本", "语音", "图像"],
        horizontal=True
    )
    
    if input_type == "文本":
        user_input = st.text_area("输入消息", placeholder="例如：今天天气怎么样？")
        
        if st.button("发送", type="primary"):
            if user_input:
                with st.spinner("处理中..."):
                    # 显示JavaScript调用示例
                    st.code(f"""
// 前端JavaScript调用示例
const client = new ChatServiceClient('{api_url}');
const result = await client.sendTextMessage('{user_id}', '{user_input}');
console.log('Task ID:', result.task_id);

// 轮询任务状态
const status = await client.pollTaskStatus(result.task_id);
console.log('Response:', status.result.final_response);

// 如果有音频回复，播放它
if (status.result.audio_response) {{
    client.playBase64Audio(status.result.audio_response);
}}
                    """, language="javascript")
                    
                    st.info("💡 实际调用需要在浏览器中执行JavaScript代码")
    
    elif input_type == "语音":
        st.info("🎤 语音录制功能需要浏览器麦克风权限")
        st.code("""
// 语音录制示例
const mediaRecorder = new MediaRecorder(stream);
const chunks = [];

mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
mediaRecorder.onstop = async () => {
    const blob = new Blob(chunks, { type: 'audio/wav' });
    const base64 = await blobToBase64(blob);
    
    const client = new ChatServiceClient(apiUrl);
    const result = await client.sendVoiceMessage(userId, base64);
};
        """, language="javascript")
    
    elif input_type == "图像":
        st.info("📷 图像上传功能")
        uploaded_file = st.file_uploader("上传图像", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            st.image(uploaded_file, caption="上传的图像", use_column_width=True)
            
            analysis_type = st.selectbox(
                "分析类型",
                ["general", "safety", "emotion", "activity"]
            )
            
            if st.button("分析图像", type="primary"):
                st.code(f"""
// 图像分析示例
const reader = new FileReader();
reader.onload = async function() {{
    const base64 = reader.result.split(',')[1];
    
    const client = new ChatServiceClient(apiUrl);
    const result = await client.sendImageMessage(userId, base64, '{analysis_type}');
    
    const status = await client.pollTaskStatus(result.task_id);
    console.log('Vision Result:', status.result.final_response);
}};
reader.readAsDataURL(file);
                """, language="javascript")

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
    提交任务，异步执行
    
    ```json
    {
        "user_id": "user_001",
        "trigger_type": "user_initiated",
        "input": {
            "type": "text",
            "text": "你好"
        }
    }
    ```
    
    响应:
    ```json
    {
        "task_id": "task_abc123",
        "status": "pending",
        "message": "任务已提交，正在处理中"
    }
    ```
    
    #### GET /api_task_status/{task_id}
    查询任务状态
    
    响应:
    ```json
    {
        "task_id": "task_abc123",
        "status": "completed",
        "result": {
            "final_response": "你好！有什么可以帮助你的？",
            "audio_response": "base64音频数据..."
        }
    }
    ```
    """)

# ============================================
# 视频摔倒检测测试页面
# ============================================

st.header("🎥 视频摔倒检测测试")
st.info("上传一段视频（建议5-10秒），系统将分析是否发生摔倒")

api_url = st.session_state.get('api_url', 'http://localhost:8007')

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
        with st.spinner("正在提交视频分析任务..."):
            try:
                # 调用后端API
                response = requests.post(
                    f"{api_url}/api_event_trigger",
                    json={
                        "user_id": "test_user_001",
                        "trigger_type": "event_driven",
                        "event_type": "manual_test",
                        "video_data": video_base64
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result["task_id"]
                    
                    st.success(f"✅ 任务已提交: {task_id}")
                    
                    # 轮询结果
                    with st.spinner("等待分析结果..."):
                        progress_bar = st.progress(0)
                        
                        for i in range(30):  # 最多等待60秒
                            time.sleep(2)
                            progress_bar.progress((i + 1) / 30)
                            
                            status_response = requests.get(
                                f"{api_url}/api_task_status/{task_id}"
                            )
                            status = status_response.json()
                            
                            if status["status"] == "completed":
                                # 显示结果
                                detection_result = status["result"]["result"]
                                
                                risk_level = detection_result["risk_level"]
                                confidence = detection_result["confidence"]
                                
                                # 根据风险等级显示不同样式
                                if risk_level == "critical":
                                    st.error(f"🚨 检测到摔倒！置信度: {confidence:.0%}")
                                elif risk_level == "warning":
                                    st.warning(f"⚠️ 潜在风险！置信度: {confidence:.0%}")
                                else:
                                    st.success(f"✅ 状态正常！置信度: {confidence:.0%}")
                                
                                # 显示时序证据
                                st.subheader("📈 时序分析")
                                st.info(detection_result.get("temporal_evidence", "N/A"))
                                
                                # 显示建议
                                st.subheader("💡 建议措施")
                                for rec in detection_result.get("recommendations", []):
                                    st.write(f"• {rec}")
                                
                                # 显示帧详情（可选）
                                with st.expander("📸 查看帧分析详情"):
                                    for i, frame_result in enumerate(
                                        detection_result.get("frame_analysis", [])
                                    ):
                                        st.write(
                                            f"**帧 {i+1}**: "
                                            f"风险等级={frame_result.get('risk_level', 'N/A')}, "
                                            f"描述={frame_result.get('risk_description', 'N/A')}"
                                        )
                                
                                progress_bar.empty()
                                break
                            elif status["status"] == "failed":
                                st.error(f"❌ 分析失败: {status.get('error', 'Unknown error')}")
                                progress_bar.empty()
                                break
                        else:
                            st.warning("⏰ 超时，请稍后手动查询结果")
                            progress_bar.empty()
                else:
                    st.error(f"❌ 请求失败: {response.status_code} - {response.text}")
            
            except Exception as e:
                st.error(f"请求失败: {str(e)}")
