# Student Recommendation Platform

A Django-based student networking and recommendation platform powered by Neo4j/CognoDB.

## Features

- Student signup and login
- Student profile
- Skills management
- College information
- Skill-based student recommendations
- College-based student recommendations
- Search students by:
  - Name
  - Skill
  - College
- Send connection requests
- Accept connection requests
- Reject connection requests
- View connections
- Project creation
- Project deletion
- Seed/demo data

## Technology Stack

- Python
- Django
- Neo4j / CognoDB
- Cypher
- HTML
- CSS
- Django authentication

## Recommendation Logic

Skills are normalized before storing.

For example:

Python
python
PYTHON
PyThOn

are treated as the same skill.

The system creates one shared Skill node and connects multiple students to it.

Example:

(Student: Raja)
        |
        | HAS_SKILL
        ↓
(Skill: Python)
        ↑
        | HAS_SKILL
        |
(Student: Priya)

Therefore, Raja and Priya can be recommended to each other based on their shared Python skill.

## College Recommendation

Students from the same college are recommended through the college recommendation system.

If two students have:

- The same skill
- The same college

they are displayed in the college recommendation section instead of the skill recommendation section.

## Search

The dashboard provides search functionality for:

- Student name
- Skill
- College

## Project Structure

```text
project/
│
├── manage.py
├── .env
├── README.md
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── students/
    ├── cognodb.py
    ├── views.py
    ├── urls.py
    │
    ├── templates/
    │   └── students/
    │       ├── signup.html
    │       ├── login.html
    │       ├── dashboard.html
    │       ├── profile.html
    │       ├── edit_profile.html
    │       ├── create_project.html
    │       ├── connections.html
    │       ├── connection_requests.html
    │       ├── skill_recommendation.html
    │       └── college_recommendation.html
    │
    └── management/
        └── commands/
            └── seed_data.py


note: actaully my personal opion is that, it is great for build AI tools or something to manage the data in a graph formatt bu neo4j needed open when we are working in the projec if not it will stopped by it self it makes the progress to slow