# AI Recruiter Assistant | Enterprise Recruitment Suite

A high-performance, intelligence-driven local candidate matching, ranking, and ATS compliance analyzer. The platform uses sentence embeddings (`sentence-transformers/all-MiniLM-L6-v2`) for semantic matchmaking, SQLite for relational persistence, and interactive visualization dashboards built with React and FastAPI.

---

## 🌟 Key Enterprise Features

The application has been heavily upgraded to support modern enterprise recruiting workflows:

### 1. Advanced AI Resume Parsing & Fraud Detection
* **Semantic Matchmaking:** Uses NLP models to match candidate experience against job descriptions mathematically.
* **Fraud Detection Heuristics:** Automatically scans for known "Degree Mills", unrealistic timelines (e.g., high experience with no graduation dates), and analyzes job-hopping behavior.
* **GitHub Detection:** Identifies candidate repositories and links to assess technical credibility.
* **Internship Isolation:** Correctly flags and maps internship vs. full-time experience for accurate filtering.

### 2. Deep-Dive Candidate Modal & AI Interview Prep
* **Technical Validation Generator:** The backend dynamically generates customized Beginner, Intermediate, and Advanced interview questions targeting the candidate's specific reported skills.
* **Skill Gap & Learning Roadmap:** For missing requirements, the system generates a 30-day learning roadmap, allowing recruiters to ask: *"We use X heavily. How would you approach learning it?"*
* **AI Recruiter Decision Engine:** Provides an immediate assessment (e.g., *"Strong Buy"*, *"Pass"*).

### 3. Advanced Pipeline Filtering & Analytics
* **Relational Database Mapping:** Employs advanced SQL mapping tables (`candidate_skills`, `candidate_experience`) for hyper-fast querying.
* **Multi-Condition Filtering:** A sticky left-sidebar allows you to filter the Kanban board instantly by Target Skills, Minimum ATS Score, Years of Experience, Risk Level, and Internship Experience.
* **Live Analytics Widgets:** Real-time tracking of pipeline health, shortlisted counts, and hired metrics.

### 4. Premium UI/UX
* **Glassmorphism & Skeleton Loaders:** Modern design featuring animated skeleton states while waiting for backend AI inference.
* **Responsive Interactions:** Hover states, subtle shadows, and scale transformations provide a sleek, highly responsive feel.

---

## 🗄️ Architecture Stack

* **Frontend:** React (Vite) + Lucide Icons + Recharts
* **Backend:** Python + FastAPI
* **Database:** SQLite (Relational Design)
* **NLP Pipeline:** Hugging Face `sentence-transformers/all-MiniLM-L6-v2`
* **Containerization:** Docker & Docker Compose

---

## 🛠️ Local Setup & Running the Application

To run the application locally, you will need to start both the Python backend and the React frontend in separate terminal windows.

### 1. Start the Backend (FastAPI)
```bash
# Clone the repository
git clone https://github.com/DurgamPoojitha/AI-Recruiter-Assistant.git
cd AI-Recruiter-Assistant

# Install dependencies
pip install -r requirements.txt

# Launch the FastAPI Backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
*Note: The first time you start the backend, it will download a ~90MB NLP model from Hugging Face. Subsequent starts will be instant.*

### 2. Start the Frontend (React)
Open a new terminal window:
```bash
cd AI-Recruiter-Assistant/frontend-react

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```
Navigate to **`http://localhost:5173`** in your browser to view the application!

---

## 🚀 Production Deployment Guide (100% Free via Oracle Cloud)

This application has been fully containerized with Docker, meaning it can be deployed anywhere. Because the NLP model requires memory, you need a server with at least 2GB of RAM. The **Oracle Cloud "Always Free" ARM instance** provides up to 24GB of RAM completely free forever.

### Step 1: Claim Your Free Oracle Cloud Server
1. Go to the [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) and sign up.
2. Click **Create a VM instance**.
3. Under **Image and Shape**, click "Edit":
   * Set Image to **Canonical Ubuntu 22.04**.
   * Set Shape to **Ampere ARM (VM.Standard.A1.Flex)**.
   * Slide OCPU count to **4** and Memory (RAM) to **24 GB**.
4. Scroll down to "Add SSH keys" and select **Save private key** (Keep this `.key` file safe!).
5. Click **Create** and wait for the status to turn green. Note your **Public IP Address**.

### Step 2: Open Cloud Firewalls
1. On your instance details page, click on your **Subnet**.
2. Click on the **Default Security List** -> **Add Ingress Rules**.
3. Add two rules (one for the frontend, one for the backend API):
   * Source CIDR: `0.0.0.0/0`, Destination Port Range: `80`
   * Source CIDR: `0.0.0.0/0`, Destination Port Range: `8000`

### Step 3: Connect & Deploy
Open your terminal on your local machine and SSH into your new server:
```bash
chmod 400 path/to/your/ssh-key.key
ssh -i path/to/your/ssh-key.key ubuntu@YOUR_PUBLIC_IP
```

Once inside the Ubuntu server, install Docker and open the internal firewall:
```bash
# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# (Type `exit` and SSH back in so permissions apply)

# Open internal firewall ports
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save
```

Finally, clone and spin up the Docker containers:
```bash
git clone https://github.com/DurgamPoojitha/AI-Recruiter-Assistant.git
cd AI-Recruiter-Assistant

# Start the application in detached mode
docker-compose up -d --build
```

You can now access your live, production-grade AI Recruiter Assistant by simply typing your **Public IP Address** into your web browser!
