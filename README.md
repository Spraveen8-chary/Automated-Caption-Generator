# Automated Caption Generator

Effortlessly add accurate, AI-powered captions to your videos in 40+ languages. Built as a ready-to-deploy SaaS web app with multi-user support, advanced admin dashboard, and premium gating.

***

## 🚀 Features

- 🎥 Video-to-caption generation for MP4, MOV, AVI, MKV, WebM files
- 🌍 40+ languages including English, Hindi, Tamil, Telugu, Bengali, and more
- ✨ Multiple caption styles at once: Meme, Formal, Casual, Aesthetic
- 🪄 AI transcription/translation powered by Google Gemini 2.5 Flash
- 🧑‍💻 User dashboard with authentication and usage limits (2 free videos)
- 💳 Premium accounts with unlimited uploads
- 📈 Admin dashboard: full analytics, user management, charts, all activity
- 📦 Easy deployment (Flask, SQLite, SQLAlchemy, Chart.js)
- 🎨 Modern, responsive, animated UI

***

## 📸 Screenshots

<!-- Add usage screenshots and the admin dashboard here as needed -->
1. Register Page
  <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/1725350b-6311-4312-843c-c07ee119cb61" />

2. Login Page
   <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/0d840c34-7213-4442-ad79-7b9097a6c4df" />

3. Home Page
   <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/56d6d9c0-b23e-4222-83ad-27693c4f2a8b" />

4. Options
   <img width="1280" height="720" alt="image" src="https://github.com/user-attachments/assets/8761adab-188a-4797-8536-82176a013ef5" />

5. Results
   <img width="1280" height="720" alt="image" src="https://github.com/user-attachments/assets/a0578270-d9df-40d0-bc5f-00dd29377c27" />

6. Exporting
   <img width="1280" height="720" alt="image" src="https://github.com/user-attachments/assets/67cda1a0-5ade-425f-b5c7-ca870c857b87" />

7. Reaching Subscription Limit
   <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/b94e1297-8065-4245-8d73-c728cab56a10" />

8. History
   <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/56801756-80cd-4219-94e8-76fcd249e6c4" />

9. Admin Dashboard
    <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/5602ba8a-065b-41b2-88a0-02aa6daf0ba5" />
    <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/d58cda97-69c3-42e6-9868-8f1bc96cfead" />
    <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/92536ef0-a499-4f82-bc07-f7c66257f3da" />
    <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/8ca19944-f203-418d-9951-e8e33d96482a" />


***

## 🗂️ Project Structure

```
caption-generator/
├── app.py
├── auth.py
├── models.py
├── config.py
├── requirements.txt
├── .env          # (Not committed, for secrets)
├── utils/
│   ├── transcription.py
│   ├── video_processor.py
│   └── caption_formatter.py
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── animations.css
│   │   └── admin.css
│   ├── js/
│   │   ├── main.js
│   │   └── auth.js
│   └── uploads/
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── history.html
│   └── admin_dashboard.html
```


***

## ⚙️ Quickstart

### 1. Clone and Setup

```sh
git clone https://github.com/Spraveen8-chary/Automated-Caption-Generator.git
cd Automated-Caption-Generator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```


### 2. Environment

Create a `.env` file in the project root:

```
FLASK_SECRET_KEY=your-flask-secret-here
GOOGLE_API_KEY=your_google_gemini_api_key
MAX_UPLOAD_SIZE=100
ALLOWED_EXTENSIONS=mp4,mov,avi,mkv,webm
TEMP_FOLDER=uploads
DATABASE_URL=sqlite:///caption_generator.db
```

- Get your Google API Key at https://aistudio.google.com/app/apikey


### 3. Run

```sh
python app.py
# or for production: gunicorn app:app
```

- Visit: http://localhost:5000

***

## 👤 Default Admin Credentials

- **Email:** admin@caption.generator.com
- **Password:** Praveen8

Admin users are auto-created on first run if not present.

***

## 🧑‍💼 Admin Features

- See all users
- View detailed video+caption history for every user
- See registration and processing trends with charts (Chart.js)
- Download any generated SRT
- Monthly and all-time analytics for growth and usage

***

## 🧑 User Features

- Register/Login with email
- Upload video, select multiple caption styles and language
- Download professional, stylized SRT files
- Usage limits (2 free videos) with animated UI
- Upgrade to premium for unlimited use

***

## 🛠️ Tech Stack

- Backend: **Python Flask**, SQLAlchemy, SQLite
- AI: **Google Gemini 2.5 Flash** (via google-genai SDK)
- Frontend: HTML5, CSS3, JS, Chart.js, modern SPA patterns
- Auth: Flask-Login
- Responsive, animated, and optimized for SaaS

***

## 💡 Tips \& Migrations

- If you add columns to models (like `is_admin`), use Flask-Migrate for production, or `ALTER TABLE` for SQLite, or just delete and let the app recreate the DB for fresh installs.
- Production deployment: use Gunicorn/uwsgi, set secret keys, and HTTPS.

***

## 🎯 License

(C) 2025 Your Name. All Rights Reserved.
Not for commercial use without permission.

***

**Made with ❤️ for content creators.**

***
