import {
    AdminLlmLog,
    AdminStudentRecord,
    AdminTeacherRecord,
    CourseOption,
    RawChatEvent,
    RawChatHistoryQuery,
} from "../types/admin";
import { apiClient } from "./client";

export async function fetchAdminTeachers() {
    const {data} = await apiClient.get<AdminTeacherRecord[]>("/api/teachers");
    return data;
}

export async function fetchAdminStudents() {
    const {data} = await apiClient.get<AdminStudentRecord[]>("/api/students");
    return data;
}

export async function fetchAdminLlmLogs() {
    const {data} = await apiClient.get<AdminLlmLog[]>("/api/llm-logs");
    return data;
}

export async function fetchAllCourses() {
    const {data} = await apiClient.get<CourseOption[]>("/api/5e/course/all");
    return data;
}

/** 查询某个学生在某个课程下的原始对话历史（未反序列化的事件流）。 */
export async function fetchRawChatHistory(query: RawChatHistoryQuery) {
    const {data} = await apiClient.post<RawChatEvent[]>("/api/5e/chat/raw-history", query);
    return data;
}