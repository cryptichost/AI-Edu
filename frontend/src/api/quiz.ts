import { apiClient } from "./client";
import {
    QuizListResponse,
    QuizOptionRequest,
    QuizQuestionRequest,
    QuizQuestionResponse,
    QuizRecordDetailResponse,
    QuizRecordResponse,
    QuizTakeQuestionResponse,
} from "../types/quiz";

export async function fetchAllQuizes(): Promise<QuizListResponse[]> {
    const { data } = await apiClient.post<QuizListResponse[]>("/api/quiz/list");
    return data;
}

export async function fetchQuizzesByCourse(courseId: number): Promise<QuizListResponse[]> {
    const { data } = await apiClient.post<QuizListResponse[]>("/api/quiz/list", {
        course_id: courseId
    });
    return data;
}

export async function fetchQuizQuestions(quizId: number): Promise<QuizQuestionResponse[]> {
    const { data } = await apiClient.get<QuizQuestionResponse[]>(
        `/api/quiz/questions/${quizId}`
    );
    return data;
}

/**
 * 学生作答专用：获取题目与选项，响应中不含正确答案与解析。
 * 教师编辑题目请使用 fetchQuizQuestions。
 */
export async function fetchQuizTakeQuestions(quizId: number): Promise<QuizTakeQuestionResponse[]> {
    const { data } = await apiClient.get<QuizTakeQuestionResponse[]>(
        `/api/quiz/questions/${quizId}/take`
    );
    return data;
}

/**
 * 整题保存（含选项）请求体：
 * 题目字段沿用 QuizQuestionRequest，选项列表由 QuizOptionRequest 描述。
 * 通过 Omit 派生类型去掉与编辑无关的冗余字段（不改动原类型定义）：
 * - id 为空 / 缺省的选项会被后端当作新增选项；
 * - options 不传表示不改动选项，传 [] 表示清空全部选项。
 */
export type QuizQuestionSavePayload = Partial<Omit<QuizQuestionRequest, "id">> & {
    options?: Array<Omit<QuizOptionRequest, "options" | "id"> & { id?: number }>;
};

/** 整题保存（含选项）：更新题目字段并同步该题全部选项。 */
export async function updateQuizQuestion(
    questionId: number,
    payload: QuizQuestionSavePayload
): Promise<QuizQuestionResponse> {
    const { data } = await apiClient.post<QuizQuestionResponse>(
        `/api/quiz/questions/${questionId}`,
        payload
    );
    return data;
}

/** 新增题目：在指定测验下创建一道题目（含全部选项）。 */
export async function createQuizQuestion(
    quizId: number,
    payload: QuizQuestionSavePayload
): Promise<QuizQuestionResponse> {
    const { data } = await apiClient.post<QuizQuestionResponse>(
        `/api/quiz/questions/new/${quizId}`,
        payload
    );
    return data;
}

/**
 * 按用户查询作答记录（POST /api/quiz/records/user）。
 * 返回该用户全部记录，其中 `submit_at` 为空表示「进行中」。
 */
export async function fetchQuizRecordsByUser(
    studentId: number | string, courseId?: number | string | null
): Promise<QuizRecordResponse[]> {
    const { data } = await apiClient.post<QuizRecordResponse[]>("/api/quiz/records/user", {
        user_id: studentId,
        course_id: courseId ?? null
    });
    return data;
}

/** 进入测验：在后台创建一条作答记录（submit_at 为空，表示进行中）。 */
export async function startQuizRecord(
    quizId: number, studentId: number | string
): Promise<QuizRecordResponse> {
    const { data } = await apiClient.post<QuizRecordResponse>("/api/quiz/records/start", {
        quiz_id: quizId,
        user_id: studentId
    });
    return data;
}

/** 提交测验：把该记录标记为已完成（写入 submit_at）。 */
export async function submitQuizRecord(recordId: number): Promise<QuizRecordResponse> {
    const { data } = await apiClient.post<QuizRecordResponse>(
        `/api/quiz/records/${recordId}/submit`,
        {}
    );
    return data;
}

/** 根据作答记录 id 查询测验详情（含题目、选项与作答）。 */
export async function fetchQuizRecordDetail(
    recordId: number
): Promise<QuizRecordDetailResponse> {
    const { data } = await apiClient.get<QuizRecordDetailResponse>(
        `/api/quiz/records/${recordId}`
    );
    return data;
}