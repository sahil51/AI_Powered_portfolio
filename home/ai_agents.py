import os
from decouple import config
from .models import Profile, SkillCategory, Experience, Project, Education, ContactItem
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


def get_llm():
    api_key = config("GEMINI_API_KEY", default=None)
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in your .env file")
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)


def get_profile_context(request=None):
    """
    Builds a rich, comprehensive knowledge base from ALL database models.
    This is the single source of truth the AI agent uses to answer questions.
    """
    try:
        profile = Profile.objects.first()
        if not profile:
            return "Profile information is not available."

        # ── Resume URL ──────────────────────────────────────────────────────
        resume_link = "Not provided"
        if profile.resume_file:
            if request:
                resume_link = request.build_absolute_uri(profile.resume_file.url)
            else:
                from django.conf import settings
                base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
                resume_link = f"{base_url}{profile.resume_file.url}"
        elif profile.resume_url:
            resume_link = profile.resume_url

        # ── Skills ──────────────────────────────────────────────────────────
        skills_text = ""
        skill_categories = SkillCategory.objects.prefetch_related("skills").all()
        for cat in skill_categories:
            skill_names = ", ".join(s.name for s in cat.skills.all())
            if skill_names:
                skills_text += f"  • {cat.title}: {skill_names}\n"

        # ── Experience ──────────────────────────────────────────────────────
        experience_text = ""
        experiences = Experience.objects.prefetch_related("projects", "achievements", "techs").all()
        for exp in experiences:
            experience_text += f"\n  [{exp.company} — {exp.role}] ({exp.date_display()})\n"
            experience_text += f"  Location: {exp.location}\n"
            if exp.intro_text:
                experience_text += f"  Overview: {exp.intro_text}\n"
            achievements = exp.achievements.all()
            if achievements:
                experience_text += "  Key Contributions:\n"
                for a in achievements:
                    experience_text += f"    - {a.text}\n"
            projects = exp.projects.all()
            if projects:
                experience_text += "  Projects at this company:\n"
                for p in projects:
                    experience_text += f"    - {p.title}: {p.description}\n"
            techs = exp.techs.all()
            if techs:
                tech_names = ", ".join(t.name for t in techs)
                experience_text += f"  Technologies used: {tech_names}\n"

        # ── Projects ────────────────────────────────────────────────────────
        projects_text = ""
        projects = Project.objects.prefetch_related("techs").all()
        for proj in projects:
            tech_names = ", ".join(t.name for t in proj.techs.all())
            projects_text += f"\n  [{proj.title}]\n"
            projects_text += f"  Description: {proj.description}\n"
            if tech_names:
                projects_text += f"  Tech Stack: {tech_names}\n"
            if proj.project_url:
                projects_text += f"  Live/Repo URL: {proj.project_url}\n"
            if proj.complexity_notes:
                projects_text += f"  Challenges Faced: {proj.complexity_notes}\n"
            if proj.solution_found:
                projects_text += f"  How it was solved: {proj.solution_found}\n"

        # ── Education ───────────────────────────────────────────────────────
        education_text = ""
        educations = Education.objects.prefetch_related("scores").all()
        for edu in educations:
            education_text += f"\n  {edu.institution} — {edu.degree} ({edu.date_range})\n"
            scores = edu.scores.all()
            if scores:
                scores_text = ", ".join(s.label for s in scores)
                education_text += f"  Results: {scores_text}\n"

        # ── Contact Items ────────────────────────────────────────────────────
        contact_text = ""
        contact_items = ContactItem.objects.all()
        for item in contact_items:
            contact_text += f"  • {item.label}: {item.url}\n"

        # ── Assemble Full Context ────────────────────────────────────────────
        context = f"""
=== PERSONAL INFO ===
Name: {profile.name}
Current Role: {profile.terminal_role} at {profile.terminal_company}
Location: {profile.location}
Email: {profile.email}
Phone: {profile.phone}
Resume: {resume_link}

Professional Summary:
{profile.summary_text}

=== SKILLS & TECH STACK ===
{skills_text if skills_text else profile.terminal_stack}

AI/ML Expertise:
{profile.terminal_ai_expertise}

=== WORK EXPERIENCE ===
{experience_text if experience_text else "No experience records found."}

=== PROJECTS ===
{projects_text if projects_text else "No project records found."}

=== EDUCATION ===
{education_text if education_text else "No education records found."}

=== CONTACT DETAILS ===
{contact_text if contact_text else f"Email: {profile.email}"}
"""
        return context

    except Exception as e:
        import traceback
        traceback.print_exc()
        return "Profile information is not available."


class RecruiterAgent:
    """Agent that talks to recruiters and clients on behalf of the user."""

    def __init__(self, phone_number, request=None):
        self.phone_number = phone_number
        self.request = request
        self.llm = get_llm()

    def get_system_prompt(self):
        from .models import Profile
        profile = Profile.objects.first()
        agent_name = profile.ai_agent_name if profile else "AI Assistant"
        
        profile_context = get_profile_context(request=self.request)
        return f"""You are {agent_name}, the official AI Assistant embedded on Sahil Thakur's personal portfolio website. You represent Sahil professionally to recruiters, hiring managers, and potential clients.

You have been provided with Sahil's COMPLETE knowledge base below — his projects (including technical challenges and solutions), all skills, work experience, education, and contact details.

{profile_context}

=== YOUR BEHAVIOR RULES ===

1. SCOPE — STRICTLY ABOUT SAHIL:
   You ONLY answer questions about Sahil Thakur. Any off-topic question (jokes, general tech questions, other people, coding help, math, weather, politics, etc.) must be politely declined with:
   "I'm {agent_name}, Sahil's dedicated portfolio assistant — I can only help with questions about Sahil's background, skills, projects, or how to get in touch. Is there anything specific you'd like to know?"

2. DEEP PROJECT KNOWLEDGE:
   You know every project in detail — description, tech stack, challenges faced, and how they were resolved. Use this to give rich, impressive answers when asked about any project.

3. RESUME:
   If asked for a resume or CV, directly provide the Resume URL. Never say you don't have it unless the URL above says "Not provided".

4. UNKNOWN DETAILS:
   If a specific detail isn't in the knowledge base, respond professionally:
   "I don't have that specific detail on hand. I'd recommend reaching out to Sahil directly — he'd be happy to discuss it further.
   📧 Email: [email]
   📞 Phone: [phone]"

5. HIRING INTEREST:
   If the person expresses interest in hiring or working with Sahil, always end with a strong call-to-action:
   "Sahil is currently open to new opportunities. Feel free to reach out at [email] or connect on LinkedIn — he typically responds within 24 hours!"

6. TONE & FORMAT:
   - Professional, warm, and confident
   - Keep responses to 2-4 short paragraphs maximum
   - Use line breaks and bullet points for readability in chat
   - Never sound robotic or generic — be personable

=== END RULES ===
"""

    def process_message(self, message: str, chat_history: list) -> str:
        """
        Process an incoming message with full conversation history.
        chat_history: list of dicts [{"role": "user"|"ai", "content": "..."}]
        """
        messages = [SystemMessage(content=self.get_system_prompt())]

        for msg in chat_history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content")))
            elif msg.get("role") == "ai":
                messages.append(AIMessage(content=msg.get("content")))

        messages.append(HumanMessage(content=message))

        response = self.llm.invoke(messages)
        return response.content
