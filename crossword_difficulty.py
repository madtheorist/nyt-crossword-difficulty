
import re
from datetime import date

import requests
import streamlit as st
from bs4 import BeautifulSoup


st.set_page_config(
    page_title="Get NYT Crossword Difficulty",
    layout="centered",
)


@st.cache_data(ttl=3600)
def get_stats(puzzle_date: str) -> dict:
    """Fetch the global statistics for a crossword date."""

    date.fromisoformat(puzzle_date)

    url = f"https://xwstats.com/puzzles/{puzzle_date}"

    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Isolate the Global Stats section
    match = re.search(
        r"Global Stats\s+(.*?)\s+(?:©|$)",
        text,
        re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            "Could not locate the Global Stats section. "
            "The website may have changed its layout."
        )

    stats = match.group(1)

    difficulty = re.search(
        r"Difficulty\s+(.*?)\s+Median Solve Time",
        stats,
        re.IGNORECASE,
    )

    median_time = re.search(
        r"Median Solve Time\s+([\d:]+)",
        stats,
        re.IGNORECASE,
    )

    median_solver = re.search(
        r"Median Solver\s+(.+?)"
        r"(?=\s*⚡|\s*🐢|$)",
        stats,
        re.IGNORECASE,
    )

    if not difficulty:
        raise ValueError(
            "Difficulty rating not found."
        )

    return {
        "difficulty": difficulty.group(1),
        "median_time": (
            median_time.group(1)
            if median_time else "N/A"
        ),
        "median_solver": (
            median_solver.group(1).strip()
            if median_solver else "N/A"
        ),
    }


st.title("Crossword Difficulty")
st.caption(
    "Look up NYT crossword difficulty without "
    "seeing the puzzle or its answers."
    " Difficulty is relative to the day of the week."
)

selected_date = st.date_input(
    "Select puzzle date",
    value=date.today(),
    min_value=date(2000, 1, 1),
    max_value=date.today(),
)

if st.button(
    "Fetch difficulty",
    type="primary",
    use_container_width=True,
):
    puzzle_date = selected_date.isoformat()

    with st.spinner("Fetching crossword statistics..."):
        try:
            result = get_stats(puzzle_date)

            st.session_state["result"] = {
                "date": puzzle_date,
                **result,
            }

        except requests.HTTPError as e:
            st.error(
                f"Could not retrieve that puzzle "
                f"(HTTP {e.response.status_code})."
            )

        except requests.RequestException:
            st.error(
                "Network error. Please check your "
                "connection and try again."
            )

        except ValueError as e:
            st.error(str(e))


if "result" in st.session_state:
    result = st.session_state["result"]

    st.divider()

    st.subheader(
        date.fromisoformat(result["date"]).strftime(
            "%A, %-d %B %Y"
        )
    )

    st.metric(
        "Difficulty",
        result["difficulty"],
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Median solve time",
            result["median_time"],
        )

    with col2:
        st.metric(
            "Median solver",
            result["median_solver"],
        )

    st.caption(
        "Statistics from XWStats. "
        "No puzzle clues or solutions are displayed."
    )