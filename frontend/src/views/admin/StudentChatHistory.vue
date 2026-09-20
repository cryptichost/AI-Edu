<template>
  <div class="admin-shell">
    <PageHero
      eyebrow="对话审计"
      title="学生对话记录查询"
      description="按学生与课程维度检索历史对话，查看每次会话的消息明细，便于复盘学生学习过程、定位问题上下文。"
      :badges="heroBadges"
      tone="admin"
    />

    <section class="card-panel chat-filter-panel">
      <div class="section-head">
        <div>
          <h2>查询条件</h2>
          <p class="hero-desc">先选择学生与课程，再按时间和关键词进一步缩小范围。</p>
        </div>
        <div class="chat-filter-actions">
          <el-button type="primary" :loading="loading" @click="handleQuery">查询</el-button>
          <el-button plain :disabled="loading" @click="handleReset">重置</el-button>
        </div>
      </div>

      <div class="admin-filter-grid chat-filter-grid">
        <div class="field">
          <span>学生</span>
          <el-select
            v-model="queryState.studentId"
            placeholder="请选择学生"
            filterable
            clearable
          >
            <el-option
              v-for="student in studentOptions"
              :key="student.id"
              :value="student.id"
              :label="student.label"
            />
          </el-select>
        </div>

        <div class="field">
          <span>课程</span>
          <el-select
            v-model="queryState.courseId"
            placeholder="请选择课程"
            filterable
            clearable
          >
            <el-option
              v-for="course in courseOptions"
              :key="course.id"
              :value="course.id"
              :label="course.label"
            />
          </el-select>
        </div>
      </div>
    </section>

    <section v-if="error" class="info-card error-banner">
      <strong>查询失败</strong>
      <p>{{ error }}</p>
    </section>

    <section v-if="!hasQueried" class="card-panel chat-placeholder">
      <strong>请先选择查询条件</strong>
      <p>选择学生和课程后点击「查询」，即可查看该学生在指定课程下的历史对话记录。</p>
    </section>

    <section v-else-if="loading" class="card-panel chat-placeholder">
      <strong>正在查询...</strong>
      <p>对话记录加载中，请稍候。</p>
    </section>

    <section v-else-if="!sessions.length" class="card-panel chat-placeholder">
      <strong>暂无对话记录</strong>
      <p>当前条件未匹配到任何会话，可尝试放宽时间范围或更换筛选条件。</p>
    </section>

    <section v-else class="stack-list">
      <article v-for="session in sessions" :key="session.id" class="list-card chat-session-card">
        <div class="section-head">
          <div>
            <div class="list-title">{{ session.title || "未命名会话" }}</div>
            <div class="list-meta">
              {{ session.studentName }} · {{ session.courseName }}<template v-if="session.module">
                · {{ getModuleLabel(session.module) }}</template> ·
              {{ formatDateTime(session.startedAt) }} ·
              消息 {{ session.messageCount }}
            </div>
          </div>
          <el-button plain @click="toggleSession(session.id)">
            {{ expandedIds.has(session.id) ? "收起详情" : "展开详情" }}
          </el-button>
        </div>

        <div v-if="expandedIds.has(session.id)" class="chat-message-list">
          <div
            v-for="message in session.messages"
            :key="message.id"
            class="chat-message"
            :class="message.role === 'user' ? 'chat-message--user' : 'chat-message--assistant'"
          >
            <div class="chat-message-head">
              <span class="chat-message-role">{{ message.role === "user" ? "学生" : "AI 助教" }}</span>
              <span class="chat-message-time">{{ formatDateTime(message.time) }}</span>
            </div>
            <pre class="chat-message-content">{{ message.content || "（空消息）" }}</pre>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import PageHero from "../../components/ui/PageHero.vue";
import { fetchAdminStudents, fetchAllCourses, fetchRawChatHistory } from "../../api/admin";
import type {
  AdminStudentRecord,
  RawChatEvent,
  RawChatFunctionCall,
  RawChatFunctionResponse,
} from "../../types/admin";

type TimeRange = "all" | "today" | "week" | "month";

interface OptionRow {
  id: string | number;
  label: string;
}

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  time: string;
}

