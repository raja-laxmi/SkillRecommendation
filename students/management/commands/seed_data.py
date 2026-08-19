from django.core.management.base import BaseCommand

from students import cognodb


class Command(BaseCommand):
    help = "Create demo students, skills and colleges in CognoDB"

    def handle(self, *args, **options):

        demo_students = [
            {
                "student_id": "DEMO001",
                "name": "Raja",
                "email": "raja@example.com",
                "bio": "Python and Django developer",
                "college": "Mesco College",
                "location": "Hyderabad",
                "skills": ["Python", "Django"],
            },
            {
                "student_id": "DEMO002",
                "name": "Priya",
                "email": "priya@example.com",
                "bio": "Python developer interested in backend development",
                "college": "ABC College",
                "location": "Hyderabad",
                "skills": ["python"],
            },
            {
                "student_id": "DEMO003",
                "name": "Anu",
                "email": "anu@example.com",
                "bio": "Django and React developer",
                "college": "Mesco College",
                "location": "Hyderabad",
                "skills": ["Django", "React"],
            },
            {
                "student_id": "DEMO004",
                "name": "Rahul",
                "email": "rahul@example.com",
                "bio": "Java developer",
                "college": "XYZ College",
                "location": "Hyderabad",
                "skills": ["Java"],
            },
        ]

        for data in demo_students:

            # ------------------------------------------------
            # Student
            # ------------------------------------------------

            cognodb.create_student(
                data["student_id"],
                data["name"],
                data["email"],
                data["bio"],
            )

            # ------------------------------------------------
            # Skills
            # ------------------------------------------------

            for skill_name in data["skills"]:

                cognodb.add_skill_to_student_by_name(
                    data["student_id"],
                    skill_name,
                )

            # ------------------------------------------------
            # College
            # ------------------------------------------------

            college_id = cognodb.make_college_id(
                data["college"]
            )

            cognodb.get_or_create_college(
                college_id,
                data["college"],
                data["location"],
            )

            cognodb.add_student_college(
                data["student_id"],
                college_id,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created/updated: {data['name']}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed data completed successfully."
            )
        )