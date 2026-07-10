# StudyPools 🏊

StudyPools is a web application built with Flask that takes the mess out of collaborative studying. It allows users to create dedicated, private group workspaces ("study pools"), upload their coursework materials natively, and generate algorithm-driven document summaries using language models. Crucially, the app isolates file tracking so that your readings and summaries are completely locked to the specific group space you are working in.

---

## 💻 Core Features

* **Secure Authentication:** User accounts, logins, and hashed password security to keep profiles private.
* **Isolated Group Pools:** Dedicated shared spaces where group members can collaborate without their documents leaking into other pools.
* **Smart File Parsing:** Powered by Microsoft's MarkItDown, the app automatically extracts text from various formats like PDFs, Word files, and PowerPoint slides, converting them into clean Markdown text.
* **Contextual Summarization Engine:** A targeted endpoint that handles OpenAI API requests. It checks the active `group_id` before processing, ensuring the AI only looks at and summarizes files belonging to that specific workspace.
* **Factual AI Summaries:** Generates quick reference overviews based strictly on the text inside the uploaded documents, preventing hallucinations or random data mixing.

---

## 📊 Relational Database Design

The app replaces messy local file tracking with a structured relational database (SQLite managed via SQLAlchemy ORM). The database stores:

* **User Profiles:** Core account credentials and personal settings.
* **Study Groups:** Tracking metadata for each created pool workspace.
* **Group Memberships:** The specific rules mapping which users have access to which pools.
* **Notes & Documents:** Secure storage paths and metadata for uploaded notes, strictly bound to their respective user and group IDs.

---
## SEO Tech Developer — Summer Residency (2026)

### Created By 👾
* **Aaron Bezi**
* **Cailan Jeremiah-Barry**
* **Diego Perez-Aguilar**
* **Sheyla Almanzar-Abreu**
