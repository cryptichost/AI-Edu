<template>
  <div class="course-quiz-dialog">
    <!-- ============ 记录列表视图 ============ -->
    <template v-if="view === 'list'">
      <div class="course-quiz-top">
        <div class="course-quiz-top-copy">
          <h2>📝 在线测验</h2>
          <p class="muted">
            {{
              courseName
                ? `在「${courseName}」中参加过的测验都会记录在这里，点击即可回看作答详情`
                : "参加过的测验都会记录在这里，点击即可回看作答详情"
            }}
          </p>
        </div>
        <button type="button" class="primary-link button-like course-quiz-start-cta">
          开始测验
        </button>
      </div>

      <!-- 学生信息未就绪提示 -->
      <div v-if="!props.studentId" class="state-card course-quiz-tip">
        正在获取当前学生信息…
      </div>

      <!-- 历史作答记录 -->
      <div class="course-quiz-records">
        <div class="course-quiz-records-head">
          <strong>📋 历史作答记录</strong>
          <span v-if="!listLoading && !listError" class="muted">共 {{ mergedRecords.length }} 条</span>
        </div>

        <div v-if="listLoading" class="state-card">正在加载测验记录...</div>

        <div v-else>
          <div v-if="listError" class="state-card error-state">
            {{ listError }}
            <button type="button" class="ghost-btn course-quiz-retry" @click="reload">重试</button>
          </div>

          <div v-if="mergedRecords.length" class="course-quiz-record-list">
            <button
              v-for="item in mergedRecords"
              :key="item.key"
              type="button"
              class="course-quiz-record"
              @click="openRecord(item)"
            >
              <div class="course-quiz-record-main">
                <div class="course-quiz-record-title">
                  {{ item.title }}
                  <span v-if="item.source === 'local'" class="course-quiz-record-badge">本页完成</span>
                </div>
                <div class="course-quiz-record-meta muted">
                  {{ item.submittedAtText }}
                  <template v-if="item.summaryText"> · {{ item.summaryText }}</template>
                </div>
              </div>
              <span class="course-quiz-record-arrow">›</span>
            </button>
          </div>

          <div v-else-if="!listError" class="course-quiz-empty">
            <div class="course-quiz-empty-icon">🧪</div>
            <p>还没有测验记录</p>
            <p class="muted">点击上方「开始测验」，完成后即可在此回看作答详情</p>
          </div>
        </div>
      </div>
    </template>

    <!-- ============ 作答详情视图 ============ -->
    <template v-else-if="view === 'detail'">
      <div class="course-quiz-detail-head">
        <button type="button" class="ghost-btn" @click="closeDetail">← 返回记录</button>
        <span class="muted">作答详情</span>
      </div>

      <div v-if="detailLoading" class="state-card">正在加载作答详情...</div>
      <div v-else-if="detailError" class="state-card error-state">{{ detailError }}</div>

      <div v-else-if="detailModel" class="course-quiz-detail">
        <!-- 概要 -->
        <div class="course-quiz-detail-summary">
          <div class="course-quiz-detail-summary-main">
            <h3>{{ detailModel.title }}</h3>
            <p class="muted">{{ detailModel.submitText }}</p>
          </div>
          <div class="course-quiz-score-pill">
            <span class="course-quiz-score-num">{{ detailModel.correct }}</span>
            <span class="course-quiz-score-total">/ {{ detailModel.total || "-" }}</span>
            <span class="course-quiz-score-label">答对</span>
          </div>
        </div>

        <!-- 题目列表 -->
        <div class="course-quiz-question-list">
          <article
            v-for="(question, index) in detailModel.questions"
            :key="question.key"
            class="course-quiz-question-card"
          >
            <header class="course-quiz-question-head">
              <span class="course-quiz-question-no">第 {{ index + 1 }} 题</span>
              <span
                class="course-quiz-question-state"
                :class="question.correct ? 'is-right' : question.answered ? 'is-wrong' : 'is-skip'"
              >
                {{ question.correct ? "回答正确" : question.answered ? "回答错误" : "未作答" }}
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
    </template>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { apiClient } from "../../../api/client";

