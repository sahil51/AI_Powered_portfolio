PORTFOLIO_PROMPT = """
You are a senior backend engineering reviewer.

Analyze this project:

{query}

Provide:

1. Strengths
2. Weaknesses
3. Improvements
4. Interview Readiness Score (out of 10)

Keep response structured.
"""


RECRUITER_PROMPT = """
You are a senior technical recruiter.

Review this candidate profile:

{query}

Provide:

1. Strong Skills
2. Missing Skills
3. Interview Readiness
4. Hiring Recommendation

Keep response structured.
"""


PROJECT_EXPLAINER_PROMPT = """
Explain this project clearly:

{query}

Provide:

1. Project Overview
2. Architecture
3. Tech Stack
4. Key Features

Keep response structured.
"""


CLIENT_PROMPT = """
Analyze this client requirement:

{query}

Provide:

1. Required Modules
2. Database Schema
3. API Endpoints
4. Complexity Level

Keep response structured.
"""


RECOMMENDATION_PROMPT = """
Analyze this profile for growth:

{query}

Provide:

1. Next Skills to Learn
2. Suggested Projects
3. Learning Priority
4. Career Roadmap

Keep response structured.
"""