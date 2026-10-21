
from django.test import TestCase, Client
from django.urls import reverse
from core.models import Project, Contact, Document, SharedPurpose, SharedExpense, ExpenseSplit, Payment
from decimal import Decimal

class EndToEndTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client = Client()
        self.client.force_login(self.user)
        # Create test project
        self.project1 = Project.objects.create(project_name="Test Project A", location="NYC", purchase_cost=1000, development_cost=500, land_area="1000")
        self.project2 = Project.objects.create(project_name="Test Project B", location="LA", purchase_cost=2000, development_cost=1000, land_area="2000")
        
        # Create contacts
        self.contact1 = Contact.objects.create(name="John Doe", mobile="12345", project=self.project1)
        self.contact2 = Contact.objects.create(name="Jane Doe", mobile="67890", project=self.project2)

    def test_dashboard_global(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Project A")
        self.assertContains(response, "Test Project B")

    def test_dashboard_filtered(self):
        response = self.client.get(reverse('dashboard') + f"?project_id={self.project1.pk}")
        self.assertEqual(response.status_code, 200)

    def test_contact_list_rendering(self):
        response = self.client.get(reverse('contact_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "12345")
        self.assertContains(response, "Test Project A")

    def test_document_creation_and_list(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        doc_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        doc = Document.objects.create(title="Deed", file=doc_file, project=self.project1, related_to="Land")
        
        response = self.client.get(reverse('document_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Deed")
        self.assertContains(response, "Test Project A")

    def test_shared_purpose_project_link(self):
        purpose = SharedPurpose.objects.create(name="Survey", project=self.project2)
        expense = SharedExpense.objects.create(purpose=purpose, description="Survey cost", total_amount=100, paid_by=self.contact1)
        ExpenseSplit.objects.create(shared_expense=expense, participant=self.contact1, amount=50)
        ExpenseSplit.objects.create(shared_expense=expense, participant=self.contact2, amount=50)
        
        self.assertEqual(purpose.project, self.project2)
        response = self.client.get(reverse('shared_expense_list'))
        self.assertEqual(response.status_code, 200)
