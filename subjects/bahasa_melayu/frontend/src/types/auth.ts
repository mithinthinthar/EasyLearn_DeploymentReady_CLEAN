export interface LoginResponse {
  user_id: string;
  email: string;
  picture?: string | null;
  name?: string | null;
  role: "student" | "teacher" | "parent";
  student_code?: string | null;
}

export interface AuthUser {
  user_id: string;
  email: string;
  picture?: string | null;
  name?: string | null;
  role: "student" | "teacher" | "parent";
  student_code?: string | null;
}
