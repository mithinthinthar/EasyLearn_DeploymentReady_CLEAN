import json
import math
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.base import clone

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, AdaBoostRegressor

BACKEND_DIR = Path(__file__).resolve().parent
MODEL_DIR = BACKEND_DIR / "models"

MODEL_PATH = MODEL_DIR / "grade_score_regressor_model.pkl"
METRICS_PATH = MODEL_DIR / "grade_score_regressor_metrics.json"

DATASET_PATH = BACKEND_DIR / "model_refinement" / "synthetic_exports" / "synthetic_grade_training.csv"

GRADE_LABELS = ["G", "E", "D", "C", "C+", "B", "B+", "A-", "A", "A+"]
GRADE_TO_INDEX = {grade: index for index, grade in enumerate(GRADE_LABELS)}

FEATURE_COLUMNS = [
    "total_questions_attempted",
    "overall_accuracy",
    "recent_accuracy",
    "paper1_accuracy",
    "paper2_accuracy",
    "score_ratio_percent",
    "hard_accuracy_percent",
    "avg_time_per_question",
    "total_sessions",
    "active_days",
    "total_study_minutes",
    "avg_session_minutes",
    "study_consistency_score",
    "max_streak",
    "avg_topic_mastery",
    "weak_topic_count",
    "strong_topic_count",
]

TARGET_SCORE_COLUMN = "target_score"
TARGET_GRADE_COLUMN = "target_grade"


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def score_to_grade(score):
    score = safe_float(score)

    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "A-"
    if score >= 65:
        return "B+"
    if score >= 60:
        return "B"
    if score >= 55:
        return "C+"
    if score >= 50:
        return "C"
    if score >= 45:
        return "D"
    if score >= 40:
        return "E"
    return "G"


def within_one_grade_band_accuracy(y_true_grades, y_pred_grades):
    correct = 0
    total = 0

    for actual, predicted in zip(y_true_grades, y_pred_grades):
        if actual not in GRADE_TO_INDEX or predicted not in GRADE_TO_INDEX:
            continue

        total += 1

        if abs(GRADE_TO_INDEX[actual] - GRADE_TO_INDEX[predicted]) <= 1:
            correct += 1

    if total == 0:
        return 0.0

    return correct / total


def exact_grade_accuracy(y_true_grades, y_pred_grades):
    if len(y_true_grades) == 0:
        return 0.0

    correct = sum(
        1 for actual, predicted in zip(y_true_grades, y_pred_grades)
        if actual == predicted
    )

    return correct / len(y_true_grades)


def grade_band_mae(y_true_grades, y_pred_grades):
    errors = []

    for actual, predicted in zip(y_true_grades, y_pred_grades):
        if actual in GRADE_TO_INDEX and predicted in GRADE_TO_INDEX:
            errors.append(abs(GRADE_TO_INDEX[actual] - GRADE_TO_INDEX[predicted]))

    if not errors:
        return 0.0

    return sum(errors) / len(errors)


def validate_dataset(df):
    missing_columns = []

    for column in FEATURE_COLUMNS + [TARGET_SCORE_COLUMN, TARGET_GRADE_COLUMN]:
        if column not in df.columns:
            missing_columns.append(column)

    if missing_columns:
        raise RuntimeError(
            "Missing required columns in synthetic_grade_training.csv:\n"
            + "\n".join(f"- {column}" for column in missing_columns)
        )

    if df.empty:
        raise RuntimeError("synthetic_grade_training.csv is empty.")


