import os
import hashlib

from dotenv import load_dotenv
from neo4j import GraphDatabase


# ============================================================
# NEO4J CONNECTION
# ============================================================

load_dotenv()

NEO4J_URI = os.getenv("COGNODB_URI") 
NEO4J_USERNAME = os.getenv("COGNODB_USERNAME") 
NEO4J_PASSWORD = os.getenv("COGNODB_PASSWORD") 

if not NEO4J_URI:
    raise RuntimeError("NEO4J_URI is missing from .env")

if not NEO4J_USERNAME:
    raise RuntimeError("NEO4J_USERNAME is missing from .env")

if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD is missing from .env")


driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
)


# ============================================================
# HELPERS
# ============================================================

def _node_to_dict(node):
    """Convert a Neo4j Node into a normal Python dictionary."""
    if node is None:
        return None
    return dict(node)


def normalize_skill_name(name):
    """
    Make skill matching case-insensitive.

    Python / PYTHON / python / PyThOn
    all become: python
    """
    return " ".join(name.strip().lower().split())


def make_skill_id(normalized_name):
    """
    Stable ID for a skill.

    The same normalized skill always gets the same ID.
    Example:
        python -> SK-...
        Python -> same SK-...
    """
    digest = hashlib.sha256(
        normalized_name.encode("utf-8")
    ).hexdigest()[:8]

    return f"SK-{digest}"


def normalize_college_name(name):
    return " ".join(name.strip().lower().split())


def make_college_id(name):
    normalized = normalize_college_name(name)
    digest = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()[:8]

    return f"COL-{digest}"


# ============================================================
# CONNECTION TEST
# ============================================================

def test_connection():
    with driver.session() as session:
        record = session.run(
            "RETURN 'CognoDB connected!' AS message"
        ).single()

        return record["message"]


# Backward-compatible name if another file uses it.
def test_cognodb():
    return test_connection()


# ============================================================
# STUDENT
# ============================================================

def create_student(student_id, name, email, bio=""):
    with driver.session() as session:
        record = session.run(
            """
            MERGE (s:Student {student_id: $student_id})
            SET s.name = $name,
                s.email = $email,
                s.bio = $bio
            RETURN s
            """,
            student_id=student_id,
            name=name,
            email=email,
            bio=bio,
        ).single()

        return _node_to_dict(record["s"])


def get_student(student_id):
    with driver.session() as session:
        record = session.run(
            """
            MATCH (s:Student {student_id: $student_id})
            RETURN s
            """,
            student_id=student_id,
        ).single()

        return _node_to_dict(record["s"]) if record else None


def update_student(student_id, name, email, bio=""):
    with driver.session() as session:
        record = session.run(
            """
            MATCH (s:Student {student_id: $student_id})
            SET s.name = $name,
                s.email = $email,
                s.bio = $bio
            RETURN s
            """,
            student_id=student_id,
            name=name,
            email=email,
            bio=bio,
        ).single()

        return _node_to_dict(record["s"]) if record else None


def delete_student(student_id):
    with driver.session() as session:
        record = session.run(
            """
            MATCH (s:Student {student_id: $student_id})
            DETACH DELETE s
            RETURN count(s) AS deleted
            """,
            student_id=student_id,
        ).single()

        return record["deleted"]


# ============================================================
# SKILLS
# ============================================================

def create_skill(skill_id, name):
    """
    Backward-compatible function.

    Creates/fetches a skill by normalized name.
    The normalized name is the real identity used for matching.
    """
    normalized_name = normalize_skill_name(name)

    with driver.session() as session:
        record = session.run(
            """
            MERGE (skill:Skill {
                normalized_name: $normalized_name
            })
            ON CREATE SET
                skill.skill_id = $skill_id,
                skill.name = $name
            ON MATCH SET
                skill.name = coalesce(skill.name, $name)
            RETURN skill
            """,
            skill_id=skill_id,
            name=name.strip(),
            normalized_name=normalized_name,
        ).single()

        return _node_to_dict(record["skill"])


