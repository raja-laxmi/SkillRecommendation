from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class SignupViewTests(TestCase):
	def signup_data(self):
		return {
			"name": "Test Student",
			"email": "student@example.com",
			"password": "strong-password",
			"bio": "A test student",
			"college_name": "Test College",
			"location": "Test City",
			"skills": "Python, Django",
		}

	@patch("students.views.cognodb.add_student_college")
	@patch("students.views.cognodb.create_college")
	@patch("students.views.cognodb.make_college_id", return_value="COL-test")
	@patch("students.views.cognodb.add_skill_to_student_by_name")
	@patch("students.views.cognodb.get_student", return_value={})
	@patch("students.views.cognodb.create_student")
	def test_signup_creates_account_and_sends_college(
		self,
		create_student,
		get_student,
		add_skill,
		make_college_id,
		create_college,
		add_student_college,
	):
		response = self.client.post(
			reverse("students:signup"),
			self.signup_data(),
		)

		self.assertEqual(
			response["Location"],
			reverse("students:dashboard"),
		)
		self.assertTrue(User.objects.filter(email="student@example.com").exists())
		create_college.assert_called_once_with(
			"COL-test",
			"Test College",
			"Test City",
		)
		add_student_college.assert_called_once()

	@patch(
		"students.views.cognodb.create_student",
		side_effect=ConnectionError("database unavailable"),
	)
	def test_signup_rolls_back_account_when_database_fails(self, create_student):
		response = self.client.post(
			reverse("students:signup"),
			self.signup_data(),
		)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(User.objects.filter(email="student@example.com").exists())
		self.assertContains(
			response,
			"Unable to create account because the database is unavailable.",
		)
