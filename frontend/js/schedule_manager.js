/**
 * ScheduleManager - 定时任务管理器
 * 使用localStorage存储定时任务，JS定时器触发
 */
class ScheduleManager {
    constructor() {
        this.STORAGE_KEY = 'careagent_schedules';
        this.checkInterval = 60 * 1000; // 每分钟检查一次
        this.timer = null;
        this.schedules = [];
        
        this.init();
    }
    
    /**
     * 初始化
     */
    init() {
        this.loadSchedules();
        this.startChecker();
        
        // 页面可见性变化时重新检查
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                console.log('[ScheduleManager] 页面恢复，立即检查定时任务');
                this.checkSchedules();
            }
        });
        
        console.log(`[ScheduleManager] 已加载 ${this.schedules.length} 个定时任务`);
    }
    
    /**
     * 从localStorage加载定时任务
     */
    loadSchedules() {
        try {
            const stored = localStorage.getItem(this.STORAGE_KEY);
            if (stored) {
                this.schedules = JSON.parse(stored);
                // 过滤掉已过期的任务
                this.schedules = this.schedules.filter(s => !s.expired);
                this.saveSchedules();
            }
        } catch (e) {
            console.error('[ScheduleManager] 加载定时任务失败:', e);
            this.schedules = [];
        }
    }
    
    /**
     * 保存到localStorage
     */
    saveSchedules() {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.schedules));
        } catch (e) {
            console.error('[ScheduleManager] 保存定时任务失败:', e);
        }
    }
    
    /**
     * 添加定时任务（支持 audio_reminder）
     */
    addSchedule(schedule) {
        const newSchedule = {
            id: `schedule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: schedule.type || 'medication_reminder',
            cron: schedule.cron,
            message: schedule.message,
            context: schedule.context || {},
            audio_reminder: schedule.audio_reminder || null,  // 存储提醒语音
            enabled: true,
            expired: false,
            lastTriggered: null,
            createdAt: new Date().toISOString()
        };
        
        this.schedules.push(newSchedule);
        this.saveSchedules();
        
        console.log('[ScheduleManager] 添加定时任务:', newSchedule.id);
        return newSchedule;
    }
    
    /**
     * 删除定时任务
     */
    removeSchedule(scheduleId) {
        this.schedules = this.schedules.filter(s => s.id !== scheduleId);
        this.saveSchedules();
        console.log('[ScheduleManager] 删除定时任务:', scheduleId);
    }
    
    /**
     * 启用/禁用定时任务
     */
    toggleSchedule(scheduleId, enabled) {
        const schedule = this.schedules.find(s => s.id === scheduleId);
        if (schedule) {
            schedule.enabled = enabled;
            this.saveSchedules();
            console.log('[ScheduleManager] 切换定时任务状态:', scheduleId, enabled);
        }
    }
    
    /**
     * 启动定时器检查
     */
    startChecker() {
        if (this.timer) {
            clearInterval(this.timer);
        }
        
        this.timer = setInterval(() => {
            this.checkSchedules();
        }, this.checkInterval);
        
        console.log('[ScheduleManager] 定时器已启动，每分钟检查一次');
    }
    
    /**
     * 停止定时器
     */
    stopChecker() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
            console.log('[ScheduleManager] 定时器已停止');
        }
    }
    
    /**
     * 检查所有定时任务
     */
    checkSchedules() {
        const now = new Date();
        
        this.schedules.forEach(schedule => {
            if (!schedule.enabled || schedule.expired) {
                return;
            }
            
            // 解析cron表达式
            if (this.shouldTrigger(schedule.cron, now)) {
                this.triggerSchedule(schedule);
            }
        });
    }
    
    /**
     * 判断是否应该触发
     */
    shouldTrigger(cronExpression, now) {
        try {
            const parts = cronExpression.split(' ');
            if (parts.length !== 5) {
                console.error('[ScheduleManager] cron表达式格式错误:', cronExpression);
                return false;
            }
            
            const [minute, hour, day, month, weekday] = parts;
            
            // 检查分钟
            if (!this.matchCronField(minute, now.getMinutes())) return false;
            
            // 检查小时
            if (!this.matchCronField(hour, now.getHours())) return false;
            
            // 检查日期
            if (!this.matchCronField(day, now.getDate())) return false;
            
            // 检查月份
            if (!this.matchCronField(month, now.getMonth() + 1)) return false;
            
            // 检查星期
            if (!this.matchCronField(weekday, now.getDay())) return false;
            
            return true;
        } catch (e) {
            console.error('[ScheduleManager] cron解析失败:', e);
            return false;
        }
    }
    
    /**
     * 匹配cron字段
     */
    matchCronField(field, value) {
        if (field === '*') return true;
        
        // 处理逗号分隔的列表
        if (field.includes(',')) {
            const values = field.split(',').map(v => parseInt(v));
            return values.includes(value);
        }
        
        // 处理范围
        if (field.includes('-')) {
            const [start, end] = field.split('-').map(v => parseInt(v));
            return value >= start && value <= end;
        }
        
        // 处理步长
        if (field.includes('/')) {
            const [start, step] = field.split('/').map(v => parseInt(v));
            return (value - start) % step === 0;
        }
        
        // 直接匹配
        return parseInt(field) === value;
    }
    
    /**
     * 触发定时任务（播放 audio_reminder）
     */
    async triggerSchedule(schedule) {
        const now = new Date();
        const lastTriggered = schedule.lastTriggered ? new Date(schedule.lastTriggered) : null;
        
        // 防止一分钟内重复触发
        if (lastTriggered && (now - lastTriggered) < 60000) {
            return;
        }
        
        console.log('[ScheduleManager] 触发定时任务:', schedule.id, schedule.message);
        
        try {
            // 震动提醒（如果支持）
            if (navigator.vibrate) {
                navigator.vibrate([200, 100, 200]);
            }
            
            // 播放提醒语音（如果有）
            if (schedule.audio_reminder) {
                console.log('[ScheduleManager] 播放提醒语音');
                this.playAudioReminder(schedule.audio_reminder);
            }
            
            // 显示通知（如果支持）
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('CareAgent 提醒', {
                    body: schedule.message,
                    icon: '/favicon.ico'
                });
            }
            
            // 更新最后触发时间
            schedule.lastTriggered = now.toISOString();
            this.saveSchedules();
            
            console.log('[ScheduleManager] 定时任务触发成功:', schedule.id);
            
        } catch (e) {
            console.error('[ScheduleManager] 定时任务触发失败:', e);
        }
    }
    
    /**
     * 播放提醒语音
     */
    playAudioReminder(base64Audio, format = 'wav') {
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
                console.log('[ScheduleManager] 提醒语音播放成功');
                
                // 播放结束后释放URL
                audio.onended = () => {
                    URL.revokeObjectURL(audioUrl);
                };
            }).catch(e => {
                console.error('[ScheduleManager] 提醒语音播放失败:', e);
                URL.revokeObjectURL(audioUrl);
            });
            
        } catch (e) {
            console.error('[ScheduleManager] 提醒语音解码失败:', e);
        }
    }
    
    /**
     * 获取所有定时任务
     */
    getAllSchedules() {
        return this.schedules;
    }
    
    /**
     * 获取定时任务数量
     */
    getCount() {
        return this.schedules.filter(s => s.enabled && !s.expired).length;
    }
    
    /**
     * 清空所有定时任务
     */
    clearAll() {
        this.schedules = [];
        this.saveSchedules();
        console.log('[ScheduleManager] 已清空所有定时任务');
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScheduleManager;
}
