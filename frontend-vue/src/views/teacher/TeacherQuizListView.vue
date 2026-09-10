<template>
  <div class="quiz-shell">
    <!-- 顶部面板：与其他教师页面保持一致的 hero 面板 -->
    <section class="hero-panel app-hero app-hero--teacher">
      <div class="app-hero-copy">
        <p class="eyebrow">测验中心</p>
        <h1>测验列表</h1>
        <p class="hero-desc">
          集中查看本课程下的全部测验，支持按主题快速 AI 生成测验草稿，发布后学生即可参与作答。
        </p>
      </div>
      <div class="app-hero-actions">
        <button class="ghost-btn" type="button" @click="refreshQuizzes">刷新</button>
        <button class="ghost-btn" type="button" @click="openCreateQuiz">新建测验</button>
        <button class="ghost-btn emphasis" type="button" @click="openAiCreateQuiz">AI 一键出题</button>
      </div>
    </section>

    <!-- 错误提示（预留，接入后台后使用） -->
    <section v-if="error" class="card-panel state-card error-state">{{ error }}</section>
    <section v-if="notice" class="card-panel state-card quiz-notice">{{ notice }}</section>

    <!-- 全部测验列表 -->
    <section class="card-panel">
      <div class="section-head">
        <h3>全部测验</h3>
        <span class="muted">共 {{ quizzes.length }} 条</span>
      </div>

      <div class="industry-table-wrap">
        <table class="industry-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>标题</th>
              <th>课程</th>
              <th>状态</th>
              <th>题目数</th>
              <th>总分</th>
              <th>创建时间</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in quizzes" :key="item.id">
              <td class="cell-id">{{ item.id }}</td>
              <td>{{ displayTitle(item) }}</td>
              <td>{{ item.course_name }}</td>
              <td>
                <span :class="['status-chip', statusClass(item.status)]">{{ statusLabel(item.status) }}</span>
              </td>
              <td>{{ item.question_count ?? 0 }}</td>
              <td>{{ item.total_score ?? 0 }}</td>
              <td>{{ formatTime(item.created_at) }}</td>
              <td>{{ formatTime(item.updated_at) }}</td>
              <td class="actions-cell">
                <button class="ghost-btn small" type="button" @click="openQuizDetail(item)">查看</button>
                <button class="ghost-btn small" type="button">结果分析</button>
                <button class="ghost-btn small" type="button">删除</button>
              </td>
            </tr>
            <tr v-if="!quizzes.length">
              <td colspan="9" class="empty-cell">
                <div class="quiz-empty">
                  <span class="quiz-empty-icon">🧪</span>
                  <p>暂无测验</p>
                  <p class="muted">点击右上角「新建测验」或「AI 一键出题」创建测验</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 测验题目详情对话框 -->
    <div v-if="detail.visible" class="modal-mask" @click.self="closeQuizDetail">
      <div class="modal-card quiz-detail-modal">
        <div class="section-head">
          <div>
            <h3>测验详情</h3>
            <p class="muted quiz-detail-sub">{{ detailTitle }}</p>
          </div>
          <div class="quiz-detail-head-actions">
            <button class="ghost-btn emphasis small" type="button" :disabled="detail.loading" @click="openQuestionCreate">新增题目</button>
            <button class="ghost-btn" type="button" @click="closeQuizDetail">关闭</button>
          </div>
        </div>

        <section v-if="detail.loading" class="state-card">题目加载中...</section>
        <section v-else-if="detail.error" class="state-card error-state">
          {{ detail.error }}
          <button class="ghost-btn" type="button" @click="loadQuizDetail">重试</button>
        </section>
        <template v-else>
          <section v-if="!detail.questions.length" class="state-card quiz-detail-empty">
            <p>该测验暂无题目</p>
            <button class="ghost-btn emphasis" type="button" @click="openQuestionCreate">新增第一题</button>
          </section>
          <section v-else class="quiz-question-list">
            <article v-for="(q, index) in detail.questions" :key="q.id" class="quiz-question-card">
              <header class="quiz-question-head">
                <span class="quiz-question-no">第 {{ index + 1 }} 题</span>
                <span class="muted">题型：{{ questionTypeLabel(q) }}</span>
                <span class="muted">分值：{{ q.score }}</span>
                <button class="ghost-btn small quiz-question-edit" type="button" @click="openQuestionEditor(q, index)">编辑</button>
              </header>
              <p class="quiz-question-content">{{ q.content || "（无题干）" }}</p>

              <ul v-if="q.options.length" class="quiz-option-list">
                <li
                  v-for="(opt, optIdx) in q.options"
                  :key="opt.id"
                  :class="['quiz-option', { 'is-correct': opt.is_correct }]"
                >
                  <span class="quiz-option-text">{{ opt.content }}</span>
                  <span v-if="opt.is_correct" class="quiz-option-correct">正确答案</span>
                </li>
              </ul>

              <p v-if="q.analysis" class="quiz-question-analysis">
                <strong>解析：</strong>{{ q.analysis }}
              </p>
            </article>
          </section>
        </template>
      </div>
    </div>

    <!-- 题目编辑/新增对话框 -->
    <div v-if="editor.visible && editor.form" class="modal-mask quiz-edit-mask" @click.self="cancelQuestionEdit">
      <div class="modal-card quiz-edit-modal">
        <div class="section-head">
          <div>
            <h3>{{ editor.isNew ? "新增题目" : "编辑题目" }}</h3>
            <p class="muted quiz-detail-sub">
              {{ editor.isNew ? "将新增到当前测验" : `第 ${editor.questionIndex + 1} 题` }}
            </p>
          </div>
          <button class="ghost-btn" type="button" @click="cancelQuestionEdit">取消</button>
        </div>

        <section v-if="editor.error" class="state-card error-state">{{ editor.error }}</section>

        <div class="quiz-edit-body">
          <label class="quiz-edit-field">
            <span>题型</span>
            <select v-model.number="editor.form.question_type" class="input quiz-edit-control">
              <option v-for="opt in questionTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </label>

          <label class="quiz-edit-field">
            <span>分值</span>
            <input v-model.number="editor.form.score" class="input quiz-edit-control" type="number" min="0" step="1" />
          </label>

          <label class="quiz-edit-field">
            <span>题干</span>
            <textarea v-model="editor.form.content" class="input quiz-edit-control input-textarea" rows="3" placeholder="输入题目内容" />
          </label>

          <div class="quiz-edit-options-head">
            <strong>选项</strong>
            <button class="ghost-btn small" type="button" @click="addOptionRow">+ 添加选项</button>
          </div>

          <div v-if="editor.form.options.length" class="quiz-edit-options">
            <div v-for="(opt, oi) in editor.form.options" :key="opt.uid" class="quiz-edit-option">
              <span class="quiz-edit-option-key">{{ optionLetter(oi) }}</span>
              <label class="quiz-edit-correct">
                <input type="checkbox" v-model="opt.is_correct" />
                正确
              </label>
              <input v-model="opt.content" class="input quiz-edit-option-input" type="text" placeholder="选项内容" />
              <button class="ghost-btn small quiz-edit-option-remove" type="button" @click="removeOptionRow(opt.uid)">删除</button>
            </div>
          </div>
          <p v-else class="muted quiz-edit-options-empty">暂无选项，可点击上方「+ 添加选项」</p>

          <label class="quiz-edit-field">
            <span>解析</span>
            <textarea v-model="editor.form.analysis" class="input quiz-edit-control input-textarea" rows="3" placeholder="答案解析（可选）" />
          </label>
        </div>

        <div class="quiz-edit-footer">
          <button class="ghost-btn emphasis" type="button" :disabled="editor.saving" @click="saveQuestionEdit">
            {{ editor.saving ? "保存中..." : "保存" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import {
  createQuizQuestion,
  fetchAllQuizes,
  fetchQuizQuestions,
  updateQuizQuestion,
  type QuizQuestionSavePayload,
} from "../../api/quiz";
import type { QuizListResponse, QuizQuestionResponse } from "../../types/quiz";

const quizzes = ref<QuizListResponse[]>([]);
const error = ref("");
const notice = ref("");

// 题目编辑表单：单行选项
type EditOptionRow = {
  uid: number;
  id?: number;
  content: string;
  is_correct: boolean;
};

type EditQuestionForm = {
  id: number;
  question_type: number;
  content: string;
  score: number;
  analysis: string;
  options: EditOptionRow[];
};

const editor = reactive<{
  visible: boolean;
  saving: boolean;
  error: string;
  questionIndex: number;
  isNew: boolean;
  form: EditQuestionForm | null;
}>({
  visible: false,
  saving: false,
  error: "",
  questionIndex: 0,
  isNew: false,
  form: null,
});

// 新增选项的本地唯一标识（负值，避免与数据库 id 冲突）
let editOptionUid = -1;

// 测验详情弹窗状态
const detail = reactive<{
  visible: boolean;
  loading: boolean;
  quiz: QuizListResponse | null;
  questions: QuizQuestionResponse[];
  error: string;
}>({
  visible: false,
  loading: false,
  quiz: null,
  questions: [],
  error: "",
});

const detailTitle = computed(() => {
  if (!detail.quiz) return "";
  const parts = [String(detail.quiz.id)];
  if (detail.quiz.title) parts.push(String(detail.quiz.title));
  if (detail.quiz.course_name) parts.push(detail.quiz.course_name);
  return parts.join(" · ");
});

// ================= 展示辅助函数 =================

/** 标题字段在 SQL/模型中是数值列，统一转字符串展示 */
function displayTitle(item: QuizListResponse) {
  return item.course_name === null || item.course_name === undefined || item.course_name === "" ? "-" : String(item.title);
}

function statusLabel(status: number) {
  if (status === 1) return "已发布";
  return "草稿";
}

function statusClass(status: number) {
  if (status === 1) return "chip-published";
  return "chip-draft";
}

function formatTime(value?: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

const QUESTION_TYPE_LABELS: Record<number, string> = {
  1: "单选题",
  2: "多选题",
  3: "判断题",
};

function questionTypeLabel(q: QuizQuestionResponse) {
  const label = QUESTION_TYPE_LABELS[q.question_type];
  if (label) return label;
  if (q.options && q.options.length > 0) return "选择题";
  return `题型 ${q.question_type}`;
}

/** 编辑下拉可选项：已知题型 + 当前题目若为未收录题型的兜底项 */
const questionTypeOptions = computed(() => {
  const entries = Object.entries(QUESTION_TYPE_LABELS).map(([value, label]) => ({
    value: Number(value),
    label,
  }));
  const current = editor.form?.question_type;
  if (typeof current === "number" && current > 0 && !QUESTION_TYPE_LABELS[current]) {
    entries.push({ value: current, label: `题型 ${current}` });
  }
  return entries;
});

/** 选项按字母 A/B/C/D… 编号展示 */
function optionLetter(index: number) {
  return String.fromCharCode(65 + index);
}

// ================= 测验详情（查看按钮） =================

async function openQuizDetail(item: QuizListResponse) {
  detail.quiz = item;
  detail.visible = true;
  detail.error = "";
  detail.questions = [];
  notice.value = "";
  await loadQuizDetail();
}

async function loadQuizDetail() {
  if (!detail.quiz) return;
  detail.loading = true;
  detail.error = "";
  try {
    detail.questions = await fetchQuizQuestions(detail.quiz.id);
  } catch (err) {
    console.error("加载测验题目失败:", err);
    detail.error = "测验题目加载失败，请稍后重试";
  } finally {
    detail.loading = false;
  }
}

function closeQuizDetail() {
  detail.visible = false;
  detail.questions = [];
  detail.error = "";
  detail.quiz = null;
}

// ================= 题目编辑（编辑按钮） =================

function openQuestionEditor(q: QuizQuestionResponse, index: number) {
  editor.isNew = false;
  editor.questionIndex = index;
  editor.error = "";
  editor.form = {
    id: q.id,
    question_type: q.question_type,
    content: q.content ?? "",
    score: q.score,
    analysis: q.analysis ?? "",
    options: (q.options || []).map((o) => ({
      uid: o.id,
      id: o.id,
      content: o.content ?? "",
      is_correct: !!o.is_correct,
    })),
  };
  editor.visible = true;
}

/** 新增题目：打开空表单，保存时追加到测验末尾 */
function openQuestionCreate() {
  if (!detail.quiz) return;
  editor.isNew = true;
  editor.questionIndex = detail.questions.length;
  editor.error = "";
  editor.form = {
    id: 0,
    question_type: 1,
    content: "",
    score: 10,
    analysis: "",
    options: [],
  };
  editor.visible = true;
}

function cancelQuestionEdit() {
  if (editor.saving) return;
  editor.visible = false;
  editor.form = null;
  editor.error = "";
}

function addOptionRow() {
  if (!editor.form) return;
  editor.form.options.push({ uid: editOptionUid--, content: "", is_correct: false });
}

function removeOptionRow(uid: number) {
  if (!editor.form || editor.saving) return;
  const idx = editor.form.options.findIndex((o) => o.uid === uid);
  if (idx !== -1) editor.form.options.splice(idx, 1);
}

async function saveQuestionEdit() {
  if (!editor.form || editor.saving) return;
  const form = editor.form;
  editor.error = "";

  const content = (form.content || "").trim();
  if (!content) {
    editor.error = "请填写题干内容";
    return;
  }
  if (typeof form.score !== "number" || Number.isNaN(form.score) || form.score < 0) {
    editor.error = "分值需为非负数字";
    return;
  }
  for (const opt of form.options) {
    if (!(opt.content || "").trim()) {
      editor.error = "存在空白选项内容，请填写或删除该选项";
      return;
    }
  }

  const payload: QuizQuestionSavePayload = {
    question_type: form.question_type,
    content,
    score: form.score,
    analysis: (form.analysis || "").trim(),
    options: form.options.map((o) => ({
      ...(o.id ? { id: o.id } : {}),
      content: (o.content || "").trim(),
      is_correct: o.is_correct,
    })),
  };

  editor.saving = true;
  try {
    if (editor.isNew) {
      // —— 新增题目 ——
      if (!detail.quiz) {
        throw new Error("测验信息缺失，无法新增题目");
      }
      const created = await createQuizQuestion(detail.quiz.id, payload);
      detail.questions.push(created);
      // 同步测验聚合字段（detail.quiz 与列表行同一对象引用）
      detail.quiz.question_count = (detail.quiz.question_count ?? 0) + 1;
      detail.quiz.total_score = (detail.quiz.total_score ?? 0) + (created.score || 0);
      notice.value = `已新增题目（共 ${detail.questions.length} 题）`;
    } else {
      // —— 编辑已有题目 ——
      const updated = await updateQuizQuestion(form.id, payload);
      const target = detail.questions.findIndex((item) => item.id === updated.id);
      if (target !== -1) {
        detail.questions[target] = updated;
      } else {
        // 兜底：题目列表与后端不同步时整体刷新
        await loadQuizDetail();
      }
      notice.value = `题目已保存（第 ${editor.questionIndex + 1} 题）`;
    }
    editor.visible = false;
    editor.form = null;
    editor.error = "";
  } catch (err) {
    console.error("保存题目失败:", err);
    editor.error = err instanceof Error ? err.message : "题目保存失败，请稍后重试";
  } finally {
    editor.saving = false;
  }
}

// ================ 删除测验 ================

function removeQuiz(quiz_id:string) {
  
}

// ================= 操作占位（后续接入后台逻辑） =================

async function refreshQuizzes() {
  notice.value = "";
  quizzes.value = await fetchAllQuizes();
}

function openAiCreateQuiz() {
  // TODO: 打开「AI 一键出题」弹窗
}

onMounted(()=>{
    void refreshQuizzes();
})
</script>

<style scoped>
.quiz-shell {
  display: grid;
  gap: 16px;
}

/* 强调按钮：主操作（AI 一键出题） */
.ghost-btn.emphasis {
  border-color: #2563eb;
  color: #1d4ed8;
  background: linear-gradient(135deg, #eff4ff, #e8f0ff);
  font-weight: 700;
}

/* 表格内小按钮 */
.ghost-btn.small {
  padding: 4px 10px;
}

.actions-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 空状态提示 */
.empty-cell {
  padding: 32px 12px !important;
}

.quiz-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
}

.quiz-empty-icon {
  font-size: 36px;
  line-height: 1;
}

.quiz-empty p {
  margin: 0;
}

/* ID 列弱化 */
.cell-id {
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

/* 状态标签 */
.status-chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.status-chip.chip-draft {
  color: #64748b;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
}

.status-chip.chip-published {
  color: #1d4ed8;
  background: #e8f0ff;
  border: 1px solid #bfd2f6;
}

.status-chip.chip-closed {
  color: #7c3aed;
  background: #f3e8ff;
  border: 1px solid #e9d5ff;
}

/* ================= 测验详情弹窗 ================= */
.modal-mask {
  position: fixed;
  z-index: 99;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.modal-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
}

.quiz-detail-modal {
  width: min(760px, 92vw);
  max-height: 82vh;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.quiz-detail-sub {
  margin-top: 2px;
  font-size: 13px;
}

.quiz-detail-head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: none;
}

.quiz-detail-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
}

.quiz-detail-empty p {
  margin: 0;
}

.ghost-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.quiz-question-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  padding-right: 4px;
}

.quiz-question-card {
  border: 1px solid #dbe4f0;
  border-radius: 10px;
  padding: 14px 16px;
  background: #f8fbff;
}

.quiz-question-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 14px;
  margin-bottom: 8px;
}

.quiz-question-no {
  font-weight: 700;
  color: #1d4ed8;
}

.quiz-question-content {
  margin: 0 0 10px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.quiz-option-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.quiz-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border: 1px solid #dbe4f0;
  border-radius: 8px;
  background: #fff;
  font-size: 14px;
}

.quiz-option.is-correct {
  border-color: #16a34a;
  background: #f0fdf4;
}

.quiz-option-key {
  flex: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #e8f0ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.quiz-option.is-correct .quiz-option-key {
  background: #16a34a;
  color: #fff;
}

.quiz-option-text {
  flex: 1;
  word-break: break-word;
}

.quiz-option-correct {
  flex: none;
  font-size: 12px;
  font-weight: 700;
  color: #16a34a;
  white-space: nowrap;
}

.quiz-question-analysis {
  margin: 10px 0 0;
  padding: 8px 10px;
  border-left: 3px solid #2563eb;
  background: #eff4ff;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

/* ================= 题目编辑对话框 ================= */
.quiz-edit-mask {
  z-index: 120;
}

.quiz-edit-modal {
  width: min(680px, 92vw);
  max-height: 86vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.quiz-question-edit {
  margin-left: auto;
}

.quiz-edit-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.quiz-edit-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.quiz-edit-control,
.quiz-edit-option-input {
  width: 100%;
  border: 1px solid #d0d7de;
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
  color: #0f172a;
  font-size: 14px;
  font-weight: 400;
  transition: border-color 0.2s ease;
}

.quiz-edit-control:focus,
.quiz-edit-option-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.input-textarea {
  resize: vertical;
}

.quiz-edit-options-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: #334155;
}

.quiz-edit-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quiz-edit-options-empty {
  margin: 0;
}

.quiz-edit-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quiz-edit-option-key {
  flex: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #e8f0ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.quiz-edit-correct {
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #16a34a;
  white-space: nowrap;
  cursor: pointer;
}

.quiz-edit-correct input {
  accent-color: #16a34a;
  cursor: pointer;
}

.quiz-edit-option-input {
  flex: 1;
}

.quiz-edit-option-remove {
  flex: none;
}

.quiz-edit-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 4px;
}

.quiz-notice {
  color: #065f46;
  background: #ecfdf5;
  border-color: #a7f3d0;
}

@media (max-width: 900px) {
  .app-hero-actions {
    justify-content: flex-start;
    width: 100%;
  }
}
</style>
