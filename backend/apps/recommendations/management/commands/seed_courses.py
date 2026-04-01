"""Seed courses for learning recommendations."""
from django.core.management.base import BaseCommand
from apps.recommendations.models import Course


COURSES = [
    # Docker
    ("Docker for Beginners", "Udemy", "https://www.udemy.com/course/docker-tutorial-for-devops-run-docker-containers/",
     ["Docker", "Containerization", "DevOps"]),
    ("Docker and Kubernetes: The Complete Guide", "Udemy", "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/",
     ["Docker", "Kubernetes", "DevOps", "CI/CD"]),

    # Kubernetes
    ("Kubernetes for the Absolute Beginners", "Udemy", "https://www.udemy.com/course/learn-kubernetes/",
     ["Kubernetes", "Docker", "DevOps"]),
    ("Certified Kubernetes Administrator (CKA)", "Linux Foundation", "https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/",
     ["Kubernetes", "Linux", "DevOps"]),

    # AWS
    ("AWS Certified Solutions Architect – Associate", "AWS", "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
     ["AWS", "Cloud Computing", "Terraform"]),
    ("AWS for Beginners", "Coursera", "https://www.coursera.org/learn/aws-fundamentals-going-cloud-native",
     ["AWS", "Cloud Computing"]),

    # Python
    ("Python for Everybody", "Coursera", "https://www.coursera.org/specializations/python",
     ["Python", "Data Science", "Programming"]),
    ("Complete Python Bootcamp", "Udemy", "https://www.udemy.com/course/complete-python-bootcamp/",
     ["Python", "Programming", "Algorithms"]),

    # Machine Learning
    ("Machine Learning Specialization", "Coursera", "https://www.coursera.org/specializations/machine-learning-introduction",
     ["Machine Learning", "Python", "Deep Learning", "Statistics"]),
    ("Deep Learning Specialization", "Coursera", "https://www.coursera.org/specializations/deep-learning",
     ["Deep Learning", "Machine Learning", "TensorFlow", "Keras"]),

    # Data Science
    ("Data Science Professional Certificate", "IBM / Coursera", "https://www.coursera.org/professional-certificates/ibm-data-science",
     ["Data Science", "Python", "SQL", "Machine Learning", "Pandas", "NumPy"]),
    ("Applied Data Science with Python", "Coursera", "https://www.coursera.org/specializations/data-science-python",
     ["Python", "Data Science", "Pandas", "NumPy", "matplotlib"]),

    # SQL & Databases
    ("The Complete SQL Bootcamp", "Udemy", "https://www.udemy.com/course/the-complete-sql-bootcamp/",
     ["SQL", "PostgreSQL", "Databases"]),
    ("Databases and SQL for Data Science", "Coursera", "https://www.coursera.org/learn/sql-data-science",
     ["SQL", "Databases", "Data Science"]),

    # JavaScript & React
    ("The Complete JavaScript Course", "Udemy", "https://www.udemy.com/course/the-complete-javascript-course/",
     ["JavaScript", "Node.js", "Programming"]),
    ("React - The Complete Guide", "Udemy", "https://www.udemy.com/course/react-the-complete-guide-incl-redux/",
     ["React", "JavaScript", "TypeScript"]),

    # Terraform
    ("HashiCorp Certified: Terraform Associate", "HashiCorp", "https://developer.hashicorp.com/certifications/infrastructure-automation",
     ["Terraform", "AWS", "Infrastructure as Code", "DevOps"]),

    # Ansible
    ("Ansible for the Absolute Beginner", "Udemy", "https://www.udemy.com/course/learn-ansible/",
     ["Ansible", "Linux", "DevOps", "Automation"]),

    # Linux
    ("Linux Command Line Basics", "Udemy", "https://www.udemy.com/course/linux-command-line-volume1/",
     ["Linux", "Scripting", "DevOps"]),

    # CI/CD
    ("Jenkins, From Zero to Hero", "Udemy", "https://www.udemy.com/course/jenkins-from-zero-to-hero/",
     ["Jenkins", "CI/CD", "DevOps", "Docker"]),

    # Git
    ("Git & GitHub Bootcamp", "Udemy", "https://www.udemy.com/course/git-and-github-bootcamp/",
     ["Git", "GitHub", "Version Control"]),

    # TypeScript
    ("Understanding TypeScript", "Udemy", "https://www.udemy.com/course/understanding-typescript/",
     ["TypeScript", "JavaScript", "React"]),

    # System Design
    ("Grokking the System Design Interview", "Educative", "https://www.educative.io/courses/grokking-modern-system-design-interview-for-engineers-managers",
     ["System Design", "Scalability", "Distributed Systems"]),

    # Django / Backend
    ("Django for Everybody", "Coursera", "https://www.coursera.org/specializations/django",
     ["Django", "Python", "REST API", "PostgreSQL"]),
    ("Build REST APIs with Django REST Framework", "Udemy", "https://www.udemy.com/course/build-a-backend-rest-api-with-python-django-advanced/",
     ["Django", "REST API", "Python", "PostgreSQL"]),

    # Spark / Big Data
    ("Spark and Python for Big Data", "Udemy", "https://www.udemy.com/course/spark-and-python-for-big-data-with-pyspark/",
     ["Spark", "Python", "Hadoop", "Big Data"]),

    # Communication / Soft Skills
    ("Communication Foundations", "LinkedIn Learning", "https://www.linkedin.com/learning/communication-foundations",
     ["Communication", "Team Management", "Stakeholder Management"]),
]


class Command(BaseCommand):
    help = "Seed courses for learning recommendations"

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for title, provider, url, skills in COURSES:
            _, was_created = Course.objects.get_or_create(
                title=title,
                provider=provider,
                defaults={"url": url, "skills_taught": skills},
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Courses seeded: {created} created, {skipped} already existed"
        ))