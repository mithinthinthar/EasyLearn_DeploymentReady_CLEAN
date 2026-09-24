import { useEffect, useState } from "react";

export type Language = "en" | "bm";

type TranslationKey = keyof typeof translations.en;

export const LANGUAGE_STORAGE_KEY = "selectedLanguage";
export const LANGUAGE_CHANGE_EVENT = "easylearn-language-change";

export const translations = {
  en: {
    home: "Home",
    quiz: "Quiz",
    dashboard: "Dashboard",
    logout: "Logout",
    pleaseSignIn: "Please sign in",
    languageLabel: "Language",
    english: "EN",
    bahasaMelayu: "BM",
    back: "Back",
    backToHome: "Back to Home",
    generateMoreQuestionsButton: "Generate More Questions",
    TryAgain: "Try Again",

    easy: "Easy",
    medium: "Medium",
    hard: "Hard",
    easyDescription: "Basic practice",
    mediumDescription: "SPM standard",
    hardDescription: "Exam challenge",

    homeHeroTitle: "Welcome back.",
    homeHeroSubtitle: "Select a paper below to begin your session.",
    choosePracticeLevel: "Choose Your Practice Level",
    choosePracticeLevelDescription:
      "Select a difficulty before choosing your BM revision topic.",
    currentLevel: "Current level",
    recommendedForYou: "Recommended for You",
    updateRecommendations: "Update Recommendations",
    updating: "Updating...",
    loadingRecommendations: "Loading recommendations...",
    noRecommendationAvailable: "No recommendation available yet.",
    recommendationLoadError: "Unable to load recommendations right now.",

    paper1: "Paper 1",
    paper2: "Paper 2",
    paper3: "Paper 3",
    paper4: "Paper 4",
    paper1Upper: "PAPER 1",
    paper2Upper: "PAPER 2",
    paper3Upper: "PAPER 3",
    paper4Upper: "PAPER 4",

    longEssayTitle: "Long Essay",
    longEssayDescription:
      "Practice structured long essay writing based on SPM examination standards.",
    shortEssayTitle: "Short Essay",
    shortEssayDescription:
      "Practice short essay writing with clear structure, relevant points and accurate language.",

    exampleEssay: "Example Essay",
    practice: "Practice",
    tipsNotes: "Tips / Notes",

    golonganKataTitle: "Word Classes",
    golonganKataDescription:
      "Identify nouns, verbs, adjectives and function words in different sentence contexts.",

    binaAyatTitle: "Build Sentences",
    binaAyatDescription:
      "Build complete, grammatical and meaningful sentences using the words given.",

    jenisAyatTitle: "Sentence Types",
    jenisAyatDescription:
      "Practise statement, question, command, exclamation and sentence transformations.",

    kesalahanBahasaTitle: "Identify Language Errors",
    kesalahanBahasaDescription:
      "Detect and correct errors in spelling, grammar, word usage and sentence structure.",

    pemahamanTitle: "Reading Comprehension",
    pemahamanDescription:
      "Answer questions based on reading materials, stated information, implied meaning and higher-order thinking responses.",

    rumusanTitle: "Summary Writing",
    rumusanDescription:
      "Practise identifying important points and writing a concise, accurate and grammatical summary.",

    speakingSectionTitle: "Speaking Test",
    speakingSectionDescription:
      "Practise oral responses, reading aloud, stimulus-based questions and higher-order thinking speaking tasks.",

    listeningSectionTitle: "Listening Test",
    listeningSectionDescription:
      "Practise listening comprehension through audio-based tasks and structured responses.",

    listeningPracticeTitle: "Listening Practice",
    listeningPracticeSubtitle: "Listen to the audio and answer all questions.",
    preparingListeningQuiz: "Preparing your listening quiz...",
    pleaseWaitGeneratingListening:
      "Please wait. The system is generating your listening audio and questions.",
    generateMoreListeningTitle: "Need More Questions?",
    generateMoreListeningHardDescription:
      "This fixed listening practice is used for Hard difficulty. Click below to generate a new AI listening test.",
    generateMoreListeningButton: "Generate More Questions",
    audio: "Audio",
    listenBeforeAnswering: "*Please listen to the audio before answering.",
    marks: "marks",
    showAnswers: "Show Answers",
    hideAnswers: "Hide Answers",
    answerScheme: "Answer Scheme",

    quizPageTitle: "Bahasa Melayu Examination Practice",
    quizPageSubtitle:
      "Select a difficulty, then choose a paper and section to begin your practice.",
    chooseQuizLevel: "Choose Your Quiz Level",
    chooseQuizLevelDescription:
      "Select a difficulty before starting your BM quiz.",
    currentQuizLevel: "Current quiz level",
    start: "Start",

    paper1Writing: "Paper 1 – Writing",
    paper2GrammarReading: "Paper 2 – Grammar & Reading Comprehension",
    paper3Speaking: "Paper 3 – Speaking Test",
    paper4Listening: "Paper 4 – Listening Test",

    karanganPendek: "Short Essay",
    karanganPanjang: "Long Essay",
    karanganPendekMeta: "150–200 words • 30 marks",
    karanganPanjangMeta: "350–500 words • 70 marks",

    quizGolonganKata: "Identify Word Classes",
    quizGolonganKataMeta: "Questions on identifying word classes",

    quizBinaAyat: "Build Sentences",
    quizBinaAyatMeta: "Build sentences using the given words",

    quizJenisAyat: "Identify Sentence Types",
    quizJenisAyatMeta: "Transform sentence forms accurately",

    quizKesalahanBahasa: "Identify Language Errors",
    quizKesalahanBahasaMeta: "Identify and correct language errors",

    quizPemahaman: "Reading Comprehension",
    quizPemahamanMeta: "Passages and comprehension questions",

    quizRumusan: "Summary Writing",
    quizRumusanMeta: "Organise information in a concise form",

    quizUjianBertutur: "Speaking Test",
    quizUjianBertuturMeta: "Answer the questions given",

    quizUjianMendengar: "Listening Test",
    quizUjianMendengarMeta: "Answer the questions given",

    shortEssayPracticeTitle: "Short Essay Practice",
    longEssayPracticeTitle: "Long Essay Practice",
    submitEssay: "Submit Essay",
    markingEssay: "Marking...",
    generatingQuestion: "Generating...",
    newQuestion: "New Question",
    tryAgainButton: "Try Again",
    essayResultTitle: "Marking Result",
    score: "Score",
    percentage: "Percentage",
    grade: "Grade",
    wordCount: "Word count",
    topicRelevance: "Topic relevance",
    essayFeedback: "Feedback",
    improvementSuggestions: "Suggestions for Improvement",
    rubric: "Rubric",
    rubricContent: "Content",
    rubricLanguage: "Language",
    rubricGrammar: "Grammar",
    rubricVocabulary: "Vocabulary",
    rubricCoherence: "Cohesion and coherence",
    offTopicWarning:
      "Warning: This essay may not fully answer the question.",
    emptyEssayError: "Please write your essay before submitting.",
    shortEssayTooShortError:
      "Your essay is too short. Please write a more complete answer.",
    longEssayTooShortError:
      "Your essay is too short. Please write a more complete answer.",
    essayMarkError: "Failed to mark essay. Please try again.",
    essayGenerateError: "Failed to generate a new question. Please try again.",
    generatedQuestionError: "The new question could not be generated.",
    mustAttemptBeforeNewQuestion:
      "Please answer and submit this question before generating a new one.",
    generatedPracticeNotice:
      "This new question is generated for extra practice and will not be recorded in the dashboard.",
    shortGeneratedInstruction:
      "Based on the question below, write your opinion. Your response should be between 150 and 200 words.",
    shortGeneratedPlaceholder: "Write your short essay here...",
    longGeneratedInstruction:
      "Write an essay based on the question below. Your essay should be between 350 and 500 words.",
    longGeneratedPlaceholder: "Write your long essay here...",

    paper2PracticeResult: "Practice Result",
    checkAnswer: "Check Answer",
    submitAnswers: "Submit Answers",
    dragAllWordsBeforeChecking: "Please drag all words into a category before checking your answer.",
    markingAnswer: "Marking...",
    overallFeedback: "Overall Feedback",
    yourAnswer: "Your Answer",
    correctAnswer: "Correct Answer",
    feedback: "Feedback",
    notAnswered: "Not answered",
    question: "Question",
    answerPlaceholder: "Write your answer here...",
    selectAnswer: "-- Select an answer --",
    mustAnswerAllQuestions: "Please answer all questions before submitting.",
    paper2PracticeCompleted: "Your practice answers have been checked.",
    isiScore: "Content score",
    bahasaScore: "Language score",

    speakingPracticeTitle: "Speaking Practice",
    speakingPracticeSubtitle:
      "Read each question and record your spoken answer. Your answer will be assessed based on grammar, pronunciation, fluency and ideas.",
    sectionIndividual: "Part A: Individual",
    sectionGroup: "Part B: Group Discussion",
    readingQuestionLabel: "Reading / Question 1",
    stimulusQuestionLabel: "Stimulus Question",
    kbatQuestionLabel: "HOTS Question",
    extraPracticeLabel: "Extra Practice",
    speakingExtraNotMarked:
      "This question is for extra practice and will not be submitted for marking.",
    recordAudio: "Record Audio",
    stopRecording: "Stop Recording",
    uploadAudio: "Upload File",
    speakingOr: "or",
    clickToRecord: "Click to start recording",
    recordingInProgress: "Recording...",
    audioFormats: "WAV, MP3, M4A, OGG, WebM",
    loginToGenerateQuestion: "Please sign in first to generate a new question.",
    loginToEvaluateSpeaking:
      "Please sign in first to use speaking evaluation.",
    microphoneAccessError:
      "Unable to access microphone. Please allow microphone permission.",
    completeFiveAudiosError:
      "Please complete recording or upload audio for the 5 main questions first.",
    audioTooShort: "Recording is too short. Please record again. Minimum 3 seconds.",
    audioTooLong: "Recording is too long. Please shorten it. Maximum 5 minutes.",
    submittingAnswer: "Submitting...",
    submitAnswer: "Submit Answer",
    speakingPracticeResult: "Speaking Practice Result",
    speakingOverallScore: "Overall Score",
    overallComment: "Overall Comment",
    grammarVocabulary: "Grammar and Vocabulary",
    pronunciation: "Pronunciation",
    fluency: "Fluency",
    ideas: "Ideas",
    readingWer: "Reading WER",
    transcription: "Transcription",
    noSpeechDetected: "No speech could be detected.",
    ideasFeedbackByQuestion: "Ideas Feedback by Question",
    audioWarningTitle: "Recording Warning",
    overallAnalysis: "Overall Analysis",
    questionFeedback: "Question Feedback",
    clipBreakdown: "Breakdown by Clip",
    clipId: "ID",
    band: "Band",
    loadingQuestions: "Loading questions...",

    dashboardTitle: "Performance Overview",
    dashboardSubtitle:
      "Track your scores, recent trend, and a simple grade predictor based on your saved quiz results.",
    dashboardLoading: "Loading dashboard...",
    dashboardLoadError:
      "Unable to load dashboard right now. Please refresh and try again.",

    averageQuizScore: "Average Quiz Score",
    totalQuestions: "Total Questions",
    gradePredictor: "Grade Predictor",
    basedOnRecentQuizPerformance: "Based on recent quiz performance",

    performanceTrend: "Performance Trend",
    attemptsSaved: "attempts saved",
    noQuizHistory:
      "No quiz history yet. Finish one quiz and this chart will wake up.",

    quickInsight: "Quick Insight",
    latestResult: "Latest result",
    scored: "scored",
    withGrade: "with grade",
    savedOn: "Saved on",
    noResultSaved: "No result saved yet.",

    strengthVsFocusArea: "Strength vs Focus Area",
    strongestTopic: "Strongest topic",
    focusNextOn: "Focus next on",
    average: "average",
  },

  bm: {
    home: "Laman Utama",
    quiz: "Kuiz",
    dashboard: "Papan Pemuka",
    logout: "Log Keluar",
    pleaseSignIn: "Sila log masuk",
    languageLabel: "Bahasa",
    english: "EN",
    bahasaMelayu: "BM",
    back: "Kembali",
    backToHome: "Kembali ke Laman Utama",
    generateMoreQuestionsButton: "Jana Soalan Tambahan",
    TryAgain: "Cuba Lagi",

    easy: "Mudah",
    medium: "Sederhana",
    hard: "Sukar",
    easyDescription: "Latihan asas",
    mediumDescription: "Standard SPM",
    hardDescription: "Cabaran peperiksaan",

    homeHeroTitle: "Selamat kembali.",
    homeHeroSubtitle: "Pilih kertas di bawah untuk memulakan sesi anda.",
    choosePracticeLevel: "Pilih Tahap Latihan",
    choosePracticeLevelDescription:
      "Pilih tahap kesukaran sebelum memilih topik ulang kaji BM.",
    currentLevel: "Tahap semasa",
    recommendedForYou: "Disyorkan untuk Anda",
    updateRecommendations: "Kemas Kini Cadangan",
    updating: "Mengemas kini...",
    loadingRecommendations: "Sedang memuatkan cadangan...",
    noRecommendationAvailable: "Tiada cadangan tersedia lagi.",
    recommendationLoadError: "Tidak dapat memuatkan cadangan buat masa ini.",

    paper1: "Kertas 1",
    paper2: "Kertas 2",
    paper3: "Kertas 3",
    paper4: "Kertas 4",
    paper1Upper: "KERTAS 1",
    paper2Upper: "KERTAS 2",
    paper3Upper: "KERTAS 3",
    paper4Upper: "KERTAS 4",

    longEssayTitle: "Karangan Panjang",
    longEssayDescription:
      "Latih penulisan karangan panjang berstruktur berdasarkan standard peperiksaan SPM.",
    shortEssayTitle: "Karangan Pendek",
    shortEssayDescription:
      "Latih penulisan karangan pendek dengan struktur jelas, isi relevan dan bahasa yang tepat.",

    exampleEssay: "Karangan Contoh",
    practice: "Latihan",
    tipsNotes: "Tips / Nota",

    golonganKataTitle: "Golongan Kata",
    golonganKataDescription:
      "Kenal pasti kata nama, kata kerja, kata adjektif dan kata tugas dalam pelbagai konteks ayat.",

    binaAyatTitle: "Bina Ayat",
    binaAyatDescription:
      "Bina ayat yang lengkap, gramatis dan bermakna menggunakan perkataan yang diberi.",

    jenisAyatTitle: "Jenis Ayat",
    jenisAyatDescription:
      "Latih ayat penyata, ayat tanya, ayat perintah, ayat seruan dan penukaran bentuk ayat.",

    kesalahanBahasaTitle: "Cari Kesalahan Bahasa",
    kesalahanBahasaDescription:
      "Kenal pasti dan betulkan kesalahan ejaan, tatabahasa, penggunaan kata dan struktur ayat.",

    pemahamanTitle: "Pemahaman",
    pemahamanDescription:
      "Jawab soalan berdasarkan bahan bacaan, maklumat tersurat, maksud tersirat dan respons KBAT.",

    rumusanTitle: "Rumusan",
    rumusanDescription:
      "Latih mengenal pasti isi penting dan menulis rumusan yang ringkas, tepat dan gramatis.",

    speakingSectionTitle: "Ujian Bertutur",
    speakingSectionDescription:
      "Latih respons lisan, bacaan kuat, soalan berdasarkan stimulus dan tugasan bertutur KBAT.",

    listeningSectionTitle: "Ujian Mendengar",
    listeningSectionDescription:
      "Latih pemahaman mendengar melalui tugasan berasaskan audio dan respons berstruktur.",

    listeningPracticeTitle: "Latihan Ujian Mendengar",
    listeningPracticeSubtitle: "Dengar audio dan jawab semua soalan.",
    preparingListeningQuiz: "Menyediakan ujian mendengar anda...",
    pleaseWaitGeneratingListening:
      "Sila tunggu. Sistem sedang menjana audio dan soalan ujian mendengar.",
    generateMoreListeningTitle: "Mahukan Soalan Tambahan?",
    generateMoreListeningHardDescription:
      "Latihan mendengar tetap ini digunakan untuk tahap Sukar. Klik butang di bawah untuk menjana ujian mendengar AI baharu.",
    generateMoreListeningButton: "Jana Soalan Tambahan",
    audio: "Audio",
    listenBeforeAnswering: "*Sila dengar audio sebelum menjawab.",
    marks: "markah",
    showAnswers: "Tunjukkan Jawapan",
    hideAnswers: "Sembunyikan Jawapan",
    answerScheme: "Skema Jawapan",

    quizPageTitle: "Latihan Peperiksaan Bahasa Melayu",
    quizPageSubtitle:
      "Pilih tahap kesukaran, kemudian pilih kertas dan bahagian untuk memulakan latihan.",
    chooseQuizLevel: "Pilih Tahap Kuiz",
    chooseQuizLevelDescription:
      "Pilih tahap kesukaran sebelum memulakan kuiz BM.",
    currentQuizLevel: "Tahap kuiz semasa",
    start: "Mula",

    paper1Writing: "Kertas 1 – Penulisan",
    paper2GrammarReading: "Kertas 2 – Tatabahasa & Pemahaman",
    paper3Speaking: "Kertas 3 – Ujian Bertutur",
    paper4Listening: "Kertas 4 – Ujian Mendengar",

    karanganPendek: "Karangan Pendek",
    karanganPanjang: "Karangan Panjang",
    karanganPendekMeta: "150–200 patah perkataan • 30 markah",
    karanganPanjangMeta: "350–500 patah perkataan • 70 markah",

    quizGolonganKata: "Kenal Pasti Golongan Kata",
    quizGolonganKataMeta: "Soalan mengenal pasti golongan kata",

    quizBinaAyat: "Bina Ayat",
    quizBinaAyatMeta: "Membina ayat berdasarkan perkataan diberi",

    quizJenisAyat: "Kenal Pasti Jenis Ayat",
    quizJenisAyatMeta: "Menukar bentuk ayat secara tepat",

    quizKesalahanBahasa: "Kenal Pasti Kesalahan Bahasa",
    quizKesalahanBahasaMeta: "Mengenal pasti dan membetulkan kesalahan",

    quizPemahaman: "Pemahaman",
    quizPemahamanMeta: "Petikan dan soalan pemahaman",

    quizRumusan: "Rumusan",
    quizRumusanMeta: "Menyusun maklumat dalam bentuk ringkas",

    quizUjianBertutur: "Ujian Bertutur",
    quizUjianBertuturMeta: "Jawab soalan yang diberi",

    quizUjianMendengar: "Ujian Mendengar",
    quizUjianMendengarMeta: "Jawab soalan yang diberi",

    shortEssayPracticeTitle: "Latihan Karangan Pendek",
    longEssayPracticeTitle: "Latihan Karangan Panjang",
    submitEssay: "Hantar Karangan",
    markingEssay: "Sedang menyemak karangan...",
    generatingQuestion: "Menjana...",
    newQuestion: "Soalan Baharu",
    tryAgainButton: "Cuba Lagi",
    essayResultTitle: "Keputusan Semakan",
    score: "Markah",
    percentage: "Peratus",
    grade: "Gred",
    wordCount: "Jumlah perkataan",
    topicRelevance: "Kesesuaian tajuk",
    essayFeedback: "Maklum Balas",
    improvementSuggestions: "Cadangan Penambahbaikan",
    rubric: "Rubrik",
    rubricContent: "Isi kandungan",
    rubricLanguage: "Bahasa",
    rubricGrammar: "Tatabahasa",
    rubricVocabulary: "Kosa kata",
    rubricCoherence: "Kohesi dan koherensi",
    offTopicWarning:
      "Amaran: Karangan ini mungkin kurang menjawab kehendak soalan.",
    emptyEssayError: "Sila tulis karangan sebelum menghantar.",
    shortEssayTooShortError:
      "Karangan terlalu pendek. Sila tulis jawapan yang lebih lengkap.",
    longEssayTooShortError:
      "Karangan terlalu pendek. Sila tulis jawapan yang lebih lengkap.",
    essayMarkError: "Gagal menyemak karangan. Sila cuba lagi.",
    essayGenerateError: "Gagal menjana soalan baharu. Sila cuba lagi.",
    generatedQuestionError: "Soalan baharu tidak berjaya dijana.",
    mustAttemptBeforeNewQuestion:
      "Sila jawab dan hantar soalan ini dahulu sebelum menjana soalan baharu.",
    generatedPracticeNotice:
      "Soalan baharu ini dijana untuk latihan tambahan dan tidak akan direkodkan dalam dashboard.",
    shortGeneratedInstruction:
      "Berdasarkan soalan di bawah, huraikan pendapat anda. Panjangnya huraian anda hendaklah antara 150 hingga 200 patah perkataan.",
    shortGeneratedPlaceholder: "Tulis karangan pendek anda di sini...",
    longGeneratedInstruction:
      "Tulis sebuah karangan berdasarkan soalan di bawah. Panjangnya karangan anda hendaklah antara 350 hingga 500 patah perkataan.",
    longGeneratedPlaceholder: "Tulis karangan panjang anda di sini...",

    paper2PracticeResult: "Keputusan Latihan",
    checkAnswer: "Semak Jawapan",
    submitAnswers: "Hantar Jawapan",
    dragAllWordsBeforeChecking: "Sila seret semua perkataan ke kategori sebelum menyemak jawapan.",
    markingAnswer: "Menyemak...",
    overallFeedback: "Maklum Balas Keseluruhan",
    yourAnswer: "Jawapan Anda",
    correctAnswer: "Jawapan Betul",
    feedback: "Maklum Balas",
    notAnswered: "Belum dijawab",
    question: "Soalan",
    answerPlaceholder: "Tulis jawapan anda di sini...",
    selectAnswer: "-- Pilih jawapan --",
    mustAnswerAllQuestions: "Sila jawab semua soalan sebelum menghantar.",
    paper2PracticeCompleted: "Jawapan latihan anda telah disemak.",
    isiScore: "Markah isi",
    bahasaScore: "Markah bahasa",

    speakingPracticeTitle: "Latihan Ujian Bertutur",
    speakingPracticeSubtitle:
      "Baca setiap soalan dan rakam jawapan anda secara lisan. Jawapan anda akan dinilai berdasarkan tatabahasa, sebutan, kefasihan dan idea.",
    sectionIndividual: "Bahagian A: Individu",
    sectionGroup: "Bahagian B: Perbincangan Kumpulan",
    readingQuestionLabel: "Bacaan / Soalan 1",
    stimulusQuestionLabel: "Soalan Rangsangan",
    kbatQuestionLabel: "Soalan KBAT",
    extraPracticeLabel: "Latihan Tambahan",
    speakingExtraNotMarked:
      "Soalan ini untuk latihan tambahan dan tidak dihantar kepada sistem pemarkahan.",
    recordAudio: "Rekod Audio",
    stopRecording: "Henti Rakaman",
    uploadAudio: "Muat Naik Fail",
    speakingOr: "atau",
    clickToRecord: "Klik untuk mula merakam",
    recordingInProgress: "Sedang merakam...",
    audioFormats: "WAV, MP3, M4A, OGG, WebM",
    loginToGenerateQuestion: "Sila log masuk dahulu untuk menjana soalan baharu.",
    loginToEvaluateSpeaking:
      "Sila log masuk dahulu untuk menggunakan penilaian lisan.",
    microphoneAccessError:
      "Gagal akses mikrofon. Sila benarkan penggunaan mikrofon.",
    completeFiveAudiosError:
      "Sila lengkapkan rakaman atau muat naik audio untuk 5 soalan utama dahulu.",
    audioTooShort: "Rakaman terlalu pendek. Sila rakam semula. Minimum 3 saat.",
    audioTooLong: "Rakaman terlalu panjang. Sila ringkaskan. Maksimum 5 minit.",
    submittingAnswer: "Sedang menghantar...",
    submitAnswer: "Hantar Jawapan",
    speakingPracticeResult: "Keputusan Latihan Bertutur",
    speakingOverallScore: "Markah Keseluruhan",
    overallComment: "Ulasan Keseluruhan",
    grammarVocabulary: "Tatabahasa dan Kosa Kata",
    pronunciation: "Sebutan",
    fluency: "Kefasihan",
    ideas: "Idea",
    readingWer: "WER Bacaan",
    transcription: "Transkripsi",
    noSpeechDetected: "Tiada pertuturan dapat dikesan.",
    ideasFeedbackByQuestion: "Maklum Balas Idea Mengikut Soalan",
    audioWarningTitle: "Amaran Rakaman",
    overallAnalysis: "Analisis Keseluruhan",
    questionFeedback: "Maklum Balas Soalan",
    clipBreakdown: "Pecahan Mengikut Klip",
    clipId: "ID",
    band: "Band",
    loadingQuestions: "Memuatkan soalan...",

    dashboardTitle: "Gambaran Prestasi",
    dashboardSubtitle:
      "Pantau markah, trend terkini dan ramalan gred ringkas berdasarkan keputusan kuiz yang disimpan.",
    dashboardLoading: "Sedang memuatkan papan pemuka...",
    dashboardLoadError:
      "Tidak dapat memuatkan papan pemuka buat masa ini. Sila refresh dan cuba lagi.",

    averageQuizScore: "Purata Markah Kuiz",
    totalQuestions: "Jumlah Soalan",
    gradePredictor: "Ramalan Gred",
    basedOnRecentQuizPerformance: "Berdasarkan prestasi kuiz terkini",

    performanceTrend: "Trend Prestasi",
    attemptsSaved: "percubaan disimpan",
    noQuizHistory:
      "Tiada sejarah kuiz lagi. Selesaikan satu kuiz dan carta ini akan dipaparkan.",

    quickInsight: "Maklumat Ringkas",
    latestResult: "Keputusan terkini",
    scored: "mendapat markah",
    withGrade: "dengan gred",
    savedOn: "Disimpan pada",
    noResultSaved: "Tiada keputusan disimpan lagi.",

    strengthVsFocusArea: "Kekuatan vs Fokus Latihan",
    strongestTopic: "Topik terkuat",
    focusNextOn: "Fokus seterusnya",
    average: "purata",
  },
} as const;

export function getSavedLanguage(): Language {
  const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY);

  if (saved === "bm" || saved === "en") {
    return saved;
  }

  return "en";
}

export function setSavedLanguage(language: Language) {
  localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  window.dispatchEvent(new CustomEvent(LANGUAGE_CHANGE_EVENT, { detail: language }));
}

export function useLanguage() {
  const [language, setLanguageState] = useState<Language>(getSavedLanguage);

  useEffect(() => {
    function handleLanguageChange() {
      setLanguageState(getSavedLanguage());
    }

    window.addEventListener(LANGUAGE_CHANGE_EVENT, handleLanguageChange);
    window.addEventListener("storage", handleLanguageChange);

    return () => {
      window.removeEventListener(LANGUAGE_CHANGE_EVENT, handleLanguageChange);
      window.removeEventListener("storage", handleLanguageChange);
    };
  }, []);

  function setLanguage(language: Language) {
    setSavedLanguage(language);
    setLanguageState(language);
  }

  function t(key: TranslationKey) {
    return translations[language][key];
  }

  return { language, setLanguage, t };
}