const props = defineProps<{
  courseId?: string;
  studentId?: string;
  courseName?: string;
  nodeName?: string;
}>();

/* ---------------- 常量 ---------------- */
const STORAGE_PREFIX = "course-quiz-dialog";

/* ---------------- 类型 ---------------- */
interface ParsedOption {
  key: string;
  text: string;
}
interface LocalAnswerItem {
  raw: string;
  stem: string;
  options: ParsedOption[];
  selected: string;
  correctKey: string;
  isCorrect: boolean;
}
interface LocalRun {
  id: string;
  topic: string;
  submittedAt: string;
  total: number;
  correct: number;
  questions: LocalAnswerItem[];
}
interface ServerRecordListItem {
  id: number;
  updated_at?: string | null;
}
interface ServerQuestionOption {
  id: number;
  content: string;
  is_correct: number | boolean;
}
interface ServerQuestionAnswer {
  id: number;
  user_answer: string | number | null;
  is_correct: number | boolean;
}
interface ServerQuestion {
  id: number;
  question_type?: string | null;
  content: string;
  analysis?: string | null;
  options?: ServerQuestionOption[];
  answers?: ServerQuestionAnswer[];
}
interface ServerQuizDetail {
  record: { id: number; quiz_id?: number | null; user_id?: number | null; start_at?: string | null; submit_at?: string | null };
  quiz: {
    id: number;
    title?: number | string | null;
    question_count?: number | null;
    course_id?: number | null;
    total_score?: number | null;
  } | null;
  questions: ServerQuestion[];
}
interface RecordItem {
  key: string;
  source: "server" | "local";
  recordId?: number;
  run?: LocalRun;
  title: string;
  submittedAtText: string;
  submittedAt?: string;
  summaryText?: string;
  detail?: ServerQuizDetail;
}
interface DetailQuestionModel {
  key: string;
  stem: string;
  correct: boolean;
  answered: boolean;
  analysis?: string;
  optionModels: Array<{
    key: string;
    text: string;
    cls: string;
    correctMark: string;
  }>;
  userAnswerText: string;
  correctKeyText: string;
}
interface DetailModel {
  title: string;
  submitText: string;
  correct: number;
  total: number;
  questions: DetailQuestionModel[];
}

/* ---------------- 视图状态 ---------------- */
const view = ref<"list" | "detail">("list");

/* ----- 记录列表 ----- */
const listLoading = ref(false);
const listError = ref("");
const serverRecords = ref<ServerRecordListItem[]>([]);
const serverDetailCache = new Map<number, ServerQuizDetail>();
const localRuns = ref<LocalRun[]>([]);

const numericUserId = computed(() => {
  const value = (props.studentId ?? "").trim();
  return /^\d+$/.test(value) ? value : "";
});

function storageKey() {
  return `${STORAGE_PREFIX}:${props.studentId || "anon"}:${props.courseId || "default"}`;
}
function readLocalRuns(): LocalRun[] {
  try {
    const raw = window.localStorage.getItem(storageKey());
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as LocalRun[]) : [];
  } catch {
    return [];
  }
}

