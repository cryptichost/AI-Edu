<template>
  <div class="course-quiz-take-panel">
    <!-- ============ 选择测验视图 ============ -->
    <template v-if="stage === 'picker'">
      <div class="course-quiz-detail-head">
        <button type="button" class="ghost-btn" @click="backToRecords">← 返回记录</button>
        <span class="muted">选择要参加的测验</span>
      </div>

      <div class="course-quiz-records-head">
        <strong>🎯 {{ courseLabel }} 的测验</strong>
        <span v-if="!pickerLoading && !pickerError" class="muted">共 {{ courseQuizzes.length }} 个</span>
      </div>

      <div v-if="pickerLoading" class="state-card">正在加载测验列表...</div>

      <div v-else-if="pickerError" class="state-card error-state">
        {{ pickerError }}
        <button type="button" class="ghost-btn course-quiz-retry" @click="loadCourseQuizzes">重试</button>
      </div>

      <div v-else-if="courseQuizzes.length" class="course-quiz-record-list">
        <button
          v-for="quiz in courseQuizzes"
          :key="quiz.id"
          type="button"
          class="course-quiz-record"
          @click="startQuiz(quiz)"
        >
          <div class="course-quiz-record-main">
            <div class="course-quiz-record-title">
              {{ quiz.title || `测验 #${quiz.id}` }}
              <span class="course-quiz-record-badge">{{ quiz.question_count ?? 0 }} 题</span>
            </div>
            <div class="course-quiz-record-meta muted">
              <template v-if="quiz.course_name">{{ quiz.course_name }}</template>
              <template v-if="quiz.total_score != null"> · 满分 {{ quiz.total_score }}</template>
            </div>
          </div>
          <span class="course-quiz-record-arrow">›</span>
        </button>
      </div>

      <div v-else class="course-quiz-empty">
        <div class="course-quiz-empty-icon">📭</div>
        <p>当前课程暂无可用测验</p>
        <p class="muted">请等待教师发布测验后再试</p>
      </div>
    </template>

    <!-- ============ 作答视图 ============ -->
    <template v-else-if="stage === 'take'">
      <div class="course-quiz-detail-head">
        <button type="button" class="ghost-btn" @click="exitTake">← 退出测验</button>
        <span class="muted">{{ activeQuiz?.title || "在线测验" }}</span>
      </div>

      <div v-if="takeLoading" class="state-card">正在加载题目...</div>
      <div v-else-if="takeError" class="state-card error-state">{{ takeError }}</div>

      <template v-else-if="currentTakeQuestion">
        <div class="course-quiz-detail-summary">
          <div class="course-quiz-detail-summary-main">
            <h3>{{ activeQuiz?.title || "在线测验" }}</h3>
            <p class="muted">第 {{ takeIndex + 1 }} / {{ takeTotal }} 题</p>
          </div>
          <div class="course-quiz-take-progress">
            <span class="course-quiz-take-progress-text">已答 {{ answeredCount }} / {{ takeTotal }}</span>
            <div class="course-quiz-take-progress-bar">
              <span :style="{ width: takeProgressWidth }"></span>
            </div>
          </div>
        </div>

        <!-- 题号导航：可点击跳转，方便前后切换与检查未作答题目 -->
        <div class="course-quiz-nav-strip">
          <button
            v-for="(question, index) in takeQuestions"
            :key="question.key"
            type="button"
            class="course-quiz-nav-dot"
            :class="{
              'is-current': index === takeIndex,
              'is-answered': !!takeAnswers[question.key],
            }"
            @click="goToQuestion(index)"
          >
            {{ index + 1 }}
          </button>
        </div>

        <article class="course-quiz-question-card">
          <p class="course-quiz-question-content">{{ currentTakeQuestion.stem }}</p>

          <div v-if="currentTakeQuestion.options.length" class="course-quiz-option-list">
            <button
              v-for="option in currentTakeQuestion.options"
              :key="option.key"
              type="button"
              class="course-quiz-take-option"
              :class="takeOptionClass(option.key)"
              @click="selectTakeOption(option.key)"
            >
              <span class="course-quiz-option-key">{{ option.key.toUpperCase() }}</span>
              <span class="course-quiz-option-text">{{ option.text }}</span>
            </button>
          </div>

          <div class="course-quiz-take-actions">
            <div class="course-quiz-take-nav">
              <button
                type="button"
                class="ghost-btn"
                :disabled="takeIndex === 0"
                @click="prevTakeQuestion"
              >
                上一题
              </button>
              <button
                type="button"
                class="ghost-btn"
                :disabled="isLastTakeQuestion"
                @click="nextTakeQuestion"
              >
                下一题
              </button>
            </div>
            <div class="course-quiz-take-submit-group">
              <span v-if="unansweredCount" class="course-quiz-take-hint muted">
                还有 {{ unansweredCount }} 题未作答
              </span>
              <button
                type="button"
                class="primary-link button-like course-quiz-take-submit"
                :disabled="submitting"
                @click="submitQuiz"
              >
                {{ submitting ? "提交中..." : "提交测验" }}
              </button>
            </div>
          </div>
        </article>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { fetchAllQuizes, fetchQuizzesByCourse, fetchQuizTakeQuestions, startQuizRecord, submitQuizRecord } from "../../../../api/quiz";
