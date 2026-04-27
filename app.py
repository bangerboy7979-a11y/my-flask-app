from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

app.config["UPLOAD_FOLDER"] = "static/uploads"


# ---------- HOME ----------
@app.route("/")
def home():
    return redirect("/login")


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        # 🔥 EMPTY CHECK
        if not username or not password:
            return "Username & Password required ❌"

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # 🔥 DUPLICATE USER CHECK
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            conn.close()
            return "Username already exists ❌"

        # 🔥 SAVE USER
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/feed")
        else:
            return "Invalid credentials ❌"

    return render_template("login.html")


# ---------- FEED ----------
@app.route("/feed", methods=["GET", "POST"])
def feed():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":

        image = request.files.get("image")
        video = request.files.get("video")

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image.save(path)

            cursor.execute(
                "INSERT INTO posts (image, video, user) VALUES (?, ?, ?)",
                (filename, None, session["user"])
            )
            conn.commit()

        elif video and video.filename != "":
            filename = secure_filename(video.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            video.save(path)

            cursor.execute(
                "INSERT INTO posts (image, video, user) VALUES (?, ?, ?)",
                (None, filename, session["user"])
            )
            conn.commit()

        return redirect("/feed")

    cursor.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cursor.fetchall()

    conn.close()

    return render_template("feed.html", posts=posts)

# ---------- REELS PAGE ----------
@app.route("/reels", methods=["GET", "POST"])
def reels():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        file = request.files["video"]

        if file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            cursor.execute(
                "INSERT INTO posts (video, user) VALUES (?, ?)",
                (filename, session["user"])
            )
            conn.commit()

        return redirect("/reels")

    cursor.execute("SELECT * FROM posts WHERE video IS NOT NULL ORDER BY id DESC")
    posts = cursor.fetchall()

    conn.close()

    return render_template("reels.html", posts=posts)


# ---------- CREATE ----------
@app.route("/create", methods=["GET", "POST"])
def create():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        file = request.files["image"]

        if file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            cursor.execute(
                "INSERT INTO posts (image, user) VALUES (?, ?)",
                (filename, session["user"])
            )
            conn.commit()

        return redirect("/feed")

    return render_template("create.html")


# ---------- MESSAGES ----------
# ---------- MESSAGES ----------
@app.route("/messages")
def messages():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # sab users
    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()

    conn.close()

    return render_template("messages.html", users=users)

# ---------- CHAT ----------
@app.route("/chat/<username>", methods=["GET", "POST"])
def chat(username):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # 🔥 SEND MESSAGE
    if request.method == "POST":
        text = request.form.get("message")
        image = request.files.get("image")

        filename = None

        # 🔥 IMAGE SAVE (SAFE VERSION)
        if image and image.filename != "":
            from werkzeug.utils import secure_filename
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # 🔥 EMPTY MESSAGE CHECK (important)
        if text or filename:
            cursor.execute(
                "INSERT INTO messages (sender, receiver, text, image) VALUES (?, ?, ?, ?)",
                (session["user"], username, text, filename)
            )
            conn.commit()

        return redirect(f"/chat/{username}")   # 🔥 DUPLICATE SEND FIX

    # 🔥 LOAD MESSAGES
    cursor.execute("""
        SELECT * FROM messages
        WHERE (sender=? AND receiver=?)
        OR (sender=? AND receiver=?)
        ORDER BY id ASC
    """, (session["user"], username, username, session["user"]))

    chats = cursor.fetchall()

    conn.close()

    return render_template("chat.html", chats=chats, username=username)

# ---------- COMMENT ----------
@app.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    if "user" not in session:
        return redirect("/login")

    text = request.form["comment"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO comments (post_id, user, text) VALUES (?, ?, ?)",
        (post_id, session["user"], text)
    )
    conn.commit()
    conn.close()

    return redirect("/feed")


# ---------- DELETE ----------
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT image, video, user FROM posts WHERE id=?", (id,))
    data = cursor.fetchone()

    if data:
        image, video, owner = data

        if owner != session["user"]:
            return "Unauthorized ❌"

        if image:
            path = os.path.join(app.config["UPLOAD_FOLDER"], image)
            if os.path.exists(path):
                os.remove(path)

        if video:
            path = os.path.join(app.config["UPLOAD_FOLDER"], video)
            if os.path.exists(path):
                os.remove(path)

    cursor.execute("DELETE FROM posts WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/feed")


# ---------- PROFILE ----------
@app.route("/profile/<username>")
def profile(username):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # posts
    cursor.execute("SELECT * FROM posts WHERE user=?", (username,))
    posts = cursor.fetchall()

    # followers count
    cursor.execute("SELECT COUNT(*) FROM followers WHERE following=?", (username,))
    followers = cursor.fetchone()[0]

    # following count
    cursor.execute("SELECT COUNT(*) FROM followers WHERE follower=?", (username,))
    following = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        posts=posts,
        username=username,
        count=len(posts),
        followers=followers,
        following=following
    )
    
    # ---------- FOLLOW ----------
@app.route("/follow/<username>")
def follow(username):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # already follow check
    cursor.execute("""
        SELECT * FROM followers 
        WHERE follower=? AND following=?
    """, (session["user"], username))

    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO followers (follower, following)
            VALUES (?, ?)
        """, (session["user"], username))
        conn.commit()

    conn.close()

    return redirect("/profile/" + username)

# ---------- UNFOLLOW ----------
@app.route("/unfollow/<username>")
def unfollow(username):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM followers 
        WHERE follower=? AND following=?
    """, (session["user"], username))

    conn.commit()
    conn.close()

    return redirect("/profile/" + username)

# ---------- BLOCK ----------
@app.route("/block/<username>")
def block(username):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # already block check
    cursor.execute("""
        SELECT * FROM blocks 
        WHERE blocker=? AND blocked=?
    """, (session["user"], username))

    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO blocks (blocker, blocked)
            VALUES (?, ?)
        """, (session["user"], username))
        conn.commit()

    conn.close()

    return redirect("/feed")

# ---------- UNBLOCK ----------
@app.route("/unblock/<username>")
def unblock(username):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM blocks 
        WHERE blocker=? AND blocked=?
    """, (session["user"], username))

    conn.commit()
    conn.close()

    return redirect("/profile/" + username)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)                                                                                                                                                                                                                           