def load_training_dataset():
    if not DATASET_PATH.exists():
        raise RuntimeError(
            f"Training dataset not found:\n{DATASET_PATH}\n\n"
            "Run the synthetic data generator with --export-csv first."
        )

    df = pd.read_csv(DATASET_PATH)
    validate_dataset(df)

    for column in FEATURE_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    df[TARGET_SCORE_COLUMN] = pd.to_numeric(
        df[TARGET_SCORE_COLUMN],
        errors="coerce",
    )

    df = df.dropna(subset=[TARGET_SCORE_COLUMN, TARGET_GRADE_COLUMN]).copy()

    df[TARGET_SCORE_COLUMN] = df[TARGET_SCORE_COLUMN].clip(lower=0, upper=100)

    # Ensure grade label is always consistent with target_score.
    # This does not change the score label; it only standardizes the grade mapping.
    df[TARGET_GRADE_COLUMN] = df[TARGET_SCORE_COLUMN].apply(score_to_grade)

    for column in [
        "overall_accuracy",
        "recent_accuracy",
        "paper1_accuracy",
        "paper2_accuracy",
    ]:
        df[column] = df[column].clip(lower=0, upper=1)

    for column in [
        "score_ratio_percent",
        "hard_accuracy_percent",
        "study_consistency_score",
        "avg_topic_mastery",
    ]:
        df[column] = df[column].clip(lower=0, upper=100)

    non_negative_columns = [
        "total_questions_attempted",
        "avg_time_per_question",
        "total_sessions",
        "active_days",
        "total_study_minutes",
        "avg_session_minutes",
        "max_streak",
        "weak_topic_count",
        "strong_topic_count",
    ]

    for column in non_negative_columns:
        df[column] = df[column].clip(lower=0)

    return df


def evaluate_regression_model(model, X_test, y_test_score, y_test_grade):
    predicted_scores = model.predict(X_test)
    predicted_scores = [max(0, min(100, safe_float(score))) for score in predicted_scores]

    predicted_grades = [score_to_grade(score) for score in predicted_scores]

    mae = mean_absolute_error(y_test_score, predicted_scores)
    mse = mean_squared_error(y_test_score, predicted_scores)
    rmse = math.sqrt(mse)
    r2 = r2_score(y_test_score, predicted_scores)

    exact_acc = exact_grade_accuracy(list(y_test_grade), predicted_grades)
    within_one = within_one_grade_band_accuracy(list(y_test_grade), predicted_grades)
    band_mae = grade_band_mae(list(y_test_grade), predicted_grades)

    return {
        "predicted_scores": predicted_scores,
        "predicted_grades": predicted_grades,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "exact_grade_accuracy": exact_acc,
        "within_one_grade_band_accuracy": within_one,
        "grade_band_mae": band_mae,
    }