function formatTime(value?: string | null): string {
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

function isTruthy(value: number | boolean | undefined): boolean {
  return value === true || value === 1;
}

/* ----- 记录解析（服务端） ----- */
function buildServerSummary(detail: ServerQuizDetail): { correct: number; total: number } {
  let correct = 0;
  for (const question of detail.questions) {
    const answers = question.answers ?? [];
    if (answers.some((answer) => isTruthy(answer.is_correct))) correct += 1;
  }
  return { correct, total: detail.questions.length };
}

function serverItemTitle(detail: ServerQuizDetail, fallbackId: number): string {
  const rawTitle = detail.quiz?.title;
  const titleText =
    rawTitle != null && String(rawTitle).trim() !== "" ? String(rawTitle) : "";
  if (titleText) return titleText;
  return detail.quiz ? `知识测验 #${detail.quiz.id}` : `测验记录 #${fallbackId}`;
}

async function loadServerRecords() {
  if (!numericUserId.value) return;
  try {
    const { data } = await apiClient.get<ServerRecordListItem[]>(
      `/api/quiz/users/${numericUserId.value}/records`
    );
    serverRecords.value = Array.isArray(data) ? data : [];
  } catch (error) {
    listError.value =
      error instanceof Error
        ? `服务端记录加载失败：${error.message}`
        : "服务端记录加载失败，请稍后重试";
  }
}

async function expandServerDetails() {
  const items = serverRecords.value;
  for (const item of items) {
    try {
      const cached = serverDetailCache.get(item.id);
      if (cached) continue;
      const { data } = await apiClient.get<ServerQuizDetail>(`/api/quiz/records/${item.id}`);
      serverDetailCache.set(item.id, data);
    } catch {
      /* 单条详情失败不影响其余记录 */
    }
  }
}

function parseQuestion(questionText: string): { stem: string; options: ParsedOption[] } {
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

/* ----- 合并列表 ----- */
const mergedRecords = computed<RecordItem[]>(() => {
  const items: RecordItem[] = [];

  for (const run of localRuns.value) {
    items.push({
      key: `local:${run.id}`,
      source: "local",
      run,
      title: run.topic || "未命名测验",
      submittedAtText: formatTime(run.submittedAt),
      submittedAt: run.submittedAt,
      summaryText: `得分 ${run.correct}/${run.total}`,
    });
  }

  for (const record of serverRecords.value) {
    const detail = serverDetailCache.get(record.id);
    let summaryText = "";
    if (detail) {
      const { correct, total } = buildServerSummary(detail);
      if (total > 0) summaryText = `答对 ${correct}/${total}`;
    }
    items.push({
      key: `server:${record.id}`,
      source: "server",
      recordId: record.id,
      title: detail ? serverItemTitle(detail, record.id) : `测验记录 #${record.id}`,
      submittedAtText: formatTime(record.updated_at),
      submittedAt: record.updated_at ?? undefined,
      summaryText,
      detail,
    });
  }

  return items.sort((a, b) => {
    const timeA = a.submittedAt ? new Date(a.submittedAt).getTime() : 0;
    const timeB = b.submittedAt ? new Date(b.submittedAt).getTime() : 0;
    return timeB - timeA;
  });
});

async function reload() {
  listError.value = "";
  listLoading.value = true;
  try {
    await Promise.all([loadServerRecords(), expandServerDetails()]);
  } finally {
    listLoading.value = false;
  }
}

function loadLocalRuns() {
  localRuns.value = readLocalRuns();
}

/* ----- 作答详情 ----- */
const detailLoading = ref(false);
const detailError = ref("");
const detailModel = ref<DetailModel | null>(null);

function localQuestionModels(run: LocalRun): DetailQuestionModel[] {
  return run.questions.map((item, index) => {
    const optionModels = item.options.map((option) => {
      const isCorrectOption = option.key === item.correctKey;
      const isWrongPick = option.key === item.selected && !item.isCorrect;
      const correctMark = isCorrectOption
        ? "✓"
        : isWrongPick
          ? "✗"
          : "";
      return {
        key: option.key,
        text: option.text,
        cls: isCorrectOption ? "right" : isWrongPick ? "wrong" : "",
        correctMark,
      };
    });
    return {
      key: `local-${index}`,
      stem: item.stem || item.raw,
      correct: item.isCorrect,
      answered: true,
      optionModels,
      userAnswerText: item.selected ? item.selected.toUpperCase() : "",
      correctKeyText: item.correctKey ? item.correctKey.toUpperCase() : "",
    };
  });
}

function buildDetailFromServer(detail: ServerQuizDetail): DetailModel {
  const questions: DetailQuestionModel[] = (detail.questions ?? []).map((question, index) => {
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
      correct,
      answered,
      analysis: question.analysis || undefined,
      optionModels,
      userAnswerText: selectedTexts.length ? selectedTexts.join("、") : answered ? "未匹配到选项" : "",
      correctKeyText: correctKeys.length ? correctKeys.join("、") : "",
    };
  });

  const { correct } = buildServerSummary(detail);
  return {
    title: serverItemTitle(detail, detail.record.id),
    submitText: `提交于 ${formatTime(detail.record.submit_at)}`,
    correct,
    total: detail.questions.length,
    questions,
  };
}

async function openRecord(item: RecordItem) {
  if (item.source === "local" && item.run) {
    detailModel.value = {
      title: item.run.topic || "未命名测验",
      submitText: `完成于 ${formatTime(item.run.submittedAt)}`,
      correct: item.run.correct,
      total: item.run.total,
      questions: localQuestionModels(item.run),
    };
    view.value = "detail";
    return;
  }

  if (item.source === "server" && item.recordId != null) {
    detailLoading.value = true;
    detailError.value = "";
    detailModel.value = null;
    try {
      let detail = serverDetailCache.get(item.recordId);
      if (!detail) {
        const { data } = await apiClient.get<ServerQuizDetail>(
          `/api/quiz/records/${item.recordId}`
        );
        detail = data;
        serverDetailCache.set(item.recordId, detail);
      }
      detailModel.value = buildDetailFromServer(detail);
      view.value = "detail";
    } catch (error) {
      detailError.value =
        error instanceof Error ? `加载作答详情失败：${error.message}` : "加载作答详情失败";
    } finally {
      detailLoading.value = false;
    }
  }
}

function closeDetail() {
  detailModel.value = null;
  detailError.value = "";
  view.value = "list";
}

/* ----- 生命周期 ----- */
watch(
  () => [props.courseId, props.studentId],
  () => {
    loadLocalRuns();
    void reload();
  }
);

onMounted(() => {
  loadLocalRuns();
  void reload();
});
</script>

<style scoped>
.course-quiz-dialog {
  width: 100%;
  box-sizing: border-box;
  padding: 22px 26px 30px;
  text-align: left;
}

/* ---------- 顶部 CTA ---------- */
.course-quiz-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  flex-wrap: wrap;
  margin-bottom: 22px;
}
.course-quiz-top-copy h2 {
  margin: 0 0 6px;
  font-size: 21px;
  color: #1e293b;
}
.course-quiz-top-copy p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  max-width: 460px;
}
.course-quiz-start-cta {
  flex-shrink: 0;
  font-size: 14px;
  padding: 10px 22px;
}
.course-quiz-tip {
  margin-bottom: 18px;
}

