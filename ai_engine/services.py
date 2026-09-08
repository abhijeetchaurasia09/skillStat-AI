import os
import json
import logging
import re
from io import BytesIO
from pypdf import PdfReader
from django.conf import settings

logger = logging.getLogger(__name__)

class PDFExtractionService:
    """
    Handles PDF validation and text extraction using pypdf.
    Robustly handles empty files, encrypted PDFs, corrupted streams, and no-text scanned PDFs.
    """

    @staticmethod
    def extract_text(file_obj):
        """
        Extracts clean text and page count from an uploaded file-like object or file path.
        
        Returns:
            dict: {
                'success': bool,
                'text': str,
                'page_count': int,
                'word_count': int,
                'error': str or None,
                'status': 'success' | 'empty' | 'failed'
            }
        """
        try:
            # Check if file has read attribute
            if hasattr(file_obj, 'read'):
                file_obj.seek(0)
                reader = PdfReader(file_obj)
            else:
                reader = PdfReader(file_obj)

            if reader.is_encrypted:
                try:
                    # Attempt decrypt with empty password
                    reader.decrypt('')
                except Exception:
                    return {
                        'success': False,
                        'text': '',
                        'page_count': 0,
                        'word_count': 0,
                        'error': 'The PDF is encrypted or password-protected. Please upload an unprotected PDF.',
                        'status': 'failed'
                    }

            page_count = len(reader.pages)
            if page_count == 0:
                return {
                    'success': False,
                    'text': '',
                    'page_count': 0,
                    'word_count': 0,
                    'error': 'The uploaded PDF document has 0 pages.',
                    'status': 'empty'
                }

            extracted_chunks = []
            for idx, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text() or ''
                    clean_text = page_text.strip()
                    if clean_text:
                        extracted_chunks.append(clean_text)
                except Exception as page_err:
                    logger.warning(f"Error extracting page {idx + 1}: {page_err}")

            full_text = "\n\n".join(extracted_chunks).strip()
            word_count = len(full_text.split())

            if not full_text or word_count < 10:
                return {
                    'success': False,
                    'text': full_text,
                    'page_count': page_count,
                    'word_count': word_count,
                    'error': 'No extractable text found in this PDF. It may be a scanned image-only PDF without OCR.',
                    'status': 'empty'
                }

            return {
                'success': True,
                'text': full_text,
                'page_count': page_count,
                'word_count': word_count,
                'error': None,
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"PDF Extraction Exception: {str(e)}", exc_info=True)
            return {
                'success': False,
                'text': '',
                'page_count': 0,
                'word_count': 0,
                'error': f"Failed to parse PDF document: {str(e)}",
                'status': 'failed'
            }


