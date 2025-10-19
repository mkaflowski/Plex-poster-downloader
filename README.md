# FanPlex - Plex Poster Downloader

A Docker application that connects to your Plex server and finds all movies that don't have a "FanPlex" label, then automatically sets high-quality posters from either fanart.tv or TMDB.

## Features

- Connects to any Plex server using URL and token authentication
- Scans all movie libraries on your Plex server
- Identifies movies without the "FanPlex" label
- **Automatic poster processing** for all found movies
- **Two poster sources**: fanart.tv (community artwork) or TMDB (official posters)
- **Language preferences**: Gets posters in your preferred language with English fallback
- **Smart original language detection**: Automatically uses original language posters for movies from specific countries (e.g., Polish posters for Polish films)
- **Smart selection**: Chooses highest-rated/most-voted posters
- **Label management**: Adds "FanPlex" label and optionally removes "Overlay" label
- **Two run modes**: Run once or scheduled daily runs
- Runs in a secure Docker container

## Poster Sources

### **fanart.tv (Default)**
- Community-driven artwork with voting system
- High-quality fan-created posters
- Language-specific options available
- Sorts by most likes/votes

### **TMDB (Optional)**
- Official movie database posters
- Professional artwork from studios
- Vote ratings and counts available
- Generally more reliable/stable

## Run Modes

### RUN Mode (Default)
- Executes once and exits
- Perfect for manual runs or cron jobs
- Container stops after completion

### TIME Mode
- Runs daily at a specified time
- Container stays running and schedules the job
- Configurable run time (24-hour format)
- Optional immediate run on startup

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Access to a Plex server
- Plex authentication token
- API key for your chosen poster source

### Getting Your API Keys

#### **Plex Token**
1. Log into your Plex Web App
2. Go to Settings > Network > Show Advanced
3. Or follow this guide: [Finding an authentication token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)

#### **fanart.tv API Key (if using fanart.tv)**
1. Go to https://fanart.tv/get-an-api-key/
2. Sign up for free account
3. Get your personal API key

#### **TMDB API Key (required)**
1. Go to https://www.themoviedb.org/settings/api
2. Sign up and request API key
3. Required for movie ID lookups and country detection
4. Also used directly if PREFER_TMDB=true

### Setup

Install from Docker Hub.

### Manual setup

1. Clone or download these files to a directory
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and configure your settings:
   ```bash
   # Basic Plex connection
   PLEX_URL=http://your-plex-server-ip:32400
   PLEX_TOKEN=your_plex_token
   
   # Choose poster source
   PREFER_TMDB=false  # Use fanart.tv
   PREFER_TMDB=true   # Use TMDB
   
   # API Keys (based on your choice)
   FANART_API_KEY=your_fanart_key  # Required if PREFER_TMDB=false
   TMDB_API_KEY=your_tmdb_key      # Always required
   
   # Language preference
   MOVIE_LANGUAGE=en  # English, es (Spanish), fr (French), etc.
   
   # Original language detection
   ORIGINAL_LANGUAGE_COUNTRIES="PL,IT"  # Polish and Italian movies get original language posters
   ```

### Running the Application

#### Custom Configuration
Edit your `.env` file:
```bash
RUN_MODE=TIME
RUN_TIME=14:30  # Run daily at 2:30 PM
RUN_ON_STARTUP=true  # Run immediately when container starts
PREFER_TMDB=true  # Use TMDB posters
MOVIE_LANGUAGE=en  # Default to English posters
ORIGINAL_LANGUAGE_COUNTRIES="PL,IT,ES"  # Use original language for these countries
IGNORE_OVERLAY_TAGGED=true  # Also skip movies with 'Overlay' label
```

Then run:
```bash
docker-compose up -d --build
```

#### Direct Docker Commands
```bash
# Build the image
docker build -t plex-movie-finder .

# Run once with fanart.tv
docker run --env-file .env plex-movie-finder

# Run scheduled with TMDB posters
docker run -d --env-file .env \
  -e RUN_MODE=TIME \
  -e RUN_TIME=10:30 \
  -e PREFER_TMDB=true \
  plex-movie-finder
```

## Configuration Options

