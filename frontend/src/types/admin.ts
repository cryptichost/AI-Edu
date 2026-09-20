export interface AdminTeacherRecord {
    username: string;
    name: string;
    display_name?: string;
    email?: string;
    students?: string[];
}

export interface AdminStudentPreference {
    course_type?: Array<{ name?: string }>;
}

export interface AdminStudentRecord {
    user_id: string;
    username: string;
    stu_name: string;
    display_name?: string;
    email?: string;
    img?: string;
    teacher?: string;
    learning_goals?: string[];
    preference?: AdminStudentPreference;
}

export interface AdminLlmLog {
    timestamp: string;
    module?: string;
    metadata?: Record<string, unknown>;
    request?: {
        model?: string;
        messages?: Array<{ role: string; content: string }>;
    };
    response?: {
        usage?: {
            prompt_tokens?: number;
            completion_tokens?: number;
            total_tokens?: number;
        };
        choices?: Array<{
            message?: {
                content?: string;
            };
        }>;
    };
}

export interface CourseOption {
    id: number;
    name: string;
}

/** 原始对话历史查询参数，对应 POST /api/5e/chat/raw-history 的请求体。 */
export interface RawChatHistoryQuery {
    student_id: string;
    course_id: number;
}

/** 内容片段中携带的模型工具调用信息。 */
export interface RawChatFunctionCall {
    id?: string | null;
    name?: string | null;
    args?: Record<string, unknown>;
}

/** 内容片段中携带的工具执行结果。 */
export interface RawChatFunctionResponse {
    id?: string | null;
    name?: string | null;
    response?: Record<string, unknown>;
}

/** 单个内容片段，可能包含纯文本、工具调用、工具返回或它们的组合。 */
export interface RawChatContentPart {
    text?: string | null;
    function_call?: RawChatFunctionCall | null;
    function_response?: RawChatFunctionResponse | null;
}

export interface RawChatContent {
    parts: RawChatContentPart[];
    role: string;
}

/** 未经反序列化的原始对话事件，对应后端 events.event_data。 */
export interface RawChatEvent {
    model_version?: string;
    content?: RawChatContent;
    partial?: boolean;
    finish_reason?: string;
    invocation_id?: string;
    author?: string;
    id?: string;
    /** Unix 时间戳（秒）。 */
    timestamp?: number;
}