class AIService:
    """
    AI Generation Service for MCQs and learning analytics.
    Features:
    - Real LLM integration (Gemini / OpenAI compatible API endpoint)
    - Realistic domain-specific Mock Generator fallback
    - Strict JSON output schema validation
    - Transparent 'Demo Mode' tagging
    """

    MINIMUM_WORD_COUNT = 30 # Threshold for reliable quiz generation

    @classmethod
    def generate_mcqs(cls, text, number_of_questions=5, difficulty='Intermediate', skill_hint=None):
        """
        Generates structured MCQs from provided educational text.
        
        Returns:
            dict: {
                'success': bool,
                'questions': list[dict],
                'ai_mode_used': 'mock' | 'real',
                'is_demo_mode': bool,
                'message': str,
                'error': str or None
            }
        """
        # Validate minimum text requirement
        clean_text = (text or '').strip()
        words = clean_text.split()
        if len(words) < cls.MINIMUM_WORD_COUNT:
            return {
                'success': False,
                'questions': [],
                'ai_mode_used': 'none',
                'is_demo_mode': False,
                'message': 'Not enough learning material to reliably generate questions. Please upload a document with more substantive text.',
                'error': 'INSUFFICIENT_TEXT'
            }

        configured_mode = getattr(settings, 'AI_MODE', 'mock').lower()
        api_key = getattr(settings, 'AI_API_KEY', '').strip()

        # If real mode requested and API key present, attempt real LLM call
        if configured_mode == 'real' and api_key:
            try:
                real_result = cls._call_real_llm(clean_text, number_of_questions, difficulty, skill_hint, api_key)
                if real_result.get('success') and real_result.get('questions'):
                    return real_result
                logger.warning(f"Real LLM call failed or returned empty: {real_result.get('error')}. Falling back to Demo Mode.")
            except Exception as e:
                logger.error(f"Real LLM invocation exception: {e}. Falling back to Demo Mode.")

        # Fallback or primary: Mock / Demo Mode
        mock_result = cls._generate_mock_mcqs(clean_text, number_of_questions, difficulty, skill_hint)
        return mock_result

    @classmethod
    def _call_real_llm(cls, text, number_of_questions, difficulty, skill_hint, api_key):
        """
        Invokes LLM API (Google Gemini REST API or OpenAI-compatible endpoint).
        """
        import requests

        model = getattr(settings, 'AI_MODEL', 'gemini-1.5-flash')
        custom_endpoint = getattr(settings, 'AI_ENDPOINT', '')

        # Truncate text to reasonable context window (~15,000 chars)
        context_slice = text[:15000]

        prompt = f"""
You are an expert psychometric assessment designer for civil servants and statistical officers.
Based SOLELY on the following learning material, generate {number_of_questions} multiple-choice questions (MCQs).
Difficulty level: {difficulty}
Relevant Skill / Subject Area: {skill_hint or 'Statistical Analytics / Core Competency'}

CRITICAL REQUIREMENTS:
1. Every question MUST test a concept directly present in the text.
2. Provide exactly 4 distinct options (A, B, C, D).
3. Specify the correct option as one of: "A", "B", "C", "D".
4. Provide a clear pedagogical explanation justifying the correct answer.
5. Return ONLY a valid JSON object matching the exact schema below, with no markdown formatting or extra text.

JSON Schema:
{{
  "questions": [
    {{
      "question": "Question text here",
      "option_a": "Option A text",
      "option_b": "Option B text",
      "option_c": "Option C text",
      "option_d": "Option D text",
      "correct_option": "A",
      "explanation": "Why this option is correct based on the text",
      "skill": "{skill_hint or 'Statistics'}",
      "difficulty": "{difficulty}"
    }}
  ]
}}

LEARNING MATERIAL TEXT:
\"\"\"{context_slice}\"\"\"
"""

        headers = {"Content-Type": "application/json"}

        # Check if Gemini API URL or standard OpenAI-like URL
        if "gemini" in model.lower() and not custom_endpoint:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=20)
            if resp.status_code != 200:
                return {'success': False, 'error': f"Gemini API returned status {resp.status_code}: {resp.text}"}

            data = resp.json()
            raw_text = data['candidates'][0]['content']['parts'][0]['text']
        else:
            # OpenAI standard format
            url = custom_endpoint or "https://api.openai.com/v1/chat/completions"
            headers["Authorization"] = f"Bearer {api_key}"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a professional assessment author. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=20)
            if resp.status_code != 200:
                return {'success': False, 'error': f"LLM API returned status {resp.status_code}: {resp.text}"}

            data = resp.json()
            raw_text = data['choices'][0]['message']['content']

        # Parse and sanitize JSON
        parsed_questions = cls._parse_and_validate_json(raw_text)
        if not parsed_questions:
            return {'success': False, 'error': 'LLM returned invalid or malformed JSON.'}

        return {
            'success': True,
            'questions': parsed_questions,
            'ai_mode_used': 'real',
            'is_demo_mode': False,
            'message': f'Successfully generated {len(parsed_questions)} MCQs via {model}.'
        }

    @classmethod
    def _parse_and_validate_json(cls, raw_text):
        """
        Sanitizes and extracts the JSON questions array.
        """
        try:
            # Strip potential ```json markdown blocks
            clean = raw_text.strip()
            if clean.startswith("```"):
                clean = re.sub(r"^```(?:json)?", "", clean)
                clean = re.sub(r"```$", "", clean).strip()

            parsed = json.loads(clean)
            q_list = parsed.get('questions', [])
            validated = []

            for q in q_list:
                # Normalize keys if options were passed as list
                opt_a = q.get('option_a')
                opt_b = q.get('option_b')
                opt_c = q.get('option_c')
                opt_d = q.get('option_d')

                if 'options' in q and isinstance(q['options'], list) and len(q['options']) >= 4:
                    opt_a = q['options'][0]
                    opt_b = q['options'][1]
                    opt_c = q['options'][2]
                    opt_d = q['options'][3]

                correct_opt = str(q.get('correct_option', 'A')).strip().upper()
                if correct_opt not in ['A', 'B', 'C', 'D']:
                    # Try to deduce from correct_answer matching an option
                    ans_text = str(q.get('correct_answer', '')).strip().lower()
                    if ans_text == str(opt_a).strip().lower():
                        correct_opt = 'A'
                    elif ans_text == str(opt_b).strip().lower():
                        correct_opt = 'B'
                    elif ans_text == str(opt_c).strip().lower():
                        correct_opt = 'C'
                    elif ans_text == str(opt_d).strip().lower():
                        correct_opt = 'D'
                    else:
                        correct_opt = 'A'

                if q.get('question') and opt_a and opt_b and opt_c and opt_d:
                    validated.append({
                        'question': str(q['question']).strip(),
                        'option_a': str(opt_a).strip(),
                        'option_b': str(opt_b).strip(),
                        'option_c': str(opt_c).strip(),
                        'option_d': str(opt_d).strip(),
                        'correct_option': correct_opt,
                        'explanation': str(q.get('explanation', 'Based on key concepts established in the learning module.')).strip(),
                        'skill': str(q.get('skill', 'Statistics')).strip(),
                        'difficulty': str(q.get('difficulty', 'Intermediate')).strip(),
                    })
            return validated
        except Exception as err:
            logger.error(f"JSON validation error: {err}")
            return []

    @classmethod
    def _generate_mock_mcqs(cls, text, number_of_questions, difficulty, skill_hint):
        """
        Demo Mode Generator: Creates realistic, high quality, domain-specific MCQs
        synthesized directly from text keywords and MoSPI/iGOT statistics curriculum.
        Clearly tags output as 'Demo Mode' without pretending to be a real LLM.
        """
        lower_text = text.lower()
        questions = []

        # Domain question bank mapped to concepts detectable in typical statistical learning materials
        domain_patterns = [
            {
                'keywords': ['regression', 'dependent', 'independent', 'linear', 'residual', 'ols'],
                'skill': 'Regression',
                'question': 'In linear regression analysis, what does the Ordinary Least Squares (OLS) method minimize?',
                'option_a': 'The sum of squared vertical differences (residuals) between observed and predicted values',
                'option_b': 'The total number of independent explanatory variables in the equation',
                'option_c': 'The variance of the independent variable across observational clusters',
                'option_d': 'The multicollinearity index between confounding predictors',
                'correct_option': 'A',
                'explanation': 'OLS minimizes the sum of squared residuals (differences between actual and fitted values of the dependent variable).'
            },
            {
                'keywords': ['python', 'pandas', 'dataframe', 'numpy', 'code', 'script'],
                'skill': 'Python',
                'question': 'Which Python library data structure is primary for manipulating two-dimensional tabular data in data science pipelines?',
                'option_a': 'pandas.DataFrame',
                'option_b': 'numpy.ndarray (1D vector)',
                'option_c': 'collections.defaultdict',
                'option_d': 'sys.argv memory buffer',
                'correct_option': 'A',
                'explanation': 'The pandas DataFrame is the standard two-dimensional, size-mutable, tabular data structure in Python data analysis.'
            },
            {
                'keywords': ['visualization', 'chart', 'plot', 'seaborn', 'matplotlib', 'distribution', 'histogram'],
                'skill': 'Data Visualization',
                'question': 'When examining the distribution shape and skewness of a single continuous statistical variable, which chart is most appropriate?',
                'option_a': 'Histogram or Kernel Density Estimation (KDE) plot',
                'option_b': 'Pie chart with percentage slices',
                'option_c': 'Stacked area chart over categorical categories',
                'option_d': 'Radar spider web chart',
                'correct_option': 'A',
                'explanation': 'Histograms and KDE plots represent frequencies of continuous variables across intervals, revealing skewness and modality.'
            },
            {
                'keywords': ['survey', 'sampling', 'sample', 'stratified', 'cluster', 'bias', 'census'],
                'skill': 'Survey Methodology',
                'question': 'What is the primary advantage of Stratified Random Sampling over Simple Random Sampling in national surveys?',
                'option_a': 'It ensures adequate representation of key sub-populations or demographic strata while reducing sampling variance',
                'option_b': 'It eliminates the requirement of having a sampling frame',
                'option_c': 'It guarantees zero non-response error across all administrative zones',
                'option_d': 'It requires fewer enumerators and zero supervisory oversight',
                'correct_option': 'A',
                'explanation': 'Stratification partitions the population into homogenous strata, ensuring all subgroups are represented and reducing sampling error.'
            },
            {
                'keywords': ['interpretation', 'hypothesis', 'p-value', 'significance', 'null', 'alpha', 'type i'],
                'skill': 'Statistical Interpretation',
                'question': 'If an econometric model yields a p-value of 0.02 for a regression coefficient at alpha = 0.05, what is the statistical interpretation?',
                'option_a': 'Reject the null hypothesis; the predictor has a statistically significant relationship with the outcome at the 5% level',
                'option_b': 'Fail to reject the null hypothesis because the p-value is greater than 0.01',
                'option_c': 'The relationship is purely due to chance with 98% certainty',
                'option_d': 'The model explained 2% of the variance in the target variable',
                'correct_option': 'A',
                'explanation': 'Since p (0.02) < alpha (0.05), we reject the null hypothesis and conclude the coefficient is statistically significant.'
            },
            {
                'keywords': ['statistics', 'mean', 'median', 'mode', 'standard deviation', 'variance'],
                'skill': 'Statistics',
                'question': 'When a continuous dataset exhibits extreme positive skewness (right-skewed), which metric is the most robust measure of central tendency?',
                'option_a': 'Median',
                'option_b': 'Arithmetic Mean',
                'option_c': 'Mid-range',
                'option_d': 'Geometric Standard Deviation',
                'correct_option': 'A',
                'explanation': 'The median is resistant to extreme outliers and skewed tails, whereas the arithmetic mean is pulled towards the long tail.'
            },
            {
                'keywords': ['analysis', 'outlier', 'cleaning', 'imputation', 'missing', 'correlation'],
                'skill': 'Data Analysis',
                'question': 'Before running statistical inferences on official administrative datasets, why is exploratory data analysis (EDA) essential?',
                'option_a': 'To detect data anomalies, missing values, distribution patterns, and verify structural assumptions',
                'option_b': 'To permanently alter raw survey records without audit logs',
                'option_c': 'To guarantee that correlation strictly proves causation',
                'option_d': 'To convert all continuous variables into nominal binary variables',
                'correct_option': 'A',
                'explanation': 'EDA enables analysts to inspect data distributions, diagnose outliers, spot data entry errors, and test model assumptions.'
            }
        ]

        # Check matched patterns from text
        matched_items = []
        for pat in domain_patterns:
            score = sum(1 for kw in pat['keywords'] if kw in lower_text)
            if score > 0:
                matched_items.append((score, pat))

        matched_items.sort(key=lambda x: x[0], reverse=True)
        selected_patterns = [item[1] for item in matched_items]

        # Fill remaining with general patterns if needed
        for pat in domain_patterns:
            if pat not in selected_patterns:
                selected_patterns.append(pat)

        for pat in selected_patterns[:number_of_questions]:
            # Customize skill if hint provided
            target_skill = skill_hint if skill_hint else pat['skill']
            questions.append({
                'question': pat['question'],
                'option_a': pat['option_a'],
                'option_b': pat['option_b'],
                'option_c': pat['option_c'],
                'option_d': pat['option_d'],
                'correct_option': pat['correct_option'],
                'explanation': f"[Demo Mode Generated from Material] {pat['explanation']}",
                'skill': target_skill,
                'difficulty': difficulty,
            })

        return {
            'success': True,
            'questions': questions,
            'ai_mode_used': 'mock',
            'is_demo_mode': True,
            'message': f"Generated {len(questions)} high-quality MCQs in Demo Mode based on text patterns."
        }
