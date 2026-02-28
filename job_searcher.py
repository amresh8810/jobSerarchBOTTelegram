"""
🔍 Job Searcher Module
Uses JSearch API (RapidAPI) to search jobs from:
  → LinkedIn, Indeed, Glassdoor, ZipRecruiter, etc.
"""

import httpx
import asyncio
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

JSEARCH_BASE_URL = "https://jsearch.p.rapidapi.com"


class JobSearcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }

    async def search_jobs(self, query: str, num_results: int = 8) -> list[dict]:
        """
        Search for jobs using JSearch API.
        
        Args:
            query: Job search query (e.g., "Python Developer Mumbai")
            num_results: Number of results to fetch
            
        Returns:
            List of job dictionaries with title, company, location, salary, description
        """
        # Enhance query for Indian market
        enhanced_query = self._enhance_query(query)
        
        params = {
            "query": enhanced_query,
            "page": "1",
            "num_pages": "1",
            "date_posted": "all",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    f"{JSEARCH_BASE_URL}/search",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException:
            logger.error("JSearch API timeout")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"JSearch API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"JSearch API error: {e}")
            return []

        if data.get("status") != "OK":
            logger.error(f"JSearch API status not OK: {data.get('status')}")
            return []

        raw_jobs = data.get("data", [])
        if not raw_jobs:
            return []

        parsed_jobs = []
        for job in raw_jobs[:num_results]:
            parsed = self._parse_job(job)
            if parsed:
                parsed_jobs.append(parsed)

        return parsed_jobs

    def _enhance_query(self, query: str) -> str:
        """Enhance search query for better results."""
        query = query.strip()
        
        # Add "India" if no location mentioned and query is short
        location_keywords = [
            "mumbai", "delhi", "bangalore", "bengaluru", "pune", "hyderabad",
            "chennai", "kolkata", "ahmedabad", "india", "remote", "us", "uk",
            "noida", "gurgaon", "gurugram", "jaipur", "lucknow", "indore"
        ]
        
        query_lower = query.lower()
        has_location = any(loc in query_lower for loc in location_keywords)
        
        if not has_location and len(query.split()) <= 3:
            query = f"{query} India"
        
        return query

    def _parse_job(self, raw: dict) -> Optional[dict]:
        """Parse raw API response into clean job dict."""
        try:
            title = raw.get("job_title", "").strip()
            if not title:
                return None

            company = raw.get("employer_name", "N/A").strip()
            
            # Build location
            city = raw.get("job_city", "")
            state = raw.get("job_state", "")
            country = raw.get("job_country", "")
            is_remote = raw.get("job_is_remote", False)

            if is_remote:
                location = "🏠 Remote"
                if country:
                    location += f" ({country})"
            else:
                parts = [p for p in [city, state, country] if p]
                location = ", ".join(parts) if parts else "N/A"

            # Salary parsing
            salary = self._parse_salary(raw)

            # Description
            description = raw.get("job_description", "")
            description = self._clean_description(description)

            # Job type
            employment_type = raw.get("job_employment_type", "")
            job_type_map = {
                "FULLTIME": "Full-time",
                "PARTTIME": "Part-time",
                "CONTRACTOR": "Contract",
                "INTERN": "Internship",
                "TEMPORARY": "Temporary"
            }
            job_type = job_type_map.get(employment_type, employment_type or "Full-time")

            # Apply URL
            apply_url = (
                raw.get("job_apply_link") or
                raw.get("job_google_link") or
                ""
            )

            # Company URL / logo
            company_url = raw.get("employer_website", "") or ""
            if company_url and not company_url.startswith("http"):
                company_url = f"https://{company_url}"

            # Rating
            rating = raw.get("employer_company_type", "")

            # Posted date
            posted_at = raw.get("job_posted_at_datetime_utc", "")
            posted = self._format_posted_date(posted_at)

            # Required skills
            skills = raw.get("job_required_skills", []) or []
            skills_str = ", ".join(skills[:5]) if skills else ""

            # Experience
            experience = raw.get("job_required_experience", {})
            exp_years = experience.get("required_experience_in_months", 0)
            if exp_years:
                exp_str = f"{exp_years // 12}+ years" if exp_years >= 12 else f"{exp_years} months"
            else:
                exp_str = ""

            return {
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "description": description,
                "job_type": job_type,
                "apply_url": apply_url,
                "company_url": company_url,
                "rating": rating,
                "posted": posted,
                "skills": skills_str,
                "experience": exp_str,
                "is_remote": is_remote,
                "source": self._get_source(raw),
            }

        except Exception as e:
            logger.warning(f"Failed to parse job: {e}")
            return None

    def _parse_salary(self, raw: dict) -> str:
        """Extract and format salary information."""
        # Try min/max salary fields
        min_salary = raw.get("job_min_salary")
        max_salary = raw.get("job_max_salary")
        salary_currency = raw.get("job_salary_currency", "INR")
        salary_period = raw.get("job_salary_period", "")

        period_map = {
            "YEAR": "/year",
            "MONTH": "/month",
            "HOUR": "/hour",
            "DAY": "/day",
        }
        period_str = period_map.get(salary_period, "/year") if salary_period else ""

        currency_symbols = {
            "INR": "₹",
            "USD": "$",
            "GBP": "£",
            "EUR": "€",
        }
        symbol = currency_symbols.get(salary_currency, salary_currency)

        if min_salary and max_salary:
            min_f = self._format_number(min_salary, salary_currency)
            max_f = self._format_number(max_salary, salary_currency)
            return f"{symbol}{min_f} - {symbol}{max_f}{period_str}"
        elif min_salary:
            return f"{symbol}{self._format_number(min_salary, salary_currency)}+{period_str}"
        elif max_salary:
            return f"Up to {symbol}{self._format_number(max_salary, salary_currency)}{period_str}"

        # Try parsing from highlights
        highlights = raw.get("job_highlights", {})
        for section in highlights.values():
            for item in (section or []):
                if any(kw in item.lower() for kw in ["salary", "lakh", "₹", "$", "ctc", "per month", "annum"]):
                    return item.strip()

        return "Not mentioned"

    def _format_number(self, num: float, currency: str) -> str:
        """Format number with Indian/international notation."""
        if currency == "INR":
            # Convert to Lakhs for INR
            if num >= 100000:
                return f"{num/100000:.1f}L"
            elif num >= 1000:
                return f"{num/1000:.0f}K"
            else:
                return f"{num:.0f}"
        else:
            if num >= 1000000:
                return f"{num/1000000:.1f}M"
            elif num >= 1000:
                return f"{num/1000:.0f}K"
            else:
                return f"{num:.0f}"

    def _clean_description(self, text: str) -> str:
        """Clean and truncate job description."""
        if not text:
            return "Description not available"

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Remove special characters that break Markdown
        text = text.replace("*", "").replace("`", "").replace("_", " ")

        # Get first meaningful paragraph (max 400 chars)
        sentences = text.split(". ")
        result = ""
        for s in sentences:
            if len(result) + len(s) > 400:
                break
            result += s + ". "

        return result.strip() or text[:400]

    def _format_posted_date(self, date_str: str) -> str:
        """Format posted date to human readable."""
        if not date_str:
            return ""
        try:
            from datetime import datetime, timezone
            posted = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            diff = now - posted
            days = diff.days
            if days == 0:
                return "Aaj posted"
            elif days == 1:
                return "Kal posted"
            elif days <= 7:
                return f"{days} din pehle"
            elif days <= 30:
                return f"{days // 7} hafte pehle"
            else:
                return f"{days // 30} mahine pehle"
        except Exception:
            return ""

    def _get_source(self, raw: dict) -> str:
        """Get job source platform."""
        publisher = raw.get("job_publisher", "")
        if publisher:
            return publisher
        apply_link = raw.get("job_apply_link", "")
        if "linkedin" in apply_link:
            return "LinkedIn"
        elif "indeed" in apply_link:
            return "Indeed"
        elif "glassdoor" in apply_link:
            return "Glassdoor"
        elif "naukri" in apply_link:
            return "Naukri"
        return "Job Portal"