def get_or_create_skill(name):
    normalized_name = normalize_skill_name(name)

    if not normalized_name:
        return None

    skill_id = make_skill_id(normalized_name)

    return create_skill(
        skill_id,
        name.strip(),
    )


def add_skill_to_student(student_id, skill_id):
    with driver.session() as session:
        record = session.run(
            """
            MATCH (s:Student {student_id: $student_id})
            MATCH (skill:Skill {skill_id: $skill_id})
            MERGE (s)-[:HAS_SKILL]->(skill)
            RETURN skill
            """,
            student_id=student_id,
            skill_id=skill_id,
        ).single()

        return _node_to_dict(record["skill"]) if record else None


def add_skill_to_student_by_name(student_id, skill_name):
    """
    The main skill function.

    If Python already exists:
        connect student -> existing Python node.

    If Python does not exist:
        create Python node -> connect student.

    Case-insensitive and whitespace-normalized.
    """
    skill = get_or_create_skill(skill_name)

    if not skill:
        return None

    return add_skill_to_student(
        student_id,
        skill["skill_id"],
    )


def get_student_skills(student_id):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (s:Student {student_id: $student_id})
                  -[:HAS_SKILL]->(skill:Skill)
            RETURN skill
            ORDER BY skill.name
            """,
            student_id=student_id,
        )

        return [
            _node_to_dict(record["skill"])
            for record in result
        ]


# ============================================================
# LOOKING FOR SKILL
# ============================================================

def add_looking_for_skill(student_id, skill_id):
    with driver.session() as session:
        session.run(
            """
            MATCH (s:Student {student_id: $student_id})
            MATCH (skill:Skill {skill_id: $skill_id})
            MERGE (s)-[:LOOKING_FOR]->(skill)
            """,
            student_id=student_id,
            skill_id=skill_id,
        )


# ============================================================
# COLLEGE
# ============================================================

def create_college(college_id, name, location=""):
    normalized_name = normalize_college_name(name)

    with driver.session() as session:
        record = session.run(
            """
            MERGE (c:College {
                normalized_name: $normalized_name
            })
            ON CREATE SET
                c.college_id = $college_id,
                c.name = $name,
                c.location = $location
            ON MATCH SET
                c.name = coalesce(c.name, $name),
                c.location = coalesce(c.location, $location)
            RETURN c
            """,
            college_id=college_id,
            name=name.strip(),
            location=location.strip(),
            normalized_name=normalized_name,
        ).single()

        return _node_to_dict(record["c"])


def get_or_create_college(college_id, name, location=""):
    return create_college(
        college_id,
        name,
        location,
    )


def add_student_college(student_id, college_id):
    with driver.session() as session:
        record = session.run(
            """
            MATCH (s:Student {student_id: $student_id})
            MATCH (c:College {college_id: $college_id})

            // A student should have only one current college.
            OPTIONAL MATCH (s)-[old:STUDIES_AT]->(:College)
            DELETE old

            MERGE (s)-[:STUDIES_AT]->(c)

            RETURN c
            """,
            student_id=student_id,
            college_id=college_id,
        ).single()

        return _node_to_dict(record["c"]) if record else None


# Backward-compatible alias.
def add_college_to_student(student_id, college_id):
    return add_student_college(
        student_id,
        college_id,
    )


def update_college_for_student(student_id, college_id):
    return add_student_college(
        student_id,
        college_id,
    )


def get_student_college(student_id):
    with driver.session() as session:
        record = session.run(
            """
            MATCH (s:Student {student_id: $student_id})
                  -[:STUDIES_AT]->(college:College)
            RETURN college
            """,
            student_id=student_id,
        ).single()

        return _node_to_dict(record["college"]) if record else None


# ============================================================
# PROJECTS
# ============================================================

def create_project(project_id, name, description, image=None):
    with driver.session() as session:
        record = session.run(
            """
            MERGE (p:Project {project_id: $project_id})
            SET p.name = $name,
                p.description = $description,
                p.image = $image
            RETURN p
            """,
            project_id=project_id,
            name=name,
            description=description,
            image=image,
        ).single()

        return _node_to_dict(record["p"])


def add_student_project(student_id, project_id):
    with driver.session() as session:
        session.run(
            """
            MATCH (s:Student {student_id: $student_id})
            MATCH (p:Project {project_id: $project_id})
            MERGE (s)-[:WORKED_ON]->(p)
            """,
            student_id=student_id,
            project_id=project_id,
        )


# Backward-compatible alias.
def add_project_student(student_id, project_id):
    return add_student_project(
        student_id,
        project_id,
    )


def get_student_projects(student_id):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (s:Student {student_id: $student_id})
                  -[:WORKED_ON]->(project:Project)
            RETURN project
            ORDER BY project.name
            """,
            student_id=student_id,
        )

        return [
            _node_to_dict(record["project"])
            for record in result
        ]


