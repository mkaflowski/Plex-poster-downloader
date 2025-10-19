#!/usr/bin/env python3
"""
Plex Movie Finder - Find movies without 'Overlay' label and set fanart covers
"""
import os
import sys
import time
import schedule
import requests
from datetime import datetime
from plexapi.server import PlexServer

# Load environment variables from .env file (for local development)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env vars


def get_plex_connection():
    """Establish connection to Plex server"""
    plex_url = os.getenv('PLEX_URL')
    plex_token = os.getenv('PLEX_TOKEN')

    if not plex_url or not plex_token:
        print("ERROR: PLEX_URL and PLEX_TOKEN environment variables are required")
        sys.exit(1)

    try:
        plex = PlexServer(plex_url, plex_token)
        print(f"Connected to Plex server: {plex.friendlyName}")
        return plex
    except Exception as e:
        print(f"ERROR: Could not connect to Plex server: {e}")
        sys.exit(1)


def get_movie_details_from_tmdb(tmdb_id, imdb_id=None):
    """Get movie details including country and original language from TMDB"""
    tmdb_api_key = os.getenv('TMDB_API_KEY')

    if not tmdb_api_key:
        return None

    try:
        # Get TMDB ID if we only have IMDB ID
        if not tmdb_id and imdb_id and imdb_id.startswith('tt'):
            find_url = f"https://api.themoviedb.org/3/find/{imdb_id}"
            find_params = {"api_key": tmdb_api_key, "external_source": "imdb_id"}

            find_response = requests.get(find_url, params=find_params, timeout=10)
            if find_response.status_code == 200:
                find_data = find_response.json()
                if find_data.get('movie_results'):
                    tmdb_id = find_data['movie_results'][0]['id']

        if not tmdb_id:
            return None

        # Get movie details
        details_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        details_params = {"api_key": tmdb_api_key}

        response = requests.get(details_url, params=details_params, timeout=10)
        if response.status_code == 200:
            data = response.json()

            # Extract relevant information
            original_language = data.get('original_language', '')
            production_countries = [country['iso_3166_1'] for country in data.get('production_countries', [])]

            return {
                'tmdb_id': tmdb_id,
                'original_language': original_language,
                'production_countries': production_countries
            }

        return None

    except Exception as e:
        print(f"     ⚠️  Failed to get movie details: {e}")
        return None


def determine_poster_language(movie_details):
    """Determine which language to use for poster based on movie origin"""
    # Get the list of countries that should use original language
    # Format: "PL,IT,ES" - comma-separated country codes
    original_lang_countries = os.getenv('ORIGINAL_LANGUAGE_COUNTRIES', '').upper().split(',')
    original_lang_countries = [c.strip() for c in original_lang_countries if c.strip()]

    # Get default preferred language
    default_lang = os.getenv('MOVIE_LANGUAGE', 'en')

    # If no movie details or no countries configured, use default
    if not movie_details or not original_lang_countries:
        return default_lang

    production_countries = movie_details.get('production_countries', [])
    original_language = movie_details.get('original_language', '')

    # Check if any production country matches our configured countries
    for country in production_countries:
        if country in original_lang_countries:
            # Use the movie's original language
            print(f"     🌍 Movie from {country} - using original language: {original_language}")
            return original_language

    # No match, use default preference
    return default_lang


