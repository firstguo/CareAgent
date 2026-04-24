/**
 * ChatServiceClient - Chat Service REST API客户端
 */
class ChatServiceClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }
    
    /**
     * 提交任务
     */
    async submitTask(taskInput) {
        try {
            const response = await fetch(`${this.baseUrl}/api_planning`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(taskInput)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('[ChatServiceClient] 任务提交成功:', result.task_id);
            return result;
            
        } catch (e) {
            console.error('[ChatServiceClient] 任务提交失败:', e);
            throw e;
        }
    }
    
    /**
     * 查询任务状态
     */
    async getTaskStatus(taskId) {
        try {
            const response = await fetch(`${this.baseUrl}/api_task_status/${taskId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            return result;
            
        } catch (e) {
            console.error('[ChatServiceClient] 查询任务状态失败:', e);
            throw e;
        }
    }
    
    /**
     * 轮询任务状态直到完成
     */
    async pollTaskStatus(taskId, interval = 3000, maxAttempts = 100) {
        let attempts = 0;
        
        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const status = await this.getTaskStatus(taskId);
                    
                    if (status.status === 'completed') {
                        resolve(status);
                        return;
                    }
                    
                    if (status.status === 'failed') {
                        reject(new Error(`任务失败: ${status.error || '未知错误'}`));
                        return;
                    }
                    
                    attempts++;
                    if (attempts >= maxAttempts) {
                        reject(new Error('任务超时'));
                        return;
                    }
                    
                    setTimeout(poll, interval);
                    
                } catch (e) {
                    reject(e);
                }
            };
            
            poll();
        });
    }
    
    /**
     * 发送文本消息（支持多轮对话）
     */
    async sendTextMessage(userId, text) {
        try {
            const response = await fetch(`${this.baseUrl}/api_planning`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    trigger_type: 'user_initiated',
                    input: {
                        type: 'text',
                        text: text
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('[ChatServiceClient] 对话响应:', result);
            return result;
            
        } catch (e) {
            console.error('[ChatServiceClient] 发送消息失败:', e);
            throw e;
        }
    }
    
    /**
     * 发送语音消息（支持多轮对话）
     */
    async sendVoiceMessage(userId, audioData, sampleRate = 16000) {
        try {
            const response = await fetch(`${this.baseUrl}/api_planning`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    trigger_type: 'user_initiated',
                    input: {
                        type: 'voice',
                        audio_data: audioData,
                        sample_rate: sampleRate
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('[ChatServiceClient] 语音响应:', result);
            return result;
            
        } catch (e) {
            console.error('[ChatServiceClient] 发送语音失败:', e);
            throw e;
        }
    }
    
    /**
     * 发送视频消息（摔倒检测）
     */
    async sendVideoMessage(userId, videoData) {
        try {
            const response = await fetch(`${this.baseUrl}/api_planning`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    trigger_type: 'event_driven',
                    event_type: 'fall_detection',
                    input: {
                        type: 'video',
                        video_data: videoData
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('[ChatServiceClient] 视频检测响应:', result);
            return result;
            
        } catch (e) {
            console.error('[ChatServiceClient] 发送视频失败:', e);
            throw e;
        }
    }
    
    /**
     * 处理对话响应（支持双语音）
     */
    async handleConversationResponse(result, options = {}) {
        const {
            onTextResponse = null,
            onAudioConfirm = null,
            onAudioReminder = null,
            onScheduleDetected = null
        } = options;
        
        // 模式检测：conversation 或 task（异步任务）
        if (result.mode === 'conversation') {
            // 同步对话响应
            const response = result.response;
            const audioConfirm = result.audio_confirm;
            const audioReminder = result.audio_reminder;
            const schedule = result.schedule;
            
            // 处理文本回复
            if (onTextResponse && response) {
                onTextResponse(response);
            }
            
            // 立即播放确认语音
            if (onAudioConfirm && audioConfirm) {
                onAudioConfirm(audioConfirm);
            }
            
            // 如果检测到定时任务
            if (schedule && onScheduleDetected) {
                onScheduleDetected(schedule);
            }
            
            // 存储提醒语音供定时触发时使用
            if (audioReminder && schedule) {
                // 将 audio_reminder 存入 schedule 对象，供前端定时触发时播放
                schedule.audio_reminder = audioReminder;
                
                if (onAudioReminder) {
                    onAudioReminder(audioReminder, schedule);
                }
            }
            
            return {
                type: 'conversation',
                sessionId: result.session_id,
                response: response,
                hasSchedule: !!schedule,
                schedule: schedule
            };
        } else {
            // 异步任务响应（视频检测等）
            return {
                type: 'task',
                taskId: result.task_id,
                status: result.status
            };
        }
    }
    
    /**
     * 播放Base64音频
     */
    playBase64Audio(base64Audio, format = 'wav') {
        try {
            // 将Base64转换为Blob
            const byteCharacters = atob(base64Audio);
            const byteNumbers = new Array(byteCharacters.length);
            
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: `audio/${format}` });
            
            // 创建Audio对象并播放
            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);
            
            audio.play().then(() => {
                console.log('[ChatServiceClient] 音频播放成功');
                
                // 播放结束后释放URL
                audio.onended = () => {
                    URL.revokeObjectURL(audioUrl);
                };
            }).catch(e => {
                console.error('[ChatServiceClient] 音频播放失败:', e);
                URL.revokeObjectURL(audioUrl);
            });
            
        } catch (e) {
            console.error('[ChatServiceClient] 音频解码失败:', e);
        }
    }
    
    /**
     * 健康检查
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            const result = await response.json();
            return result;
        } catch (e) {
            console.error('[ChatServiceClient] 健康检查失败:', e);
            throw e;
        }
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatServiceClient;
}