/* ---------- 记录列表 ---------- */
.course-quiz-records-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 12px;
}
.course-quiz-records-head strong {
  font-size: 15px;
  color: #1e293b;
}
.course-quiz-records-head .muted {
  font-size: 12px;
}
.course-quiz-empty {
  text-align: center;
  padding: 42px 20px;
}
.course-quiz-empty-icon {
  font-size: 40px;
  margin-bottom: 10px;
}
.course-quiz-empty p {
  margin: 4px 0;
  color: #475569;
  font-size: 14px;
}
.course-quiz-empty p.muted {
  font-size: 12px;
}
.course-quiz-record-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 46vh;
  overflow-y: auto;
  padding-right: 4px;
}
.course-quiz-record {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  box-sizing: border-box;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 13px 16px;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  font: inherit;
  color: inherit;
}
.course-quiz-record:hover {
  border-color: #2563eb;
  box-shadow: 0 2px 10px rgba(37, 99, 235, 0.08);
}
.course-quiz-record-main {
  min-width: 0;
}
.course-quiz-record-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.course-quiz-record-badge {
  font-size: 11px;
  font-weight: 400;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  padding: 1px 8px;
}
.course-quiz-record-meta {
  margin-top: 4px;
  font-size: 12px;
}
.course-quiz-record-arrow {
  color: #94a3b8;
  font-size: 20px;
  line-height: 1;
  flex-shrink: 0;
}
.course-quiz-retry {
  margin-left: 10px;
  font-size: 12px;
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
.course-quiz-score-pill {
  display: flex;
  align-items: baseline;
  gap: 4px;
  flex-shrink: 0;
  background: #eff6ff;
  border-radius: 12px;
  padding: 8px 14px;
}
.course-quiz-score-num {
  font-size: 24px;
  font-weight: 700;
  color: #2563eb;
}
.course-quiz-score-total {
  font-size: 14px;
  color: #64748b;
}
.course-quiz-score-label {
  font-size: 12px;
  color: #64748b;
  margin-left: 6px;
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