interface ChatSession {
  id: string;
  title: string;
  studentName: string;
  courseName: string;
  module: string;
  startedAt: string;
  messageCount: number;
  messages: ChatMessage[];
}

const queryState = reactive<{
  studentId: string;
  courseId: string | number;
  timeRange: TimeRange;
  keyword: string;
}>({
  studentId: "",
  courseId: "",
  timeRange: "all",
  keyword: "",
});

// 全部学生原始数据，由后台接口返回。
const students = ref<AdminStudentRecord[]>([]);

// 学生下拉菜单选项，来源于 students。
const studentOptions = ref<OptionRow[]>([]);

const courseOptions = ref<OptionRow[]>([]);

const sessions = ref<ChatSession[]>([]);
const expandedIds = ref(new Set<string>());
const hasQueried = ref(false);
const loading = ref(false);
const error = ref("");

const heroBadges = computed(() => [
  `学生 ${studentOptions.value.length}`,
  `课程 ${courseOptions.value.length}`,
]);

// 将后端返回的原始事件流按 queryState 转换为页面可展示的会话记录。
async function fetchSessions(): Promise<ChatSession[]> {
  const studentId = String(queryState.studentId);
  const courseId = Number(queryState.courseId);

  const events = await fetchRawChatHistory({
    student_id: studentId,
    course_id: courseId,
  });

  const messages = applyLocalFilters(mapEventsToMessages(events));
  if (!messages.length) return [];

  const studentLabel =
    studentOptions.value.find((item) => item.id === Number(studentId))!.label;
  const courseLabel =
    courseOptions.value.find((item) => String(item.id) === String(courseId))?.label ??
    String(courseId);

  return [
    {
      id: `${studentId}-${courseId}`,
      title: `${studentLabel} 的对话记录`,
      studentName: studentLabel,
      courseName: courseLabel,
      module: "",
      startedAt: messages[0]?.time ?? "",
      messageCount: messages.length,
      messages,
    },
  ];
}

/** 将原始事件流转换为消息列表，跳过流式中间态 */
function mapEventsToMessages(events: RawChatEvent[]): ChatMessage[] {
  const messages: ChatMessage[] = [];
  events
    .filter((event) => !event.partial)
    .forEach((event) => {
      const parts = event.content?.parts ?? [];
      parts.forEach((part) => {
        const segments: string[] = [];
        const text = parsePartContent(part.text);
        if (text) segments.push(text);
        if (part.function_call) segments.push(formatFunctionCall(part.function_call));
        if (part.function_response) segments.push(formatFunctionResponse(part.function_response));
        const content = segments.join("\n\n").trim();
        if (!content) return;
        messages.push({
          id: messages.length + 1,
          role: event.author === "user" ? "user" : "assistant",
          content,
          time: toDateString(event.timestamp),
        });
      });
    });
  return messages;
}

/** 将工具调用渲染为可读文本，便于在对话记录中审计。 */
function formatFunctionCall(call: RawChatFunctionCall): string {
  const name = call.name || "未知工具";
  const args = call.args && Object.keys(call.args).length ? stringifyPayload(call.args) : "{}";
  return `[工具调用] ${name}\n${args}`;
}

/** 将工具返回渲染为可读文本，便于在对话记录中审计。 */
function formatFunctionResponse(resp: RawChatFunctionResponse): string {
  const name = resp.name || "未知工具";
  return `[工具返回] ${name}\n${stringifyPayload(resp.response)}`;
}

/** 安全地把任意负载格式化为缩进 JSON 文本。 */
function stringifyPayload(payload: unknown): string {
  if (payload === undefined || payload === null) return "{}";
  try {
    return JSON.stringify(payload, null, 2) ?? String(payload);
  } catch {
    return String(payload);
  }
}

/** 助手消息的 text 可能是 {"content": "..."} 形式的 JSON，需要解包为纯文本。 */
function parsePartContent(text?: string | null): string {
  const raw = (text ?? "").trim();
  if (!raw) return "";
  if (!raw.startsWith("{")) return raw;
  try {
    const parsed = JSON.parse(raw) as { content?: unknown };
    if (typeof parsed.content === "string") return parsed.content;
  } catch {
    // 非 JSON，按纯文本处理
  }
  return raw;
}

