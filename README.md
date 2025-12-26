# Netflix Recap

A personalized "Year in Review" for your Netflix viewing habits, inspired by end-of-year recaps. Build your own interactive carousel-style summary of the shows and movies you watched.

**Live Demo:** [https://isfarbaset.github.io/netflix-recap/](https://isfarbaset.github.io/netflix-recap/)

## Features

- Interactive carousel/story UI (swipe, click, or use keyboard)
- Total watch time and titles watched
- Top 5 most-watched shows with play counts and hours
- Monthly viewing breakdown with bar chart
- Time of day patterns (Morning, Afternoon, Evening, Night)
- Longest streaming streak and binge session stats
- Personalized "Streaming Personality" type
- Fun facts and comparisons

## Build Your Own

### Prerequisites

- Python 3.8+
- Quarto CLI ([install here](https://quarto.org/docs/get-started/))

### Step 1: Clone the Repository

```bash
git clone https://github.com/isfarbaset/netflix-recap.git
cd netflix-recap
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Get Your Netflix Data

1. Go to [Netflix.com](https://www.netflix.com)
2. Click your profile icon > **Account**
3. Scroll down to **Security & Privacy**
4. Click **Download your personal information**
5. Select your profile and request the data
6. Wait for Netflix's email (can take up to 24 hours)
7. Download and extract the ZIP file

### Step 4: Add Your Data

Copy your extracted Netflix data folder into the `data/` directory:

```
netflix-recap/
└── data/
    └── YOUR_FOLDER_NAME/           # e.g., 288417895899340834
        └── CONTENT_INTERACTION/
            └── ViewingActivity.csv  # This is the key file
```

The data processor will automatically find the `ViewingActivity.csv` file.

### Step 5: Process Your Data

Run the data processing script:

```bash
python scripts/process_netflix_data.py data
```

This will:
- Parse your viewing history
- Filter to the current year (2025)
- Remove trailers, hooks, and very short views
- Calculate all statistics
- Generate `data/recap_stats.json`

You should see output like:
```
Netflix Recap - Data Processing Complete!
==========================================
Total Watch Time: XXX.X hours (X.X days)
Titles Watched: XXX
Unique Shows: XX
#1 Show: Your Top Show (XX plays)
...
```

### Step 6: Build the Site

```bash
quarto render
```

### Step 7: Preview Locally

```bash
quarto preview
```

Open [http://localhost:4000](http://localhost:4000) to see your personalized Netflix Recap!

## Deploy to GitHub Pages

1. Create a new repository on GitHub (e.g., `netflix-recap`)

2. Update the remote (if you cloned this repo):
   ```bash
   git remote set-url origin https://github.com/YOUR_USERNAME/netflix-recap.git
   ```

3. Push to GitHub:
   ```bash
   git add -A
   git commit -m "My Netflix Recap"
   git push -u origin main
   ```

4. Enable GitHub Pages:
   - Go to your repo's **Settings** > **Pages**
   - Set source to **Deploy from a branch**
   - Select `main` branch and `/docs` folder
   - Click **Save**

5. Your site will be live at:
   ```
   https://YOUR_USERNAME.github.io/netflix-recap/
   ```

## Customization

### Change the Year

Edit `scripts/process_netflix_data.py` and change the `year` parameter:

```python
stats = process_netflix_data(data_path, year=2024)  # Change to desired year
```

Then re-run the processing script.

### Customize Styling

Edit `styles.css` to change colors, fonts, or layout. Key CSS variables:

```css
:root {
    --netflix-red: #E50914;
    --netflix-black: #141414;
    --netflix-dark: #0a0a0a;
    --netflix-gray: #808080;
    --netflix-light: #e5e5e5;
}
```

### Add/Remove Slides

Edit `index.qmd` to modify the carousel slides. Each slide follows this structure:

```html
<div class="slide" data-slide="X">
    <div class="slide-content">
        <!-- Your content here -->
    </div>
</div>
```

## Project Structure

```
netflix-recap/
├── _quarto.yml              # Quarto configuration
├── index.qmd                # Main carousel page
├── stats.qmd                # Detailed stats page
├── insights.qmd             # Insights and analysis
├── about.qmd                # About page
├── styles.css               # Custom styling
├── images/
│   └── netflix-logo.png     # Logo image
├── data/                    # Your Netflix data (gitignored)
│   └── recap_stats.json   # Generated statistics
├── scripts/
│   └── process_netflix_data.py  # Data processing script
├── docs/                    # Generated site (for GitHub Pages)
└── README.md
```

## Privacy

All data processing happens **100% locally** on your machine. Your viewing history is never uploaded anywhere. The `data/` folder is gitignored by default.

## Troubleshooting

**"No ViewingActivity.csv found"**
- Make sure your Netflix export folder is inside the `data/` directory
- The file should be at `data/*/CONTENT_INTERACTION/ViewingActivity.csv`

**"No data found for year XXXX"**
- Check that you have viewing activity for the specified year
- Try changing the year in the processing script

**Quarto render fails**
- Make sure Quarto is installed: `quarto --version`
- Install it from [quarto.org](https://quarto.org/docs/get-started/)

## License

MIT License - feel free to fork and customize for your own Netflix Recap!
