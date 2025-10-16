import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.media import MediaMetadata


def parse_relative_time(relative_time: str) -> Tuple[datetime, datetime]:
    relative_time = relative_time.lower().strip()
    now = datetime.now(timezone.utc)
    start = now

    # Pattern for "X unit(s) ago" format
    ago_pattern = r"(\d+)\s*(second|minute|hour|day|week|month|year)s?\s+ago"
    match = re.match(ago_pattern, relative_time)

    if match:
        value = int(match.group(1))
        unit = match.group(2)

        if unit == "second":
            start = now - timedelta(seconds=value)
        elif unit == "minute":
            start = now - timedelta(minutes=value)
        elif unit == "hour":
            start = now - timedelta(hours=value)
        elif unit == "day":
            start = now - timedelta(days=value)
        elif unit == "week":
            start = now - timedelta(weeks=value)
        elif unit == "month":
            start = now - timedelta(days=value * 30)  # Approximate
        elif unit == "year":
            start = now - timedelta(days=value * 365)  # Approximate

        return start, now

    # Handle special keywords
    if relative_time == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    elif relative_time == "yesterday":
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    elif relative_time == "last week":
        days_since_monday = now.weekday()
        this_monday = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        last_monday = this_monday - timedelta(weeks=1)
        last_sunday = last_monday + timedelta(
            days=6, hours=23, minutes=59, seconds=59, microseconds=999999
        )
        return last_monday, last_sunday

    elif relative_time == "this week":
        days_since_monday = now.weekday()
        start = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return start, now

    elif relative_time == "last month":
        first_of_this_month = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        last_month_end = first_of_this_month - timedelta(microseconds=1)
        last_month_start = last_month_end.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        return last_month_start, last_month_end

    elif relative_time == "this month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now

    elif relative_time == "last year":
        start = now.replace(
            year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        end = now.replace(
            year=now.year - 1,
            month=12,
            day=31,
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )
        return start, end

    elif relative_time == "this year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now

    # Default to last 24 hours if not recognized
    logging.warning(
        f"Unrecognized time expression '{relative_time}', defaulting to last 24 hours"
    )
    start = now - timedelta(days=1)
    return start, now


def parse_time_range(time_range: str, date: datetime) -> Tuple[datetime, datetime]:
    time_range = time_range.lower().strip()

    if time_range == "morning":
        start = date.replace(hour=6, minute=0, second=0, microsecond=0)
        end = date.replace(hour=11, minute=59, second=59, microsecond=999999)
    elif time_range == "afternoon":
        start = date.replace(hour=12, minute=0, second=0, microsecond=0)
        end = date.replace(hour=17, minute=59, second=59, microsecond=999999)
    elif time_range == "evening":
        start = date.replace(hour=18, minute=0, second=0, microsecond=0)
        end = date.replace(hour=21, minute=59, second=59, microsecond=999999)
    elif time_range == "night":
        start = date.replace(hour=22, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        # Default to full day
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

    return start, end


def filter_media_by_date_time(
    db: Session,
    user_id: UUID,
    relative_time: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    time_range: Optional[str] = None,
) -> List[MediaMetadata]:
    try:
        query = db.query(MediaMetadata)
        from app.models.media import Media

        query = query.join(Media, MediaMetadata.media_id == Media.id).filter(
            Media.user_id == user_id
        )

        if relative_time:
            start_dt, end_dt = parse_relative_time(relative_time)

            if time_range:
                start_dt, _ = parse_time_range(time_range, start_dt)
                _, end_dt = parse_time_range(time_range, end_dt)

            query = query.filter(
                and_(
                    MediaMetadata.created_at >= start_dt,
                    MediaMetadata.created_at <= end_dt,
                )
            )

        elif start_date or end_date:
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                if time_range:
                    start_dt, _ = parse_time_range(time_range, start_dt)
                query = query.filter(MediaMetadata.created_at >= start_dt)

            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                if time_range:
                    _, end_dt = parse_time_range(time_range, end_dt)
                else:
                    end_dt = end_dt.replace(
                        hour=23, minute=59, second=59, microsecond=999999
                    )
                query = query.filter(MediaMetadata.created_at <= end_dt)

        # Handle time range only (defaults to today)
        elif time_range:
            today = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start_dt, end_dt = parse_time_range(time_range, today)
            query = query.filter(
                and_(
                    MediaMetadata.created_at >= start_dt,
                    MediaMetadata.created_at <= end_dt,
                )
            )

        results = query.order_by(MediaMetadata.created_at.desc()).all()
        logging.info(f"Temporal filter found {len(results)} media items")
        return results

    except Exception as e:
        logging.error(f"Error in temporal filtering: {e}")
        return []


def get_media_in_date_range(
    db: Session,
    user_id: UUID,
    days_ago: int = 3,
) -> List[MediaMetadata]:
    relative_time = f"{days_ago} days ago" if days_ago > 0 else "today"

    return filter_media_by_date_time(
        db=db,
        relative_time=relative_time,
        user_id=user_id,
    )
