<template>
  <div class="course-quiz-detail-panel">
    <div class="course-quiz-detail-head">
      <button type="button" class="ghost-btn" @click="emit('close')">← 返回记录</button>
      <span class="muted">作答详情</span>
    </div>

    <div v-if="loading" class="state-card">正在加载作答详情...</div>
    <div v-else-if="error" class="state-card error-state">{{ error }}</div>

    <div v-else-if="model" class="course-quiz-detail">
      <!-- 概要 -->
      <div class="course-quiz-detail-summary">
        <div class="course-quiz-detail-summary-main">
          <h3>{{ model.title }}</h3>
          <p class="muted">{{ model.submitText }}</p>
          <p v-if="model.note" class="course-quiz-detail-note muted">
            {{ model.note }}
          </p>
        </div>
      </div>

      <!-- 题目列表 -->
      <div class="course-quiz-question-list">
        <article
          v-for="(question, index) in model.questions"
          :key="question.key"
          class="course-quiz-question-card"
        >
          <header class="course-quiz-question-head">
            <span class="course-quiz-question-no">第 {{ index + 1 }} 题</span>
            <span
              class="course-quiz-question-state"
              :class="`is-${question.state}`"
            >
              {{ question.stateText }}
            </span>
          </header>

          <p class="course-quiz-question-content">{{ question.stem }}</p>

          <ul v-if="question.optionModels.length" class="course-quiz-option-list">
            <li
              v-for="option in question.optionModels"
              :key="`${question.key}-${option.key}`"
              class="course-quiz-option"
              :class="option.cls"
            >
              <span class="course-quiz-option-key">{{ option.key.toUpperCase() }}</span>
              <span class="course-quiz-option-text">{{ option.text }}</span>
              <span v-if="option.correctMark" class="course-quiz-option-mark">{{
                option.correctMark
              }}</span>
            </li>
          </ul>

          <footer v-if="question.userAnswerText" class="course-quiz-question-foot">
            <span>你的答案：{{ question.userAnswerText }}</span>
            <span v-if="question.correctKeyText" class="course-quiz-answer-correct">
              正确答案：{{ question.correctKeyText }}
            </span>
          </footer>

          <p v-if="question.analysis" class="course-quiz-question-analysis">
            💡 {{ question.analysis }}
          </p>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { fetchQuizRecordDetail } from "../../../../api/quiz.js";
import type {
  QuizDetailModel,
  QuizDetailQuestionModel,
  QuizRecordDetailResponse,
} from "../../../../types/quiz.js";
import { formatTime, isTruthy, parseQuestion, serverItemTitle } from "./courseQuizShared";

const props = defineProps<{
  /** 要查看的作答记录 id。 */
  recordId: number | null;
}>();

const emit = defineEmits<{ (e: "close"): void }>();

const loading = ref(false);
const error = ref("");
const model = ref<QuizDetailModel | null>(null);

/** 后台当前只保存记录（进入/提交时间），未保存逐题作答明细。 */
function buildDetailFromServer(detail: QuizRecordDetailResponse): QuizDetailModel {
  const answeredCount = (detail.questions ?? []).filter(
    (question) => (question.answers ?? []).length > 0
  ).length;

  const questions: QuizDetailQuestionModel[] = (detail.questions ?? []).map((question, index) => {
    const parsed = parseQuestion(question.content ?? "");
    const options = question.options ?? [];
    const answers = question.answers ?? [];

    let correct = false;
    let answered = false;
    const selectedTexts: string[] = [];
    const selectedOptionIndexes = new Set<number>();

    for (const answer of answers) {
      answered = true;
      if (isTruthy(answer.is_correct)) correct = true;
      const matchedIndex = options.findIndex((option) => {
        if (answer.user_answer == null) return false;
        const idMatched =
          /^\d+$/.test(String(answer.user_answer)) && option.id === Number(answer.user_answer);
        const textMatched = String(option.content).trim() === String(answer.user_answer).trim();
        return idMatched || textMatched;
      });
      if (matchedIndex >= 0) {
        selectedOptionIndexes.add(matchedIndex);
        selectedTexts.push(String.fromCharCode(65 + matchedIndex));
      } else {
        selectedTexts.push(String(answer.user_answer));
      }
    }

    const optionModels =
      options.length > 0
        ? options.map((option, optionIndex) => {
            const key = String.fromCharCode(97 + optionIndex);
            const isCorrectOption = isTruthy(option.is_correct);
            const isSelected = selectedOptionIndexes.has(optionIndex);
            const isWrongPick = isSelected && !isCorrectOption;
            let cls = "";
            if (isCorrectOption) cls = "right";
            else if (isWrongPick) cls = "wrong";
            return {
              key,
              text: option.content,
              cls,
              correctMark: isCorrectOption ? "✓" : isWrongPick ? "✗" : "",
            };
          })
        : parsed.options.map((option) => ({
            key: option.key,
            text: option.text,
            cls: "",
            correctMark: "",
          }));

    const stem = parsed.stem || question.content || "(无题干)";
    const correctKeys = options
      .filter((option) => isTruthy(option.is_correct))
      .map((option) => String.fromCharCode(65 + options.indexOf(option)));

    return {
      key: `server-${index}-${question.id}`,
      stem,
      state: correct ? "right" : answered ? "wrong" : "skip",
      stateText: correct ? "回答正确" : answered ? "回答错误" : "未作答",
      analysis: question.analysis || undefined,
      optionModels,
      userAnswerText: selectedTexts.length ? selectedTexts.join("、") : answered ? "未匹配到选项" : "",
      correctKeyText: correctKeys.length ? correctKeys.join("、") : "",
    };
  });

  const submitAtText = detail.record.submit_at
    ? `提交于 ${formatTime(detail.record.submit_at)}`
    : `开始于 ${formatTime(detail.record.start_at)} · 尚未提交`;

  return {
    title: serverItemTitle(detail, detail.record.id),
    submitText: submitAtText,
    note:
      questions.length && !answeredCount
        ? "本次仅保存了测验记录（进入/提交时间），未保存逐题作答明细。"
        : undefined,
    questions,
  };
}

