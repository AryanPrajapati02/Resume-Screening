# AI Resume Screening Platform

An AI-powered resume screening and candidate ranking system that uses semantic similarity and skill matching to find the best candidates for job positions.

![Resume Screening](https://img.shields.io/badge/Status-Production-green)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-purple)

## Features

- **AI-Powered Matching** - Uses Groq LLM for intelligent candidate analysis
- **Semantic Search** - Sentence-transformers for understanding resume content
- **Skill Extraction** - Automatically extracts skills from resumes and job descriptions
- **Smart Ranking** - Ranks candidates based on multiple factors:
  - Semantic similarity
  - Skill coverage
  - Experience alignment
  - Domain expertise
- **Resume Validation** - Validates uploaded documents are actual resumes
- **Modern UI** - Clean, professional React frontend

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLite** - Lightweight database for storing resumes and jobs
- **FAISS** - Vector similarity search
- **Groq API** - LLM for feature extraction and matching
- **Sentence-Transformers** - Semantic embeddings

### Frontend
- **React** - User interface
- **Vite** - Fast build tool
- **CSS** - Custom styling (no Tailwind)

## Project Structure

```
├── backend/
│   ├── api/           # API endpoints
│   ├── database/      # SQLite & FAISS
│   ├── models/        # Pydantic schemas
│   ├── services/      # Business logic
│   └── main.py        # FastAPI app
├── core/
│   ├── step1_input_processing/   # PDF parsing
│   ├── step2_semantic_understanding/  # Embeddings
│   ├── step3_feature_extraction/     # Skill extraction
│   └── step4_matching_logic/          # Matching algorithm
├── frontend/
│   ├── src/           # React components
│   └── vite.config.js # Vite configuration
└── test/              # Test scripts
```

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/YuvrajSinghBhadoria2/Resume-Screening.git
cd Resume-Screening

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_api_key_here" > .env
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Run Development Server

```bash
# Start backend (from project root)
uvicorn backend.main:app --reload --port 8000

# Start frontend (in separate terminal)
cd frontend
npm run dev
```

Open http://localhost:5173 to view the app.

## API Endpoints

### Resume Management
- `POST /api/resumes/bulk` - Upload multiple resumes
- `GET /api/resumes/{id}` - Get resume by ID
- `DELETE /api/resumes/{id}` - Delete resume
- `POST /api/resumes/clear` - Clear all resumes

### Job Management
- `POST /api/jobs` - Create job description
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{id}` - Get job by ID
- `POST /api/jobs/clear` - Clear all jobs

### Matching
- `POST /api/match/all` - Match all resumes to latest job
- `POST /api/match` - Match single resume to job

### Ranking
- `GET /api/rank/latest` - Get latest ranking results

## How It Works

### 1. Resume Upload
Resumes are parsed from PDF format and validated to ensure they are actual resumes (not offer letters or contracts).

### 2. Feature Extraction
Using Groq LLM, the system extracts:
- **Skills** - Technical and soft skills
- **Experience** - Work history and roles
- **Projects** - Notable projects
- **Domain** - Industry expertise

### 3. Job Description Analysis
Job descriptions are analyzed to extract:
- **Required Skills** - Technical requirements
- **Responsibilities** - Key duties
- **Seniority Level** - Experience level needed
- **Domain** - Industry focus

### 4. Matching Algorithm
Candidates are ranked using a weighted scoring system:

| Factor | Weight | Description |
|--------|---------|-------------|
| Semantic Similarity | 40% | Text similarity between resume and JD |
| Skill Coverage | 30% | AI-verified skill match |
| Experience | 20% | Seniority level alignment |
| Domain Bonus | 10% | Industry expertise overlap |

### 5. Results
Candidates are classified as:
- **Best** (≥70%) - Highly qualified
- **Good** (50-69%) - Potentially suitable
- **Rejected** (<50%) - Below requirements

## Deployment

### Render (Free Tier)

1. Create account at https://render.com
2. Connect GitHub repository
3. Create Web Service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `GROQ_API_KEY`
5. Deploy!

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | API key from Groq |

## Usage

1. **Upload Resumes** - Drag and drop PDF resumes
2. **Add Job Description** - Paste job requirements
3. **Run Matching** - Click submit to analyze
4. **View Results** - See ranked candidates with:
   - Match score
   - Strong matches
   - Missing skills
   - Weak areas

## Testing

```bash
# Test resume parsing
python test/test_resume_parser.py

# Test JD cleaning
python test/test_jd_cleaner.py

# Test embeddings
python test/test_embeddings.py

# Test feature extraction
python test/test_step3.py

# Test full pipeline
python test/test_full_pipeline.py
```

## License

MIT License - See LICENSE file for details.

## Author

Yuvraj Singh Bhadoria

## Acknowledgments

- Groq for providing LLM API
- Hugging Face for sentence-transformers
- FastAPI for the excellent web framework
