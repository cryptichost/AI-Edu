import { apiClient, completeQuiz } from "./client";
import { fetchCurrentUser, logoutUser } from "./login";
import { generateLearningPlanFromQuiz } from "./student";

import type {
  QuizAnswerResponse,
  QuizQuestion,
  QuizStartResponse,
  QuizState,
  QuizSummaryResponse,
} from "./client";
import type { LearningPlanEntry } from "../types/student";
import type { IndustryChartRow, IndustryJob, IndustryResult } from "../types/industry";

export type {
  IndustryChartRow,
  IndustryJob,
  IndustryResult,
  LearningPlanEntry,
  QuizQuestion,
  QuizState,
};

export { fetchCurrentUser, logoutUser, completeQuiz, generateLearningPlanFromQuiz };

export async function startQuiz(payload: { subject: string; lang_choice?: string }) {
  const { data } = await apiClient.post<QuizStartResponse>("/api/quiz/start", {
    subject: payload.subject,
    lang_choice: payload.lang_choice ?? "auto",
  });
  return data;
}

export async function answerQuiz(payload: { choice: string; state: QuizState }) {
  const { data } = await apiClient.post<QuizAnswerResponse>("/api/quiz/answer", payload);
  return data;
}

export async function generateQuizSummary(payload: {
  topic: string;
  score: number;
  total: number;
  user_answers: Array<Record<string, unknown>>;
  questions: Array<Record<string, unknown>>;
}) {
  const { data } = await apiClient.post<QuizSummaryResponse>("/api/quiz/summary", payload);
  return data;
}

