# MathSy - SPM Mathematic Preparation System (Bilingual)

## Personalized AI-Powered SPM Mathematics Learning Platform

MathSy is an **AI-powered personalized learning platform designed to support Malaysian SPM Mathematics students** through intelligent question solving, AI tutoring, personalized learning, machine learning-based recommendations, and learning analytics.

The system combines **Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), Machine Learning, mathematical verification, and adaptive learning techniques** to provide students with a personalized learning experience aligned with the SPM Mathematics syllabus. It support both Bahasa Melayu and English syllabus to tackle for both DLP and Non-DLP Mathematics syllabus. With a user friendly laptop/tablet/mobile interface.

> Final Year Project — Bachelor of Science (Hons) in Computer Science with a Specialism in Artificial Intelligence
> Asia Pacific University of Technology & Innovation (APU)

---

# Project Overview

Mathematics is an important subject in the Malaysian SPM examination, but students often face difficulties identifying their weaknesses, understanding complex questions, and receiving personalized guidance outside the classroom.

Traditional learning platforms generally provide the same exercises and resources to every student.

**MathSy aims to address this limitation by adapting the learning experience to each individual student.**

The platform integrates multiple AI and machine learning components to:

* Process mathematics questions
* Provide AI-powered mathematical tutoring
* Generate step-by-step mathematical solutions
* Check students' mathematical working
* Retrieve relevant SPM questions and marking schemes
* Predict student performance
* Analyze study patterns
* Recommend topics for improvement
* Adapt practice based on student mastery
* Generate targeted review questions
* Track student learning progress

---

# Main Features

## 1. Quick Snap AI

Quick Snap allows students to upload an image of a mathematics question.

The system analyzes the question and provides two learning modes.

### Generate Solution

The system:

```text
Question Image
      ↓
Question Understanding
      ↓
Topic Identification
      ↓
RAG Retrieval
      ↓
Mathematical Solver
      ↓
LLM Explanation
      ↓
Verified Solution
```

The generated solution provides a structured, step-by-step explanation designed for SPM students.

### Check My Work

Students can submit their own working and receive feedback on their solution.

The system analyzes the student's approach and compares it against the expected solution and relevant marking scheme.

This allows students to understand:

* Where they made mistakes
* Which step was incorrect
* Why the mistake occurred
* How the solution should be approached

---

# 2. AI Mathematics Tutor

MathSy includes an AI-powered mathematics chatbot designed to act as a virtual mathematics tutor.

The chatbot supports students by providing:

* Step-by-step explanations
* Concept explanations
* Follow-up questions
* Hints and guidance
* Error clarification
* Mathematical problem solving
* English and Bahasa Melayu explanations

Instead of simply returning an answer, the tutor is designed to help students understand the reasoning behind the solution.

---

# 3. Retrieval-Augmented Generation (RAG)

MathSy uses **Retrieval-Augmented Generation (RAG)** to ground AI-generated responses in SPM-specific learning materials.

Relevant SPM questions and marking schemes are stored and indexed for retrieval.

### RAG Architecture

```text
                Student Question
                       │
                       ▼
              Question Processing
                       │
                       ▼
              Context Extraction
                       │
                       ▼
                Vector Search
                       │
                       ▼
               Pinecone Retrieval
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    Similar Questions         Marking Schemes
          │                         │
          └────────────┬────────────┘
                       ▼
                  LLM Reasoning
                       │
                       ▼
              Mathematical Solver
                       │
                       ▼
                 Verification
                       │
                       ▼
               Final Explanation
```

The RAG component helps ensure that generated responses remain relevant to the **SPM Mathematics syllabus and marking expectations**.

---

# 4. Mathematical Solver & Verification

Large Language Models are not always reliable at mathematical calculations.

MathSy therefore uses a hybrid approach combining LLM reasoning with deterministic mathematical tools.

The system can route problems to specialized mathematical solving logic such as:

* Algebra
* Equations
* Geometry
* Trigonometry
* Statistics
* Probability
* Taxation
* Matrices

Mathematical calculations can be verified using:

