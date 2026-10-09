# EduFund Match

EduFund Match is a hybrid backend recommendation engine designed for the Indian scholarship landscape. It bridges the gap between predictive profiling and strict legal compliance.

## Key Features
- **Machine Learning Layer:** Uses a Random Forest Classifier (`scikit-learn`) trained on student features to predict financial vulnerability tiers.
- **Deterministic Policy Filters:** Applies strict rule-based checking for income thresholds, caste categories, and gender mandates (e.g., AICTE Pragati scheme).
- **Defensive Programming:** Features robust input validation loops with error handling to gracefully catch invalid user data during live demos.
- **Structured Architecture:** Relies on externalized CSV databases (`pandas`) for scalability.
