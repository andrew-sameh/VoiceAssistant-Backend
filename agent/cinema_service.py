import os
import re
from datetime import datetime, timedelta
from typing import Dict, Optional
import aiohttp


class CinemaService:
    def __init__(self):
        self.business_hours = {
            "Monday": ("9:00", "23:00"),
            "Tuesday": ("9:00", "23:00"),
            "Wednesday": ("9:00", "23:00"),
            "Thursday": ("9:00", "23:00"),
            "Friday": ("9:00", "23:00"),
            "Saturday": ("9:00", "23:00"),
            "Sunday": ("9:00", "23:00"),
        }
        self.base_url = os.getenv("RES_BASE_URL", "http://localhost:8000")
        self.tmdb_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
        self.tmdb_api_key = os.getenv("TMDB_READ_ACCESS_KEY")

    def recommend_room(self, people_count: int) -> str:
        if people_count <= 4:
            return "Small Room"
        elif people_count <= 7:
            return "Medium Room"
        elif people_count <= 10:
            return "Large Room"
        else:
            return "I'm sorry, we don't have a room for that many people, our largest room can accommodate 10 people."

    def validate_phone_number(self, phone: str) -> bool:
        us_phone_pattern = r"^(?:\+1\s?)?(?:\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}$"
        return bool(re.match(us_phone_pattern, phone))

    def validate_datetime(self, date_str: str, time_str: str) -> tuple[bool, str]:
        try:
            # Parse the date and time
            booking_datetime = datetime.strptime(
                f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
            )

            # Check if it's in the past
            if booking_datetime < datetime.now():
                return False, "Cannot book appointments in the past"

            # Get day of week
            day_of_week = booking_datetime.strftime("%A")

            # Check if within business hours
            if day_of_week in self.business_hours:
                open_time = datetime.strptime(
                    self.business_hours[day_of_week][0], "%H:%M"
                ).time()
                close_time = datetime.strptime(
                    self.business_hours[day_of_week][1], "%H:%M"
                ).time()
                booking_time = booking_datetime.time()

                if not (open_time <= booking_time <= close_time):
                    return False, f"We're not open at {time_str} on {day_of_week}s"

            return True, "Valid date and time"
        except ValueError:
            return False, "Invalid date or time format"

    async def process_reservation(self, reservation_data: Dict) -> Dict:
        # Validate phone number
        # if not self.validate_phone_number(reservation_data.get('phone', '')):
        #     return {
        #         'success': False,
        #         'error': 'Invalid US phone number format'
        #     }

        # Validate date and time if provided
        date_str = reservation_data.get("date")
        time_str = reservation_data.get("time")
        booking_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        reservation_obj = {
            "name": reservation_data.get("name"),
            "number": reservation_data.get("phone_number"),
            "people_count": reservation_data.get("party_size"),
            "date": booking_datetime.date().isoformat(),
            "time": booking_datetime.time().isoformat(),
            "room": reservation_data.get("room"),
            "movie_id": reservation_data.get("movie_id"),
            "movie_name": reservation_data.get("movie_name"),
            "movie_desc": reservation_data.get("movie_desc"),
            "movie_image": f"https://image.tmdb.org/t/p/original{reservation_data.get('movie_image')}",
            "snack_package": reservation_data.get("include_snacks", False),
            "status": "confirmed",
        }
        print(f"{reservation_obj = }")

        # Create reservation
        booking = await self.create_reservation(reservation_obj)
        print(f"{booking = }")

        # self.bookings.append(booking)

        return {"success": True, **booking}

    async def get_reservation(self, reservation_id: int):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/reservations/{reservation_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get reservation: {response.status}")

    async def create_reservation(self, reservation_data: dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/reservations", json=reservation_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to create reservation: {response.status}")

    async def update_reservation(self, reservation_id: int, reservation_data: dict):
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{self.base_url}/reservations/{reservation_id}", json=reservation_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to update reservation: {response.status}")

    async def retrieve_movie(self, query: str) -> Optional[Dict]:
        async with aiohttp.ClientSession() as session:

            async with session.get(
                f"{self.tmdb_url}/search/movie",
                headers={
                    "Authorization": f"Bearer {self.tmdb_api_key}",
                    "accept": "application/json",
                },
                params={
                    "query": query,
                    "include_adult": "false",
                    "language": "en-US",
                    "page": 1,
                },
            ) as response:
                if response.status == 200:
                    try:
                        movie = await response.json()
                        return movie['results'][0]
                    except IndexError:
                        raise Exception("No movie found")
                else:
                    raise Exception(f"Failed to update reservation: {response.status}")
