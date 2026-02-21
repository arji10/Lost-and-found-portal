# 🚀 Deployment Guide: Smart Lost & Found Portal

Follow these steps to host your portal online using **GitHub** and **Render.com**.

## Step 1: Push your code to GitHub
1.  Log in to your [GitHub](https://github.com) account.
2.  Create a new repository named `smart-lost-found`.
3.  Open a terminal in your project folder (`c:\Users\80449\OneDrive\Desktop\lost and found portal`) and run:
    ```bash
    git init
    git add .
    git commit -m "Initial commit for deployment"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/smart-lost-found.git
    git push -u origin main
    ```

## Step 2: Create a Web Service on Render
1.  Go to [Render.com](https://render.com) and sign up (connect your GitHub account).
2.  Click the **"New +"** button and select **"Web Service"**.
3.  Choose your repository from the list.

## Step 3: Configure Deployment Settings
Render will ask for some details. Use these exact values:
-   **Name:** `smart-lost-found`
-   **Environment:** `Python 3`
-   **Region:** Choose the one closest to you.
-   **Branch:** `main`
-   **Build Command:** `pip install -r requirements.txt`
-   **Start Command:** `gunicorn app:app`

## Step 4: Environment Variables (Important)
1.  In the Render dashboard for your service, go to the **"Environment"** tab.
2.  Add a Secret File or individual variables:
    -   Key: `SECRET_KEY` | Value: `your_random_secret_string`
    -   Key: `PYTHON_VERSION` | Value: `3.11.0`

> [!TIP]
> **Fixing the Build Error:**
> The error you got was because Render tried to use Python 3.14 (experimental). By setting `PYTHON_VERSION` to **3.11.0**, the app will build correctly with `scikit-learn`.

## Step 5: Initialize the Database on Render
Since your app needs the database and sample data:
1.  Go to the **"Shell"** tab in your Render dashboard once the app is "Live".
2.  Run the seed script manually once:
    ```bash
    python seed_data.py
    ```

## Step 6: Access your portal
Your app will be available at a link like:
👉 `https://smart-lost-found-xxxx.onrender.com`

---

> [!IMPORTANT]
> **Persistent Storage Note:**
> This project uses an SQLite database (`database.db`). On free hosting like Render, any data you add (new posts) will be deleted whenever the app restarts or you redeploy.
> - **For testing:** This is fine.
> - **For real use:** You should connect a PostgreSQL database (also available for free on Render).
