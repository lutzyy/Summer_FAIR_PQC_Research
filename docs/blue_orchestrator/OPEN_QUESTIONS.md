# Open questions (ask; do not guess)

1. **Rule-based grader:** Spec assumes Sebastian’s grader already labels runs. Repo has none. Is the provisional `adversary/blue/rule_grader.py` + `rule_based_grades` table acceptable until his lands?
2. **Zeek / Suricata:** Are they running on MIDAS and tied to run time windows? If not, confirm “without sensors” as the default evidence condition.
3. **Success criteria per attack:** Spec requires an explicit rubric. Proposed definitions are in `adversary/blue/rubric/v1.yaml` — please confirm or rewrite before gold adjudication.
4. **vLLM:** Confirm model + context length for Blue Agent (code assumes Qwen2.5-14B-Instruct, 8192).
5. **Crypto config switching:** Today = two containers. Is a future single-target config switch (env/rebuild) planned, or stay multi-container?
6. **`contract.py` / `runs` schema:** Spec forbids changing keys. Tool stderr/exit status are not stored — OK to leave them out of the run row and only cite what collectors can gather?
7. **Branch name:** Spec/user asked for `blue_agent`; Cloud Agent defaults use `cursor/…-98c1`. This work is on `blue_agent` as requested.