| Environment Variable | Default         | Description                                            |
|----------------------|-----------------|--------------------------------------------------------|
| `PLEX_URL`           | Required        | Your Plex server URL                                   |
| `PLEX_TOKEN`         | Required        | Your Plex authentication token                         |
| `RUN_MODE`           | `RUN`           | `RUN` (once) or `TIME` (scheduled)                     |
| `RUN_TIME`           | `09:00`         | Daily run time in HH:MM format                         |
| `RUN_ON_STARTUP`     | `false`         | Run immediately when container starts (TIME mode only) |
| `PREFER_TMDB`        | `false`         | Use TMDB instead of fanart.tv                          |
| `FANART_API_KEY`     | -               | fanart.tv API key (required if PREFER_TMDB=false)      |
| `TMDB_API_KEY`       | Required        | TMDB API key (always required)                         |
| `MOVIE_LANGUAGE`     | `en`            | Preferred poster language (2-letter ISO code)          |
| `ORIGINAL_LANGUAGE_COUNTRIES` | -      | Comma-separated country codes (e.g., "PL,IT,ES") - movies from these countries use original language posters |
| `IGNORE_OVERLAY_TAGGED` | `false`      | Also ignore movies with 'Overlay' label                |
| `TZ`                 | `Europe/Warsaw` | Your timezone                                          |

## Original Language Detection

The `ORIGINAL_LANGUAGE_COUNTRIES` feature allows you to automatically use original language posters for movies from specific countries, while using your preferred language for everything else.

### How It Works

1. Script checks the movie's production country via TMDB
2. If the country matches your configured list, it uses the movie's original language
3. Otherwise, it uses your `MOVIE_LANGUAGE` preference

### Example Scenarios

**Configuration:**
```bash
MOVIE_LANGUAGE=en
ORIGINAL_LANGUAGE_COUNTRIES="PL,IT"
```

**Results:**
- 🇵🇱 Polish movie → Gets Polish poster (original language)
- 🇮🇹 Italian movie → Gets Italian poster (original language)
- 🇺🇸 American movie → Gets English poster (your preference)
- 🇫🇷 French movie → Gets English poster (your preference)

**Benefits:**
- No need to manually configure language per movie
- Perfect for international movie collections
- Respects cultural authenticity for specific regions
- Falls back to your preference for everything else

## Label Management

### Default Behavior (IGNORE_OVERLAY_TAGGED=false)
- Processes movies **without** 'FanPlex' label
- Adds 'FanPlex' label after successful processing
- Removes 'Overlay' label if present

### Extended Filtering (IGNORE_OVERLAY_TAGGED=true) 
- Processes movies **without** 'FanPlex' OR 'Overlay' labels
- Useful if you have existing overlay processing workflows
- Still adds 'FanPlex' and removes 'Overlay' after processing

## Troubleshooting

**Connection Error**: Verify your PLEX_URL and PLEX_TOKEN in the `.env` file

**Missing TMDB API Key**: TMDB API key is now required for all operations (country detection and ID lookups)

**Original Language Not Working**: Make sure TMDB_API_KEY is set correctly and the movie has production country information in TMDB

## Security Notes

- The container runs as a non-root user
- Environment variables are used for sensitive configuration
- No data is modified on your Plex server except poster uploads
- API keys are not logged or displayed

## PyCharm/Local Development

For testing locally in PyCharm:
1. Install requirements: `pip install PlexAPI schedule python-dotenv requests`
2. Create `.env` file with your configuration
3. Set PyCharm run configuration environment variables or use the `.env` file
4. Run `main.py` directly

### Custom Poster Selection
The app shows all available posters with their stats, so you can:
- See which poster was selected and why
- Manually download different posters using the displayed URLs
- Understand the quality/popularity of available options

### Batch Processing
- Use `RUN_MODE=RUN` for one-time batch processing
- Use `RUN_MODE=TIME` for automated daily processing
- Combine with `IGNORE_OVERLAY_TAGGED=true` to avoid reprocessing

### Integration with Other Tools
- The 'FanPlex' label can be used by other Plex tools
- Compatible with existing overlay workflows
- Can be run alongside other Plex automation tools

## Customization

You can modify `main.py` to:
- Search for different labels
- Filter by specific libraries  
- Export results to a file
- Add different poster sources
- Change poster selection criteria
- Add notification systems