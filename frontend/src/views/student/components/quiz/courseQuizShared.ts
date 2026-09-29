import type { QuizRecordDetailResponse, QuizTakeQuestionResponse } from "../../../../types/quiz";
import type { ParsedOption, TakeQuestion } from "../../../../types/quiz";

// 供作答面板等组件从本模块直接引入这些类型。
export type { ParsedOption, TakeQuestion } from "../../../../types/quiz";

export function isTruthy(value: number | boolean | undefined): boolean {
  return value === true || value === 1;
}

/** 从服务端详情中取测验标题，取不到时回退到记录 id。 */
export function serverItemTitle(detail: QuizRecordDetailResponse, fallbackId: number): string {
  const rawTitle = detail.quiz?.title;
  const titleText = rawTitle != null && String(rawTitle).trim() !== "" ? String(rawTitle) : "";
  if (titleText) return titleText;
  return detail.quiz ? `知识测验 #${detail.quiz.id}` : `测验记录 #${fallbackId}`;
}

export function formatTime(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** 从题目文本中拆出题干与 A/B/C/D 选项。 */
export function parseQuestion(questionText: string): { stem: string; options: ParsedOption[] } {
  const lines = questionText
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const optionRegex = /^([A-Da-d])[\.\):：\s]*(.+)$/;
  const options: ParsedOption[] = [];
  const stemLines: string[] = [];
  for (const line of lines) {
    const match = line.match(optionRegex);
    if (match) {
      options.push({ key: match[1].toLowerCase(), text: match[2] });
    } else {
      stemLines.push(line);
    }
  }
  return { stem: stemLines.join("\n"), options };
}

/**
 * 把作答接口返回的题目（content 内嵌选项 + options 列表）转成作答模型。
 * 作答接口不返回正确答案，因此这里不带任何判分信息。
 */
export function buildTakeQuestions(questions: QuizTakeQuestionResponse[]): TakeQuestion[] {
  return questions.map((question, index) => {
    const parsed = parseQuestion(question.content ?? "");
    const options = question.options ?? [];
    const optionModels: ParsedOption[] = options.length
      ? options.map((option, optionIndex) => ({
          key: String.fromCharCode(97 + optionIndex),
          text: option.content,
        }))
      : parsed.options;
    return {
      key: `take-${question.id}-${index}`,
      raw: question.content ?? "",
      stem: parsed.stem || question.content || "(无题干)",
      options: optionModels,
    };
  });
}
