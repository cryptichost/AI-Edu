export interface QuizListResponse {
    id: number;
    title: string;
    course_name: string;
    question_count: number;
    status: number;
    total_score: number;
    created_at?: string;
    updated_at?: string;
}

export interface QuizQuestionResponse {
    id: number;
    question_type: number;
    content?: string;
    score: number;
    analysis?: string;
    created_at?: string;
    updated_at?: string;
    options: QuizOptionResponse[];
}

export interface QuizOptionResponse {
    id: number;
    content: string;
    is_correct: boolean;
    created_at?: string;
    updated_at?: string;
}

/** 学生作答用题目：不含正确答案与解析。 */
export interface QuizTakeQuestionResponse {
    id: number;
    question_type: number;
    content?: string;
    score: number;
    options: QuizTakeOptionResponse[];
}

/** 学生作答用选项：不含 is_correct。 */
export interface QuizTakeOptionResponse {
    id: number;
    content: string;
}

export interface QuizOptionRequest {
    id: number;
    content: string;
    is_correct: boolean;
    created_at?: string;
    updated_at?: string;
    options: QuizQuestionRequest[];
}

export interface QuizQuestionRequest {
    id: number;
    question_type: number;
    content?: string;
    score: number;
    analysis?: string;
    created_at?: string;
    updated_at?: string;
}

/** 作答记录列表项（POST /api/quiz/records/user、/records/start、/records/{id}/submit）。 */
export interface QuizRecordResponse {
    id: number;
    quiz_id?: number | null;
    user_id?: number | null;
    /** 进入测验时间。 */
    start_at?: string | null;
    /** 提交时间；为空表示「进行中」（已进入但未提交）。 */
    submit_at?: string | null;
}

/** 作答记录本身的信息。 */
export interface QuizRecordInfo {
    id: number;
    quiz_id?: number | null;
    user_id?: number | null;
    start_at?: string | null;
    submit_at?: string | null;
}

/** 作答记录关联的测验信息。 */
export interface QuizDetailInfo {
    id: number;
    title?: number | string | null;
    question_count?: number | null;
    course_id?: number | string | null;
    /** 测验所属课程/知识点名称（由后台关联 course_nodes 得到）。 */
    course_name?: string | null;
    status?: number | null;
    total_score?: number | null;
    created_at?: string | null;
    updated_at?: string | null;
}

/** 作答详情中的选项。 */
export interface QuizOptionDetail {
    id: number;
    question_id?: number;
    content: string;
    is_correct: number | boolean;
    created_at?: string | null;
    updated_at?: string | null;
}

/** 作答详情中的作答记录。 */
export interface QuizAnswerDetail {
    id: number;
    question_id?: number;
    user_answer: string | number | null;
    is_correct: number | boolean;
    created_at?: string | null;
    updated_at?: string | null;
}

/** 作答详情中的题目（含选项与作答）。 */
export interface QuizQuestionDetail {
    id: number;
    quiz_id?: number | null;
    question_type?: string | number | null;
    content?: string | null;
    score?: number | null;
    analysis?: string | null;
    created_at?: string | null;
    updated_at?: string | null;
    options: QuizOptionDetail[];
    answers: QuizAnswerDetail[];
}

/** 作答详情响应（GET /api/quiz/records/{record_id}）。 */
export interface QuizRecordDetailResponse {
    record: QuizRecordInfo;
    quiz: QuizDetailInfo | null;
    questions: QuizQuestionDetail[];
}

/** 从题目文本中解析出的选项。 */
export interface ParsedOption {
  key: string;
  text: string;
}

/** 作答过程中的题目模型（不含正确答案）。 */
export interface TakeQuestion {
  key: string;
  raw: string;
  stem: string;
  options: ParsedOption[];
}

export interface QuizRecordItem {
  key: string;
  recordId: number;
  title: string;
  /** 时间描述：进行中显示「开始于」，已提交显示「完成于」。 */
  timeText: string;
  submittedAt?: string;
  /** 记录角标文案（「进行中」「已提交」）。 */
  badgeText: string;
  /** 是否为「进行中」的记录（已进入测验但尚未提交）。 */
  pending: boolean;
  detail?: QuizRecordDetailResponse;
}

export interface QuizDetailModel {
  title: string;
  submitText: string;
  /** 后台未保存作答明细时的说明文案。 */
  note?: string;
  questions: QuizDetailQuestionModel[];
}

export interface QuizDetailQuestionModel {
  key: string;
  stem: string;
  /** right/wrong 为服务端已判分结果；done 为已作答但未判分；skip 为未作答。 */
  state: "right" | "wrong" | "done" | "skip";
  stateText: string;
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