* **SymPy**
* Custom Python mathematical logic
* Rule-based validation

### Hybrid Reasoning

```text
                Mathematics Question
                         │
                         ▼
                   LLM Reasoning
                         │
                         ▼
                 Solver Selection
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
    LLM Solution                  Math Solver
                                        │
                                        ▼
                                      SymPy
                                        │
          └──────────────┬──────────────┘
                         ▼
                    Verification
                         │
                         ▼
                 Final AI Response
```

This architecture reduces dependency on the LLM for numerical calculations while preserving its ability to generate natural-language explanations.

---

# 5. Machine Learning System

MathSy also includes a dedicated **Machine Learning component** for analyzing student learning behavior and providing personalized insights.

The machine learning component consists of three main models:

```text
                    Student Data
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
   Grade Prediction   Study Pattern   Topic
       Model            Analyzer     Recommender
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                Student Learning Profile
                         │
                         ▼
                Personalized Experience
```

---

## 5.1 Grade Prediction Model

The Grade Prediction Model estimates a student's potential mathematics performance based on their historical learning and assessment data.

Possible input features include:

* Previous test scores
* Question accuracy
* Practice frequency
* Topic performance
* Number of attempts
* Learning activity
* Historical assessment results

The model provides an estimated performance outcome that can help identify students who may require additional support.

### Example Workflow

```text
Student Performance Data
          ↓
Feature Processing
          ↓
Machine Learning Model
          ↓
Predicted Performance
          ↓
Student Dashboard
```

---

# 5.2 Study Pattern Analyzer

The Study Pattern Analyzer analyzes how students interact with the platform.

It can examine patterns such as:

* Study frequency
* Study duration
* Practice frequency
* Question attempts
* Accuracy
* Topic engagement
* Performance trends

The objective is to identify meaningful learning behaviors and provide insights into how the student studies.

### Example

```text
Student Activity
       ↓
Data Collection
       ↓
Feature Extraction
       ↓
Pattern Analysis
       ↓
Learning Behaviour Insights
```

---

# 5.3 Topic Recommender

The Topic Recommender identifies mathematics topics that students should focus on based on their historical performance.

The recommendation system considers factors such as:

* Topic accuracy
* Recent performance
* Question difficulty
* Attempt history
* Student mastery
* Weak-topic identification

### Recommendation Flow

```text
Student Performance
        ↓
Topic Performance Analysis
        ↓
Identify Weak Topics
        ↓
Recommendation Model
        ↓
Recommended Topics
        ↓
Personalized Practice
```

The objective is to avoid giving every student the same practice questions.

---

# 6. Adaptive Learning

MathSy incorporates an **ELO-inspired rating system** to estimate student mastery and question difficulty.

The system maintains ratings for both:

```text
Student Mastery
       +
Question Difficulty
       ↓
Performance Update
       ↓
Updated Mastery
       ↓
Future Question Selection
```

As students answer questions, their estimated mastery can change according to their performance.

This enables the platform to provide progressively more appropriate practice questions.

---

# 7. Targeted Review Generation

When a student struggles with a question, MathSy can generate a targeted review question based on the original problem.

The generated question attempts to preserve:

* Mathematical concept
* Topic
* Difficulty
* SPM-style structure

while changing the question values or context.

### Example

```text
Student gets Question Wrong
            ↓
       Identify Topic
            ↓
      Analyze Difficulty
            ↓
     Generate Variant
            ↓
       New Question
            ↓
      Student Practices
            ↓
      Update Mastery
```

This creates a continuous learning cycle rather than treating each question as an isolated activity.

---

# 8. Student Dashboard & Learning Analytics

MathSy provides students with an overview of their learning progress.

The dashboard can present information such as:

* Overall performance
* Mathematics accuracy
* Topic performance
* Weak areas
* Recommended topics
* Learning trends
* Study patterns
* Predicted performance
* Practice history

The goal is to help students understand **how they are progressing and where they should improve**.

---

# Overall System Architecture

MathSy consists of several interconnected components.