/** 加载作答详情：进入详情视图时按需请求后台（列表阶段不预取）。 */
async function loadDetail() {
  if (props.recordId == null) return;

  loading.value = true;
  error.value = "";
  model.value = null;
  try {
    const detail = await fetchQuizRecordDetail(props.recordId);
    model.value = buildDetailFromServer(detail);
  } catch (err) {
    error.value =
      err instanceof Error ? `加载作答详情失败：${err.message}` : "加载作答详情失败";
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.recordId,
  () => {
    void loadDetail();
  }
);

onMounted(() => {
  void loadDetail();
});
</script>

<style scoped>
.course-quiz-detail-panel {
  width: 100%;
  box-sizing: border-box;
  text-align: left;
}

/* ---------- 详情视图头部 ---------- */
.course-quiz-detail-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.course-quiz-detail-head .ghost-btn {
  font-size: 13px;
}

/* ---------- 作答详情 ---------- */
.course-quiz-detail-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 14px;
}
.course-quiz-detail-summary-main h3 {
  margin: 0 0 4px;
  font-size: 16px;
  color: #1e293b;
}
.course-quiz-detail-summary-main p {
  margin: 0;
  font-size: 12px;
}
.course-quiz-detail-note {
  margin-top: 6px !important;
  font-size: 12px;
  color: #b45309;
}

.course-quiz-question-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 56vh;
  overflow-y: auto;
  padding-right: 4px;
}
.course-quiz-question-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px 16px;
}
.course-quiz-question-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.course-quiz-question-no {
  font-size: 12px;
  font-weight: 600;
  color: #2563eb;
  background: #eff6ff;
  border-radius: 999px;
  padding: 2px 10px;
}
.course-quiz-question-state {
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 10px;
}
.course-quiz-question-state.is-right {
  color: #16a34a;
  background: #f0fdf4;
}
.course-quiz-question-state.is-wrong {
  color: #dc2626;
  background: #fef2f2;
}
.course-quiz-question-state.is-skip {
  color: #64748b;
  background: #f1f5f9;
}
.course-quiz-question-content {
  margin: 0 0 10px;
  font-size: 14px;
  line-height: 1.7;
  color: #1e293b;
  white-space: pre-wrap;
}
.course-quiz-option-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.course-quiz-option {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 13px;
  color: #334155;
  background: #f8fafc;
}
.course-quiz-option.right {
  border-color: #86efac;
  background: #f0fdf4;
  color: #14532d;
}
.course-quiz-option.wrong {
  border-color: #fca5a5;
  background: #fef2f2;
  color: #7f1d1d;
}
.course-quiz-option-key {
  font-weight: 700;
  color: #64748b;
  flex-shrink: 0;
}
.course-quiz-option.right .course-quiz-option-key {
  color: #16a34a;
}
.course-quiz-option.wrong .course-quiz-option-key {
  color: #dc2626;
}
.course-quiz-option-mark {
  margin-left: auto;
  flex-shrink: 0;
  font-weight: 600;
}
.course-quiz-question-foot {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed #e2e8f0;
  font-size: 12px;
  color: #475569;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.course-quiz-answer-correct {
  color: #16a34a;
}
.course-quiz-question-analysis {
  margin: 8px 0 0;
  font-size: 12px;
  color: #6b7280;
  background: #f8fafc;
  border-radius: 8px;
  padding: 8px 10px;
  line-height: 1.6;
}
</style>