def update_project(project_id, name, description, image=None):
    with driver.session() as session:
        record = session.run(
            """
            MATCH (p:Project {project_id: $project_id})
            SET p.name = $name,
                p.description = $description,
                p.image = $image
            RETURN p
            """,
            project_id=project_id,
            name=name,
            description=description,
            image=image,
        ).single()

        return _node_to_dict(record["p"]) if record else None


def delete_project(project_id):
    with driver.session() as session:
        record = session.run(
            """
            MATCH (p:Project {project_id: $project_id})
            DETACH DELETE p
            RETURN count(p) AS deleted
            """,
            project_id=project_id,
        ).single()

        return record["deleted"]


# ============================================================
# SKILL RECOMMENDATIONS
# ============================================================

def get_skill_recommendations(student_id, limit=10):
    """
    Recommend students who share at least one skill.

    IMPORTANT:
    If two students have the same skill node, they match.

    Students from the same college are excluded here because
    they are shown separately in college recommendations.
    """

    with driver.session() as session:
        
        result = session.run(
        """
        MATCH (me:Student {student_id: $student_id})
            -[:HAS_SKILL]->(my_skill:Skill)

        WITH me, collect(DISTINCT my_skill) AS my_skills

        MATCH (other:Student)-[:HAS_SKILL]->(other_skill:Skill)

        WHERE other.student_id <> $student_id
        AND ALL(skill IN my_skills
                WHERE NOT (other)-[:HAS_SKILL]->(skill))

        WITH other, collect(DISTINCT other_skill.name) AS other_skills

        RETURN other, other_skills As matching_skills
        ORDER BY rand()
        LIMIT $limit
        """,
        student_id=student_id,
        limit=limit,
)
        return [
    {
        "student": _node_to_dict(record["other"]),
        "matching_skills": record["matching_skills"],
    }
    for record in result
]


# Backward-compatible function name.
def find_recommendations(student_id):
    return get_skill_recommendations(student_id)


# ============================================================
# COLLEGE RECOMMENDATIONS
# ============================================================