```text
                         ┌─────────────────┐
                         │     Student     │
                         └────────┬────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │     React Frontend     │
                     │      TypeScript        │
                     │       Material UI      │
                     └────────────┬───────────┘
                                  │
                              REST API
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │     Flask Backend      │
                     │        Python          │
                     └────────────┬───────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
      ┌─────────────┐      ┌──────────────┐    ┌──────────────┐
      │  AI Tutor   │      │ Quick Snap   │    │     ML       │
      │   Chatbot   │      │  AI System   │    │   System     │
      └─────────────┘      └──────┬───────┘    └──────┬───────┘
                                  │                   │
                                  ▼                   ▼
                           ┌─────────────┐     ┌──────────────┐
                           │     RAG     │     │ ML Models    │
                           │   Pipeline  │     │              │
                           └──────┬──────┘     │ Grade        │
                                  │            │ Prediction   │
                    ┌─────────────┼───────┐    │              │
                    │             │       │    │ Study Pattern│
                    ▼             ▼       ▼    │              │
                Pinecone       MySQL   Marking │ Topic        │
                Vector DB              Schemes│ Recommender  │
                                              └──────┬───────┘
                                                     │
                                                     ▼
                                            Student Profile
                                                     │
                                                     ▼
                                            Personalized
                                             Learning
```

---

# Complete Learning Cycle

One of MathSy's key concepts is connecting all components into a continuous learning loop.

```text
                    Student
                       │
                       ▼
                 Practice Question
                       │
                       ▼
                 Solve / Submit
                       │
                       ▼
              AI Feedback & Grading
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    Update Mastery            Update ML Data
          │                         │
          │              ┌──────────┼──────────┐
          │              ▼          ▼          ▼
          │           Grade      Study      Topic
          │        Prediction   Pattern   Recommendation
          │              │          │          │
          └──────────────┴──────────┴──────────┘
                         │
                         ▼
                 Identify Weak Areas
                         │
                         ▼
                 Recommend Practice
                         │
                         ▼
                Targeted Review
                         │
                         ▼
                    Practice
                         │
                         └───────────────↺
```

This creates a **closed-loop personalized learning system**.

---

# 🛠️ Technology Stack

### Frontend

* React
* TypeScript
* Material UI
* Chart.js

### Backend

* Python
* Flask
* RESTful APIs

### Artificial Intelligence

* Large Language Models
* Prompt Engineering
* Retrieval-Augmented Generation
* AI Mathematics Tutor

### Machine Learning

* Grade Prediction
* Study Pattern Analysis
* Topic Recommendation
* Student Performance Analysis

### Mathematical Processing

* SymPy
* Custom Python mathematical solvers

### Data & Infrastructure

* MySQL
* Pinecone
* Firebase Authentication
* Git / GitHub

### Deployment

* Vercel
* Cloud-based backend/database services

---

# System Components

| Component              | Purpose                                              |
| ---------------------- | ---------------------------------------------------- |
| AI Mathematics Tutor   | Provides conversational mathematical assistance      |
| Quick Snap AI          | Processes uploaded mathematics questions             |
| Generate Solution      | Generates step-by-step solutions                     |
| Check My Work          | Evaluates student working                            |
| RAG Pipeline           | Retrieves relevant SPM questions and marking schemes |
| Mathematical Solvers   | Performs specialized mathematical calculations       |
| SymPy Verification     | Validates mathematical operations                    |
| Grade Prediction       | Predicts student performance                         |
| Study Pattern Analyzer | Identifies learning behavior                         |
| Topic Recommender      | Recommends areas for improvement                     |
| ELO-inspired System    | Estimates mastery and question difficulty            |
| Targeted Review        | Generates additional practice questions              |
| Student Dashboard      | Visualizes learning progress                         |

---

# 🎯 Project Objectives

The project aims to:

1. Develop an AI-powered SPM Mathematics learning platform.
2. Develop an AI mathematics tutor capable of providing step-by-step explanations.
3. Implement RAG using SPM questions and marking schemes.
4. Develop mathematical solving and verification mechanisms.
5. Develop machine learning models for student performance analysis.
6. Analyze student study patterns.
7. Recommend mathematics topics based on student performance.
8. Implement adaptive learning based on student mastery.
9. Generate targeted review questions.

