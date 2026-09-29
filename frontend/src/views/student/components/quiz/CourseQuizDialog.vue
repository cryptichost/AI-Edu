<template>
  <div class="course-quiz-dialog">
    <!-- ============ 测验列表 + 作答（独立组件） ============ -->
    <CourseQuizTakePanel
      v-if="taking"
      :course-id="courseId"
      :student-id="props.studentId"
      :course-name="props.courseName"
      @close="closeTakePanel"
      @started="handleQuizStarted"
      @finished="handleQuizFinished"
    />

    <!-- ============ 记录列表视图 ============ -->
    <template v-else-if="view === 'list'">
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
        <button
          type="button"
          class="primary-link button-like course-quiz-start-cta"
          @click="openTakePanel"
        >
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
          <span v-if="!quizListLoading && !quizListError" class="muted">共 {{ mergedRecords.length }} 条</span>
        </div>

        <div v-if="quizListLoading" class="state-card">正在加载测验记录...</div>

        <div v-else>
          <div v-if="quizListError" class="state-card error-state">
            {{ quizListError }}
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
                  <span
                    v-if="item.badgeText"
                    class="course-quiz-record-badge"
                    :class="{ 'is-pending': item.pending }"
                  >{{ item.badgeText }}</span>
                </div>
                <div class="course-quiz-record-meta muted">
                  {{ item.timeText }}
                </div>
              </div>
              <span class="course-quiz-record-arrow">›</span>
            </button>
          </div>

          <div v-else-if="!quizListError" class="course-quiz-empty">
            <div class="course-quiz-empty-icon">🧪</div>
            <p>还没有测验记录</p>
            <p class="muted">点击上方「开始测验」，进入测验后即会生成记录</p>
          </div>
        </div>
      </div>
    </template>

    <!-- ============ 作答详情视图（独立组件） ============ -->
    <CourseQuizDetailPanel
      v-else-if="view === 'detail'"
      :record-id="detailRecordId"
      :initial-detail="detailInitialDetail"
      @close="closeDetail"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import CourseQuizTakePanel from "./CourseQuizTakePanel.vue";
import CourseQuizDetailPanel from "./CourseQuizDetailPanel.vue";
import { fetchQuizRecordDetail, fetchQuizRecordsByUser } from "../../../../api/quiz.js";
import type { QuizRecordDetailResponse, QuizRecordResponse } from "../../../../types/quiz.js";
import { formatTime, serverItemTitle } from "./courseQuizShared";
import { getCourseIdByName } from "../../../../api/client.js";
import type { QuizRecordItem } from "../../../../types/quiz.js";

const props = defineProps<{
  studentId?: string;
  courseName?: string;
}>();

const courseId = ref<number|undefined>();

/* ---------------- 视图状态 ---------------- */
const view = ref<"list" | "detail">("list");
/** 是否正在展示「测验列表 + 作答」独立面板。 */
const taking = ref(false);

/* ----- 记录列表 ----- */
const quizListLoading = ref(false);
const quizListError = ref("");
const quizRecords = ref<QuizRecordResponse[]>([]);
const quizRecordsCache = new Map<number, QuizRecordDetailResponse>();

const numericUserId = computed(() => {
  const value = (props.studentId ?? "").trim();
  return /^\d+$/.test(value) ? value : "";
});


function normalizeName(value?: string | null): string {
  return (value ?? "").trim();
}

/* 从服务端加载一个知识点的测验信息 */
async function loadServerRecords() {
  if (!numericUserId.value) return;
  try {
    // 课程过滤在本地按课程名完成（quiz.course_id 存的是知识点 id，不是课程 id）。
    const records = await fetchQuizRecordsByUser(Number(numericUserId.value), Number(courseId.value));
    quizRecords.value = Array.isArray(records) ? records : [];
  } catch (error) {
    quizListError.value =
      error instanceof Error
        ? `服务端记录加载失败：${error.message}`
        : "服务端记录加载失败，请稍后重试";
  }
}

