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