---

# Project Structure

```text
MathSy/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── ...
│
├── backend/
│   ├── routes/
│   ├── services/
│   ├── solvers/
│   ├── models/
│   └── ...
│
├── machine-learning/
│   ├── grade-prediction/
│   ├── study-pattern/
│   ├── topic-recommender/
│   └── ...
│
├── rag/
│   ├── embeddings/
│   ├── retrieval/
│   └── ...
│
├── database/
│   ├── schema/
│   └── ...
│
├── requirements.txt
├── README.md
└── ...
```

---

# Getting Started

## Prerequisites

Make sure the following are installed:

* Python 3.x
* Node.js
* npm
* MySQL
* Git

---

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/MathSy.git

cd MathSy
```

---

## Backend

```bash
cd backend

python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# Environment Variables

Create a `.env` file for sensitive configuration.

Example:

```text
OPENAI_API_KEY=
PINECONE_API_KEY=

MYSQL_HOST=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DATABASE=

FIREBASE_API_KEY=
```

**Never commit API keys, passwords, or credentials to GitHub.**

Add the following to `.gitignore`:

```text
.env
.env.*
__pycache__/
venv/
node_modules/
```

---

# Limitations

As an academic prototype, MathSy has several limitations:

* AI-generated responses may occasionally contain errors.
* Mathematical question recognition can be affected by image quality.
* The platform is primarily focused on the SPM Mathematics syllabus.
* Machine learning performance depends on the quality and quantity of available student data.
* Recommendations may become more accurate as more learning data is collected.
* Some complex mathematical problems require additional specialized solver logic.
* AI-generated review questions require validation to ensure syllabus and difficulty alignment.

---

# Future Enhancements

Future development could include:

* Voice-based AI mathematics tutor
* Improved handwritten mathematical work recognition
* Better mathematical diagram understanding
* Teacher dashboard
* Classroom management functionality
* Support for additional SPM subjects
* Automated full SPM practice paper generation
* More advanced student knowledge modelling
* Multi-agent mathematical reasoning
* More advanced learning analytics
* Continuous model improvement using additional learning data

---

# Project Team

MathSy was developed as a Final Year Project at **Asia Pacific University of Technology & Innovation (APU)**.

### Project

**MathSy — Personalized AI-Powered SPM Mathematics Learning Platform**

### Team Members

* **Chin Ker Rou**
* **Chuah Yew Ken**

---

# Academic Context

This project was developed as part of the requirements for the **Bachelor of Science (Hons) in Computer Science with a Specialism in Artificial Intelligence**.

The project combines multiple areas of computer science and artificial intelligence:

```text
Artificial Intelligence
        │
        ├── Large Language Models
        │
        ├── Retrieval-Augmented Generation
        │
        ├── Natural Language Processing
        │
        ├── Machine Learning
        │
        ├── Recommendation Systems
        │
        ├── Adaptive Learning
        │
        └── Mathematical AI
```

---

# ⭐ What Makes MathSy Different? ⭐

MathSy is designed to go beyond simply answering mathematics questions.

Instead of:

```text
Question
   ↓
Answer
```

MathSy follows a personalized learning approach:

```text
                Student
                   ↓
              Ask / Practice
                   ↓
             AI Assistance
                   ↓
          Solve / Check Work
                   ↓
          Analyze Performance
                   ↓
       ┌───────────┴───────────┐
       ↓                       ↓
   AI / RAG                 ML Models
       │                       │
       └───────────┬───────────┘
                   ↓
           Student Profile
                   ↓
          Identify Weaknesses
                   ↓
          Recommend Topics
                   ↓
          Targeted Practice
                   ↓
           Update Mastery
                   ↓
             Learn Better
                   ↺
```

**MathSy is not simply an AI mathematics solver. It is a personalized AI learning platform designed to understand student performance, identify learning needs, and continuously adapt the learning experience.**
