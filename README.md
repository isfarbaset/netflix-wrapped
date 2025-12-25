# Netflix Wrapped

A personalized "Year in Review" for your Netflix viewing habits. Create your own Wrapped-style summary of the shows and movies you watched.

**Live Demo:** [https://isfarbaset.github.io/netflix-wrapped/](https://isfarbaset.github.io/netflix-wrapped/)

## Features

- Total watch time and titles watched
- Top 10 most-watched shows
- Monthly viewing breakdown
- Day of week and time of day patterns
- Binge watching statistics
- Personalized "Streaming Personality" type
- Fun facts and comparisons

## Setup

### Prerequisites

- Python 3.8+
- Quarto CLI ([install here](https://quarto.org/docs/get-started/))

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/isfarbaset/netflix-wrapped.git
   cd netflix-wrapped
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Get your Netflix data:
   - Go to Netflix.com > Profile > Account
   - Click "Download your personal information"
   - Wait for the email and download the ZIP
   - Extract `ViewingActivity.csv` to the `data/` folder

4. Process your data:
   ```bash
   python scripts/process_data.py
   ```

5. Build the site:
   ```bash
   quarto render
   ```

6. Preview locally:
   ```bash
   quarto preview
   ```

## Deployment to GitHub Pages

1. Push to GitHub
2. Go to repository Settings > Pages
3. Set source to "Deploy from a branch"
4. Select `main` branch and `/docs` folder
5. Your site will be live at `https://YOUR_USERNAME.github.io/netflix-wrapped`

## Project Structure

```
netflix-wrapped/
├── _quarto.yml        # Quarto configuration
├── index.qmd          # Home page
├── stats.qmd          # Detailed stats page
├── insights.qmd       # Insights and analysis
├── about.qmd          # About page
├── styles.css         # Custom styling
├── data/              # Your Netflix data (gitignored)
│   └── ViewingActivity.csv
├── scripts/
│   └── process_data.py
├── docs/              # Generated site (for GitHub Pages)
└── README.md
```

## Privacy

All data processing happens locally. Your viewing history is never uploaded anywhere.

## License

MIT License - feel free to fork and customize!