function applyLocalFilters(messages: ChatMessage[]): ChatMessage[] {
  const keyword = queryState.keyword.trim().toLowerCase();
  const now = Date.now();
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);

  return messages.filter((message) => {
    const time = message.time ? new Date(message.time).getTime() : 0;
    if (queryState.timeRange === "today" && time < todayStart.getTime()) return false;
    if (queryState.timeRange === "week" && time < now - 7 * 24 * 60 * 60 * 1000) return false;
    if (queryState.timeRange === "month" && time < now - 30 * 24 * 60 * 60 * 1000) return false;
    if (keyword && !message.content.toLowerCase().includes(keyword)) return false;
    return true;
  });
}

/** 兼容秒级与毫秒级时间戳。 */
function toDateString(timestamp?: number) {
  if (!timestamp) return "";
  const ms = timestamp > 1e12 ? timestamp : timestamp * 1000;
  return new Date(ms).toISOString();
}

async function handleQuery() {
  if (!queryState.studentId) {
    error.value = "请先选择学生";
    return;
  }
  if (queryState.courseId === "" || queryState.courseId === null) {
    error.value = "请先选择课程";
    return;
  }

  loading.value = true;
  error.value = "";
  try {
    const rows = await fetchSessions();
    sessions.value = rows;
    expandedIds.value = new Set(rows.map((row) => row.id));
    hasQueried.value = true;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "对话记录查询失败";
  } finally {
    loading.value = false;
  }
}

function handleReset() {
  queryState.studentId = "";
  queryState.courseId = "";
  queryState.timeRange = "all";
  queryState.keyword = "";
  sessions.value = [];
  expandedIds.value = new Set();
  hasQueried.value = false;
  error.value = "";
}

function toggleSession(id: string) {
  const next = new Set(expandedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  expandedIds.value = next;
}

function formatDateTime(value: string) {
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-CN");
}

function getModuleLabel(module: string) {
  const map: Record<string, string> = {
    "AgentModule.edu_agent": "AI 助教",
    "QuizModule.quiz_operations": "测验生成",
    "SummaryModule.summary_generator": "知识总结",
    "LearningPlanModule.learning_plan": "学习计划",
    "frontend.quizpage": "前端测验",
  };
  return map[module] || module || "未知模块";
}

async function getAllStudents() {
  try {
    const rows = await fetchAdminStudents();
    students.value = rows;
    studentOptions.value = rows.map((student) => {
      const name = student.display_name || student.stu_name || student.username;
      return {
        id: student.user_id,
        label: student.username ? `${name}（${student.username}）` : name,
      };
    });
  } catch (err) {
    error.value = err instanceof Error ? err.message : "学生列表加载失败";
  }
}

async function getAllCourses() {
  try {
    const rows = await fetchAllCourses();
    courseOptions.value = rows.map((course) => ({
      id: course.id,
      label: course.name,
    }));
  } catch (err) {
    error.value = err instanceof Error ? err.message : "课程列表加载失败";
  }
}

onMounted(() => {
  void getAllStudents();
  void getAllCourses();
});
</script>

<style scoped>
.chat-filter-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.chat-filter-actions {
  display: flex;
  gap: 10px;
}

.chat-result-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.chat-stat-card strong {
  display: block;
  margin-top: 6px;
  font-size: 20px;
  color: #0f172a;
}

.chat-placeholder {
  text-align: center;
  padding: 36px 20px;
  color: #64748b;
}

.chat-placeholder strong {
  display: block;
  font-size: 16px;
  color: #0f172a;
  margin-bottom: 8px;
}

.chat-session-card .section-head {
  align-items: center;
}

.chat-message-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.chat-message {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 12px 16px;
  background: #f8fbff;
}

.chat-message--user {
  background: #effcf6;
  border-color: #c7ece0;
}

.chat-message-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.chat-message-role {
  font-size: 13px;
  font-weight: 700;
  color: #0f766e;
}

.chat-message-time {
  font-size: 12px;
  color: #94a3b8;
}

.chat-message-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.75;
  color: #334155;
}

@media (max-width: 1024px) {
  .chat-filter-grid,
  .chat-result-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .chat-filter-grid,
  .chat-result-summary {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
