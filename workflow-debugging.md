# Workflow Debugging for RadioQuest

## Major Challenges
- **Git History Wipe**: Accidental `git filter-repo` erased project files. Recovered by rebuilding `app.py`, `Dockerfile`, and docs from memory.
- **VPC Connectivity**: Cloud Run couldn't reach MongoDB Atlas. Fixed with a VPC connector and static egress IP via `gcloud compute`.
- **Environment Variables**: Hardcoded `MONGO_URI` temporarily in `app.py` (warning added for production switch to `.env`).

## Solutions
- Rebuilt core files with Flask, TTS (`en-NG-Wavenet-A`), and MongoDB integration.
- Configured VPC: `gcloud compute networks vpc-access connectors create ...`.
- Deployed on Cloud Run: `gcloud run deploy radioquest-e1f5a --image gcr.io/radioquest-e1f5a/image --region us-central1`.

## Tips
- Always back up before Git history rewrites.
- Test VPC connectivity with `gcloud` logs.
- Use `.env.example` for production setups.

## Contributors
- Asher Engos (Adam Sherengos, Solo Developer) 