def get_same_college_students(student_id, limit=10):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (me:Student {student_id: $student_id})
                  -[:STUDIES_AT]->(college:College)

            MATCH (other:Student)
                  -[:STUDIES_AT]->(college)

            WHERE other.student_id <> $student_id

            RETURN DISTINCT other, college
            ORDER BY rand()
            LIMIT $limit
            """,
            student_id=student_id,
            limit=limit,
        )

        return [
            {
                "student": _node_to_dict(record["other"]),
                "college": _node_to_dict(record["college"]),
            }
            for record in result
        ]


# ============================================================
# SEARCH
# ============================================================

def search_students(student_id, query, limit=20):
    """
    Search by:
      - student name
      - skill
      - college
    """

    query = " ".join(query.strip().lower().split())

    if not query:
        return []

    with driver.session() as session:
        result = session.run(
            """
            MATCH (student:Student)
            WHERE student.student_id <> $student_id

            OPTIONAL MATCH (student)-[:HAS_SKILL]->(skill:Skill)
            OPTIONAL MATCH (student)-[:STUDIES_AT]->(college:College)

            WITH student,
                 collect(DISTINCT skill.name) AS skills,
                 college

            WHERE
                toLower(coalesce(student.name, '')) CONTAINS $query

                OR ANY(
                    skill_name IN skills
                    WHERE toLower(skill_name) CONTAINS $query
                )

                OR (
                    college IS NOT NULL
                    AND toLower(coalesce(college.name, '')) CONTAINS $query
                )

            RETURN student, skills, college
            LIMIT $limit
            """,
            student_id=student_id,
            query=query,
            limit=limit,
        )

        return [
            {
                "student": _node_to_dict(record["student"]),
                "skills": record["skills"],
                "college": _node_to_dict(record["college"])
                    if record["college"] else None,
            }
            for record in result
        ]


# ============================================================
# CONNECTION REQUESTS
# ============================================================

def send_connection_request(sender_id, receiver_id):
    if sender_id == receiver_id:
        raise ValueError("You cannot send a request to yourself.")

    with driver.session() as session:
        record = session.run(
    """
    MATCH (sender:Student {student_id: $sender_id})
    MATCH (receiver:Student {student_id: $receiver_id})

    MERGE (sender)-[r:SENT_REQUEST_TO]->(receiver)

    ON CREATE SET
        r.status = 'pending'

    ON MATCH SET
        r.status = 'pending'

    RETURN r.status AS result
    """,
    sender_id=sender_id,
    receiver_id=receiver_id
)


def get_pending_requests(student_id):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (sender:Student)
                  -[r:SENT_REQUEST_TO]->
                  (receiver:Student {student_id: $student_id})

            WHERE r.status = 'pending'

            RETURN sender
            ORDER BY sender.name
            """,
            student_id=student_id,
        )

        return [
            _node_to_dict(record["sender"])
            for record in result
        ]


# Alias used by the upgraded views.
def get_connection_requests(student_id):
    return get_pending_requests(student_id)


def accept_connection(sender_id, receiver_id):
    """
    sender_id = person who sent the request
    receiver_id = logged-in person accepting it
    """

    with driver.session() as session:
        record = session.run(
            """
            MATCH (sender:Student {student_id: $sender_id})
                  -[r:SENT_REQUEST_TO]->
                  (receiver:Student {student_id: $receiver_id})

            WHERE r.status = 'pending'

            DELETE r

            MERGE (sender)-[:CONNECTED_WITH]->(receiver)
            MERGE (receiver)-[:CONNECTED_WITH]->(sender)

            RETURN true AS accepted
            """,
            sender_id=sender_id,
            receiver_id=receiver_id,
        ).single()

        return bool(record and record["accepted"])


def accept_connection_request(receiver_id, sender_id):
    return accept_connection(
        sender_id,
        receiver_id,
    )


def reject_connection(sender_id, receiver_id):
    with driver.session() as session:
        record = session.run(
            """
            MATCH (sender:Student {student_id: $sender_id})
                  -[r:SENT_REQUEST_TO]->
                  (receiver:Student {student_id: $receiver_id})

            WHERE r.status = 'pending'

            DELETE r

            RETURN true AS rejected
            """,
            sender_id=sender_id,
            receiver_id=receiver_id,
        ).single()

        return bool(record and record["rejected"])


def reject_connection_request(receiver_id, sender_id):
    return reject_connection(
        sender_id,
        receiver_id,
    )


def get_connections(student_id):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (me:Student {student_id: $student_id})
                  -[:CONNECTED_WITH]-(other:Student)

            RETURN DISTINCT other
            ORDER BY other.name
            """,
            student_id=student_id,
        )

        return [
            _node_to_dict(record["other"])
            for record in result
        ]


# ============================================================
# CLEAN SHUTDOWN
# ============================================================

def close_driver():
    driver.close()