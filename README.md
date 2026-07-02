# Relational Database Normalization Oracle (1NF to 5NF)

A high-fidelity relational database normalization tool built using pure Python algorithms and a custom Streamlit UI matching the **ChronoTask (Outcrowd)** dark aesthetic. Designed as an academic validator and designer assistant.

## Features
- **1NF to 5NF Validation**: Step-by-step trace showing exactly where rules are broken (partial dependencies, transitive dependencies, BCNF violations, multi-valued dependencies, or join dependencies).
- **Candidate Key Finder**: Automated candidate key calculation from user-inputted FDs.
- **Closure Simulator**: Live simulator to compute attribute set closures step-by-step.
- **Decomposition Engine**:
  - **3NF Bernstein's Synthesis**: Generates canonical cover, builds lossless-join & dependency-preserving schemas.
  - **BCNF Decomposition**: Recursive binary split indicating the violating FD for each step.
  - **Chase Lossless Check**: General tabular Chase matrix verification to prove lossless-join decomposition.
  - **Dependency Preservation Check**: Standard linear validation checking if all original FDs are preserved.
- **Presets**: Standard academic templates (Student enrollment, Employee assignment, etc.) to immediately test edge cases.
- **AI Problem Import (Image/PDF)**: Upload a photo, screenshot, or PDF of a normalization question (textbook, handwritten notes, whiteboard) and the AI (Groq vision/text models) will read it and auto-fill the attributes, FDs, MVDs, and JDs on the canvas.

## Getting Started

### Prerequisites
Ensure Python (3.8+) and pip are installed.

### Setup
1. Clone or download this project.
2. Navigate into the project folder:
   ```bash
   cd normalization-validator
   ```
3. Install dependencies:
   ```bash
   py -m pip install -r requirements.txt
   ```

### Running the App
Start the Streamlit application using:
```bash
py -m streamlit run app.py
```

### Running Automated Tests
Run unit tests to verify algorithm correctness:
```bash
py -m unittest test_normalization.py
```