/* 将单次加载的测验合并到缓存中 */
async function expandServerDetails() {
  for (const item of quizRecords.value) {
    if (quizRecordsCache.has(item.id)) continue;
    try {
      const detail = await fetchQuizRecordDetail(item.id);
      quizRecordsCache.set(item.id, detail);
    } catch {
      /* 单条详情失败不影响其余记录 */
    }
  }
}

/* ----- 全部已加载的测验记录列表（全部来自后台，submit_at 为空即进行中） ----- */
const mergedRecords = computed<QuizRecordItem[]>(() => {

  const items = quizRecords.value
    .map((record) => {
      const detail = quizRecordsCache.get(record.id);
      const pending = !record.submit_at;
      const happenedAt = record.submit_at ?? record.start_at ?? undefined;
      return {
        key: `server:${record.id}`,
        recordId: record.id,
        title: detail ? serverItemTitle(detail, record.id) : `测验记录 #${record.id}`,
        timeText: `${pending ? "开始于" : "完成于"} ${formatTime(happenedAt)}`,
        submittedAt: happenedAt ?? undefined,
        badgeText: pending ? "进行中" : "已提交",
        pending,
        detail,
      };
    });

  return items.sort((a, b) => {
    const timeA = a.submittedAt ? new Date(a.submittedAt).getTime() : 0;
    const timeB = b.submittedAt ? new Date(b.submittedAt).getTime() : 0;
    return timeB - timeA;
  });
});

async function reload() {
  quizListError.value = "";
  quizListLoading.value = true;
  try {
    // 顺序执行：详情里的 course_name 用于按课程过滤记录，必须先拿到。
    await loadServerRecords();
    await expandServerDetails();
  } finally {
    quizListLoading.value = false;
  }
}

/* ----- 作答详情（展示交给 CourseQuizDetailPanel） ----- */
/** 当前正在查看的记录 id；为 null 表示未打开详情。 */
const detailRecordId = ref<number | null>(null);
/** 复用记录列表已缓存的详情，避免打开详情时重复请求。 */
const detailInitialDetail = computed(() =>
  detailRecordId.value != null ? quizRecordsCache.get(detailRecordId.value) : undefined
);

function openRecord(item: QuizRecordItem) {
  detailRecordId.value = item.recordId;
  view.value = "detail";
}

function closeDetail() {
  view.value = "list";
  detailRecordId.value = null;
}

/* ----- 测验列表 + 作答面板 ----- */
/** 打开独立的「测验列表 + 作答」面板。 */
function openTakePanel() {
  if(courseId.value){
    taking.value = true;
  }
}

function closeTakePanel() {
  taking.value = false;
}

/** 进入测验：后台已生成一条「进行中」记录，刷新列表即可看到。 */
async function handleQuizStarted(recordId: number) {
  await reload();
  if (!quizRecords.value.some((record) => record.id === recordId)) {
    // 兜底：列表接口未按预期返回时，至少把这条记录补进列表。
    quizRecords.value = [{ id: recordId, user_id: Number(numericUserId.value) || null }, ...quizRecords.value];
    void expandServerDetails();
  }
}

/** 提交测验：记录已写入提交时间，刷新列表并打开该条记录的详情。 */
async function handleQuizFinished(recordId: number) {
  taking.value = false;
  await reload();
  const finished = mergedRecords.value.find((item) => item.recordId === recordId);
  if (finished) {
    openRecord(finished);
    return;
  }
  // 列表里暂时找不到时，直接按记录 id 打开详情。
  openRecord({
    key: `server:${recordId}`,
    recordId,
    title: `测验记录 #${recordId}`,
    timeText: "",
    badgeText: "已提交",
    pending: false,
  });
}

async function getCourseId() {
  if(props.courseName){
   courseId.value = await getCourseIdByName(props.courseName);
  }
}

/* ----- 生命周期 ----- */
watch(
  () => [props.studentId, props.courseName],
  () => {
    void getCourseId();
    quizRecordsCache.clear();
  }
);

watch(
 courseId,
  () => {
    void reload();
  }
);
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
/* 进行中的记录：用暖色区分，提示尚未提交 */
.course-quiz-record-badge.is-pending {
  color: #b45309;
  background: #fffbeb;
  border-color: #fde68a;
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
</style>