Conversation opened. 1 read message.

Skip to content
Using St Stephens Episcopal School Mail with screen readers

2 of 1,300
Instructions for webdev
Inbox

Canon Ellis
Attachments
11:38 AM (3 minutes ago)
to me, Abigail

--
Canon Ellis | Upper School Computer Science Instructor
St. Stephen’s Episcopal School
6500 St. Stephen’s Drive, Austin, Texas 78746
512.327.1213
www.sstx.org
One attachment
• Scanned by Gmail

# 📚 Student Tutorial: How to Work with Your Raspberry Pi Website and Database

Welcome!
This guide will show you **step-by-step** how to:

-   Connect to your Raspberry Pi
-   Upload your website files (HTML, CSS, JavaScript)
-   Access and modify your personal database

Let's get started! 🚀

---

# 1. Connect to the Raspberry Pi (SSH)

You will connect to the Pi using **SSH** (a secure remote login tool).

## 📅 If you're on a Windows PC:

-   Download and install [**PuTTY**](https://www.putty.org/).
-   Open **PuTTY**.
-   In **Host Name**, type:

    ```
    <IP address of the Pi>
    ```

    Example:

    ```
    192.168.36.23
    ```

-   Click **Open**.

## 📅 If you're on a Mac, Linux, or Chromebook:

-   Open the **Terminal** app.
-   Type:

    ```bash
    ssh <your-username>@<Pi-IP-address>
    ```

    Example:

    ```bash
    ssh noams@192.168.36.23
    ```

-   When asked, enter your password.

---

# 2. Upload Your Website Files

Your website folder is located at:

```
/var/www/html/<your-username>/
```

Everything you put here will appear on your live website!

## 📂 If you're on Windows:

-   Download and install [**WinSCP**](https://winscp.net/).
-   Use these settings:
    -   **Protocol**: SCP or SFTP
    -   **Host name**: Pi IP address (e.g., `192.168.36.23`)
    -   **Username**: Your username
    -   **Password**: Your password
-   Connect and drag your files into:

```
/var/www/html/<your-username>/
```

## 📂 If you're on Mac/Linux/Chromebook:

Use the `scp` command:

```bash
scp index.html style.css app.js <your-username>@<Pi-IP-address>:/var/www/html/<your-username>/
```

Example:

```bash
scp index.html style.css app.js noams@192.168.36.23:/var/www/html/noams/
```

---

# 3. View Your Website

Open your web browser and visit:

```
http://<Pi-IP-address>/<your-username>/
```

Example:

```
http://192.168.36.23/noams/
```

---

# 4. Access and Edit Your Database

You have a personal **MariaDB database**!

## 4.1 Log into MariaDB

After SSH-ing into the Pi:

```bash
mysql -u <your-username> -p
```

Example:

```bash
mysql -u noams -p
```

Then enter your **database password**.

---

## 4.2 Basic MariaDB Commands

| Action              | Command                    |
| :------------------ | :------------------------- |
| List tables         | `SHOW TABLES;`             |
| See table structure | `DESCRIBE tablename;`      |
| Run a query         | `SELECT * FROM tablename;` |
| Exit database       | `exit;`                    |

---

## 4.3 Example SQL Actions

### Create a Table

```sql
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255),
  email VARCHAR(255)
);
```

### Insert a Row

```sql
INSERT INTO users (username, email) VALUES ('Noam', 'noam@example.com');
```

### View Your Data

```sql
SELECT * FROM users;
```

---

# 5. Common Problems and Solutions

| Problem                 | Solution                                 |
| :---------------------- | :--------------------------------------- |
| Can't connect?          | Double-check IP address and username     |
| Wrong password?         | Carefully retype (password is invisible) |
| Website not updating?   | Ensure files are in the correct folder   |
| Database access denied? | Check username and database password     |

---

# 6. Important Rules

-   Always name your homepage `index.html`.
-   Organize your site with `/css/`, `/js/`, and `/images/` folders.
-   Never delete or change another student's files.
-   Always exit MariaDB properly with `exit`.

---

# 🌟 Final Cheat Sheet

| Task             | Command                                                |
| :--------------- | :----------------------------------------------------- |
| Connect to Pi    | `ssh username@Pi-IP`                                   |
| Upload file      | `scp file.html username@Pi-IP:/var/www/html/username/` |
| Open database    | `mysql -u username -p`                                 |
| See your website | `http://Pi-IP/username/`                               |

---

# 🎉 Congratulations!

You now have your own live website and database on a real server!

Happy building! 🚀
instructions.md
Displaying instructions.md.
