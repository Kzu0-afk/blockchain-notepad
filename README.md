# Blockchain Notepad (BlockNotes) 

A simple, secure, and modern note-taking application powered by Django. This project serves as a foundational web application with user authentication and core note-management features and learn blockchain integration using Cardano and Blockfrost.

## Project Status: **Phase 1 Complete**

The core backend and foundational frontend functionality have been successfully implemented. The application is now operational with user registration, login, and basic note creation/viewing capabilities.

## Current Features Implemented

- **Full Project Setup**: The Django project is configured with a SQLite database and is ready for development.
- **Version Control**: The project is integrated with Git and hosted on GitHub.
- **User Authentication**:
  - User registration (Sign Up)
  - User login and session management
  - User logout
- **Note Management (CRUD Basics)**:
  - **Create**: Logged-in users can create new notes with a title and description.
  - **Read**: Users can view a list of all the notes they have personally created. Notes are private to each user.
- **Database Schema**:
  - A `User` model (using Django's built-in system for security).
  - A `Note` model with fields for title, description, timestamps, and a foreign key relationship to the user who created it.
- **Admin Panel**: A functional Django admin interface is available at `/admin/` for superusers to manage users and notes directly.

## Tech Stack

- **Backend**: Django
- **Frontend**: HTML (No CSS/JS styling yet)
- **Database**: SQLite (Default for local development)
- **Version Control**: Git & GitHub

## How to Run the Project Locally

To get the project running on your own machine, follow these steps:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Kzu0-afk/blockchain-notepad.git
    cd blockchain-notepad
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # Create the venv
    python -m venv venv

    # Activate it (Windows)
    .\venv\Scripts\activate

    # Activate it (macOS/Linux)
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    _(Currently, we only need Django, but we will add a requirements.txt file later)_

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the database migrations:**
    _(This step is important as it sets up your local database tables)_

    ```bash
    python manage.py migrate
    ```

5.  **Create a superuser (for admin access):**

    ```bash
    python manage.py createsuperuser
    ```

    Follow the prompts to create your admin account.

6.  **Run the development server:**

    ```bash
    python manage.py runserver
    ```

7.  **Access the application:**
    - The main application is at `http://127.0.0.1:8000/`.
    - The admin panel is at `http://127.0.0.1:8000/admin/`.

---

## Next Steps & Tasks for the Team

The foundation is built! Now we can divide the work to enhance the application. Here are the next major tasks. Please claim a task by creating a new branch for it (e.g., `feature/update-delete-notes`).

### Task 1: Complete Note CRUD Functionality (Backend/Django)

- **Goal**: Allow users to edit and delete their own notes.
- **Steps**:
  1.  Create two new views in `notes/views.py`: `note_update_view` and `note_delete_view`.
  2.  Create two new HTML templates: `note_update_form.html` and `note_confirm_delete.html`.
  3.  Add the corresponding URL patterns in `notes/urls.py`.
  4.  Add "Edit" and "Delete" buttons next to each note in the `note_list.html` template.
  5.  **Important**: Ensure a user can only edit or delete their _own_ notes.

### Task 2: Frontend Styling & Base Template (HTML/CSS)

- **Goal**: Make the application look clean, modern, and user-friendly.
- **Steps**:
  1.  Create a `base.html` template that includes a navigation bar, a footer, and a block for content.
  2.  Make all other templates (`login.html`, `note_list.html`, etc.) `{% extend 'base.html' %}`.
  3.  Use CSS to style all pages. Focus on:
      - Login/Signup forms.
      - The note list display (maybe use cards for each note).
      - Buttons and links.
  4.  Set up a `static` folder for our CSS files and configure it in `settings.py`.

### Task 3: Enhancing the User Experience (Frontend/JS)

- **Goal**: Add interactive elements to make the app feel more dynamic.
- **Steps**:
  1.  Add client-side validation to the forms (e.g., "Password must be 8 characters").
  2.  Implement "flash messages" to give users feedback (e.g., "Note created successfully!"). Django's `messages` framework is perfect for this.
  3.  (Advanced) Explore using JavaScript (or a library like HTMX) to allow users to delete a note without a full page reload.

### Task 4: Blockchain Integration (Research & Planning)

- **Goal**: Fulfill the "Blockchain" aspect of the project. Since we have a centralized database, a practical approach is to use the blockchain for **verification and immutability**.
- **Steps**:
  1.  **Research**: How can we "anchor" a note to a blockchain? A common method is to take a hash (e.g., SHA-256) of the note's content and store that hash on a testnet blockchain (like Ethereum's Sepolia).
  2.  **Plan**:
      - When a user saves a note, how do we trigger the hashing process?
      - Which Python libraries can we use to interact with a blockchain (e.g., `web3.py`)?
      - How can we add a "Verify on Blockchain" button to a note, which would re-hash the content and check if it matches the hash stored on-chain?
  3.  **Prototype**: Set up a wallet and try to send a simple transaction with a data hash to a testnet. This task is about figuring out the _how_ before we write the code.