import type { QuizListResponse } from "../../../../types/quiz";
import { buildTakeQuestions, type TakeQuestion } from "./courseQuizShared";

const props = defineProps<{
  courseId?: number;
  studentId?: string;
  courseName?: string;
  nodeName?: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  /** 进入测验：后台已生成一条「进行中」记录，参数为记录 id。 */
  (e: "started", recordId: number): void;
  /** 提交测验：后台已写入提交时间，参数为记录 id。 */
  (e: "finished", recordId: number): void;
}>();

/* ----- 阶段状态 ----- */
const stage = ref<"picker" | "take">("picker");

/* ----- 选择测验 ----- */
const pickerLoading = ref(false);
const pickerError = ref("");
const courseQuizzes = ref<QuizListResponse[]>([]);

const courseLabel = computed(() => {
  return (props.courseName || props.nodeName || "").trim() || "当前课程";
});

async function loadCourseQuizzes() {
  pickerLoading.value = true;
  pickerError.value = "";
  try {
    // 直接按课程从后台读取测验，避免拉取全部测验后再在前端筛选。
    // 课程 id 尚未就绪时回退到全部测验，避免列表空白。
    const courseId = props.courseId;
    const list = await fetchQuizzesByCourse(courseId!!);
    courseQuizzes.value = Array.isArray(list) ? list : [];
  } catch (error) {
    pickerError.value =
      error instanceof Error
        ? `测验列表加载失败：${error.message}`
        : "测验列表加载失败，请稍后重试";
    courseQuizzes.value = [];
  } finally {
    pickerLoading.value = false;
  }
}

function backToRecords() {
  emit("close");
}

/* ----- 作答流程 ----- */
const takeLoading = ref(false);
const takeError = ref("");
const activeQuiz = ref<QuizListResponse | null>(null);
const takeQuestions = ref<TakeQuestion[]>([]);
const takeIndex = ref(0);
/** 已选答案：题目 key -> 选项 key。作答期间不做对错判断。 */
const takeAnswers = ref<Record<string, string>>({});
/** 本次作答对应的后台记录 id：进入测验时创建，提交时复用同一条记录。 */
const activeRecordId = ref<number | null>(null);
/** 提交中，避免重复提交。 */
const submitting = ref(false);

const currentTakeQuestion = computed(() => takeQuestions.value[takeIndex.value] ?? null);
const takeTotal = computed(() => takeQuestions.value.length);
const isLastTakeQuestion = computed(() => takeIndex.value >= takeTotal.value - 1);
const answeredCount = computed(
  () => takeQuestions.value.filter((question) => !!takeAnswers.value[question.key]).length
);
const unansweredCount = computed(() => takeTotal.value - answeredCount.value);
const takeProgressWidth = computed(() =>
  takeTotal.value ? `${Math.round((answeredCount.value / takeTotal.value) * 100)}%` : "0%"
);

/** 学生 id 必须是后台 user_id（数字）；否则无法落库。 */
const numericUserId = computed(() => {
  const value = (props.studentId ?? "").trim();
  return /^\d+$/.test(value) ? Number(value) : null;
});

/**
 * 进入测验：先把题目拉下来，再请求后台创建一条「进行中」记录。
 * 记录落库成功后会通知父组件刷新记录列表。
 */
