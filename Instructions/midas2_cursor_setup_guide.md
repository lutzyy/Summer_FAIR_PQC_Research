# MIDAS 2 + Cursor — Setup Guide

This guide provides instruction on setting up the MIDAS 2 research server through Cursor. 

By the end you'll have: a working login to MIDAS 2, Cursor installed and connected to the server, and the project repository cloned and open.

> **Where commands run.** This guide uses two different machines. Watch the labels:
> - **💻 On your computer** — type these in your laptop's terminal (PowerShell on Windows, Terminal on Mac).
> - **🖥️ On the server** — type these in a terminal that is logged into MIDAS 2.
> Mixing these up is the #1 cause of confusion. The label tells you where you are.

---

## Before you start — check the following

1. **Your server username** (for example `shyjek` or `shyjek1`) and your **temporary password** from the MIDAS LAB MS Teams channel.

The server's address is **`10.0.48.7`** (this is MIDAS 2). You'll use that number throughout.

Wherever you see `<username>` below, replace it with your own server username.

---

## Part 1 — Get on the Citadel network

MIDAS 2 has a private campus address (`10.0.48.7`), which means it's **only reachable from inside the Citadel network.** Before anything else:

- Connect to the **Citadel VPN**, or be on the **on-campus network**.
- Keep the VPN on the entire time you work. If you lose the VPN, the server simply vanishes ("no such host" / connection errors) — that's expected, just reconnect.

---

## Part 2 — First login and set your password (do this in a plain terminal!)

> ⚠️ **Do this step in a plain terminal — NOT in Cursor.** Your very first login forces you to change your password, and that password-change prompt will freeze a code editor's connection. Get it done in a normal terminal first; after that, Cursor connects cleanly.

**💻 On your computer**, open a terminal:
- **Windows:** click Start, type **PowerShell**, open it.
- **Mac:** open **Terminal** (Cmd+Space, type "Terminal").

Then log in (replace `<username>`):

```
ssh <username>@10.0.48.7
```

What to expect, in order:

1. **A fingerprint question** the first time only:
   > The authenticity of host '10.0.48.7' can't be established... Are you sure you want to continue connecting?

   Type `yes` and press Enter. (This only happens once; your computer is remembering the server.)

2. **Password prompt.** Type your temporary password and press Enter.
   > **The password is invisible as you type** — no dots, no stars, nothing moves. That's normal. Type it carefully and press Enter.

3. **Forced password change.** You'll likely be asked for your current (temporary) password once more, then a new password twice. Set your permanent password here.

When you see a prompt like `<username>@midas2:~$`, you're in. Type `exit` and press Enter to log back out for now.

---

## Part 3 — Set up passwordless login (recommended)

This step lets you (and Cursor) log in without typing your password every time. It works by creating a **key** on your computer/laptop and registering its public half on the server. Skip it if you like — but it makes Cursor much smoother.

### 3a. Make a key on your computer (if you don't have one)

**💻 On your computer:**

```
ssh-keygen -t ed25519
```

Press Enter at every prompt (accept the default location, leave the passphrase empty). If it says a key already exists, you can keep your existing one — answer `n` to "overwrite."

### 3b. Copy your key up to the server

**💻 On your computer — Mac:**

```
ssh-copy-id <username>@10.0.48.7
```