def extract_model_importance(model, feature_columns):
    """
    Extract model importance for both:
    - tree models: feature_importances_
    - linear models: absolute coefficients
    """
    if hasattr(model, "steps"):
        actual_model = model.steps[-1][1]
    else:
        actual_model = model

    if hasattr(actual_model, "feature_importances_"):
        importances = actual_model.feature_importances_
        importance_type = "tree_feature_importance"

    elif hasattr(actual_model, "coef_"):
        importances = np.abs(actual_model.coef_)

        if len(importances.shape) > 1:
            importances = importances[0]

        importance_type = "absolute_linear_coefficient"

    else:
        return [], "not_available"

    importance_rows = [
        {
            "feature": feature,
            "importance": round(float(importance), 5),
        }
        for feature, importance in sorted(
            zip(feature_columns, importances),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    return importance_rows, importance_type

def train_model():
    print("Loading prepared synthetic grade training dataset...")
    df = load_training_dataset()

    print(f"Dataset loaded: {len(df)} rows")
    print("Target grade distribution:")
    print(df[TARGET_GRADE_COLUMN].value_counts().reindex(GRADE_LABELS).fillna(0).astype(int))

    print("\nTarget score summary:")
    print(df[TARGET_SCORE_COLUMN].describe())

    if len(df) < 100:
        raise RuntimeError(
            "\nNot enough training rows.\n"
            f"Rows found: {len(df)}\n"
            "Recommended: at least 300–500 synthetic students for model refinement.\n"
        )

    X = df[FEATURE_COLUMNS].copy()
    y_score = df[TARGET_SCORE_COLUMN].copy()
    y_grade = df[TARGET_GRADE_COLUMN].copy()

    stratify_target = y_grade if y_grade.value_counts().min() >= 2 else None

    # ---------------------------------------------------------
    # 70 / 15 / 15 split
    # First split out 15% final test set.
    # Remaining 85% is then split into 70% train and 15% validation.
    # validation_ratio_from_remaining = 15 / 85
    # ---------------------------------------------------------

    X_temp, X_test, y_temp_score, y_test_score, y_temp_grade, y_test_grade = train_test_split(
        X,
        y_score,
        y_grade,
        test_size=0.15,
        random_state=42,
        stratify=stratify_target,
    )

    validation_ratio_from_remaining = 0.15 / 0.85

    temp_stratify_target = (
        y_temp_grade
        if y_temp_grade.value_counts().min() >= 2
        else None
    )

    X_train, X_val, y_train_score, y_val_score, y_train_grade, y_val_grade = train_test_split(
        X_temp,
        y_temp_score,
        y_temp_grade,
        test_size=validation_ratio_from_remaining,
        random_state=42,
        stratify=temp_stratify_target,
    )

    print("\nDataset split:")
    print(f" - Training rows: {len(X_train)} ({len(X_train) / len(df) * 100:.2f}%)")
    print(f" - Validation rows: {len(X_val)} ({len(X_val) / len(df) * 100:.2f}%)")
    print(f" - Testing rows: {len(X_test)} ({len(X_test) / len(df) * 100:.2f}%)")

    candidate_models = {
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=1000,
            max_depth=None,
            min_samples_leaf=2,
            random_state=42,
        ),

        "ExtraTreesRegressor": ExtraTreesRegressor(
            n_estimators=1000,
            max_depth=None,
            min_samples_leaf=2,
            random_state=42,
        ),

        "GradientBoostingRegressor": GradientBoostingRegressor(
            n_estimators=1000,
            learning_rate=0.04,
            max_depth=5,
            random_state=42,
        ),

        "HistGradientBoostingRegressor": HistGradientBoostingRegressor(
            max_iter=1000,
            learning_rate=0.04,
            max_leaf_nodes=31,
            l2_regularization=0.05,
            random_state=42,
        ),

        "AdaBoostRegressor": AdaBoostRegressor(
            n_estimators=1000,
            learning_rate=0.04,
            random_state=42,
        ),

        "SVR_RBF": make_pipeline(
            StandardScaler(),
            SVR(
                kernel="rbf",
                C=20,
                epsilon=2.0,
                gamma="scale",
            ),
        ),

        "SVR_Linear": make_pipeline(
            StandardScaler(),
            SVR(
                kernel="linear",
                C=5,
                epsilon=2.0,
            ),
        ),

        "KNeighborsRegressor": make_pipeline(
            StandardScaler(),
            KNeighborsRegressor(
                n_neighbors=15,
                weights="distance",
                p=2,
            ),
        ),

        "RidgeRegressor": make_pipeline(
            StandardScaler(),
            Ridge(
                alpha=1.0,
                random_state=42,
            ),
        ),

        "ElasticNetRegressor": make_pipeline(
            StandardScaler(),
            ElasticNet(
                alpha=0.01,
                l1_ratio=0.2,
                random_state=42,
                max_iter=10000,
            ),
        ),

        "MLPRegressor": make_pipeline(
            StandardScaler(),
            MLPRegressor(
                hidden_layer_sizes=(64, 32),
                activation="relu",
                solver="adam",
                alpha=0.001,
                learning_rate_init=0.001,
                max_iter=1500,
                random_state=42,
                early_stopping=True,
            ),
        ),
    }

    print("\nTraining candidate models on training set and selecting using validation set...")

    model_results = []
    best_model_name = None
    best_model_template = None
    best_validation_evaluation = None
    best_selection_score = -999999

    for model_name, model in candidate_models.items():
        model.fit(X_train, y_train_score)

        validation_evaluation = evaluate_regression_model(
            model=model,
            X_test=X_val,
            y_test_score=y_val_score,
            y_test_grade=y_val_grade,
        )

        # Lower MAE is better; higher grade accuracy is better.
        normalized_mae_score = max(0, 1 - (validation_evaluation["mae"] / 20))

        selection_score = (
            normalized_mae_score * 0.40
            + validation_evaluation["exact_grade_accuracy"] * 0.35
            + validation_evaluation["within_one_grade_band_accuracy"] * 0.25
        )

        result = {
            "model_name": model_name,
            "validation_mae": round(float(validation_evaluation["mae"]), 4),
            "validation_rmse": round(float(validation_evaluation["rmse"]), 4),
            "validation_r2": round(float(validation_evaluation["r2"]), 4),
            "validation_exact_grade_accuracy": round(float(validation_evaluation["exact_grade_accuracy"]), 4),
            "validation_within_one_grade_band_accuracy": round(float(validation_evaluation["within_one_grade_band_accuracy"]), 4),
            "validation_grade_band_mae": round(float(validation_evaluation["grade_band_mae"]), 4),
            "selection_score": round(float(selection_score), 4),
        }

        model_results.append(result)

        print(
            f" - {model_name}: "
            f"VAL_MAE={validation_evaluation['mae']:.2f}, "
            f"VAL_RMSE={validation_evaluation['rmse']:.2f}, "
            f"VAL_R²={validation_evaluation['r2']:.4f}, "
            f"VAL_exact={validation_evaluation['exact_grade_accuracy'] * 100:.2f}%, "
            f"VAL_within±1={validation_evaluation['within_one_grade_band_accuracy'] * 100:.2f}%, "
            f"VAL_band_MAE={validation_evaluation['grade_band_mae']:.2f}"
        )

        if selection_score > best_selection_score:
            best_selection_score = selection_score
            best_model_name = model_name
            best_model_template = model
            best_validation_evaluation = validation_evaluation

    print("\n============================================================")
    print(f"Selected model from validation set: {best_model_name}")
    print(f"Validation MAE: {best_validation_evaluation['mae']:.2f}")
    print(f"Validation RMSE: {best_validation_evaluation['rmse']:.2f}")
    print(f"Validation R²: {best_validation_evaluation['r2']:.4f}")
    print(f"Validation exact grade accuracy: {best_validation_evaluation['exact_grade_accuracy'] * 100:.2f}%")
    print(f"Validation within ±1 grade band accuracy: {best_validation_evaluation['within_one_grade_band_accuracy'] * 100:.2f}%")
    print(f"Validation grade band MAE: {best_validation_evaluation['grade_band_mae']:.2f}")
    print("============================================================")

    # ---------------------------------------------------------
    # Final model:
    # Retrain selected model on train + validation set,
    # then evaluate once on final unseen test set.
    # ---------------------------------------------------------

    X_train_final = pd.concat([X_train, X_val], axis=0)
    y_train_final_score = pd.concat([y_train_score, y_val_score], axis=0)

    final_model = clone(best_model_template)
    final_model.fit(X_train_final, y_train_final_score)

    test_evaluation = evaluate_regression_model(
        model=final_model,
        X_test=X_test,
        y_test_score=y_test_score,
        y_test_grade=y_test_grade,
    )

    print("\nFinal evaluation on unseen test set:")
    print("============================================================")
    print(f"Final selected regression model: {best_model_name}")
    print(f"Test MAE: {test_evaluation['mae']:.2f}")
    print(f"Test RMSE: {test_evaluation['rmse']:.2f}")
    print(f"Test R²: {test_evaluation['r2']:.4f}")
    print(f"Test exact grade accuracy after score mapping: {test_evaluation['exact_grade_accuracy'] * 100:.2f}%")
    print(f"Test within ±1 grade band accuracy: {test_evaluation['within_one_grade_band_accuracy'] * 100:.2f}%")
    print(f"Test grade band MAE: {test_evaluation['grade_band_mae']:.2f}")
    print("============================================================")

    print("\nRunning cross-validation using MAE on training + validation data...")

    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    cv_negative_mae_scores = cross_val_score(
        clone(best_model_template),
        X_train_final,
        y_train_final_score,
        cv=cv,
        scoring="neg_mean_absolute_error",
    )

    cv_mae_scores = [-float(score) for score in cv_negative_mae_scores]
    cv_mae_mean = sum(cv_mae_scores) / len(cv_mae_scores)
    cv_mae_std = math.sqrt(
        sum((score - cv_mae_mean) ** 2 for score in cv_mae_scores) / len(cv_mae_scores)
    )

    print(f"CV MAE: {cv_mae_mean:.2f} ± {cv_mae_std:.2f}")
    print(f"CV MAE scores: {[round(score, 4) for score in cv_mae_scores]}")

    feature_importance, importance_type = extract_model_importance(
        final_model,
        FEATURE_COLUMNS,
    )

    model_bundle = {
        "model": final_model,
        "model_type": best_model_name,
        "mode": "score_regression",
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_SCORE_COLUMN,
        "grade_labels": GRADE_LABELS,
        "score_to_grade_rule": "SPM-style score range mapping implemented in dashboard_intelligence.py",
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "split_strategy": "70% training, 15% validation, 15% testing",
    }

    metrics = {
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "dataset_path": str(DATASET_PATH),
        "model_path": str(MODEL_PATH),
        "model_type": best_model_name,
        "mode": "score_regression",
        "split_strategy": "70% training, 15% validation, 15% testing",
        "total_rows": int(len(df)),
        "training_rows": int(len(X_train)),
        "validation_rows": int(len(X_val)),
        "testing_rows": int(len(X_test)),
        "final_training_rows": int(len(X_train_final)),
        "feature_columns": FEATURE_COLUMNS,
        "target_score_column": TARGET_SCORE_COLUMN,
        "target_grade_column": TARGET_GRADE_COLUMN,
        "grade_labels": GRADE_LABELS,
        "grade_distribution": {
            grade: int((df[TARGET_GRADE_COLUMN] == grade).sum())
            for grade in GRADE_LABELS
        },
        "score_summary": {
            "min": round(float(df[TARGET_SCORE_COLUMN].min()), 4),
            "max": round(float(df[TARGET_SCORE_COLUMN].max()), 4),
            "mean": round(float(df[TARGET_SCORE_COLUMN].mean()), 4),
            "std": round(float(df[TARGET_SCORE_COLUMN].std()), 4),
        },
        "candidate_model_results_validation": model_results,
        "selected_model": best_model_name,
        "selection_score": round(float(best_selection_score), 4),
        "selection_strategy": (
            "Candidate models were trained on the 70% training set and selected using the 15% validation set. "
            "The selected model was then retrained on training + validation data and evaluated once on the final 15% test set. "
            "Selection score used 40% normalized inverse MAE, 35% exact grade accuracy after score mapping, "
            "and 25% within-one-grade-band accuracy."
        ),
        "validation_metrics_of_selected_model": {
            "mae": round(float(best_validation_evaluation["mae"]), 4),
            "rmse": round(float(best_validation_evaluation["rmse"]), 4),
            "r2": round(float(best_validation_evaluation["r2"]), 4),
            "exact_grade_accuracy": round(float(best_validation_evaluation["exact_grade_accuracy"]), 4),
            "within_one_grade_band_accuracy": round(float(best_validation_evaluation["within_one_grade_band_accuracy"]), 4),
            "grade_band_mae": round(float(best_validation_evaluation["grade_band_mae"]), 4),
        },
        "test_metrics": {
            "mae": round(float(test_evaluation["mae"]), 4),
            "rmse": round(float(test_evaluation["rmse"]), 4),
            "r2": round(float(test_evaluation["r2"]), 4),
            "exact_grade_accuracy": round(float(test_evaluation["exact_grade_accuracy"]), 4),
            "within_one_grade_band_accuracy": round(float(test_evaluation["within_one_grade_band_accuracy"]), 4),
            "grade_band_mae": round(float(test_evaluation["grade_band_mae"]), 4),
        },
        "cross_validation": {
            "method": "KFold on training + validation set",
            "folds": 5,
            "mae_scores": [round(float(score), 4) for score in cv_mae_scores],
            "mae_mean": round(float(cv_mae_mean), 4),
            "mae_std": round(float(cv_mae_std), 4),
        },
        "importance_type": importance_type,
        "feature_importance": feature_importance,
        "note": (
            "This model predicts a continuous score first, then maps the score to an SPM grade band. "
            "The 70/15/15 split separates model training, validation-based model selection, and final testing. "
            "Hidden simulation fields such as hidden_ability and persona were not used as input features."
        ),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model_bundle, MODEL_PATH)

    with open(METRICS_PATH, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    print(f"\nRegression model saved to: {MODEL_PATH}")
    print(f"Regression metrics saved to: {METRICS_PATH}")

    print("\nTop feature importance / coefficient importance:")
    for item in feature_importance[:10]:
        print(f" - {item['feature']}: {item['importance']}")

    if not feature_importance:
        print(" - (Feature importance not available for this model type)")

if __name__ == "__main__":
    train_model()