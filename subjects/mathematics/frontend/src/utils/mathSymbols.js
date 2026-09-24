export const getEasyLearnmbols = (language = "en") => {
  const isBm = language === "bm";

  return [
    { label: "+", insert: "+", title: isBm ? "Tambah" : "Plus" },
    { label: "−", insert: "−", title: isBm ? "Tolak" : "Minus" },
    { label: "×", insert: "×", title: isBm ? "Darab" : "Multiply" },
    { label: "÷", insert: "÷", title: isBm ? "Bahagi" : "Divide" },
    { label: "=", insert: "=", title: isBm ? "Sama dengan" : "Equal" },
    { label: "≠", insert: "≠", title: isBm ? "Tidak sama dengan" : "Not equal" },

    { label: "<", insert: "<", title: isBm ? "Kurang daripada" : "Less than" },
    { label: ">", insert: ">", title: isBm ? "Lebih daripada" : "Greater than" },
    { label: "≤", insert: "≤", title: isBm ? "Kurang atau sama dengan" : "Less than or equal" },
    { label: "≥", insert: "≥", title: isBm ? "Lebih atau sama dengan" : "Greater than or equal" },
    { label: "≈", insert: "≈", title: isBm ? "Anggaran sama dengan" : "Approximately equal" },

    { label: "√", insert: "√", title: isBm ? "Punca kuasa dua" : "Square root" },
    { label: "^", insert: "^", title: isBm ? "Kuasa" : "Power" },
    { label: "²", insert: "²", title: isBm ? "Kuasa dua" : "Power of 2" },
    { label: "³", insert: "³", title: isBm ? "Kuasa tiga" : "Power of 3" },

    { label: "π", insert: "π", title: isBm ? "Pi" : "Pi" },
    { label: "±", insert: "±", title: isBm ? "Tambah atau tolak" : "Plus minus" },
    { label: "°", insert: "°", title: isBm ? "Darjah" : "Degree" },

    { label: "sin", insert: "sin(", title: isBm ? "Sinus" : "Sine" },
    { label: "cos", insert: "cos(", title: isBm ? "Kosinus" : "Cosine" },
    { label: "tan", insert: "tan(", title: isBm ? "Tangen" : "Tangent" },

    { label: "∪", insert: "∪", title: isBm ? "Kesatuan" : "Union" },
    { label: "∩", insert: "∩", title: isBm ? "Persilangan" : "Intersection" },
    { label: "∈", insert: "∈", title: isBm ? "Unsur kepada" : "Element of" },

    { label: "x̄", insert: "x̄", title: isBm ? "Min" : "Mean" },
    { label: "Σ", insert: "Σ", title: isBm ? "Jumlah / Sigma" : "Summation" },

    { label: "()", insert: "()", cursorBack: 1, title: isBm ? "Kurungan" : "Brackets" },
  ];
};

export const getEasyLearnmbolsTooltip = (language = "en") => {
  return language === "bm" ? "Simbol Matematik" : "Math symbols";
};