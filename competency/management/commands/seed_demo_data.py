from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from competency.models import Skill, UserCompetency, Assessment, AssessmentQuestion
from learning.models import Course, LearningMaterial, Recommendation
from learning.services import RecommendationService
from quizzes.models import Quiz, QuizQuestion

class Command(BaseCommand):
    help = "Seeds database with demo user (demo/demo123), skills, courses, assessments, and initial competency gaps."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Initializing SkillStat AI demo dataset..."))

        # 1. Create or reset demo user
        user, created = User.objects.get_or_create(username="demo")
        user.set_password("demo123")
        user.first_name = "Vikram"
        user.last_name = "Sharma"
        user.email = "vikram.sharma@mospi.gov.in"
        user.is_staff = True
        user.is_superuser = True
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.department = "Ministry of Statistics & Programme Implementation (MoSPI)"
        profile.job_role = "Senior Statistical Officer / Data Analyst"
        profile.bio = "Civil servant specializing in national sample surveys, macroeconomic indicators, and predictive econometric modeling."
        profile.save()

        self.stdout.write(self.style.SUCCESS(f"User created: demo / demo123 (Staff/Admin enabled)"))

        # 2. Define Skills
        skills_data = [
            {
                "name": "Statistics",
                "category": "Core Analytics",
                "required_level": 80,
                "icon": "bi-bar-chart-steps",
                "description": "Descriptive statistics, probability distributions, variance estimation, and statistical inference.",
                "demo_level": 82.0
            },
            {
                "name": "Python",
                "category": "Technical",
                "required_level": 80,
                "icon": "bi-terminal-fill",
                "description": "Python programming, pandas dataframes, numpy vectorized computation, and data scripting.",
                "demo_level": 45.0
            },
            {
                "name": "Data Analysis",
                "category": "Core Analytics",
                "required_level": 80,
                "icon": "bi-search",
                "description": "Exploratory data analysis (EDA), data wrangling, missing data imputation, and outlier detection.",
                "demo_level": 60.0
            },
            {
                "name": "Data Visualization",
                "category": "Core Analytics",
                "required_level": 80,
                "icon": "bi-pie-chart-fill",
                "description": "Information design, interactive charts, dashboards, matplotlib, seaborn, and visual storytelling.",
                "demo_level": 40.0
            },
            {
                "name": "Regression",
                "category": "Core Analytics",
                "required_level": 80,
                "icon": "bi-graph-up-arrow",
                "description": "Linear and multivariable regression, Ordinary Least Squares (OLS), residual diagnostics, and elasticity modeling.",
                "demo_level": 35.0
            },
            {
                "name": "Survey Methodology",
                "category": "Methodology",
                "required_level": 80,
                "icon": "bi-clipboard-data-fill",
                "description": "Sample design, stratified cluster sampling, survey weights, questionnaire design, and non-sampling errors.",
                "demo_level": 72.0
            },
            {
                "name": "Statistical Interpretation",
                "category": "Governance",
                "required_level": 80,
                "icon": "bi-lightbulb-fill",
                "description": "Hypothesis testing, p-values, confidence intervals, policy implication translation, and causality evaluation.",
                "demo_level": 65.0
            },
        ]

        skills_dict = {}
        for s in skills_data:
            skill, _ = Skill.objects.update_or_create(
                name=s["name"],
                defaults={
                    "category": s["category"],
                    "required_level": s["required_level"],
                    "icon": s["icon"],
                    "description": s["description"]
                }
            )
            skills_dict[s["name"]] = skill

            # Set user competency baseline
            UserCompetency.objects.update_or_create(
                user=user,
                skill=skill,
                defaults={
                    "current_level": s["demo_level"],
                    "assessment_count": 1
                }
            )

        self.stdout.write(self.style.SUCCESS("Skills and baseline competency levels populated."))

        # 3. Create Courses
        courses_data = [
            {
                "title": "Regression Fundamentals & Econometric Modeling",
                "skill": "Regression",
                "difficulty": "Intermediate",
                "duration": "6 Hours",
                "igot_id": "IGOT-STAT-301",
                "description": "Master linear regression, multivariable modeling, assumption checking, and residual diagnostics for policy forecasting."
            },
            {
                "title": "Data Visualization & Dashboard Design for Policy Insights",
                "skill": "Data Visualization",
                "difficulty": "Beginner",
                "duration": "4 Hours",
                "igot_id": "IGOT-VIS-204",
                "description": "Transform complex administrative datasets into clear, communicative charts and executive reporting dashboards."
            },
            {
                "title": "Python for Statistical Analysis & Automation",
                "skill": "Python",
                "difficulty": "Intermediate",
                "duration": "8 Hours",
                "igot_id": "IGOT-PY-102",
                "description": "Hands-on data manipulation with Pandas, NumPy, and statistical computing workflows for government officers."
            },
            {
                "title": "Exploratory Data Analysis (EDA) Fundamentals",
                "skill": "Data Analysis",
                "difficulty": "Beginner",
                "duration": "5 Hours",
                "igot_id": "IGOT-ANAL-101",
                "description": "Techniques for discovering data patterns, detecting anomalies, testing hypotheses, and checking data cleanliness."
            },
            {
                "title": "Advanced Survey Sampling & Fieldwork Methodology",
                "skill": "Survey Methodology",
                "difficulty": "Advanced",
                "duration": "10 Hours",
                "igot_id": "IGOT-SURV-401",
                "description": "Rigorous treatment of multi-stage stratified cluster sampling, weighting techniques, and non-response adjustment."
            },
            {
                "title": "Statistical Interpretation & Policy Decision Making",
                "skill": "Statistical Interpretation",
                "difficulty": "Intermediate",
                "duration": "5 Hours",
                "igot_id": "IGOT-INTP-205",
                "description": "Translate p-values, confidence bounds, and effect sizes into sound governmental decisions and white papers."
            },
            {
                "title": "Foundational Applied Statistics for Governance",
                "skill": "Statistics",
                "difficulty": "Beginner",
                "duration": "6 Hours",
                "igot_id": "IGOT-STAT-101",
                "description": "Core statistical principles: probability theory, measures of dispersion, normal distribution, and central limit theorem."
            },
        ]

        for c in courses_data:
            Course.objects.update_or_create(
                title=c["title"],
                defaults={
                    "skill": skills_dict[c["skill"]],
                    "difficulty": c["difficulty"],
                    "estimated_duration": c["duration"],
                    "igot_course_id": c["igot_id"],
                    "description": c["description"],
                    "provider": "iGOT Karmayogi / SkillStat AI",
                    "is_active": True
                }
            )

        self.stdout.write(self.style.SUCCESS("Courses populated."))

        # 4. Create Diagnostic Assessment & Questions
        assessment, _ = Assessment.objects.update_or_create(
            title="Core Competency Diagnostic Assessment",
            defaults={
                "description": "Official baseline assessment evaluating key statistical competencies for officers, researchers, and data analysts.",
                "is_active": True,
                "time_limit_minutes": 25
            }
        )

        assessment_questions_data = [
            # Regression (2 questions)
            {
                "skill": "Regression",
                "question_text": "Which technique is commonly used to model the mathematical relationship between a continuous dependent variable and one or more independent predictor variables?",
                "option_a": "Linear Regression",
                "option_b": "K-Means Clustering",
                "option_c": "Binary Hash Search",
                "option_d": "Principal Component Rotation",
                "correct_option": "A",
                "explanation": "Linear regression is the standard statistical methodology for estimating the relationship between a dependent target and independent predictors.",
                "difficulty": "Beginner"
            },
            {
                "skill": "Regression",
                "question_text": "What does a high coefficient of determination (R-squared = 0.88) indicate in an ordinary least squares regression model?",
                "option_a": "88% of the variance in the dependent variable is explained by the independent variables",
                "option_b": "The model has an 88% probability of being completely free from multicollinearity",
                "option_c": "The residuals are guaranteed to follow a standard normal distribution",
                "option_d": "The independent variables are 88% correlated with each other",
                "correct_option": "A",
                "explanation": "R-squared measures the proportion of variance in the dependent variable explained by predictors in the model.",
                "difficulty": "Intermediate"
            },
            # Python (2 questions)
            {
                "skill": "Python",
                "question_text": "In the pandas library, which method is primarily used to read a comma-separated values file into a DataFrame?",
                "option_a": "pd.read_csv()",
                "option_b": "pd.open_table()",
                "option_c": "pd.load_file()",
                "option_d": "pd.parse_records()",
                "correct_option": "A",
                "explanation": "pd.read_csv() is the standard and optimized pandas function to import CSV data into a 2D DataFrame.",
                "difficulty": "Beginner"
            },
            {
                "skill": "Python",
                "question_text": "Which vectorized numpy operation computes the element-wise boolean check for missing or null values in numerical arrays?",
                "option_a": "np.isnan()",
                "option_b": "np.is_empty()",
                "option_c": "np.check_null()",
                "option_d": "np.drop_na()",
                "correct_option": "A",
                "explanation": "np.isnan() checks elements of an array and returns a boolean array marking NaN values.",
                "difficulty": "Intermediate"
            },
            # Data Visualization (2 questions)
            {
                "skill": "Data Visualization",
                "question_text": "Which chart type is best suited to display five-number summary statistics (minimum, Q1, median, Q3, maximum) and detect outliers?",
                "option_a": "Box and Whisker Plot",
                "option_b": "Pie Chart",
                "option_c": "Stacked Bar Chart",
                "option_d": "Bubble Plot",
                "correct_option": "A",
                "explanation": "Box plots summarize distributions using quartiles, median, and visually flag potential outliers beyond the whiskers.",
                "difficulty": "Beginner"
            },
            {
                "skill": "Data Visualization",
                "question_text": "When comparing multivariate proportions across 10 categories, why are bar charts preferred over pie charts in statistical governance?",
                "option_a": "Human visual perception is much more accurate at judging length comparisons than comparing 2D angles and slice areas",
                "option_b": "Pie charts cannot support color styling",
                "option_c": "Bar charts automatically normalize data to standard deviations",
                "option_d": "Pie charts are not compatible with web browsers",
                "correct_option": "A",
                "explanation": "Psychophysical studies confirm that human perception accurately judges aligned lengths along a common axis far better than angular areas.",
                "difficulty": "Intermediate"
            },
            # Statistics (2 questions)
            {
                "skill": "Statistics",
                "question_text": "According to the Central Limit Theorem, what happens to the distribution of sample means as the sample size (n) becomes sufficiently large?",
                "option_a": "It approximates a Normal Distribution regardless of the original population distribution shape",
                "option_b": "It turns into a Uniform Distribution with equal density",
                "option_c": "The sample variance approaches infinity",
                "option_d": "The standard error becomes exactly equal to the population mean",
                "correct_option": "A",
                "explanation": "The CLT states that regardless of initial distribution shape, the distribution of sample means approaches normality as sample size increases.",
                "difficulty": "Intermediate"
            },
            {
                "skill": "Statistics",
                "question_text": "What is the relationship between Variance and Standard Deviation?",
                "option_a": "Standard Deviation is the positive square root of Variance",
                "option_b": "Variance is twice the Standard Deviation",
                "option_c": "Standard Deviation is Variance divided by sample size (n)",
                "option_d": "There is no mathematical relationship",
                "correct_option": "A",
                "explanation": "Standard deviation is defined as the square root of the variance, restoring units back to the original measurement scale.",
                "difficulty": "Beginner"
            },
            # Data Analysis (2 questions)
            {
                "skill": "Data Analysis",
                "question_text": "Which method is commonly used to treat missing numerical data when the distribution contains extreme skewness and heavy outliers?",
                "option_a": "Median Imputation",
                "option_b": "Arithmetic Mean Imputation",
                "option_c": "Replacing all nulls with zero",
                "option_d": "Removing all columns in the dataset",
                "correct_option": "A",
                "explanation": "The median is robust against extreme values; imputing with the mean would distort the central tendency in skewed data.",
                "difficulty": "Intermediate"
            },
            {
                "skill": "Data Analysis",
                "question_text": "What is an Interquartile Range (IQR)?",
                "option_a": "The difference between the 75th percentile (Q3) and the 25th percentile (Q1)",
                "option_b": "The difference between the maximum and minimum values",
                "option_c": "The average of all quartiles",
                "option_d": "The median divided by four",
                "correct_option": "A",
                "explanation": "IQR = Q3 - Q1, representing the middle 50% spread of the data.",
                "difficulty": "Beginner"
            },
            # Survey Methodology (2 questions)
            {
                "skill": "Survey Methodology",
                "question_text": "What is the primary purpose of applying survey weights (sampling weights) in national socioeconomic surveys?",
                "option_a": "To adjust for unequal selection probabilities and non-response, ensuring sample estimates accurately represent the target population",
                "option_b": "To artificially inflate the sample size to match the total census count",
                "option_c": "To ensure every respondent receives identical compensation",
                "option_d": "To eliminate the need for confidence intervals",
                "correct_option": "A",
                "explanation": "Survey weights invert inclusion probabilities so that estimates computed from sample data correctly generalize to the entire population.",
                "difficulty": "Intermediate"
            },
            {
                "skill": "Survey Methodology",
                "question_text": "What distinguishes non-sampling error from sampling error in survey administration?",
                "option_a": "Non-sampling error arises from coverage, questionnaire wording, response bias, and data entry, occurring in both sample surveys and censuses",
                "option_b": "Non-sampling error only happens when using simple random sampling",
                "option_c": "Non-sampling error can be completely eliminated by increasing sample size to infinity",
                "option_d": "Sampling error occurs only in full censuses",
                "correct_option": "A",
                "explanation": "Non-sampling errors encompass measurement errors, response bias, and data processing mistakes that can occur in any survey or census.",
                "difficulty": "Intermediate"
            },
            # Statistical Interpretation (2 questions)
            {
                "skill": "Statistical Interpretation",
                "question_text": "A policy evaluation report states: 'The intervention had a statistically significant impact (p = 0.003), but an effect size (Cohen's d) of only 0.04.' What does this mean for policymakers?",
                "option_a": "The observed difference is unlikely due to chance, but the real-world practical magnitude of the effect is negligible",
                "option_b": "The policy was wildly successful with massive macroeconomic impact",
                "option_c": "The study was invalid because p and d cannot both be small",
                "option_d": "The intervention caused 4% inflation in the country",
                "correct_option": "A",
                "explanation": "Statistical significance (low p-value) does not equate to practical significance; very large sample sizes can detect tiny, inconsequential effect sizes.",
                "difficulty": "Advanced"
            },
            {
                "skill": "Statistical Interpretation",
                "question_text": "What type of error is committed when a statistical test rejects a true null hypothesis (false positive)?",
                "option_a": "Type I Error (Alpha)",
                "option_b": "Type II Error (Beta)",
                "option_c": "Standard Error of the Mean",
                "option_d": "Multicollinearity Error",
                "correct_option": "A",
                "explanation": "A Type I error occurs when researchers reject the null hypothesis when it is actually true (concluding an effect exists when it does not).",
                "difficulty": "Beginner"
            }
        ]

        AssessmentQuestion.objects.filter(assessment=assessment).delete()
        for q in assessment_questions_data:
            AssessmentQuestion.objects.create(
                assessment=assessment,
                skill=skills_dict[q["skill"]],
                question_text=q["question_text"],
                option_a=q["option_a"],
                option_b=q["option_b"],
                option_c=q["option_c"],
                option_d=q["option_d"],
                correct_option=q["correct_option"],
                explanation=q["explanation"],
                difficulty=q["difficulty"]
            )

        self.stdout.write(self.style.SUCCESS(f"Diagnostic Assessment questions created ({len(assessment_questions_data)} questions)."))

        # 5. Populate Recommendations based on demo gaps
        RecommendationService.generate_recommendations_for_user(user)
        self.stdout.write(self.style.SUCCESS("Explainable AI recommendations generated."))

        # 6. Create a pre-seeded LearningMaterial on Regression & Data Analysis with extracted text
        material_text = """
Regression Analysis and Applied Econometrics in Public Governance.
Section 1: The Foundations of Linear Modeling.
Linear regression is a foundational statistical method used by researchers and statistical officers to model the relationship between a scalar response (dependent variable) and one or more explanatory variables (independent variables). In Ordinary Least Squares (OLS) estimation, the unknown parameters are calculated by minimizing the sum of squared vertical distances between observed responses in the dataset and the fitted responses predicted by the linear approximation.

Section 2: Diagnostic Verification and Model Assumptions.
A robust regression analysis requires verifying four classical Gauss-Markov assumptions:
1. Linearity: The relationship between the predictors and the mean of the dependent variable is linear.
2. Homoscedasticity: The variance of the residual errors is constant across all values of the independent variables.
3. Independence: The error terms are uncorrelated with one another (no autocorrelation).
4. Normality: For hypothesis testing, the residuals are assumed to be normally distributed.

When multicollinearity is present among independent variables, the standard errors of the regression coefficients become inflated, making individual t-tests unreliable even if overall R-squared remains high. To diagnose multicollinearity, analysts compute the Variance Inflation Factor (VIF). Values of VIF exceeding 5 or 10 indicate severe multicollinearity that must be addressed through feature selection or ridge regularization.
"""
        material, _ = LearningMaterial.objects.update_or_create(
            title="MoSPI Manual: Regression Analysis & Applied Econometrics",
            defaults={
                "user": user,
                "skill": skills_dict["Regression"],
                "course": Course.objects.filter(skill=skills_dict["Regression"]).first(),
                "extracted_text": material_text.strip(),
                "page_count": 4,
                "extraction_status": "success",
            }
        )

        # 7. Create a pre-generated sample Quiz linked to this material
        sample_quiz, _ = Quiz.objects.update_or_create(
            title="Knowledge Check: Regression Assumptions & Diagnostics",
            defaults={
                "user": user,
                "material": material,
                "skill": skills_dict["Regression"],
                "difficulty": "Intermediate",
                "source_type": "uploaded_pdf",
                "is_ai_generated": True,
                "ai_mode_used": "mock"
            }
        )

        sample_quiz_questions = [
            {
                "question": "What does Ordinary Least Squares (OLS) estimation minimize when fitting a linear model?",
                "option_a": "The sum of squared vertical distances (residuals) between observed and predicted values",
                "option_b": "The sum of absolute independent variable values",
                "option_c": "The variance inflation factor across all regressors",
                "option_d": "The total number of degrees of freedom in the sample",
                "correct_option": "A",
                "explanation": "OLS estimation determines coefficients by minimizing the sum of squared differences between observed values and fitted values."
            },
            {
                "question": "What statistical issue is diagnosed when the Variance Inflation Factor (VIF) exceeds 5 or 10?",
                "option_a": "Severe Multicollinearity between predictor variables",
                "option_b": "Extreme Heteroscedasticity in error variances",
                "option_c": "Under-sampling bias in field survey strata",
                "option_d": "Negative autocorrelation in time-series residuals",
                "correct_option": "A",
                "explanation": "VIF measures how much the variance of an estimated regression coefficient increases due to collinearity with other predictors."
            },
            {
                "question": "Under the Gauss-Markov theorem, what does the condition of Homoscedasticity require?",
                "option_a": "The variance of the residual errors remains constant across all values of the independent variables",
                "option_b": "The independent variables must have zero covariance with the target",
                "option_c": "All observations must belong to the exact same demographic cluster",
                "option_d": "The sample size must be infinite",
                "correct_option": "A",
                "explanation": "Homoscedasticity means constant error variance; non-constant variance is called heteroscedasticity."
            }
        ]

        QuizQuestion.objects.filter(quiz=sample_quiz).delete()
        for sq in sample_quiz_questions:
            QuizQuestion.objects.create(
                quiz=sample_quiz,
                skill=skills_dict["Regression"],
                question_text=sq["question"],
                option_a=sq["option_a"],
                option_b=sq["option_b"],
                option_c=sq["option_c"],
                option_d=sq["option_d"],
                correct_option=sq["correct_option"],
                explanation=sq["explanation"],
                difficulty="Intermediate"
            )

        self.stdout.write(self.style.SUCCESS("Sample Learning Material and AI-generated Quiz seeded."))
        self.stdout.write(self.style.SUCCESS("================================================"))
        self.stdout.write(self.style.SUCCESS("SkillStat AI demo dataset initialized successfully!"))
        self.stdout.write(self.style.SUCCESS("Demo login: username='demo', password='demo123'"))
        self.stdout.write(self.style.SUCCESS("================================================"))
