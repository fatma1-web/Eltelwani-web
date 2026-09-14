# Dar El-Telwany – Quran Learning Website

A responsive Arabic website for **Dar El-Telwany for Quran Memorization and Learning**.

The project provides a simple and user-friendly platform for presenting Quran learning programs, educational resources, Quran-related materials, and student registration.

## Features

* 🕌 Islamic-themed responsive design
* 📚 Quran learning courses and educational content
* 📖 Digital library containing Quran-related PDF resources
* 📝 Student registration form
* ❓ Questions section for visitors
* 📱 Responsive design for different screen sizes
* 🔗 Social media and contact links
* 🗄️ MySQL database integration

## Technologies Used

* **HTML5**
* **CSS3**
* **JavaScript**
* **Python**
* **Flask**
* **MySQL**

## Project Structure

```text
Eltelwani-web/
│
├── app.py
├── db.js
├── tel.sql
│
├── static/
│   ├── Files/
│   ├── images/
│   ├── script.js
│   └── style.css
│
└── templates/
    ├── index.html
    ├── about.html
    ├── academy.html
    ├── courses.html
    ├── learn.html
    ├── library.html
    ├── que.html
    ├── register.html
    └── ...
```

## Database

The project uses **MySQL** to store and manage application data.

The database structure is included in:

```text
tel.sql
```

## How to Run

### 1. Clone the repository

```bash
git clone https://github.com/fatma1-web/Eltelwani-web.git
```

### 2. Open the project folder

```bash
cd Eltelwani-web
```

### 3. Install the required Python packages

```bash
pip install flask mysql-connector-python python-dotenv
```

### 4. Configure the database

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=telwani_db
```

Import `tel.sql` into MySQL and make sure the database name matches the configuration.

### 5. Run the Flask application

```bash
python app.py
```

Then open the local address shown by Flask in your browser.

## Notes

* The `.env` file is intentionally excluded from GitHub to protect database credentials.
* PDF resources and images are included as part of the website's educational content.
* This project is a learning and practical training project and is still open to future improvements.

## Future Improvements

Possible future improvements include:

* Improved authentication and authorization
* Teacher and student dashboards
* Attendance management
* Student progress tracking
* Tasmee' management
* Parent notifications
* More advanced administration features

## Author

**Fatma Fathy**

Computer Engineering & Computer Science Student

GitHub:
https://github.com/fatma1-web
