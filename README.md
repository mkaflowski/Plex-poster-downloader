# Plex Movie Finder

A Docker application that connects to your Plex server and finds all movies that don't have a "Fanart" label, then automatically sets high-quality posters from either fanart.tv or TMDB.

## Features

- Connects to any Plex server using URL and token authentication
- Scans all movie libraries on your Plex server
- Identifies movies without the "Fanart" label
- **Two poster sources**: fanart.tv (community artwork) or TMDB (official posters)
- **Language preferences**: Gets posters in your preferred language with English fallback
- **Smart selection**: Chooses highest-rated/most-voted posters
- **Label management**: Adds "Fanart" label and optionally removes "Overlay" label
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

#### **TMDB API Key (required for both sources)**
1. Go to https://www.themoviedb.org/settings/api
2. Sign up and request API key
3. Used for movie ID lookups and TMDB posters

### Setup

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
   
   # Enable artwork processing
   ENABLE_FANART=true
   
   # Choose poster source
   PREFER_TMDB=false  # Use fanart.tv
   PREFER_TMDB=true   # Use TMDB
   
   # API Keys (based on your choice)
   FANART_API_KEY=your_fanart_key  # Required if PREFER_TMDB=false
   TMDB_API_KEY=your_tmdb_key      # Always required
   
   # Language preference
   MOVIE_LANGUAGE=en  # English, es (Spanish), fr (French), etc.
   ```

### Running the Application

#### Option 1: Run Once (RUN Mode)
```bash
# Using docker-compose profiles
docker-compose --profile run-once up --build

# Or set RUN_MODE=RUN in .env and run:
docker-compose up --build
```

#### Option 2: Scheduled Daily Runs (TIME Mode)
```bash
# Using docker-compose profiles (runs daily at 9 AM)
docker-compose --profile scheduled up -d --build

# Or set RUN_MODE=TIME in .env and run:
docker-compose up -d --build
```

#### Option 3: Custom Configuration
Edit your `.env` file:
```bash
RUN_MODE=TIME
RUN_TIME=14:30  # Run daily at 2:30 PM
RUN_ON_STARTUP=true  # Run immediately when container starts
PREFER_TMDB=true  # Use TMDB posters
MOVIE_LANGUAGE=es  # Spanish posters
IGNORE_OVERLAY_TAG=true  # Also skip movies with 'Overlay' label
```

Then run:
```bash
docker-compose up -d --build
```

#### Option 4: Direct Docker Commands
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

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `PLEX_URL` | Required | Your Plex server URL |
| `PLEX_TOKEN` | Required | Your Plex authentication token |
| `RUN_MODE` | `RUN` | `RUN` (once) or `TIME` (scheduled) |
| `RUN_TIME` | `09:00` | Daily run time in HH:MM format |
| `RUN_ON_STARTUP` | `false` | Run immediately when container starts (TIME mode only) |
| `ENABLE_FANART` | `false` | Enable poster processing |
| `PREFER_TMDB` | `false` | Use TMDB instead of fanart.tv |
| `FANART_API_KEY` | - | fanart.tv API key (required if PREFER_TMDB=false) |
| `TMDB_API_KEY` | - | TMDB API key (always required) |
| `MOVIE_LANGUAGE` | `en` | Preferred poster language (2-letter ISO code) |
| `IGNORE_OVERLAY_TAG` | `false` | Also ignore movies with 'Overlay' label |

## Output Format

The application will display:
- Run mode and configuration
- Connection status to your Plex server
- Poster source being used (fanart.tv or TMDB)
- Progress as it scans each movie library
- **All available posters** with stats (votes/ratings, language, URLs)
- **Selected poster** with reasoning
- Poster application status
- Label management (adding Fanart, removing Overlay)
- Summary count and completion timestamp

## Example Output

### fanart.tv Source
```
🎨 Artwork processing: ENABLED (using fanart.tv)
🔑 Fanart.tv API key: ✅ Set
🏷️  Ignoring only 'Fanart' label

Scanning library: Movies
Found 25 movies without 'Fanart' label (direct filter)
--------------------------------------------------
  1. Dune (2021)
     Added: 2025-09-14 20:15
     Labels: Action, Sci-Fi
     🎨 Processing artwork...
     🔍 Searching fanart.tv with TMDB ID: 438631
     📋 Found 4 poster(s) available:
         1. 👍 847 likes, 🌐 en
            URL: https://assets.fanart.tv/fanart/movies/438631/movieposter/dune-1.jpg
         2. 👍 623 likes, 🌐 en
            URL: https://assets.fanart.tv/fanart/movies/438631/movieposter/dune-2.jpg
         3. 👍 445 likes, 🌐 es
            URL: https://assets.fanart.tv/fanart/movies/438631/movieposter/dune-es.jpg
     ✅ Selected poster with most votes: 👍 847 likes, 🌐 en
     🖼️  Setting poster from fanart.tv
     ✅ Poster set successfully
     🏷️  Added 'Fanart' label
     ✅ PROCESSED (with fanart)

