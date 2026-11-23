"""Day 8 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Recap (2 minutes, from memory) =====
# Recap: predict both lines, then run. Day 6's secrets meet today's Git.
import os

os.environ.pop("CMS_API_KEY", None)  # make sure the key is not set
print(os.environ.get("CMS_API_KEY", "missing"))
# set the key for this Python process only (like process.env in Node)
os.environ["CMS_API_KEY"] = "demo-key-123"
print(os.environ.get("CMS_API_KEY", "missing")[:4] + "...")
