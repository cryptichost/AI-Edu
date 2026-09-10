import { apiClient } from "./client";
import {
    QuizListResponse,
    QuizOptionRequest,
    QuizQuestionRequest,
    QuizQuestionResponse,
} from "../types/quiz";

export async function fetchAllQuizes(): Promise<QuizListResponse[]> {
    const { data } = await apiClient.get<QuizListResponse[]>("/api/quiz/list");
    return data;
}

export async function fetchQuizQuestions(quizId: number): Promise<QuizQuestionResponse[]> {
    const { data } = await apiClient.get<QuizQuestionResponse[]>(
        `/api/quiz/questions/${quizId}`
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