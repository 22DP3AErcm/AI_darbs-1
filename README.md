# AI_darbs-1

Quick start
1. Copy `.env.example` to `.env` and fill in `HF_TOKEN` and`OPENAI_API_KEY` 
2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Edit `input.txt` with the text you want to process.

4. Run the CLI:

```bash
python main.py --file input.txt --keywords 8 --questions 5 --out outputs.json
```

Or run the tiny interactive UI:

```bash
python ui.py --interactive
```