================================================================================
SUMMARY: 25 movies processed
✅ Successful: 24
🎨 Fanart set: 22
❌ Failed: 1
================================================================================
```

### TMDB Source
```
🎨 Artwork processing: ENABLED (using TMDB)
🔑 TMDB API key: ✅ Set

  1. Inception (2010)
     🎨 Processing artwork...
     🔍 Searching TMDB for posters with ID: 27205
     📋 Found 6 poster(s) available:
         1. ⭐ 8.2 rating (1547 votes), 🌐 en
            URL: https://image.tmdb.org/t/p/w780/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg
         2. ⭐ 7.8 rating (892 votes), 🌐 es
            URL: https://image.tmdb.org/t/p/w780/edv5CZvIx5oFdNEZmOsyTdZbZup.jpg
     ✅ Selected poster with highest rating: ⭐ 8.2 rating (1547 votes), 🌐 en
     🖼️  Setting poster from TMDB
     ✅ Poster set successfully
     🏷️  Added 'Fanart' label
     ✅ PROCESSED (with fanart)
```

## Managing Scheduled Runs

### View logs from scheduled container:
```bash
docker-compose --profile scheduled logs -f plex-movie-finder-scheduled
```

### Stop scheduled container:
```bash
docker-compose --profile scheduled down
```

### Change schedule without rebuilding:
```bash
# Stop current container
docker-compose down

# Update RUN_TIME in .env file
# Restart with new schedule
docker-compose --profile scheduled up -d
```

## Language Support

Set your preferred poster language using 2-letter ISO codes:

| Language | Code | Example |
|----------|------|---------|
| English | `en` | `MOVIE_LANGUAGE=en` |
| Spanish | `es` | `MOVIE_LANGUAGE=es` |
| French | `fr` | `MOVIE_LANGUAGE=fr` |
| German | `de` | `MOVIE_LANGUAGE=de` |
| Italian | `it` | `MOVIE_LANGUAGE=it` |
| Japanese | `ja` | `MOVIE_LANGUAGE=ja` |
| Korean | `ko` | `MOVIE_LANGUAGE=ko` |
| Portuguese | `pt` | `MOVIE_LANGUAGE=pt` |
| Russian | `ru` | `MOVIE_LANGUAGE=ru` |
| Chinese | `zh` | `MOVIE_LANGUAGE=zh` |

**Fallback logic:**
1. Tries your preferred language first
2. Falls back to English if preferred language not available  
3. Uses any available poster if English not available

## Label Management

### Default Behavior (IGNORE_OVERLAY_TAG=false)
- Processes movies **without** 'Fanart' label
- Adds 'Fanart' label after successful processing
- Removes 'Overlay' label if present

### Extended Filtering (IGNORE_OVERLAY_TAG=true) 
- Processes movies **without** 'Fanart' OR 'Overlay' labels
- Useful if you have existing overlay processing workflows
- Still adds 'Fanart' and removes 'Overlay' after processing

## Troubleshooting

**Connection Error**: Verify your PLEX_URL and PLEX_TOKEN in the `.env` file

**API Key Errors**: 
- fanart.tv: Check FANART_API_KEY is valid at https://fanart.tv
- TMDB: Check TMDB_API_KEY is valid at https://themoviedb.org

**No Posters Found**: 
- Movie might not exist in chosen database
- Try switching between fanart.tv and TMDB
- Check if movie has correct IMDB/TMDB IDs in Plex

**Container Exits Immediately**: Check logs with `docker-compose logs`

**Processing Stops Early**: Usually indicates connection issues to poster APIs

**Movies Not Found**: Ensure RUN_MODE and filtering labels are set correctly

## Comparison: fanart.tv vs TMDB

| Feature | fanart.tv | TMDB |
|---------|-----------|------|
| **Poster Quality** | Community artwork, often creative | Official studio posters |
| **Selection Criteria** | Most likes/votes from fans | Highest rating from users |
| **Language Support** | Good variety | Excellent variety |
| **Reliability** | Sometimes slower/unstable | Very reliable |
| **API Rate Limits** | More restrictive | More generous |
| **Poster Styles** | Artistic, fan-made variants | Professional, consistent |
| **Coverage** | Good for popular movies | Comprehensive coverage |

**Recommendation**: 
- Use **TMDB** for reliability and official posters
- Use **fanart.tv** for unique artistic variants and fan favorites

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

## Advanced Usage

### Custom Poster Selection
The app shows all available posters with their stats, so you can:
- See which poster was selected and why
- Manually download different posters using the displayed URLs
- Understand the quality/popularity of available options

### Batch Processing
- Use `RUN_MODE=RUN` for one-time batch processing
- Use `RUN_MODE=TIME` for automated daily processing
- Combine with `IGNORE_OVERLAY_TAG=true` to avoid reprocessing

### Integration with Other Tools
- The 'Fanart' label can be used by other Plex tools
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