async function startQuiz(quiz: QuizListResponse) {
  activeQuiz.value = quiz;
  stage.value = "take";
  activeRecordId.value = null;
  takeLoading.value = true;
  takeError.value = "";
  takeQuestions.value = [];
  takeIndex.value = 0;
  takeAnswers.value = {};

  const userId = numericUserId.value;
  if (userId == null) {
    takeError.value = "当前学生信息未就绪，无法创建测验记录。";
    takeLoading.value = false;
    return;
  }

  try {
    // 作答接口不返回正确答案，前端无法也不应在提交前判分。
    const questions = await fetchQuizTakeQuestions(quiz.id);
    takeQuestions.value = buildTakeQuestions(Array.isArray(questions) ? questions : []);
    if (!takeQuestions.value.length) {
      takeError.value = "该测验暂无可作答的题目。";
      return;
    }

    // 进入测验即在后台建记录（submit_at 为空 → 进行中），未提交也会保留。
    const record = await startQuizRecord(quiz.id, userId);
    activeRecordId.value = record?.id ?? null;
    emit("started", record.id);
  } catch (error) {
    takeError.value =
      error instanceof Error ? `测验记录创建失败：${error.message}` : "测验记录创建失败，请稍后重试";
  } finally {
    takeLoading.value = false;
  }
}

function selectTakeOption(key: string) {
  const question = currentTakeQuestion.value;
  if (!question) return;
  takeAnswers.value = { ...takeAnswers.value, [question.key]: key };
}

function takeOptionClass(key: string): string {
  const question = currentTakeQuestion.value;
  if (!question) return "";
  return takeAnswers.value[question.key] === key ? "is-picked" : "";
}

function goToQuestion(index: number) {
  if (index < 0 || index >= takeTotal.value) return;
  takeIndex.value = index;
}

function prevTakeQuestion() {
  if (takeIndex.value > 0) takeIndex.value -= 1;
}

function nextTakeQuestion() {
  if (!isLastTakeQuestion.value) takeIndex.value += 1;
}

/** 提交测验：请求后台把进入时创建的那条记录标记为已完成（不判分、不存作答明细）。 */
async function submitQuiz() {
  if (submitting.value) return;
  const recordId = activeRecordId.value;
  if (recordId == null) {
    takeError.value = "测验记录尚未创建成功，请退出后重新进入测验。";
    return;
  }
  submitting.value = true;
  takeError.value = "";
  try {
    await submitQuizRecord(recordId);
    emit("finished", recordId);
  } catch (error) {
    takeError.value =
      error instanceof Error ? `测验提交失败：${error.message}` : "测验提交失败，请稍后重试";
  } finally {
    submitting.value = false;
  }
}

function exitTake() {
  activeQuiz.value = null;
  takeQuestions.value = [];
  takeAnswers.value = {};
  takeError.value = "";
  activeRecordId.value = null;
  stage.value = "picker";
}

onMounted(() => {
  void loadCourseQuizzes();
});
</script>

<style scoped>
.course-quiz-take-panel {
  width: 100%;
  box-sizing: border-box;
  text-align: left;
}

/* ---------- 头部 ---------- */
.course-quiz-detail-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.course-quiz-detail-head .ghost-btn {
  font-size: 13px;
}

/* ---------- 测验选择列表 ---------- */
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
.course-quiz-retry {
  margin-left: 10px;
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
  max-height: 52vh;
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

/* ---------- 作答概要 ---------- */
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

/* ---------- 作答题目 ---------- */
.course-quiz-question-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px 16px;
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
.course-quiz-option-key {
  font-weight: 700;
  color: #64748b;
  flex-shrink: 0;
}
.course-quiz-option-text {
  flex: 1;
}
.course-quiz-take-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 9px 12px;
  font-size: 13px;
  color: #334155;
  background: #f8fafc;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.course-quiz-take-option:hover {
  border-color: #2563eb;
}
.course-quiz-take-option.is-picked {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1e3a8a;
}
.course-quiz-take-option.is-picked .course-quiz-option-key {
  color: #2563eb;
}

/* ---------- 作答进度 ---------- */
.course-quiz-take-progress {
  flex-shrink: 0;
  min-width: 130px;
  text-align: right;
}
.course-quiz-take-progress-text {
  font-size: 12px;
  color: #64748b;
}
.course-quiz-take-progress-bar {
  margin-top: 6px;
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}
.course-quiz-take-progress-bar span {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: #2563eb;
  transition: width 0.2s ease;
}

/* ---------- 题号导航 ---------- */
.course-quiz-nav-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}
.course-quiz-nav-dot {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
}
.course-quiz-nav-dot:hover {
  border-color: #2563eb;
}
.course-quiz-nav-dot.is-answered {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #2563eb;
}
.course-quiz-nav-dot.is-current {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
}

/* ---------- 底部操作 ---------- */
.course-quiz-take-actions {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.course-quiz-take-nav,
.course-quiz-take-submit-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.course-quiz-take-actions .ghost-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.course-quiz-take-hint {
  font-size: 12px;
}
.course-quiz-take-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
