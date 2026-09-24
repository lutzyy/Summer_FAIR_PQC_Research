# Stefan — Tools & Targets

**Your half of the red team agent.** You build the things that get attacked and the tools that do the attacking. By the end you have a sealed attacker container that, on command, inspects a target's encryption, replays a recorded attack, or sends a crafted packet — and prints the result as JSON. Sebastian's agent will call your tools and store the results.

You and Sebastian work independently. The only thing that has to line up is **the contract** below. Read it first, then never change it without telling Sebastian.

> **Where you work.** Everything here runs on the **MIDAS 2** server, through **Cursor**. Connect Cursor to the server, open the project folder, and open a terminal (Ctrl+`); its prompt should read `yourusername@midas2`. Your working folder is your part of the cloned repo:
> ```
> cd ~/Summer_FAIR_PQC_Research/adversary/tools
> ```
> All of Stefan's files (Dockerfile, tools.py, nginx.conf, certs, captures) live in that `tools/` folder.

---

## The contract (read this first)

Every tool you write prints **one line of JSON** to standard output, with exactly these keys:

```json
{
  "attack_name": "tls_probe",
  "crypto_detected": "TLSv1.3 / TLS_AES_256_GCM_SHA384",
  "attack_params": {"target": "practice-target:443"},
  "outcome_notes": "Handshake completed."
}
```

- `attack_name` — short id of what you ran (`tls_probe`, `pcap_replay`, `scapy_syn_probe`).
- `crypto_detected` — what encryption the target used, or `null` if the tool doesn't inspect crypto.
- `attack_params` — any settings you used (always include `target`).
- `outcome_notes` — a short human-readable result.

That JSON shape is the handshake between your half and Sebastian's half. As long as your tools print it, the two halves snap together.

The four keys are defined once, in Sebastian's folder, at `../brain/contract.py` (it's in your clone too, since you share one repo). You don't keep your own copy — your tools just need to print those four keys.

---

## How your half fits the whole system

```
  [ practice-target ]      [ attacker ]      <-- YOUR containers, both on lab-net
       (you)                  (you)              (SEALED: no internet, no brain access)
             \                /
              \  docker exec /
               \            /
          [ agent.py ]                       <-- Sebastian (the only thing touching both sides)
               /            \
              /              \
       localhost:8000    localhost:5432
       [ vLLM brain ]    [ Postgres records ]   <-- Sebastian (normal networking)
```

Your containers live in the sealed lab. They can talk to each other and nothing else. Sebastian's agent reaches into your attacker container with `docker exec` to run your tools — that's the bridge. Your sealed box never reaches the internet, the AI model, or the database. Keep it that way.

---

## Safety & isolation (read every session)

This project uses **recorded botnet pcaps** and attack tools for **defensive research only**. They must stay inside a sealed Docker lab — never on the open network, never in GitHub.

### When to run the safety check

Run **`bash verify-lab-safety.sh`** from `adversary/tools/`:

- **Every time** you connect to MIDAS 2 and before any attack or pcap replay
- **Again** after you add or change anything: a new pcap, container, config, `tools.py`, `Dockerfile`, or network setting

Do not run `tools.py` or `tcpreplay` on the MIDAS 2 host — **only** inside the `attacker` container via `docker exec`.

Full checklist: `Instructions/lab_safety_checklist.md`

### Rules you must follow

1. **`lab-net` is `--internal`** — no route to the internet. Re-verify with the script after every change.
2. **`practice-target` and `attacker` live only on `lab-net`.** Never attach them to `bridge` or the host network.
3. **Pcaps stay local** — copy from `/shared/zareen_research/captures/` into `captures/` only. Never commit them (`captures/` and `*.pcap` are gitignored).
4. **Replay targets lab only** — always `practice-target:443` (or another container on `lab-net`), never external hosts.
5. **Never commit** `target-certs/`, `*.pem`, `.env`, or pcaps.

### Quick safety commands (manual)

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/tools
bash verify-lab-safety.sh
```

If any check **FAILs**, stop and fix before continuing.

---

## Tools you'll use — what, why, and what's already set up

You don't install Docker yourself — on MIDAS 2 you don't have admin rights, so **the server admin installs Docker and adds you to the `docker` group.** Your job is just to confirm it works. Everything else is either a Docker image (downloaded automatically) or baked into your attacker box by the Dockerfile in Step 5.

### Provided by the admin — you only verify

- **Docker** — runs every part of the project in isolated "containers." Confirm it's ready:
  ```bash
  docker --version     # shows a version
  docker ps            # lists containers without a "permission denied" error
  ```
  If `docker ps` says *permission denied*, you're not in the `docker` group yet — ask the admin to add you (this is part of the server setup). You cannot fix this yourself.
- **OpenSSL** — already installed on MIDAS 2; you use it once to make the practice target's certificate. Nothing to install.

### Pulled automatically as Docker images — no manual install

Docker downloads these the first time you use them.

- **nginx** — the web server that acts as your practice hospital target. Serves encrypted HTTPS so your tools have real crypto to inspect.
- **kalilinux/kali-rolling** — the base for your attacker box; a Linux distribution built for security testing.
- **alpine** — a tiny throwaway image used only to prove the sealed network is really sealed.

### Baked into your attacker image by the Dockerfile (Step 5)

These install *inside* the attacker box during `docker build`, while the host still has internet — so the sealed box ends up with every tool it needs and never has to reach the internet itself. You don't type these installs by hand; they're the lines in your Dockerfile. The "why" is so you know what that Dockerfile is doing.

- **python3** — runs your tool code (`tools.py`).
- **python3-scapy** — builds and sends custom network packets (your `craft` tool).
- **tcpreplay** — replays your recorded botnet captures onto the network (your `replay` tool).
- **openssl** — inspects the target's TLS handshake to see what encryption is in use (your `detect` tool).
- **dnsutils, iputils-ping** — basic network checks (look up names, ping the target).
- **ca-certificates** — standard certificate-trust files Kali expects.

---

## Step 1 — Confirm Docker works

First, check Docker is installed and you can reach it without `sudo`:

```bash
docker --version
docker ps
```

`docker --version` should print a version, and `docker ps` should list containers (probably an empty list) **without** a permission error.

Then run the standard Docker self-test — it downloads a tiny image and runs it:

```bash
docker run --rm hello-world
```

You should see a **"Hello from Docker!"** message. That confirms Docker is fully working for your account.

> If `docker ps` or `hello-world` says *permission denied*, you're not in the `docker` group yet — ask the admin to add you, then **log out and back in** (close your terminal and open a fresh one, or reconnect Cursor) so the change takes effect. You can confirm with `groups` — it should list `docker`. Don't continue until `hello-world` runs cleanly.

---

## Step 2 — Go to your folder

Your tool code and attack captures live in your part of the repo:

```bash
cd ~/Summer_FAIR_PQC_Research/adversary/tools
mkdir -p captures
```

The large botnet captures (Mirai / Bashlite / Torii) are kept in the shared data folder `/shared/zareen_research`. Copy one in and name it `sample.pcap` so later commands are simple:

```bash
cp /shared/zareen_research/captures/mirai_capture.pcap ./captures/sample.pcap
```

(Your `captures/` folder and certs are **not** committed to GitHub — they're large or sensitive and are covered by `.gitignore`.)

---

## Step 3 — Build the sealed network and prove it's sealed

Create the private network where your target and attacker will both live. The `--internal` flag is the wall that cuts it off from the outside world:

```bash
docker network create --internal lab-net
```

Now prove the wall is real. Start a throwaway container on it and try to reach the internet. **You want this to FAIL:**

```bash
docker run --rm --network lab-net alpine ping -c 2 8.8.8.8
```

If it says "bad address" or hangs and gives no replies — good, the wall works. If it actually gets replies, stop and fix the network before doing anything else. (Note: pulling the `alpine` image still works because Docker downloads images using the *host's* connection before sealing the container — that's expected.)

---

## Step 4 — Stand up the practice target

This is the fake hospital service you'll attack. You'll run a web server that speaks encrypted HTTPS, so there's real encryption for your tools to inspect. Run these from your `tools/` folder.

First, make a self-signed certificate (this is the target's encryption key — making one yourself is normal for a lab):

```bash
mkdir -p target-certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout target-certs/key.pem \
  -out target-certs/cert.pem \
  -days 365 -subj "/CN=practice-target"
```

Next, write a tiny web-server config. Create `nginx.conf` (in your `tools/` folder) with this content:

```nginx
events {}
http {
  server {
    listen 443 ssl;
    ssl_certificate     /certs/cert.pem;
    ssl_certificate_key /certs/key.pem;
    location / { return 200 "practice hospital ok\n"; }
  }
}
```

Now run the target on the sealed network:

```bash
docker run -d --name practice-target --network lab-net \
  -v "$PWD/target-certs":/certs:ro \
  -v "$PWD/nginx.conf":/etc/nginx/nginx.conf:ro \
  nginx
```

Confirm it's running:

```bash
docker ps --filter name=practice-target
```

(Later, to practice on real post-quantum encryption, you can swap this for the Open Quantum Safe demo server image — but plain nginx is the right first target.)

---

## Step 5 — Build the attacker image

Your attacker needs tools (Python, scapy, tcpreplay, openssl) installed. Because the attacker runs on the sealed network with no internet, you **bake the tools into the image now** (while the host still has internet), then run it sealed.

Create a file named `Dockerfile` (in your `tools/` folder) with this content:

```dockerfile
FROM kalilinux/kali-rolling
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-scapy tcpreplay openssl dnsutils iputils-ping ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/redteam
CMD ["sleep", "infinity"]
```

Build it (this step uses the internet — that's fine, building happens on the host):

```bash
docker build -t redteam-attacker .
```

This takes a few minutes the first time.

---

## Step 6 — Run the attacker container (sealed)

Start it on `lab-net`, mounting your `tools/` folder so your code and captures are available inside. The `--cap-add` flags let it send raw network packets (needed for scapy and tcpreplay):

```bash
docker run -d --name attacker --network lab-net \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v "$PWD":/opt/redteam \
  redteam-attacker
```

Check it can reach the target but NOT the internet:

```bash
docker exec attacker ping -c 2 practice-target   # should SUCCEED
docker exec attacker ping -c 2 8.8.8.8            # should FAIL
```

The container name `practice-target` resolves automatically because both containers share `lab-net`.

---

## Step 7 — Write the tools

Create `tools.py` in your `tools/` folder. Because the folder is mounted into the container, you edit it on the host (in Cursor) and it's instantly live inside the container.

```python
#!/usr/bin/env python3
"""Red team tools. Runs INSIDE the sealed attacker container.
Usage:  python3 tools.py detect  <target>
        python3 tools.py replay  <target> <pcap_path>
        python3 tools.py craft   <target>
Always prints ONE line of JSON with the four contract keys.
"""
import sys, json, subprocess


def detect_crypto(target: str) -> dict:
    host, _, port = target.partition(":")
    port = port or "443"
    proc = subprocess.run(
        ["openssl", "s_client", "-connect", f"{host}:{port}", "-brief"],
        input="", capture_output=True, text=True, timeout=15,
    )
    out = proc.stdout + proc.stderr
    proto = cipher = "unknown"
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("Protocol"):
            proto = s.split(":")[-1].strip()
        if s.startswith("Ciphersuite") or s.startswith("Cipher"):
            cipher = s.split(":")[-1].strip()
    ok = proto != "unknown"
    return {
        "attack_name": "tls_probe",
        "crypto_detected": f"{proto} / {cipher}",
        "attack_params": {"target": target},
        "outcome_notes": "Handshake completed." if ok else "Could not read handshake.",
    }


def replay_pcap(target: str, pcap: str) -> dict:
    proc = subprocess.run(
        ["tcpreplay", "--intf1=eth0", pcap],
        capture_output=True, text=True, timeout=60,
    )
    out = (proc.stdout + proc.stderr).strip()
    return {
        "attack_name": "pcap_replay",
        "crypto_detected": None,
        "attack_params": {"target": target, "pcap": pcap},
        "outcome_notes": out[-400:] if out else "Replay finished.",
    }


def craft_probe(target: str) -> dict:
    from scapy.all import IP, TCP, sr1, conf
    conf.verb = 0
    host, _, port = target.partition(":")
    port = int(port or "443")
    resp = sr1(IP(dst=host) / TCP(dport=port, flags="S"), timeout=5)
    if resp and resp.haslayer(TCP):
        note = f"Port {port} responded with TCP flags {resp[TCP].flags}."
    else:
        note = f"No response from port {port}."
    return {
        "attack_name": "scapy_syn_probe",
        "crypto_detected": None,
        "attack_params": {"target": target, "port": port},
        "outcome_notes": note,
    }


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "detect":
            result = detect_crypto(sys.argv[2])
        elif cmd == "replay":
            result = replay_pcap(sys.argv[2], sys.argv[3])
        elif cmd == "craft":
            result = craft_probe(sys.argv[2])
        else:
            result = {"attack_name": "none", "crypto_detected": None,
                      "attack_params": {}, "outcome_notes": f"Unknown command: {cmd}"}
    except Exception as e:
        result = {"attack_name": cmd or "none", "crypto_detected": None,
                  "attack_params": {}, "outcome_notes": f"Tool error: {e}"}
    print(json.dumps(result))
```

The `try/except` matters: even when a tool fails, it still prints valid JSON, so Sebastian's agent never chokes on your output.

---

## Step 8 — Test every tool by hand

This is the most important habit: prove each tool works when *you* run it, before any AI is involved. Run each command and confirm you get one clean line of JSON back.

```bash
docker exec attacker python3 /opt/redteam/tools.py detect practice-target:443
docker exec attacker python3 /opt/redteam/tools.py replay practice-target:443 /opt/redteam/captures/sample.pcap
docker exec attacker python3 /opt/redteam/tools.py craft  practice-target:443
```

Expected: each prints a JSON object with the four keys. The `detect` one should show a real TLS protocol and cipher from your nginx target. If a tool errors, the JSON will say why — fix it until all three are clean.

When you edit `tools.py` in Cursor, just re-run the command — no rebuild needed, because the folder is mounted.

---

## Step 9 — You're done when you can tick all of these

- [DONE] `bash verify-lab-safety.sh` passes (all checks green)
- [DONE] `docker --version`, `docker ps`, and `docker run --rm hello-world` all work without a permission error
- [DONE] `lab-net` exists and the "ping the internet" test **fails**
- [DONE] `practice-target` is running on `lab-net`
- [DONE] `attacker` is running on `lab-net`, can reach the target, cannot reach the internet
- [DONE] `tools.py detect` returns a real protocol + cipher as JSON
- [DONE] `tools.py replay` runs your capture and returns JSON
- [DONE] `tools.py craft` returns JSON
- [DONE] Your tools print exactly the four keys defined in `../brain/contract.py`

---

## Converge day — handing your half to Sebastian

**Scheduled: week of July 13, 2026, with Dr. Zareen present.** Do not attempt integration before that session. See `Instructions/converge_day.md`.

Nothing about your code changes at converge. Sebastian's agent will simply run the exact commands you tested in Step 8:

```bash
docker exec attacker python3 /opt/redteam/tools.py detect practice-target:443
```

…capture the JSON line you print, and save it to the database. Your job at converge is to:

1. Sit with Sebastian and confirm your tools' output keys match `../brain/contract.py` exactly.
2. Run `bash verify-lab-safety.sh` together — all checks must **PASS**.
3. Confirm your three commands still each print exactly one JSON line (Sebastian reads the **last** line of output, so don't print anything else to stdout).
4. Watch the first full run together: the agent picks a tool, runs *your* tool via `docker exec`, and a row appears in the database. That's the milestone.

If something breaks at converge, it's almost always one of two things: the JSON keys don't match the contract, or a tool printed extra text before the JSON. Both are quick fixes on your side.
