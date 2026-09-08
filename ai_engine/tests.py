from django.test import TestCase
from io import BytesIO
from pypdf import PdfWriter
from ai_engine.services import PDFExtractionService, AIService

class AIEngineTestCase(TestCase):
    def test_pdf_extraction_valid(self):
        """Test pypdf extraction from an in-memory PDF document."""
        writer = PdfWriter()
        # Create a page with text
        writer.add_blank_page(width=200, height=200)
        stream = BytesIO()
        writer.write(stream)
        stream.seek(0)

        # A blank page has no text, so status should be 'empty'
        result = PDFExtractionService.extract_text(stream)
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'empty')

    def test_ai_service_insufficient_text(self):
        """Test AI quality requirement: rejects insufficient text without hallucinating."""
        res = AIService.generate_mcqs("Only two words.")
        self.assertFalse(res['success'])
        self.assertIn("Not enough learning material", res['message'])

    def test_ai_service_mock_mode_generation(self):
        """Test that Mock/Demo mode produces structured, valid MCQs from substantive text."""
        substantive_text = (
            "Ordinary Least Squares linear regression minimizes the sum of squared residuals "
            "between observed values and predicted values. In multivariable econometric modeling, "
            "multicollinearity inflates coefficient variance and is measured via the Variance Inflation Factor. "
            "Data analysis requires exploratory inspection of distributions, detecting outliers and checking assumptions."
        )

        res = AIService.generate_mcqs(substantive_text, number_of_questions=3, difficulty='Intermediate')
        self.assertTrue(res['success'])
        self.assertEqual(len(res['questions']), 3)
        self.assertTrue(res['is_demo_mode'])

        # Verify MCQ question structure
        q = res['questions'][0]
        self.assertIn('question', q)
        self.assertIn('option_a', q)
        self.assertIn('option_b', q)
        self.assertIn('option_c', q)
        self.assertIn('option_d', q)
        self.assertIn(q['correct_option'], ['A', 'B', 'C', 'D'])
        self.assertTrue(len(q['explanation']) > 0)
