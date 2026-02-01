# FC League Tracker

Extract league member data from FC Mobile (FIFA Mobile) screenshots using AI vision.

## Features

- 📱 **Auto-capture** - ADB-based screenshot capture with auto-scroll
- 🤖 **AI extraction** - Uses Llama 4 Maverick via Groq for accurate OCR
- 🔄 **Deduplication** - Fuzzy name matching to handle overlapping screenshots
- 📊 **CSV export** - Sorted by activity score

## Requirements

- Python 3.10+
- Android phone with USB debugging enabled
- [ADB](https://developer.android.com/tools/adb) installed
- [Groq API key](https://console.groq.com/) (free tier available)

## Installation

```bash
git clone https://github.com/jasnoorpannu/fc_league_tracker.git
cd fc_league_tracker
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Setup

1. Create a `.env` file with your Groq API key:
```bash
echo 'GROQ_API_KEY=your_api_key_here' > .env
```

2. Connect your phone via USB and enable USB debugging

3. Open FC Mobile → League → Members

## Usage

### Step 1: Capture Screenshots
```bash
python capture/adb_capture.py
```
Press Enter when ready. The script will auto-scroll and capture screenshots.

### Step 2: Extract Member Data
```bash
python run_llm.py
```

### Output
Results saved to `output/league_members_llm.csv`:
```csv
rank,name,ovr,activity
1,TREK,125,6245
2,Dan,121,6185
...
```

## Project Structure

```
fc_league_tracker/
├── capture/
│   └── adb_capture.py    # Screenshot capture with auto-scroll
├── llm/
│   └── llm_extract.py    # Groq LLM extraction
├── ocr/                  # Tesseract OCR fallback (optional)
├── output/               # Generated CSV files
├── screenshots/          # Captured screenshots
├── run_llm.py           # Main pipeline
└── .env                 # API key (create this)
```

## License

MIT