def get_tmdb_cover(movie_title, year, imdb_id=None, tmdb_id=None):
    """Get movie poster from TMDB - prioritizes posters in movie language or English with highest vote average"""
    tmdb_api_key = os.getenv('TMDB_API_KEY')

    if not tmdb_api_key:
        print(f"     ⚠️  TMDB_API_KEY not set - skipping TMDB lookup")
        return None

    try:
        # Get movie details to determine language preference
        movie_details = get_movie_details_from_tmdb(tmdb_id, imdb_id)

        if movie_details:
            tmdb_id = movie_details['tmdb_id']
            preferred_lang = determine_poster_language(movie_details)
        else:
            preferred_lang = os.getenv('MOVIE_LANGUAGE', 'en')

        if not tmdb_id:
            print(f"     ⚠️  No TMDB ID available")
            return None

        # Get movie images from TMDB
        images_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images"
        images_params = {"api_key": tmdb_api_key}

        print(f"     🔍 Searching TMDB for posters with ID: {tmdb_id}")

        try:
            response = requests.get(images_url, params=images_params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # Look for movie posters
                if 'posters' in data and data['posters']:
                    posters = data['posters']

                    # Filter posters by preferred language first, then English as fallback
                    preferred_posters = [p for p in posters if p.get('iso_639_1', '') == preferred_lang]
                    if not preferred_posters and preferred_lang != 'en':
                        print(f"     🔍 No {preferred_lang} posters found, trying English...")
                        preferred_posters = [p for p in posters if p.get('iso_639_1', '') == 'en']
                    if not preferred_posters:
                        print(f"     🔍 No English posters found, using all available posters...")
                        preferred_posters = posters

                    # Sort by vote_average descending, then by vote_count descending
                    sorted_posters = sorted(preferred_posters,
                                            key=lambda x: (float(x.get('vote_average', 0)),
                                                           int(x.get('vote_count', 0))),
                                            reverse=True)

                    best_poster = sorted_posters[0]
                    file_path = best_poster.get('file_path', '')
                    if not file_path:
                        print(f"     ❌ No valid poster path found")
                        return None

                    selected_url = f"https://image.tmdb.org/t/p/w780{file_path}"
                    vote_average = best_poster.get('vote_average', 0)
                    vote_count = best_poster.get('vote_count', 0)
                    language = best_poster.get('iso_639_1', 'Unknown')

                    print(
                        f"     ✅ Selected poster with highest rating: ⭐ {vote_average:.1f} rating ({vote_count} votes), 🌐 {language}")
                    return selected_url
                else:
                    print(f"     ℹ️  No movie posters available for this movie")
            elif response.status_code == 404:
                print(f"     ℹ️  Movie not found on TMDB")
            elif response.status_code == 401:
                print(f"     ❌ Invalid TMDB API key")
            else:
                print(f"     ⚠️  TMDB returned status {response.status_code}")

        except requests.exceptions.ConnectionError as e:
            if "Failed to resolve" in str(e) or "Name or service not known" in str(e):
                print(f"     ❌ Cannot connect to TMDB (DNS resolution failed)")
                print(f"     ℹ️  Check your internet connection or try again later")
                return False  # Signal connection error
            else:
                print(f"     ❌ Connection error: {e}")
                return False  # Signal connection error

        except requests.exceptions.Timeout:
            print(f"     ❌ Request timeout")
            return False  # Signal connection error

        except Exception as req_error:
            print(f"     ❌ Request failed: {req_error}")
            return False  # Signal connection error

        print(f"     ❌ No TMDB poster found")
        return None

    except Exception as e:
        print(f"     ❌ TMDB lookup failed: {e}")
        return None


def get_fanart_cover(movie_title, year, imdb_id=None, tmdb_id=None):
    """Get movie poster from fanart.tv - prioritizes posters in movie language or English with most votes"""
    fanart_api_key = os.getenv('FANART_API_KEY')

    if not fanart_api_key:
        print(f"     ⚠️  FANART_API_KEY not set - skipping fanart lookup")
        return None

    try:
        # Get movie details to determine language preference
        movie_details = get_movie_details_from_tmdb(tmdb_id, imdb_id)

        if movie_details:
            tmdb_id = movie_details['tmdb_id']
            preferred_lang = determine_poster_language(movie_details)
        else:
            preferred_lang = os.getenv('MOVIE_LANGUAGE', 'en')

        # Try with TMDB ID first if available
        if tmdb_id:
            url = f"https://webservice.fanart.tv/v3/movies/{tmdb_id}"
            headers = {"api-key": fanart_api_key}

            print(f"     🔍 Searching fanart.tv with TMDB ID: {tmdb_id}")

            try:
                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code == 200:
                    data = response.json()

                    # Look for movie posters
                    if 'movieposter' in data and data['movieposter']:
                        posters = data['movieposter']

                        # Filter posters by preferred language first, then English as fallback
                        preferred_posters = [p for p in posters if p.get('lang', '') == preferred_lang]
                        if not preferred_posters and preferred_lang != 'en':
                            print(f"     🔍 No {preferred_lang} posters found, trying English...")
                            preferred_posters = [p for p in posters if p.get('lang', '') == 'en']
                        if not preferred_posters:
                            print(f"     🔍 No English posters found, using all available posters...")
                            preferred_posters = posters

                        # Sort by likes (votes) descending - most voted first
                        sorted_posters = sorted(preferred_posters, key=lambda x: int(x.get('likes', 0)), reverse=True)

                        best_poster = sorted_posters[0]
                        selected_url = best_poster['url']
                        likes = best_poster.get('likes', 0)
                        language = best_poster.get('lang', 'Unknown')

                        print(f"     ✅ Selected poster with most votes: 👍 {likes} likes, 🌐 {language}")
                        return selected_url
                    else:
                        print(f"     ℹ️  No movie posters available for this movie")
                elif response.status_code == 404:
                    print(f"     ℹ️  Movie not found on fanart.tv")
                elif response.status_code == 401:
                    print(f"     ❌ Invalid fanart.tv API key")
                else:
                    print(f"     ⚠️  Fanart.tv returned status {response.status_code}")

            except requests.exceptions.ConnectionError as e:
                if "Failed to resolve" in str(e) or "Name or service not known" in str(e):
                    print(f"     ❌ Cannot connect to fanart.tv (DNS resolution failed)")
                    print(f"     ℹ️  Check your internet connection or try again later")
                    return False  # Signal connection error
                else:
                    print(f"     ❌ Connection error: {e}")
                    return False  # Signal connection error

            except requests.exceptions.Timeout:
                print(f"     ❌ Request timeout")
                return False  # Signal connection error

            except Exception as req_error:
                print(f"     ❌ Request failed: {req_error}")
                return False  # Signal connection error

        # Try with IMDB ID if TMDB didn't work
        if imdb_id:
            # Convert IMDB ID to TMDB ID using TMDB API
            tmdb_api_key = os.getenv('TMDB_API_KEY')
            if tmdb_api_key and imdb_id.startswith('tt'):
                print(f"     🔍 Converting IMDB ID {imdb_id} to TMDB ID")
                try:
                    tmdb_url = f"https://api.themoviedb.org/3/find/{imdb_id}"
                    tmdb_params = {"api_key": tmdb_api_key, "external_source": "imdb_id"}

                    tmdb_response = requests.get(tmdb_url, params=tmdb_params, timeout=10)
                    if tmdb_response.status_code == 200:
                        tmdb_data = tmdb_response.json()
                        if tmdb_data.get('movie_results'):
                            tmdb_id = tmdb_data['movie_results'][0]['id']
                            return get_fanart_cover(movie_title, year, tmdb_id=tmdb_id)
                except Exception as tmdb_error:
                    print(f"     ⚠️  TMDB lookup failed: {tmdb_error}")

        print(f"     ❌ No fanart poster found")
        return None

    except Exception as e:
        print(f"     ❌ Fanart lookup failed: {e}")
        return None


def set_plex_poster(movie, poster_url, source="fanart.tv"):
    """Set poster for Plex movie"""
    try:
        print(f"     🖼️  Setting poster from {source}")
        movie.uploadPoster(url=poster_url)
        print(f"     ✅ Poster set successfully")
        return True
    except Exception as e:
        print(f"     ❌ Failed to set poster: {e}")
        return False


def add_fanart_label(movie):
    """Add 'Fanart' label and remove 'Overlay' label if present"""
    try:
        movie.addLabel('FanPlex')
        print(f"     🏷️  Added 'FanPlex' label")

        current_labels = [label.tag for label in movie.labels] if hasattr(movie, 'labels') and movie.labels else []
        if 'Overlay' in current_labels:
            movie.removeLabel('Overlay')
            print(f"     🗑️  Removed 'Overlay' label")

        return True
    except Exception as e:
        print(f"     ❌ Failed to update labels: {e}")
        return False


def find_movies_without_fanart(plex):
    """Find all movies that don't have the 'FanPlex' label and process them"""
    try:
        movie_libraries = [lib for lib in plex.library.sections() if lib.type == 'movie']

        if not movie_libraries:
            print("No movie libraries found on this Plex server")
            return []

        processed_movies = []

        for library in movie_libraries:
            print(f"\nScanning library: {library.title}")

            ignore_overlay = os.getenv('IGNORE_OVERLAY_TAGGED', 'false').lower() == 'true'

            try:
                if ignore_overlay:
                    movies = library.search(sort='addedAt:desc', **{'label!': ['FanPlex', 'Overlay']})
                    print(f"Found {len(movies)} movies without 'Fanart' or 'Overlay' labels (direct filter)")
                else:
                    movies = library.search(sort='addedAt:desc', **{'label!': 'FanPlex'})
                    print(f"Found {len(movies)} movies without 'Fanart' label (direct filter)")

            except Exception as filter_error:
                print(f"Direct filtering failed: {filter_error}")
                print("Falling back to checking all movies...")

                all_movies = library.search(sort='addedAt:desc')
                movies = []

                for movie in all_movies:
                    labels = []
                    if hasattr(movie, 'labels') and movie.labels:
                        labels = [label.tag for label in movie.labels]

                    if ignore_overlay:
                        if 'FanPlex' not in labels and 'Overlay' not in labels:
                            movies.append(movie)
                    else:
                        if 'FanPlex' not in labels:
                            movies.append(movie)

                if ignore_overlay:
                    print(f"Found {len(movies)} movies without 'FanPlex' or 'Overlay' labels (manual filter)")
                else:
                    print(f"Found {len(movies)} movies without 'FanPlex' label (manual filter)")

            print("-" * 50)

            for i, movie in enumerate(movies, 1):
                year = movie.year if hasattr(movie, 'year') and movie.year else None

                added_date = 'Unknown'
                if hasattr(movie, 'addedAt') and movie.addedAt:
                    added_date = movie.addedAt.strftime('%Y-%m-%d %H:%M')

                labels = []
                if hasattr(movie, 'labels') and movie.labels:
                    labels = [label.tag for label in movie.labels]

                imdb_id = None
                tmdb_id = None
                if hasattr(movie, 'guids') and movie.guids:
                    for guid in movie.guids:
                        if guid.id.startswith('imdb://'):
                            imdb_id = guid.id.replace('imdb://', '')
                        elif guid.id.startswith('tmdb://'):
                            tmdb_id = guid.id.replace('tmdb://', '')

                print(f"{i:3d}. {movie.title} ({year})")
                print(f"     Added: {added_date}")
                if labels:
                    print(f"     Labels: {', '.join(labels)}")
                else:
                    print(f"     Labels: None")

                success = True
                poster_set = False

                print(f"     🎨 Processing artwork...")
                prefer_tmdb = os.getenv('PREFER_TMDB', 'false').lower() == 'true'

                if prefer_tmdb:
                    poster_url = get_tmdb_cover(movie.title, year, imdb_id, tmdb_id)
                else:
                    poster_url = get_fanart_cover(movie.title, year, imdb_id, tmdb_id)

                if poster_url:
                    poster_source = "TMDB" if prefer_tmdb else "fanart.tv"
                    poster_set = set_plex_poster(movie, poster_url, poster_source)
                    if not poster_set:
                        success = False
                elif poster_url is False:
                    print(f"     🛑 Stopping processing due to connection error")
                    print(f"Processed {i} movies before connection error")
                    return processed_movies
                else:
                    source_name = "TMDB" if prefer_tmdb else "fanart.tv"
                    print(f"     ⚠️  No {source_name} poster available")

                fanart_label_added = add_fanart_label(movie)
                if not fanart_label_added:
                    success = False

                if success:
                    status = "✅ PROCESSED"
                else:
                    status = "❌ FAILED"

                print(f"     {status}")

                processed_movies.append({
                    'title': movie.title,
                    'year': year,
                    'library': library.title,
                    'labels': labels,
                    'added_date': added_date,
                    'success': success,
                    'poster_set': poster_set
                })

                print()

                time.sleep(1)

        return processed_movies

    except Exception as e:
        print(f"ERROR: Could not retrieve movies: {e}")
        return []


def print_movies(movies):
    """Print the summary of processed movies"""
    if not movies:
        print("\nNo movies found without 'FanPlex' label")
        return

    successful = [m for m in movies if m['success']]
    failed = [m for m in movies if not m['success']]
    with_fanart = [m for m in movies if m.get('poster_set', False)]

    print(f"\n{'=' * 80}")
    print(f"SUMMARY: {len(movies)} movies processed")
    print(f"✅ Successful: {len(successful)}")
    print(f"🎨 Fanart set: {len(with_fanart)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"{'=' * 80}")

    if successful:
        print(f"\n✅ SUCCESSFULLY PROCESSED ({len(successful)} movies):")
        for i, movie in enumerate(successful, 1):
            fanart_status = " 🎨" if movie.get('poster_set', False) else ""
            print(f"{i:3d}. {movie['title']} ({movie['year']}) - Added: {movie['added_date']}{fanart_status}")

    if failed:
        print(f"\n❌ FAILED TO PROCESS ({len(failed)} movies):")
        for i, movie in enumerate(failed, 1):
            print(f"{i:3d}. {movie['title']} ({movie['year']}) - Added: {movie['added_date']}")

    print(f"{'=' * 80}")


def main():
    """Main function"""
    print("Plex Movie Finder - Movies without 'FanPlex' label + Fanart Processing")
    print("=" * 70)

    plex = get_plex_connection()

    ignore_overlay = os.getenv('IGNORE_OVERLAY_TAGGED', 'false').lower() == 'true'
    prefer_tmdb = os.getenv('PREFER_TMDB', 'false').lower() == 'true'
    original_lang_countries = os.getenv('ORIGINAL_LANGUAGE_COUNTRIES', '')

    poster_source = "TMDB" if prefer_tmdb else "fanart.tv"
    print(f"🎨 Artwork processing: ENABLED (using {poster_source})")

    if prefer_tmdb:
        tmdb_key = os.getenv('TMDB_API_KEY')
        print(f"🔑 TMDB API key: {'✅ Set' if tmdb_key else '❌ Missing'}")
    else:
        fanart_key = os.getenv('FANART_API_KEY')
        tmdb_key = os.getenv('TMDB_API_KEY')
        print(f"🔑 Fanart.tv API key: {'✅ Set' if fanart_key else '❌ Missing'}")
        print(f"🔑 TMDB API key: {'✅ Set' if tmdb_key else '⚠️  Missing (needed for country detection)'}")

    if original_lang_countries:
        print(f"🌍 Original language countries: {original_lang_countries}")
    else:
        print(f"🌍 Original language countries: Not configured (all movies use MOVIE_LANGUAGE)")

    if ignore_overlay:
        print("🏷️  Ignoring both 'FanPlex' and 'Overlay' labels")
    else:
        print("🏷️  Ignoring only 'FanPlex' label")

    print()

    movies = find_movies_without_fanart(plex)
    print_movies(movies)

    successful = len([m for m in movies if m['success']])
    print(f"\nProcessing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total processed: {successful}/{len(movies)} movies")


def run_scheduled():
    """Wrapper function for scheduled runs"""
    print(f"\n{'=' * 60}")
    print(f"Scheduled run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}")
    main()
    print(f"{'=' * 60}")
    print(f"Scheduled run completed. Next run tomorrow at {os.getenv('RUN_TIME', '09:00')}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    run_mode = os.getenv('RUN_MODE', 'RUN').upper()
    run_time = os.getenv('RUN_TIME', '09:00')

    if run_mode == 'RUN':
        print("Mode: RUN (execute once and exit)")
        main()
        sys.exit(0)
    elif run_mode == 'TIME':
        print(f"Mode: TIME (run daily at {run_time})")
        print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            datetime.strptime(run_time, '%H:%M')
        except ValueError:
            print(f"ERROR: Invalid time format '{run_time}'. Use HH:MM format (e.g., 09:30)")
            sys.exit(1)

        schedule.every().day.at(run_time).do(run_scheduled)
        print(f"Scheduled to run daily at {run_time}")

        if os.getenv('RUN_ON_STARTUP', 'false').lower() == 'true':
            print("Running initial scan...")
            run_scheduled()

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nScheduler stopped by user")
            sys.exit(0)
    else:
        print(f"ERROR: Invalid RUN_MODE '{run_mode}'. Use 'RUN' or 'TIME'")
        sys.exit(1)