**💻 On your computer — Windows** (the `ssh-copy-id` command doesn't exist on Windows, so use this instead — it does the same thing):

```
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh <username>@10.0.48.7 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

It'll ask for your server password one last time. After it finishes, test it:

```
ssh <username>@10.0.48.7
```

If it logs you in **without** asking for a password, the key works. Type `exit` to come back.

---

## Part 4 — Create an SSH shortcut (prevents the most common Cursor errors)

This small config file tells your computer exactly how to reach MIDAS 2 — the right address and the right username. It prevents two errors people hit constantly: Cursor logging in as the wrong username, and a malformed config breaking the connection.

**💻 On your computer — Windows (PowerShell):**

```
@"
Host midas2
    HostName 10.0.48.7
    User <username>
"@ | Set-Content -Encoding ascii $env:USERPROFILE\.ssh\config
```

**💻 On your computer — Mac/Linux:**

```
cat >> ~/.ssh/config <<'EOF'
Host midas2
    HostName 10.0.48.7
    User <username>
EOF
```

Now test the shortcut:

```
ssh midas2
```

If that logs you straight in as your user, the shortcut works. You'll use the name **`midas2`** from here on instead of the IP.

> ⚠️ If you ever see an error like `line 1: no argument after keyword "<username>@10.0.48.7"`, your config file got a bad line in it. Open it and make sure it looks exactly like the three indented lines above — `Host`, `HostName`, `User`, nothing else on those lines.

---

## Part 5 — Install Cursor

Cursor is an AI-powered code editor (built on VS Code). The editor runs on your laptop, but it will run all your code and terminals on MIDAS 2.

1. **💻 On your computer**, go to **https://cursor.com** and download the installer for your operating system.
2. Run the installer and open Cursor.
3. Sign in / create a Cursor account when prompted. (If Dr. Zareen has a Teams plan for the project, use the account she invites you with.)
4. **Turn on Privacy Mode.** Open Settings (the gear icon, or Ctrl+Shift+J / Cmd+Shift+J) → find **Privacy**, and enable **Privacy Mode**. This keeps your code from being stored or used for training — important for a security research project.

---

## Part 6 — Connect Cursor to MIDAS 2

1. In Cursor, open the command palette: **Ctrl+Shift+P** (Windows) or **Cmd+Shift+P** (Mac).
2. Type **Connect to Host** and select it. (You can also click the blue `><` icon in the bottom-left corner.)
3. You should see **`midas2`** in the list (Cursor reads the shortcut you made in Part 4). Select it.
   - If you don't see it, choose **Add New SSH Host** and type `<username>@10.0.48.7` (always with your username — never just the bare IP).
4. Cursor connects and, the first time, installs a small helper on the server — give it a minute. When the bottom-left corner shows **`SSH: midas2`** (or `SSH: 10.0.48.7`), you're connected. The editor is now operating on MIDAS 2. If you don't see it just yet, simply close the Cursor application and reopen it and start with 2 again. You should see **`midas2`** in the list.

> ⚠️ **If "Connect to Host" hangs and never finishes** but `ssh midas2` works fine in your terminal, the cause is almost always a broken version of Cursor's Remote-SSH extension. Open Extensions (Ctrl+Shift+X / Cmd+Shift+X), find **Remote - SSH**, and if the version is **1.0.51 or 1.0.52**, downgrade it to **1.0.50**. Other versions are fine.

---

## Part 7 — Set up GitHub access and clone the repo

You're connected to the server, but the server needs permission to download the project from GitHub. The cleanest way is a key that lives **on the server** and is registered to **your GitHub account.**

> Note: this is a *different* key from the one in Part 3. Part 3's key lets your computer reach the server. This key lets the server reach GitHub. Same idea, different hop.

### 7a. Open a terminal on the server

In Cursor, open the terminal: **Ctrl+`** (the backtick key, top-left under Esc). The prompt should read `<username>@midas2:~$`. **🖥️ Everything in Part 7 runs here, on the MIDAS2 server.**

### 7b. Make a key on the server and show it

```
ssh-keygen -t ed25519 -C "<username> midas2"
```

(press Enter through all prompts), then display it:

```
cat ~/.ssh/id_ed25519.pub
```

Copy the entire line it prints (it starts with `ssh-ed25519 ...`).

### 7c. Add the key to your GitHub account

In your browser: GitHub → your profile picture (top-right) → **Settings** → **SSH and GPG keys** → **New SSH key**. Title it "MIDAS2 server," paste the line into the Key box, and click **Add SSH key**.

### 7d. Clone the project

Back in the server terminal, clone into your home folder:

```
cd ~
git clone git@github.com:fzareen1/Summer_FAIR_PQC_Research.git
```

The first time it'll ask "Are you sure you want to continue connecting?" — type `yes`. Then it should clone with no password prompt.

> **Quicker alternative if you don't want to set up the key:** use the HTTPS address instead —
> `git clone https://github.com/fzareen1/Summer_FAIR_PQC_Research.git`
> — and when it asks for a password, paste a **Personal Access Token** (GitHub → Settings → Developer settings → Personal access tokens → generate one with `repo` scope). Your normal GitHub password will **not** work.

### 7e. Open the project in Cursor

In Cursor: **File → Open Folder**, and select `Summer_FAIR_PQC_Research` in your home folder. Cursor reopens with the project loaded, and the terminal is a shell on MIDAS 2 inside the project. You're ready to work.

---

## You're fully set up when all of these are true

- [ ] You're on the Citadel VPN
- [ ] `ssh midas2` logs you into the server (ideally without a password)
- [ ] Cursor's bottom-left corner shows you're connected to `midas2`
- [ ] The project folder `Summer_FAIR_PQC_Research` is open in Cursor
- [ ] Cursor's terminal prompt shows `<username>@midas2` inside the project folder

---

## Quick troubleshooting

- **"No such host" / can't reach the server** → you're not on the VPN. Connect it and retry.
- **"Permission denied"** when logging in → wrong username or password. Remember the password is invisible as you type; check Caps Lock. If you've truly forgotten it, ask Dr. Zareen to reset it (you can't reset it yourself).
- **Cursor asks for a password every time** → your Part 3 key didn't get copied up. Re-run step 3b.
- **Cursor logs in as the wrong name** (e.g. your laptop username) → you added the host as a bare IP. Use the `midas2` shortcut from Part 4, which pins the correct username.
- **"Connect to Host" hangs** → check the Remote-SSH extension version (see the warning in Part 6).
- **Git clone fails on a password** → GitHub no longer accepts passwords; use the SSH key (7b–7d) or a Personal Access Token (7d alternative).
- **Stuck more than a few minutes on the same error** → grab a screenshot of the exact message and ask. Most of these are one-line fixes.
