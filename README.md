# 🤖 AI-Powered HR Hiring Helper

This app helps HR teams hire people faster.
It uses **3 AI helpers (agents)** to:

1. 📄 **Read and score resumes**
2. 📞 **Call candidates and ask simple job questions**
3. 📅 **Find an interview time and send the invite email**

> 🚧 **Status:** I am still building this. It's my solo student project. Parts marked *(planned)* are not built yet.

> ⚠️ **Very important:** The AI only **gives advice**. A real HR person makes **every big decision**.
> The AI can never reject a person, call a person, or send an interview invite on its own.

The day-by-day plan, the limits and the checklist from the project PDF are in **[information/TASKS.md](information/TASKS.md)**.

I built this project to learn, so I write the code myself. I keep two learning files:
- **[information/problem.md](information/problem.md):** the problems I faced and how I solved them, for interview practice.
- **[information/tips.md](information/tips.md):** my notes, useful code snippets and short answers about how things work (like Blind Mode).

---

## 📚 What's inside

- [What this app does](#-what-this-app-does)
- [Main features](#-main-features)
- [How it works, step by step](#-how-it-works-step-by-step)
- [The 3 AI helpers](#-the-3-ai-helpers)
- [Extra features in detail](#-extra-features-in-detail)
- [Employees and Settings](#-employees-and-settings)
- [Candidate status](#-candidate-status)
- [How the app is built](#-how-the-app-is-built)
- [Tools I use](#-tools-i-use)
- [Folders](#-folders)
- [How to run it](#-how-to-run-it)
- [Secret keys (.env)](#-secret-keys-env)
- [Outside services](#-outside-services)
- [Tests](#-tests)
- [Demo steps](#-demo-steps)
- [Safety and fairness](#-safety-and-fairness)

---

## 🧐 What this app does

HR teams get many resumes. Reading all of them, calling people, and finding interview times takes a lot of time. It's also easy to make mistakes.

This app does the boring parts for HR:
- It reads resumes and says who looks like a good match, and **why**.
- It makes a short screening call and writes down the answers.
- It finds a time that works for everyone and writes the invite email.

But HR always has the final say. There are **3 stop points** where the app waits for HR to say "yes":

1. ✋ Before calling anyone
2. ✋ Before moving someone to an interview
3. ✋ Before sending the invite email

---

## ⭐ Main features

- 📄 Upload a job post and many resumes (PDF or Word)
- 🧮 Scoring changes with the job level (Junior, Mid, Senior or Team Lead)
- 🎯 Every skill is scored on its own, with proof copied from the resume
- ✅ HR can approve, decline or change the AI's advice, and write a reason
- 👥 HR can add, edit and turn off employees (interviewers, managers)
- ⚙️ HR can change the scheduling rules (interview length, work hours and more)
- 📞 Real phone calls with **ElevenLabs** voice AI, or a pretend call for demos
- 📝 Call summaries keep "what the candidate said" apart from "what the AI thinks"
- 📅 Finds interview times and gets the time zones right
- ✉️ Writes the invite email, but sends it only after HR says yes *(built 6 Nov: Agent 3 reads the candidate's times from the call, finds free interviewers inside the Settings rules, writes the invite; HR picks a time, edits, and clicks Approve & send; a failed send can be resent; no time → an HR to-do)*
- 📊 A dashboard showing every candidate, their status and full history *(built 6 Nov: real numbers, newest candidates, to-dos, recent activity; each candidate's profile has a History box)*
- 🔁 Never calls or emails the same person twice by mistake *(tested 6 Nov with a restart test: emails, uploads and approvals are never repeated; the call part is tested when the calling agent is built)*
- 🔐 Login with roles (Admin, HR, Hiring Manager). Each person sees only what they're allowed to
- 🔄 HR can move (reschedule) or cancel an interview, and the candidate gets an update email
- 📌 An HR to-do list for problems the app can't solve alone (like "no free time found")
- 🗑️ HR can fix or delete a candidate's data, and old data is removed after a set time *(built 6 Nov: **Fix details** and **Delete** on the profile; candidates older than 90 days are deleted automatically)*
- ⏳ Scores many resumes in the background, so the screen doesn't freeze

### ⭐ Extra features (not in the project PDF, added to stand out)

- 🙈 **Blind Review Mode:** a switch that hides the name, photo, email, age hints and university, so HR sees "Candidate #7". This helps HR judge only skills, fairly. *(Built 7 Nov: the AI scores a cleaned CV without the name, email, phone or links; the **Blind Mode** switch in the menu shows "Candidate #7" until HR approves for calling; the log says if a decision was made blind. Addresses, universities and age hints are not removed yet.)*
- ✍️ **AI Job Post Writer:** HR types a few lines, and the AI writes the full job post and suggests the skills, weights, level and call questions. HR always checks and edits before saving.
- ~~💬 **"Ask Your Candidates" Chat**~~ ❌ *Dropped on 6 Nov (no time). How it would work: `information/rag.md`.* Old plan: HR asks things like *"Who has AWS and has led a team?"* and gets answers with proof lines from the resumes. It uses **RAG**: first search the resumes, then let the AI answer using only what it found.
- 📬 **CV Match Score Email:** when a candidate sends their CV through the online form, the AI scores it and emails them their **match score out of 100**, their **strengths**, their **weak points** and their **missing skills**. HR sees the same details.

---

## 🔄 How it works, step by step

```mermaid
flowchart TD
    A[HR makes a job post<br/>+ picks the level + adds skills] --> B[CVs come in<br/>online form or HR upload]
    B --> C{Can the app read the file?}
    C -- No --> M[Needs Manual Review]
    C -- Yes --> D[🤖 Agent 1: Score the resume]
    D --> S[📬 CV Match Score email<br/>to the candidate]
    D --> E{{✋ HR stop 1:<br/>Call this person?}}
    E -- No --> X[Closed]
    E -- Yes --> F[🤖 Agent 2: Screening call]
    F --> G{{✋ HR stop 2:<br/>Move to interview?}}
    G -- No --> X
    G -- Yes --> H[🤖 Agent 3: Find a time + write the email]
    H --> I{{✋ HR stop 3:<br/>Send the email?}}
    I -- Yes --> J[Interview Scheduled ✅]
    I -- Change it --> H
```

1. HR makes a job post. HR adds the job title, job post, level, must-have and nice-to-have skills, minimum experience, location and work type (office, remote or hybrid), and the call questions.
2. CVs come in. A candidate can send their CV through the **online form**, or HR can upload CVs. The app pulls the words out of each file. If a file is broken, a human checks it.
3. **Agent 1** scores each resume and puts the best matches at the top.
4. 📬 If the CV came from the online form, the candidate gets their **CV Match Score email**.
5. ✋ HR picks who to call. **A score alone never calls or rejects anyone.**
6. **Agent 2** calls the person, asks if it's okay to record, and asks the job questions.
7. ✋ HR reads the call notes and picks who goes to an interview.
8. **Agent 3** finds a free time and writes the invite email.
9. ✋ HR checks the email and clicks Confirm. Only then is it sent.
10. Every step is saved in the history.

---

## 🤖 The 3 AI helpers

### Agent 1: The Resume Scorer 📄

**Job:** Read each resume and compare it with the job post.

**It gives back:** a score from 0 to 100, a score for each part, proof lines from the resume, what's missing or unclear, and any warnings.

#### Different jobs, different scoring

A junior person and a team lead are **not** judged the same way.
When HR makes a job, they pick a level. Each level cares about different things:

| What is checked | Junior | Mid | Senior | Team Lead |
|---|---|---|---|---|
| Skills | 35% | 40% | 35% | 25% |
| Experience | 10% | 25% | 35% | 25% |
| Projects | 30% | 20% | 15% | 10% |
| Education | 20% | 10% | 5% | 5% |
| Leadership | — | — | 5% | 30% |
| Other | 5% | 5% | 5% | 5% |
| **Total** | 100% | 100% | 100% | 100% |

What each level looks for:
- **Junior:** good projects, internships, courses and certificates. Having little work experience is **okay**.
- **Mid:** has really used the skills in a job and can build things alone.
- **Senior:** lots of real experience, owns big systems, makes design choices.
- **Team Lead:** everything a senior has, **plus** leading people (team size, mentoring, planning).

Leadership counts **only** if the resume says it clearly, like "Led a team of 5". A job title alone is not enough.

These numbers are fixed for each level. HR picks the level when making a job, and that picks the weights. They live in the scoring prompts, not in the database.

#### The CV evaluation prompt template

Agent 1 has **one prompt for each level**, in `app/agents/resume_scoring/prompts.py`. Each prompt gives the AI an expert role (like "an engineering manager who hires team leads"), the weight table for that level, and the same scoring rules. The AI scores 6 parts from 0 to 5, works out the total out of 100, and lists strengths, weak points, missing skills and proof lines. To change the criteria, I edit the tables in that file.

Python then checks the answer: Pydantic makes sure every number is in range, a trick-phrase check warns HR, and each proof line is checked against the real CV. HR always reviews the score.

#### Every skill gets its own score

> *(Planned, not in the current version. Right now Agent 1 scores the 6 parts and lists missing skills.)*

HR marks each skill as:
- **Must-have** or **Nice-to-have**
- How important it is (for example Python = 3, SQL = 2, Docker = 1)
- **Required level from 1 to 5** (for example Python needs 4, SQL needs 2)
- Minimum years *(optional)*

Then the AI gives each skill a number from 0 to 5:

| Number | What it means |
|---|---|
| 0 | Not found |
| 1 | Only written in a skills list, no proof |
| 2 | Used in a project or course |
| 3 | Used at a job |
| 4 | Used at a job for a long time, with good results |
| 5 | Expert, led work using this skill |

Example:

| Skill | Type | Score | Proof from the resume |
|---|---|---|---|
| Python | Must-have | 4 | "Built 3 FastAPI services handling 1M requests a day (2021–2024)" |
| SQL | Must-have | 2 | "Used PostgreSQL in my final-year project" |
| Docker | Nice-to-have | 0 | Not found |

The app compares the candidate's level with the required level, like "Python: has 3, needs 4". If a must-have skill is missing or below the required level, the AI **only warns HR**. It never rejects the person.

#### Rules Agent 1 must follow
- Always show proof from the resume.
- Don't give points just for repeating words many times.
- If it can't find something, say "not found". **Never make things up.**
- Missing info does **not** mean the person doesn't have the skill.
- Never use age, gender, religion, race or anything like that.
- Never punish someone for "too much experience" or an old graduation year. Those can hint at age.
- If a resume has a trick line like "Ignore your rules", the AI ignores it.

---

### Agent 2: The Phone Screener 📞

**Job:** Call the candidate and ask a few simple job questions.

**It gives back:** whether the call happened, whether the person agreed to recording, the questions and answers, when the person is free, questions without a clear answer, a short summary, and a suggested next step for HR.

#### Rules Agent 2 must follow
- Say **"I am an AI assistant"** at the start, and explain why it's calling.
- Ask **"Is it okay if I record this call?"** If the person says no, offer another way (like a call with a real person).
- Ask **only** job questions: experience, notice period, work style and so on.
- **Never** ask about age, religion, family, health, race or politics.
- If the person wants a real human, stop and pass it to HR.
- If nobody picks up, try again, but only up to the limit.
- If it reaches **voicemail**, leave a short polite message (no job details) and mark "No answer".
- If the **line is bad** and it can't hear well, end politely and mark the answers "unclear".
- If the person needs **another language** or has **trouble using a phone call**, end politely and tell HR to offer another way (for example an email form or a call with a real person).
- If the person says **"stop"**, end the call right away and mark it in the history.
- **Never** make up an answer. If an answer is unclear, mark it for HR.
- **It can never reject anyone.** HR decides.

---

### Agent 3: The Scheduler 📅

**Job:** Find an interview time that works for everyone, then write the invite email.

**It gives back:** the time choices, the chosen time, the time zone, the meeting details, the email draft, and whether HR approved and whether the email was sent.

#### Rules Agent 3 must follow
- Offer **only** times when people are really free.
- Get the time zones right. A time zone is the local time in each place.
- The email must have: job name, date, time, time zone, interview length, meeting link, interviewer name, and who to contact to change the time.
- Send **only after** HR clicks Confirm.
- Never send the same email twice.
- HR can **move (reschedule)** or **cancel** an interview. The candidate gets an update email, again only after HR says yes.
- If no time works for both people, add a task to the **HR to-do list** so HR can sort it out by hand.
- If no time works, or sending fails, tell HR. **Never pretend the email was sent.**

---

## ⭐ Extra features in detail

### 🙈 Blind Review Mode

**How the data flows:**

1. **A CV comes in.** All the details (name, email, phone, CV file) are saved **in full** in the database. Nothing is lost.
2. **The AI scores a cleaned copy.** Before the CV text goes to the AI, the app removes the name, email, phone, address, photo and links. So the AI judges **only skills and experience**, and less personal data goes to the outside AI service.
3. **HR reviews in Blind Mode.** When the switch is on, the screen hides the name, photo, email, phone, address, age hints and university. HR sees "Candidate #7".
4. **HR approves → details unlock.** When HR clicks "Approve for Screening", that candidate's real details show again, because the app needs the phone number to call them.
5. **The app contacts the candidate.** Agent 2 takes the phone number **from the database**, not from the screen.

Extra rules:
- The data is only **hidden**, never deleted.
- Blind Mode works in the chat too.
- The history saves whether HR approved with Blind Mode on or off.

### ✍️ AI Job Post Writer
- HR types a short idea, like "need junior Python dev, Lahore, hybrid".
- The AI suggests: the full job post, the level, must-have and nice-to-have skills with weights, and 5 job-only call questions.
- HR **must check and edit** before saving. The AI only suggests.

### 💬 "Ask Your Candidates" Chat (RAG) ❌ dropped on 6 Nov

*Not built, because of time. My RAG notes are in `information/rag.md`. The old plan stays below.*
- Resumes are cut into small pieces and saved in **Chroma** (a small search database on your computer) as embeddings. Embeddings are numbers that capture the meaning of the text.
- When HR asks a question, the app finds the best matching pieces and the AI answers **only from them**, with the proof line and candidate number for each claim.
- If the answer isn't in the resumes, it says "I couldn't find that". It never makes things up.
- It follows the login roles (a Hiring Manager sees only their own jobs) and Blind Mode.
- It refuses questions about age, gender, religion, family or health.
- When a candidate is deleted, their pieces are deleted from Chroma too.

### 📬 CV Match Score Email

**What happens:**

1. A candidate fills in the **online form** for a job and uploads their CV. *(The form service is not chosen yet. I'll pick it when I build this feature.)*
2. The form sends the details to my app.
3. **Agent 1** scores the CV using the **same 4 level rules** (Junior, Mid, Senior or Team Lead) and the skill-by-skill scoring.
4. The app emails the candidate:
   - their **CV Match Score**, for example "72 / 100"
   - their **strengths**, for example "Strong Python and API work"
   - their **weak points**, for example "SQL depth is not clear"
   - their **missing skills**, for example "Docker not found"
5. The same score and details are **saved for HR** and shown on the candidate's page.

**Safety guards:**
- The email says clearly: *"This is an automatic CV match check, not a hiring decision. A person from our team reviews every application."*
- It talks only about **job skills**. It never says "rejected".
- *(Changed 6 Nov)* HR sends it by clicking **Send score to candidate** after scoring. The text is in `app/core/score_email.py`.
- The form asks the candidate to agree to get an automatic feedback email.
- If the CV can't be read, or the AI's answer is broken, **no score email is sent**. The app sends a simple "we got your CV" email instead, and HR checks it.
- Each candidate gets the score email **only once** per job.
- Admin can turn the automatic email **on or off** in Settings.
- Every email is saved in the history (CommunicationLog).

This email is just feedback. It doesn't move the candidate forward. **Calls and interview invites still need HR approval.**

---

## 👥 Employees and Settings

### Employees page

HR can **add, see, edit and turn off** employees.

| What is saved | Example |
|---|---|
| Name and email | Sara Khan, sara@company.test |
| Role | Interviewer / Hiring Manager / HR / Admin |
| Team | Engineering |
| Time zone | Asia/Karachi |
| Can conduct interviews? | Yes or No |
| Available days and times | Only if Yes. For example Mon 10:00–13:00 and Wed 14:00–17:00 |
| Busy times | Leave days and meetings. These block a time even if it's normally free |
| Active? | Yes or No |

People are **turned off** instead of deleted, so old interviews and history stay safe.

*(Built 6 Nov: `app/core/employees.py` + the Employees page. Every change is saved in the audit log. A turned-off person is not offered as a hiring manager.)*

### 🔐 Login and who can see what

Everyone must **log in**. Passwords are saved scrambled (hashed), never as plain text.

| Role | What they can do |
|---|---|
| **Admin** | Everything. Manages employees, settings, email templates and scoring presets |
| **HR Recruiter** | Makes jobs, sees all candidates, approves or declines at all 3 stops, sends emails |
| **Hiring Manager / Interviewer** | Sees **only** candidates for their own jobs. Sees summaries and interview times. Can't approve or send |

Candidates don't log in. They only use the online form and get calls and emails.

### Scheduling Settings page

*(Built 7 Nov: interview length, break, time zone, online or in the office, days ahead, notice, times to offer, max per day, call tries and how long to keep data. A wrong value is refused, and every change is saved in the history. Interviews can be **moved** or **cancelled** from the Interviews page, with an email to the candidate.)*

HR can change these rules any time:

| Setting | Starting value |
|---|---|
| Interview length | 45 minutes |
| Break between interviews | 15 minutes |
| Work hours | 09:00–18:00 |
| Work days | Mon–Fri |
| Main time zone | Asia/Karachi |
| How many days ahead to book | 7 days |
| Shortest notice | 24 hours |
| How many time choices to offer | 3 |
| Most interviews per person per day | 4 |
| Meeting type | Online link or office address |
| Call tries if nobody answers | 2 (4 hours apart) |
| How long to keep candidate data | 90 days, then delete |
| Send the CV Match Score email automatically | On |

Every change is saved in the history.

### Email text

*(Changed 6 Nov: the Templates page was removed.)* The email text is written in the code. The CV Match Score email is in
`app/core/score_email.py` and its design in `app/core/score_email.html` (Jinja2). Red Mail sends it with Gmail. The invite, moved and cancelled emails come with the scheduling agent (Day 7). Every email is saved in
`communication_logs` (who, when, which email, and if it was sent).

---

## 🚦 Candidate status

Each candidate has a **status**. It shows where they are in the process.

```mermaid
stateDiagram-v2
    [*] --> ResumeReceived
    ResumeReceived --> NeedsManualReview: file can't be read
    ResumeReceived --> ScoredHRReview: Agent 1
    NeedsManualReview --> ScoredHRReview: fixed by a human
    ScoredHRReview --> ApprovedForScreening: ✋ HR says yes
    ApprovedForScreening --> ScreeningPending
    ScreeningPending --> ScreeningCompletedHRReview: Agent 2
    ScreeningCompletedHRReview --> ApprovedForInterview: ✋ HR says yes
    ApprovedForInterview --> InterviewProposed: Agent 3
    InterviewProposed --> InterviewScheduled: ✋ HR confirms + email sent
    ScoredHRReview --> Closed
    ScreeningCompletedHRReview --> Closed
    InterviewProposed --> Closed
    InterviewScheduled --> [*]
    Closed --> [*]
```

| Status | What it means |
|---|---|
| Resume Received | The resume has arrived. Waiting to read and score it. |
| Needs Manual Review | Something went wrong. A human needs to check. |
| Scored (HR Review) | The AI scored it. Waiting for HR. |
| Approved for Calling | HR said "yes, call this person". (Renamed from "Approved for Screening" on 5 Nov.) |
| Screening Pending | The call is waiting to happen. |
| Screening Completed (HR Review) | The call is done. Waiting for HR. |
| Approved for Interview | HR said "yes, interview this person". |
| Interview Proposed | Looking for a good time. |
| Interview Scheduled | The email was sent. All done! ✅ |
| Closed | HR stopped the process and wrote a reason. |

---

## 🏗️ How the app is built

*(planned)* The app has separate parts. Each part has one job.

```
┌──────────────────────────────────────────────────────────┐
│   The screens HR uses (Dashboard)  +  Online CV form     │
└───────────────────────────┬──────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────┐
│                     Backend (the engine)                 │
│   ┌──────────────────────────────────────────────────┐   │
│   │   LangGraph: controls the steps + HR stop points │   │
│   └──────┬──────────────────┬──────────────────┬─────┘   │
│   ┌──────▼──────┐   ┌───────▼──────┐   ┌───────▼─────┐   │
│   │  Agent 1    │   │   Agent 2    │   │   Agent 3   │   │
│   │  Scorer     │   │  Screener    │   │  Scheduler  │   │
│   └──────┬──────┘   └───────┬──────┘   └───────┬─────┘   │
└──────────┼──────────────────┼──────────────────┼─────────┘
           │                  │                  │
   ┌───────▼──────┐   ┌───────▼──────┐   ┌───────▼────────┐
   │  AI model +  │   │ ElevenLabs / │   │ Calendar/Email │
   │ resume reader│   │ pretend call │   │ (pretend for   │
   └──────────────┘   └──────────────┘   │  now)          │
           │                             └────────────────┘
   ┌───────▼──────────────────────────────────────────────┐
   │   Database: jobs, candidates, scores, calls,         │
   │   interviews, emails, employees, settings, history   │
   └──────────────────────────────────────────────────────┘
```

### How LangGraph and LangChain help

- **LangGraph** is like a map of the steps. Each candidate walks through the map:
  `read → score → HR stop 1 → call → HR stop 2 → schedule → HR stop 3 → send`
- At each **HR stop**, LangGraph uses `interrupt()`. This **pauses** everything until HR clicks a button. The app can't skip a stop.
- LangGraph **saves its place** after every step (this is called a "checkpoint"). If the app crashes, it carries on from where it stopped and does **not** call or email anyone twice.
- **LangChain** is how each agent talks to the AI. Each AI job is a simple **chain**: `prompt | llm | parser`. The `|` sign means "then".
- It uses `with_structured_output()` so the AI always answers in a neat, fixed shape.
- **LangGraph runs the big steps, and a chain does the AI work inside a step.** The code stays basic, and the features stay high level.
- With LangChain, I can switch to another AI later by changing `.env` and adding that AI's package.

### What is saved (database tables)

| Table | What's in it |
|---|---|
| Employee | name, email, role, team, time zone, can interview?, active?, scrambled password |
| EmployeeAvailability | one row for each free time: employee, day of the week, start time, end time |
| EmployeeBusyTime | one row for each one-off busy time: employee, start, end, reason |
| SchedulingSettings | interview length, break, work hours and days, time zone, booking days, notice, time choices, max per day, call tries, data keep days, auto score email on/off, who changed it, when |
| Job | job id, title, job post, level, minimum experience, location, work type (office/remote/hybrid), hiring manager, scoring weights, status, made by, made at |
| ScreeningQuestion | the call questions for each job, in order |
| JobSkill | skill name, must-have or nice-to-have, importance, required level (1 to 5), minimum years |
| LevelWeights | the starting weights for each level (Junior, Mid, Senior, Team Lead) |
| Candidate | candidate id, name, contact info, time zone, resume file, where the CV came from (form or HR upload), consent choices, current status |
| ResumeEvaluation | total score, part scores, skill scores with proof, strengths, weak points, missing skills, warnings, AI model used |
| Screening | call status, recording consent, answers, summary, which HR person checked it, when |
| Interview | candidate, interviewer, time choices, chosen time, time zone, meeting details, status |
| CommunicationLog | every email or call: when, how, which template version, did it arrive |
| EmailTemplate | score, "got your CV", invite, reschedule and cancel emails + call script, with version numbers |
| HRTask | the HR to-do list: problems the app can't solve alone |
| AuditEvent | the history: who did what, to what, and when |

---

## 🧰 Tools I use

*(planned)*

| Part | Tool | What it does |
|---|---|---|
| Language | Python 3.12 | The coding language |
| Package manager | **uv** | Installs Python and the tools into `.venv` |
| Screens | **Streamlit** | Makes the HR web pages, in `frontend/`. Each page has its own `.css` file. ✅ Decided |
| Webhooks | **FastAPI** | Only receives data from outside my app: ElevenLabs call results. *(The Day 11 online CV form was dropped on 6 Nov.)* The pages call Python directly. ✅ Decided |
| Steps and HR stops | **LangGraph** | Controls the flow and waits for HR |
| Talking to the AI | **LangChain** | Sends prompts and gets neat answers back |
| AI model | **Groq** (with `langchain-groq`) | The "brain". The model name is set in `.env` |
| Checking data | Pydantic | Makes sure data has the right shape |
| Login | bcrypt | Scrambles passwords so they're never saved as plain text |
| Resume search (chat) | ~~Chroma + embeddings~~ | ❌ Dropped on 6 Nov with the RAG chat. Notes only: `information/rag.md` |
| Online CV form | *(to be chosen)* | Where candidates send their CV |
| Database | **SQLite** + hand-written SQL | Saves everything in one file. I write the tables, queries and indexes myself. SQLAlchemy only runs them with `text()`. ✅ Decided |
| Reading resumes | **MarkItDown** | A Microsoft library that pulls the words out of PDF and Word files with one simple call |
| Phone calls | **ElevenLabs** ✅ Decided 5 Nov | Voice AI agent. The same 4 questions for every job: congratulations, available date and time, previous job, why shift. The **script agent** phones the candidate (Twilio number in ElevenLabs) when HR clicks Call, and saves the answers and a summary of the call. Low limits: 3 min per call, 20 calls a day. Notes: `information/elevenlabs.md` |
| Calendar and email | Pretend (mock) versions | Fake versions for safe testing |
| Tests | pytest | Checks that the code works |

### Why SQLite?

- **Nothing to install.** The whole database is just one file in the project folder.
- **It's real SQL.** I write my own tables, queries and indexes, so I learn SQL too.
- **LangGraph works with it.** LangGraph can save its place (checkpoints) straight into SQLite.
- **Good for a student project.** The project PDF suggests it too.
- **Easy to move later.** SQLAlchemy runs my SQL. To switch to PostgreSQL one day, I change `DATABASE_URL` and fix any SQL that works differently there.

---

## 📁 Folders

*(planned)*

```
HR_Automation/
├── app/
│   ├── api/              # FastAPI, only for the ElevenLabs webhook (main.py for now)
│   ├── agents/           # The 3 AI helpers, plus the AI Job Post Writer
│   │   ├── resume_scoring/   # Agent 1, and reader.py (reads PDF and Word files)
│   │   ├── job_writer/       # ⭐ Short idea -> full job draft (own Groq key)
│   │   ├── screening_call/
│   │   └── scheduling/
│   ├── workflow/         # LangGraph steps and HR stop points
│   ├── integrations/     # AI, ElevenLabs, form, calendar, email (real + pretend)
│   ├── extras/           # ⭐ Blind mode, job post writer, RAG chat, match score email
│   ├── models/           # Data shapes (Pydantic)
│   └── core/             # Settings, logging, safety
│       └── database/     # Connection, schema.sql, init_db.py and the .db files
├── frontend/             # The Streamlit web app (see information/streamlit.md)
│   ├── app.py            # Start file: login check and menu
│   ├── base.css          # Styles shared by every page
│   └── pages/            # One folder per page: page.py + page.css
├── .streamlit/           # config.toml: the theme (colors, font)
├── config/               # Scoring presets, call questions, email templates
├── sample_data/
│   ├── job_descriptions/ # Fake job posts
│   └── resumes/          # Empty: CVs come from the web now (5 Nov)
├── tests/                # Tests for AC-01 to AC-12
├── docs/                 # Diagram, test results, final report
├── pyproject.toml        # The list of Python tools (managed by uv)
├── uv.lock               # The exact version of every tool
├── information/          # All my project notes
│   ├── CLAUDE.md         # Project rules and short summary
│   ├── TASKS.md          # Plan, limits and PDF checklist
│   ├── problem.md        # Problems I faced and how I solved them
│   ├── tips.md           # My notes and code snippets
│   ├── streamlit.md      # Everything I learned about Streamlit and CSS
│   └── fastapi.md        # My backend: every file, request and error, with full code
└── README.md             # This file
```

---

## ▶️ How to run it

### What you need first
- [uv](https://docs.astral.sh/uv/), a fast tool that installs Python and Python packages
- Git
- A **Groq** API key. An API key is like a password for the AI.
- *(optional)* An ElevenLabs account, for real phone calls

### Set it up

```bash
# 1. Download the project
git clone <repository-url>
cd HR_Automation

# 2. Install Python and all the tools into a clean space called .venv
uv sync

# 3. Make a new file named .env in the main folder, and add your keys
#    The settings table below lists every key
```

### Start the app

```bash
# Start the app. The pages call the Python code directly, so this is the only command
uv run streamlit run frontend/app.py

# Later, only for the ElevenLabs results webhook (the Day 11 online CV form was dropped on 6 Nov):
# uv run uvicorn app.api.main:app --reload
```

Then open the HR screens: http://localhost:8501

---

## 🔑 Secret keys (.env)

The `.env` file holds secret keys. **Never upload it to GitHub.**

| Name | What it is | Example |
|---|---|---|
| `LLM_PROVIDER` | Which AI company to use | `groq` |
| `GROQ_API_KEY` | The password for Groq, my AI service. LangChain finds it by this name | `gsk_...` |
| `GROQ_JOB_WRITER_API_KEY` | A second Groq key, only for the AI Job Post Writer, so it doesn't use up Agent 1's free limit | `gsk_...` |
| `LLM_MODEL` | Which AI model to use | *(model name)* |
| `DATABASE_URL` | Where the database file is | `sqlite:///./app/core/database/hr_automation.db` |
| `CHECKPOINT_DB_PATH` | Where LangGraph saves its place | `./app/core/database/checkpoints.db` |
| `CHROMA_PATH` | Where the chat's resume search store is saved | `./chroma_db` |
| `EMBEDDING_MODEL` | The model that turns text into embeddings for the chat | *(model name)* |
| `USE_MOCK_CALLS` | `true` = pretend call, `false` = real ElevenLabs call | `true` |
| `ELEVENLABS_API_KEY` | The password for ElevenLabs | `...` |
| `ELEVENLABS_AGENT_ID` | The ID of my voice agent in ElevenLabs | `...` |
| `SMTP_EMAIL` | The Gmail address that sends the CV Match Score email. Empty = MOCK (not really sent). Works since 6 Nov | `...` |
| `SMTP_APP_PASSWORD` | A Gmail **app password** (not my normal password) | `...` |
| `ELEVENLABS_PHONE_NUMBER_ID` | The phone number ElevenLabs calls from | `...` |
| `ELEVENLABS_WEBHOOK_SECRET` | Checks that call notes really came from ElevenLabs | `...` |
| `FORM_WEBHOOK_SECRET` | Checks that new CVs really came from my online form | `...` |
| `USE_MOCK_CALENDAR` | Use the pretend calendar | `true` |
| `USE_MOCK_EMAIL` | Use the pretend email (saves it, doesn't really send) | `true` |
| `MAX_UPLOAD_MB` | Biggest resume file allowed | `5` |
| `LANGSMITH_API_KEY` | *(optional)* Lets you watch the AI's steps while fixing bugs | `...` |
| `LOG_LEVEL` | How much detail to write in logs | `INFO` |

Scheduling rules (time zone, interview length, call tries) are **not** in `.env`. HR changes them on the **Settings page**.

---

## 🔌 Outside services

| Service | For testing (default) | Real version (optional) |
|---|---|---|
| AI model | Real API | — |
| Phone calls | **Pretend call** (you type the answers) | **ElevenLabs** voice call |
| Online CV form | *(to be chosen)* | *(to be chosen)* |
| Calendar | **Pretend calendar** (built from employee available times and busy times) | Google or Outlook calendar |
| Email | **Pretend email** (saved, not really sent) | Gmail, Outlook or SMTP |

Every pretend part has a **MOCK** label on the screen, so nobody gets confused.

### How the ElevenLabs call works

1. I make a voice agent in ElevenLabs and give it rules: say it's an AI, ask about recording, and ask only job questions.
2. I connect a phone number to it (for example through Twilio).
3. My app tells ElevenLabs: "Call this person, for this job, with these questions."
4. When the call ends, ElevenLabs sends the call text back to my app. This is called a "webhook". The app checks the secret key to make sure it's really from ElevenLabs.
5. Agent 2 turns the call text into neat answers and a summary for HR.

> ⚠️ While testing, **only call your own phone** or a friend who said yes. Never call real candidates.

---

## 🧪 Tests

```bash
uv run pytest                     # run all tests
uv run pytest tests/acceptance    # run the tests for AC-01 to AC-12
```

The results will be written in `docs/test_results.md` *(planned)*.

---

## 🎬 Demo steps

*(planned)* Using the fake data in `sample_data/`:

1. Log in as HR. Make a **Junior** job with the ⭐ **AI Job Post Writer**, and a **Team Lead** job.
2. Send a fake CV through the ⭐ **online form**. Show the ⭐ **CV Match Score email** the candidate gets.
3. Upload the other fake resumes, including the broken one. Watch it get marked "Needs Manual Review".
4. Look at the scores. See how the same resume gets a different score for each job. Turn on ⭐ **Blind Review Mode**.
5. Ask the ⭐ **chat**: "Who has led a team?"
6. Approve some candidates to call.
7. Add interviewers on the Employees page and change some Settings.
8. Make the calls (pretend, or ElevenLabs to your own phone). Show:
   - a person who says **no to recording**
   - a person who **asks for a human**
9. Approve someone for an interview. Pick a time and confirm the email.
10. Open the dashboard and look at the full history.

**First login:** the app starts empty. Click **Create an account** on the login page to make the first HR account (saved in the `hr_accounts` table, password scrambled with bcrypt). Only HR logs in.

---

## 🛡️ Safety and fairness

- **A human decides.** HR must say yes at all 3 stop points.
- **Fair scoring.** The app never uses age, gender, religion, race, voice, accent or feelings.
- **Be honest.** The AI always says it's an AI. A real human is always an option.
- **Ask first.** The app asks before recording a call, and saves the answer.
- **Fake data only.** I never use real people's resumes while building or testing.
- **No tricks.** If a resume has hidden instructions, the AI ignores them.
- **Keep secrets safe.** Keys live in `.env` and are never put in the code.
- **Log less.** Logs never hold full resumes, phone numbers, keys or full call text.
- **Keep a history.** Every score change, approval, call, calendar check and email is saved.
- **Delete when asked.** Candidate data is kept for 90 days (you can change this in Settings), then deleted. HR can also fix or delete a candidate's data any time.
- **Only the right people.** Everyone logs in, and each role sees only what it needs.
- **Fairness check.** I test that two resumes that are the same except for the name (or gender hint) get the same score.
- **Less personal data to the AI.** Names and contact details are removed before a CV is sent to the AI for scoring.
- **Safe connections.** Real services (AI, ElevenLabs) are reached over HTTPS, which is encrypted.

---

*My solo student project. Built with fake data, for learning.*
