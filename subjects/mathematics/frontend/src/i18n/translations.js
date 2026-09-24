// frontend/src/i18n/translations.js
export const translations = {
  english: {
    // Header
    header_home: "Home",
    header_quick_snap: "Quick Snap",
    header_practice: "Practice",
    header_logout: "Logout",

    // Header pop-up
    header_student_id: "Student ID",
    header_language: "Language",
    header_language_english: "English",
    header_language_bm: "Bahasa Melayu",
    header_saving: "Saving...",
    header_student_id_tooltip:
      "This student ID is used by parents to connect their account with the student's account.",
    header_logout_title: "Confirm logout?",
    header_logout_desc: "You will be signed out from your current session.",
    header_logout_cancel: "Cancel",
    header_logout_confirm: "Logout",

    // Student Dashboard
    dashboard_hello: "Hello",
    dashboard_subtitle:
      "Let’s continue improving your SPM Mathematics performance today! Here is your performance overview.",
    dashboard_predicted_grade: "SPM Predicted Grade",
    dashboard_updated_now: "Updated: Just now",
    dashboard_practice_accuracy: "Correct Attempt Rate",
    dashboard_study_pattern: "Study Pattern Insight",
    dashboard_proof: "Proof",
    dashboard_ai_suggestion: "AI Suggestion",
    dashboard_total_study_time: "Total Study Time",
    dashboard_topic_mastery: "Topic Mastery",
    dashboard_mastered: "Mastered",
    dashboard_average: "Average",
    dashboard_review: "Review",
    dashboard_topics: "Topics",
    dashboard_no_data: "No data yet.",
    dashboard_grade_trend: "Grade Progression Trend",
    dashboard_grade_trend_desc:
      "Tracks how your AI-predicted SPM grade has changed over your last 10 practice sessions.",
    dashboard_topic_recommendations: "Topic Recommendations",
    dashboard_high_priority: "High Priority",
    dashboard_secondary_review: "Secondary Review",
    dashboard_reason: "Reason",
    dashboard_practice_now: "Practice Now",
    dashboard_analyzing: "Analyzing your study patterns...",

    // New Dashboard
    dashboard_confidence_short: "Confidence",
    dashboard_total_questions_attempted: "Questions Attempted",
    dashboard_paper1_short: "Paper 1",
    dashboard_paper2_short: "Paper 2",
    dashboard_live_accuracy: "Live Accuracy",

    dashboard_ai_performance_overview: "AI Performance Overview",
    dashboard_refresh: "Refresh",
    dashboard_recent_performance_trend: "Recent Performance Trend",
    dashboard_live_trend: "Live Trend",
    dashboard_trend_improving: "Improving recently",
    dashboard_trend_declining: "Dropping recently",
    dashboard_trend_stable: "Stable recently",
    dashboard_strength: "Strength",
    dashboard_concern: "Concern",
    dashboard_ai_feedback_summary: "Feedback Summary",

    dashboard_study_planner_consistency: "Study Planner & Consistency",
    dashboard_practice_this_session: "Practice This Session",
    dashboard_study_consistency: "Study Consistency",
    dashboard_current_streak: "Current streak",
    dashboard_best_streak: "Best streak",
    dashboard_days: "days",
    dashboard_next_reminder: "Next reminder",
    dashboard_on_track: "On track this week",
    dashboard_sessions_remaining: "{count} remaining this week",
    dashboard_sessions: "sessions",

    dashboard_study_insights_schedule:
      "Study Insights & Personalized Schedule",
    dashboard_consistency_heatmap: "Consistency Heatmap",
    dashboard_consistency_across_year: "Consistency Across the Year",
    dashboard_consistency_subtitle:
      "How consistently you spent time learning in the system",
    dashboard_active_days: "active days",
    dashboard_best_day: "Best day",
    dashboard_best_study_time_window: "Best study time window",
    dashboard_personalized_study_schedule:
      "Personalized Study Schedule",
    dashboard_recommended_session_length:
      "Recommended Session Length",
    dashboard_weekly_target: "Weekly Target",
    dashboard_weekly_target_progress: "Weekly Target Progress",
    dashboard_sessions_done: "sessions done",
    dashboard_next_suggested_session: "Next Suggested Session",

  dashboard_trend_no_data: "No trend data yet",
  dashboard_trend_need_more_days: "Need another practice day",
  dashboard_trend_placeholder_no_data_title: "No trend data yet",
  dashboard_trend_placeholder_no_data_desc:
    "Start practising so EasyLearn can track your daily performance.",
  dashboard_trend_placeholder_one_day_title:
    "Trend will appear after your next practice day",
  dashboard_trend_placeholder_one_day_desc:
    "You already have practice records for today. Practise on another day to see how your performance changes over time.",
    
    // Quick Snap
    quicksnap_title: "Quick Snap",
    quicksnap_subtitle:
      "Choose a mode, upload one image, and get fast visual Mathematics support.",
    quicksnap_tab_solve: "Solve Question",
    quicksnap_tab_check: "Check My Work",
    quicksnap_drag_title: "Drag & drop an image here",
    quicksnap_drag_subtitle: "Supports JPG or PNG",
    quicksnap_browse: "Browse Files",
    quicksnap_take_photo: "Take Photo",
    quicksnap_remove: "Remove",
    quicksnap_processing: "Processing...",
    quicksnap_solve_now: "Solve Now",
    quicksnap_check_now: "Check Now",
    quicksnap_detected_question: "AI DETECTED QUESTION",
    quicksnap_solution_title: "Step-by-Step Solution",
    quicksnap_checking_title: "Checking Feedback",
    quicksnap_final_answer: "FINAL ANSWER",
    quicksnap_score: "Score",
    quicksnap_correctness_summary: "Correctness Summary",
    quicksnap_strengths: "Strengths",
    quicksnap_improvements: "Areas to Improve",
    quicksnap_continue_chat: "Ask Follow-Up in Tutor Chat",
    quicksnap_continue_chat_phase6:
      "Chatbot handoff will be added in later.",
    quicksnap_prompt_solve: "Upload an image of a Math question.",
    quicksnap_prompt_check:
      "Upload image containing question + your working.",
    quicksnap_error_title: "Unable to process",
    quicksnap_no_result: "No result yet.",

    // Practice Page
    practice_title: "Practice Center",
    practice_subtitle:
      "Select a form and chapter to begin your targeted SPM practice.",
    practice_preferred_language: "Preferred Question Language",
    practice_form4: "Form 4",
    practice_form5: "Form 5",
    practice_paper1: "Paper 1",
    practice_paper2: "Paper 2",

    // Chatbot
    chatbot_title: "AI Math Tutor",
    chatbot_online: "Online",
    chatbot_history: "Chat History",
    chatbot_new_chat: "New Chat",
    chatbot_history_title: "Your Chat History",
    chatbot_select_language:
      "Hello! Please select your preferred language",
    chatbot_placeholder: "Ask EasyLearn anything...",
    chatbot_thinking: "AI is thinking...",
    chatbot_error:
      "Sorry, I am having trouble connecting to the server. Please make sure your Flask backend is running!",
    chatbot_welcome:
      "I am your AI Math Tutor. You can now ask any SPM Mathematics question.",
    chatbot_fab_tooltip: "Ask AI Tutor!",
    chatbot_history_empty: "No chat history yet.",
    chatbot_history_hint: "Start a new conversation to begin asking questions.",
    chatbot_history_loading: "Loading...",
    chatbot_edit_title: "Edit title",
    chatbot_delete_chat: "Delete chat",
    chatbot_edit_title_prompt: "Enter a new chat title:",
    chatbot_delete_confirm: "Are you sure you want to hide this chat from your history?",
    chatbot_delete_error: "Failed to delete chat.",
    chatbot_update_title_error: "Failed to update title.",
    chatbot_delete_confirm_title: "Delete this chat?",
    chatbot_delete_confirm_body:
      "This chat will be deleted permanently from the your chat history.",
    chatbot_cancel: "Cancel",
    chatbot_confirm: "Confirm",
    chatbot_save: "Save",
    chatbot_thinking_label: "AI is thinking",
    chatbot_typing_label: "AI is replying",

    // Full Page Chatbot
    chatbot_open_full_page: "Open full chatbot page",
    chatbot_expand_busy: "Please wait until the AI finishes replying.",
    chatbot_fullpage_subtitle:
      "Continue longer conversations, review history, and manage your chats.",
    chatbot_mobile_history_tab: "History",
    chatbot_mobile_chat_tab: "Chat",

    // Parent Home
    parent_home_title: "Parent Home",
    parent_home_subtitle:
      "Monitor your child’s progress and manage linked student accounts.",
    parent_welcome_back: "Welcome back",
    parent_manage_text: "Add or manage your child accounts easily.",
    parent_total_linked_children: "Total Linked Children",
    parent_link_child_title: "Link Child Account",
    parent_student_code: "Student Code",
    parent_nickname_optional: "Nickname (Optional)",
    parent_link_child_button: "Link Child",
    parent_linked_children_title: "Linked Children",
    parent_no_children: "No linked children yet.",
    parent_unlink: "Unlink",
    parent_view_dashboard: "Dashboard",
    parent_student_id: "Student ID",
    parent_linked_on: "Linked on",

    parent_toast_success_title: "Success",
    parent_toast_error_title: "Something went wrong",
    parent_toast_enter_student_code: "Please enter a student code.",
    parent_toast_load_children_failed:
      "Failed to load linked children.",
    parent_toast_link_success: "Child linked successfully.",
    parent_toast_link_failed: "Failed to link child.",
    parent_toast_unlink_success: "Child unlinked successfully.",
    parent_toast_unlink_failed: "Failed to unlink child.",
    parent_unlink_dialog_title: "Confirm unlink?",
    parent_unlink_dialog_desc:
      "Are you sure you want to unlink {name}? You can link this child again later using the student code.",
    parent_unlink_dialog_desc_fallback:
      "Are you sure you want to unlink this child?",
    parent_unlink_dialog_cancel: "Cancel",
    parent_unlink_dialog_confirm: "Unlink",

    // Parent Child Dashboard
    parent_child_dashboard_back_to_children: "Back to Parent Home",
    parent_child_dashboard_subtitle:
      "Parent view of this child’s learning performance, study pattern, and recommended revision focus.",
    parent_child_dashboard_read_only: "Read Only",
    parent_child_dashboard_total_questions:
      "Total Questions Attempted",
    parent_child_dashboard_load_failed:
      "Failed to load child dashboard.",
    parent_child_dashboard_child: "Child",

    parent_child_dashboard_refresh_tooltip: "Refresh dashboard",
    parent_child_dashboard_refreshing: "Refreshing...",

    parent_dashboard_grade_trend_desc:
      "Tracks how this child’s AI-predicted SPM grade has changed over recent practice sessions.",
    parent_dashboard_consistency_subtitle:
      "This child’s learning activity across the year",
    parent_dashboard_study_insights_schedule:
      "Study Insights & Personalized Schedule",
    parent_dashboard_personalized_study_schedule:
      "Personalized Study Schedule",
    parent_dashboard_study_schedule_subtitle:
      "Suggested study timing and weekly learning consistency for this child.",
    parent_dashboard_ai_overview_subtitle:
      "A parent-friendly summary of this child’s learning performance.",
  },

  bm: {
    // Header
    header_home: "Laman Utama",
    header_quick_snap: "Snap Pantas",
    header_practice: "Latihan",
    header_logout: "Log Keluar",

    // Header pop-up
    header_student_id: "ID Pelajar",
    header_language: "Bahasa",
    header_language_english: "Bahasa Inggeris",
    header_language_bm: "Bahasa Melayu",
    header_saving: "Menyimpan...",
    header_student_id_tooltip:
      "ID pelajar ini digunakan oleh ibu bapa untuk menghubungkan akaun mereka dengan akaun pelajar.",
    header_logout_title: "Sahkan log keluar?",
    header_logout_desc:
      "Anda akan log keluar daripada sesi semasa anda.",
    header_logout_cancel: "Batal",
    header_logout_confirm: "Log Keluar",

    // Student Dashboard
    dashboard_hello: "Hai",
    dashboard_subtitle:
      "Mari terus tingkatkan prestasi Matematik SPM anda hari ini! Berikut ialah gambaran prestasi anda.",
    dashboard_predicted_grade: "Gred Ramalan SPM",
    dashboard_updated_now: "Dikemas kini: Baru sahaja",
    dashboard_practice_accuracy: "Kadar Jawapan Betul",
    dashboard_study_pattern: "Corak Pembelajaran",
    dashboard_proof: "Bukti",
    dashboard_ai_suggestion: "Cadangan",
    dashboard_total_study_time: "Jumlah Masa Belajar",
    dashboard_topic_mastery: "Penguasaan Topik",
    dashboard_mastered: "Dikuasai",
    dashboard_average: "Sederhana",
    dashboard_review: "Perlu Ulang Kaji",
    dashboard_topics: "Topik",
    dashboard_no_data: "Belum ada data.",
    dashboard_grade_trend: "Trend Perkembangan Gred",
    dashboard_grade_trend_desc:
      "Menunjukkan perubahan gred ramalan SPM AI anda berdasarkan 10 sesi latihan terakhir.",
    dashboard_topic_recommendations: "Cadangan Topik",
    dashboard_high_priority: "Keutamaan Tinggi",
    dashboard_secondary_review: "Semakan Kedua",
    dashboard_reason: "Sebab",
    dashboard_practice_now: "Latih Sekarang",
    dashboard_analyzing:
      "Sedang menganalisis corak pembelajaran anda...",

    // New Dashboard
    dashboard_confidence_short: "Keyakinan",
    dashboard_total_questions_attempted: "Jumlah Soalan Dijawab",
    dashboard_paper1_short: "Kertas 1",
    dashboard_paper2_short: "Kertas 2",
    dashboard_live_accuracy: "Ketepatan Semasa",

    dashboard_ai_performance_overview: "Gambaran Prestasi AI",
    dashboard_refresh: "Muat Semula",
    dashboard_recent_performance_trend: "Trend Prestasi Terkini",
    dashboard_live_trend: "Trend Semasa",
    dashboard_trend_improving: "Semakin baik",
    dashboard_trend_declining: "Menurun baru-baru ini",
    dashboard_trend_stable: "Stabil baru-baru ini",
    dashboard_strength: "Kekuatan",
    dashboard_concern: "Kebimbangan",
    dashboard_ai_feedback_summary: "Rumusan Maklum Balas AI",

    dashboard_study_planner_consistency:
      "Pelan Belajar & Konsistensi",
    dashboard_practice_this_session: "Berlatih Sesi Ini",
    dashboard_study_consistency: "Konsistensi Belajar",
    dashboard_current_streak: "Streak semasa",
    dashboard_best_streak: "Streak terbaik",
    dashboard_days: "hari",
    dashboard_next_reminder: "Peringatan seterusnya",
    dashboard_on_track: "Minggu ini di landasan",
    dashboard_sessions_remaining: "{count} lagi minggu ini",
    dashboard_sessions: "sesi",

    dashboard_study_insights_schedule:
      "Cerapan Pembelajaran & Jadual Peribadi",
    dashboard_consistency_heatmap: "Peta Haba Konsistensi",
    dashboard_consistency_across_year:
      "Konsistensi Sepanjang Tahun",
    dashboard_consistency_subtitle:
      "Sejauh mana anda konsisten meluangkan masa belajar dalam sistem",
    dashboard_active_days: "hari aktif",
    dashboard_best_day: "Hari terbaik",
    dashboard_best_study_time_window: "Waktu belajar terbaik",
    dashboard_personalized_study_schedule:
      "Jadual Belajar Peribadi",
    dashboard_recommended_session_length:
      "Tempoh Sesi Disyorkan",
    dashboard_weekly_target: "Sasaran Mingguan",
    dashboard_weekly_target_progress:
      "Kemajuan Sasaran Mingguan",
    dashboard_sessions_done: "sesi selesai",
    dashboard_next_suggested_session:
      "Sesi Dicadangkan Seterusnya",

    dashboard_trend_no_data: "Belum ada data trend",
    dashboard_trend_need_more_days: "Perlu satu hari latihan lagi",
    dashboard_trend_placeholder_no_data_title: "Belum ada data trend",
    dashboard_trend_placeholder_no_data_desc:
      "Mula menjawab latihan supaya EasyLearn boleh menjejak prestasi harian anda.",
    dashboard_trend_placeholder_one_day_title:
      "Trend akan dipaparkan selepas hari latihan seterusnya",
    dashboard_trend_placeholder_one_day_desc:
      "Anda sudah mempunyai rekod latihan hari ini. Teruskan berlatih pada hari lain untuk melihat perubahan prestasi.",

    // Quick Snap
    quicksnap_title: "Snap Pantas",
    quicksnap_subtitle:
      "Pilih mod, muat naik satu imej, dan dapatkan bantuan visual Matematik dengan cepat.",
    quicksnap_tab_solve: "Selesaikan Soalan",
    quicksnap_tab_check: "Semak Jalan Kerja Saya",
    quicksnap_drag_title: "Seret & lepaskan imej di sini",
    quicksnap_drag_subtitle: "Menyokong JPG atau PNG",
    quicksnap_browse: "Pilih Fail",
    quicksnap_take_photo: "Ambil Gambar",
    quicksnap_remove: "Buang",
    quicksnap_processing: "Sedang memproses...",
    quicksnap_solve_now: "Selesaikan Sekarang",
    quicksnap_check_now: "Semak Sekarang",
    quicksnap_detected_question: "SOALAN DIKESAN AI",
    quicksnap_solution_title: "Penyelesaian Langkah Demi Langkah",
    quicksnap_checking_title: "Maklum Balas Semakan",
    quicksnap_final_answer: "JAWAPAN AKHIR",
    quicksnap_score: "Skor",
    quicksnap_correctness_summary: "Rumusan Ketepatan",
    quicksnap_strengths: "Kekuatan",
    quicksnap_improvements: "Perlu Dibaiki",
    quicksnap_continue_chat: "Tanya Susulan dalam Tutor Chat",
    quicksnap_continue_chat_phase6:
      "Handoff chatbot akan dibuat dalam phase seterusnya.",
    quicksnap_prompt_solve: "Muat naik imej soalan Matematik.",
    quicksnap_prompt_check:
      "Muat naik imej yang mengandungi soalan + jalan kerja anda.",
    quicksnap_error_title: "Tidak dapat diproses",
    quicksnap_no_result: "Belum ada keputusan.",
    
    // Practice Page
    practice_title: "Pusat Latihan",
    practice_subtitle:
      "Pilih tingkatan dan bab untuk memulakan latihan SPM yang disasarkan.",
    practice_preferred_language: "Bahasa Soalan Pilihan",
    practice_form4: "Tingkatan 4",
    practice_form5: "Tingkatan 5",
    practice_paper1: "Kertas 1",
    practice_paper2: "Kertas 2",

    // Chatbot
    chatbot_title: "Tutor Matematik AI",
    chatbot_online: "Dalam Talian",
    chatbot_history: "Sejarah Chat",
    chatbot_new_chat: "Chat Baharu",
    chatbot_history_title: "Sejarah Chat Anda",
    chatbot_select_language:
      "Hai! Sila pilih bahasa pilihan anda",
    chatbot_placeholder: "Tanya kepada EasyLearn...",
    chatbot_thinking: "AI sedang berfikir...",
    chatbot_error:
      "Maaf, saya menghadapi masalah untuk berhubung dengan pelayan. Pastikan backend Flask anda sedang berjalan!",
    chatbot_welcome:
      "Saya ialah Tutor Matematik AI anda. Anda kini boleh bertanya apa-apa soalan Matematik SPM.",
    chatbot_fab_tooltip: "Tanya Tutor AI!",
    chatbot_history_empty: "Belum ada sejarah chat.",
    chatbot_history_hint: "Mulakan perbualan baharu untuk mula bertanya.",
    chatbot_history_loading: "Memuatkan...",
    chatbot_edit_title: "Edit tajuk",
    chatbot_delete_chat: "Padam chat",
    chatbot_edit_title_prompt: "Masukkan tajuk chat baharu:",
    chatbot_delete_confirm: "Adakah anda pasti mahu sembunyikan chat ini daripada sejarah anda?",
    chatbot_delete_error: "Gagal memadam chat.",
    chatbot_update_title_error: "Gagal mengemas kini tajuk.",
    chatbot_delete_confirm_title: "Padam chat ini?",
    chatbot_delete_confirm_body:
      "Chat ini akan dipadamkan secara kekal daripada sejarah anda.",
    chatbot_cancel: "Batal",
    chatbot_confirm: "Sahkan",
    chatbot_save: "Simpan",
    chatbot_thinking_label: "AI sedang berfikir",
    chatbot_typing_label: "AI sedang membalas",

    // Full Page Chatbot
    chatbot_open_full_page: "Buka halaman chatbot penuh",
    chatbot_expand_busy: "Sila tunggu sehingga AI selesai membalas.",
    chatbot_fullpage_subtitle:
     "Teruskan perbualan yang lebih panjang, semak sejarah, dan urus chat anda.",
    chatbot_mobile_history_tab: "Sejarah",
    chatbot_mobile_chat_tab: "Chat",

    // Parent Home
    parent_home_title: "Halaman Ibu Bapa",
    parent_home_subtitle:
      "Pantau prestasi anak anda dan urus akaun pelajar yang dipautkan.",
    parent_welcome_back: "Selamat kembali",
    parent_manage_text:
      "Tambah atau urus akaun anak anda dengan mudah.",
    parent_total_linked_children: "Jumlah Anak Dipautkan",
    parent_link_child_title: "Pautkan Akaun Anak",
    parent_student_code: "Kod Pelajar",
    parent_nickname_optional: "Nama Panggilan (Pilihan)",
    parent_link_child_button: "Pautkan Anak",
    parent_linked_children_title: "Anak Dipautkan",
    parent_no_children: "Belum ada anak yang dipautkan.",
    parent_unlink: "Nyahpaut",
    parent_view_dashboard: "Dashboard",
    parent_student_id: "ID Pelajar",
    parent_linked_on: "Dipautkan pada",

    parent_toast_success_title: "Berjaya",
    parent_toast_error_title: "Ralat",
    parent_toast_enter_student_code: "Sila masukkan kod pelajar.",
    parent_toast_load_children_failed:
      "Gagal memuatkan senarai anak dipautkan.",
    parent_toast_link_success: "Anak berjaya dipautkan.",
    parent_toast_link_failed: "Gagal memautkan anak.",
    parent_toast_unlink_success: "Anak berjaya dinyahpaut.",
    parent_toast_unlink_failed: "Gagal menyahpaut anak.",
    parent_unlink_dialog_title: "Sahkan nyahpaut?",
    parent_unlink_dialog_desc:
      "Adakah anda pasti mahu menyahpaut {name}? Anda masih boleh pautkan semula anak ini kemudian menggunakan kod pelajar.",
    parent_unlink_dialog_desc_fallback:
      "Adakah anda pasti mahu menyahpaut anak ini?",
    parent_unlink_dialog_cancel: "Batal",
    parent_unlink_dialog_confirm: "Nyahpaut",

    // Parent Child Dashboard
    parent_child_dashboard_back_to_children: "Kembali ke Halaman Ibu Bapa",
    parent_child_dashboard_subtitle:
      "Paparan ibu bapa tentang prestasi pembelajaran, corak belajar dan cadangan ulang kaji anak ini.",
    parent_child_dashboard_read_only: "Baca Sahaja",
    parent_child_dashboard_total_questions:
      "Jumlah Soalan Dijawab",
    parent_child_dashboard_load_failed:
      "Gagal memuatkan dashboard anak.",
    parent_child_dashboard_child: "Anak",

    parent_child_dashboard_refresh_tooltip: "Muat semula dashboard",
    parent_child_dashboard_refreshing: "Sedang memuat semula...",

    parent_dashboard_grade_trend_desc:
      "Menunjukkan perubahan gred ramalan SPM AI anak ini berdasarkan sesi latihan terkini.",
    parent_dashboard_consistency_subtitle:
      "Aktiviti pembelajaran anak ini sepanjang tahun",
    parent_dashboard_study_insights_schedule:
      "Cerapan Pembelajaran & Jadual Belajar",
    parent_dashboard_personalized_study_schedule:
      "Jadual Belajar",
    parent_dashboard_study_schedule_subtitle:
      "Cadangan waktu belajar dan konsistensi pembelajaran mingguan untuk anak ini.",
    parent_dashboard_ai_overview_subtitle:
      "Ringkasan mesra ibu bapa tentang prestasi pembelajaran anak ini.",
  },
};