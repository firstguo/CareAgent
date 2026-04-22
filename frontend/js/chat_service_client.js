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
     * 发送文本消息
     */
    async sendTextMessage(userId, text) {
        return this.submitTask({
            user_id: userId,
            trigger_type: 'user_initiated',
            input: {
                type: 'text',
                text: text
            }
        });
    }
    
    /**
     * 发送语音消息
     */
    async sendVoiceMessage(userId, audioData, sampleRate = 16000) {
        return this.submitTask({
            user_id: userId,
            trigger_type: 'user_initiated',
            input: {
                type: 'voice',
                audio_data: audioData,
                sample_rate: sampleRate
            }
        });
    }
    
    /**
     * 发送图像消息
     */
    async sendImageMessage(userId, imageData, analysisType = 'general') {
        return this.submitTask({
            user_id: userId,
            trigger_type: 'user_initiated',
            input: {
                type: 'image',
                image_data: imageData,
                analysis_type: analysisType
            }
        });
    }
    
    /**
     * 发送多模态消息
     */
    async sendMultimodalMessage(userId, text, audioData, imageData) {
        return this.submitTask({
            user_id: userId,
            trigger_type: 'user_initiated',
            input: {
                type: 'multimodal',
                text: text,
                audio_data: audioData,
                image_data: imageData
            }
        });
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
