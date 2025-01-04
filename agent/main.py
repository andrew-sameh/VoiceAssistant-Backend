import os
import logging
import random
from typing import Annotated

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import AgentCallContext, VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero, cartesia, elevenlabs
from cinema_service import CinemaService

load_dotenv()

logger = logging.getLogger("demo")
logger.setLevel(logging.INFO)
cinema_service = CinemaService()


class AssistantFnc(llm.FunctionContext):
    """
    The class defines a set of LLM functions that the assistant can execute.
    """

    @llm.ai_callable(description="Collect and validate customer contact information")
    async def set_customer_info(
        self,
        name: Annotated[str, llm.TypeInfo(description="Customer's full name")],
        phone_number: Annotated[
            str, llm.TypeInfo(description="Customer's phone number")
        ],
    ) -> str:
        # if not cinema_service.validate_phone_number(phone_number.replace(" ", "")):
        #     return "The phone number provided is invalid. Please provide a valid US phone number, hint: it's 10 digits and starts with 1"

        self.current_reservation = getattr(self, "current_reservation", {})
        self.current_reservation.update({"name": name, "phone_number": phone_number.replace(" ", "")})
        return (
            "Thank you, {name}. I've saved your contact information. "
            "Now, could you tell me the preferred date and time for your reservation?"
        )
    
    @llm.ai_callable(description="give information about an existing reservation")
    async def check_existing_reservation(
        self,
        reservation_id: Annotated[int, llm.TypeInfo(description="The reservation Id to get information about")],
    ) -> str:
        try:
            reservation = await cinema_service.get_reservation(reservation_id)
            self.old_reservation = getattr(self, "old_reservation", {})
            self.old_reservation.update(reservation)
            return reservation
        except Exception as e:
            return f"Sorry, I couldn't find the reservation. Please provide a valid reservation ID."

    # Cancel an existing reservation
    @llm.ai_callable(description="Cancel an existing reservation")
    async def cancel_reservation(
        self,
        reservation_id: Annotated[int, llm.TypeInfo(description="The reservation Id to cancel")],
    ) -> str:
        try:
            result = await cinema_service.update_reservation(reservation_id, {"status": "cancelled"})
            return "Your reservation has been successfully canceled. We hope to see you soon!"
        except Exception as e:
            return f"Sorry, I couldn't cancel the reservation. Please try again later!"


    # Update an existing reservation
    # @llm.ai_callable(description="Update an existing reservation")
    # async def update_reservation(
    #     self,
    #     reservation_id: Annotated[int, llm.TypeInfo(description="The reservation Id to update")],
    #     movie_name: Annotated[str|None, llm.TypeInfo(description="Name of the movie the customer wants to watch")],
    #     date: Annotated[str|None, llm.TypeInfo(description="Preferred date for the reservation in YYYY-MM-DD format")],
    #     time: Annotated[str|None, llm.TypeInfo(description="Preferred time for the reservation in HH:MM format")],
    #     party_size: Annotated[int|None, llm.TypeInfo(description="Number of people attending the reservation")],
    #     include_snakes: Annotated[bool|None, llm.TypeInfo(description="Whether the reservation includes snacks package or not")],
    # ) -> str:
    #     try:
    #         result = await cinema_service.update_reservation(reservation_id, {"movie_name": movie_name, "date": date, "time": time, "party_size": party_size, "include_snakes": include_snakes})
    #         return "Your reservation has been successfully updated. Enjoy your movie!"
    #     except Exception as e:
    #         return f"Sorry, I couldn't update the reservation. Please try again later!"

    @llm.ai_callable(
        description="Collect reservation details such as movie, party size, date, and time"
    )
    async def reservation_details(
        self,
        movie_name: Annotated[
            str,
            llm.TypeInfo(description="Name of the movie the customer wants to watch"),
        ],
        date: Annotated[
            str,
            llm.TypeInfo(
                description="Preferred date for the reservation in YYYY-MM-DD format, the current year is 2025 as the customer might not mention it"
            ),
        ],
        time: Annotated[
            str,
            llm.TypeInfo(
                description="Preferred time for the reservation in HH:MM format"
            ),
        ],
        party_size: Annotated[
            int, llm.TypeInfo(description="Number of people attending the reservation")
        ],
        include_snakes: Annotated[
            bool, llm.TypeInfo(description="Whether the reservation includes snacks package or not")
        ],
    ) -> str:
        self.current_reservation = getattr(self, "current_reservation", {})
        if not self.current_reservation.get("name") or not self.current_reservation.get(
            "phone_number"
        ):
            return (
                "Before booking your reservation, I need your contact information. "
                "Could you please provide your name and phone number?"
            )
        if date and time:
            is_valid, message = cinema_service.validate_datetime(date, time)
            if not is_valid:
                return  message

        room = cinema_service.recommend_room(party_size)
        movie = await cinema_service.retrieve_movie(movie_name)
        print(f"{movie = }")
        self.current_reservation.update(
            {
                "movie_name": movie_name,
                "movie_id": movie.get("id",0),
                "movie_desc": movie.get("overview",""),
                "movie_image": movie.get("poster_path",""),
                "date": date,
                "time": time,
                "party_size": party_size,
                "include_snacks": include_snakes,
                "room": room,
            }
        )
        return (
            f"Thank you! I have noted your reservation for '{movie_name}' on {date} at {time} "
            f"for {party_size} people I recommend {room}. Shall I proceed to confirm the reservation?"
        )

    @llm.ai_callable(description="Confirm reservation details and finalize the booking")
    async def confirm_reservation(
        self,
        customer_confirmation: Annotated[
            bool,
            llm.TypeInfo(
                description="Customer's confirmation to proceed with the reservation"
            ),
        ],
    ) -> str:
        if not self.current_reservation:
            return (
                "It seems I don't have all the details yet. Please provide your name, phone number, movie, date, "
                "time, and the number of attendees to proceed with the reservation."
            )

        if not customer_confirmation:
            return "No problem! Let me know if you want to confirm the reservation or if you need to make any changes."

        # Process booking with the cinema service
        result = await cinema_service.process_reservation(self.current_reservation)

        if result.get("success"):
            confirmation_id = result["id"]
            movie = result["movie_name"]
            date = result["date"]
            time = result["time"]
            self.current_reservation = {}
            return (
                f"Your reservation is confirmed! Reservation ID: {confirmation_id}. "
                f"Enjoy watching '{movie}' on {date} at {time}. Please save your reservation ID for reference."
            )
        else:
            return (
                f"Sorry, I couldn't complete the reservation due to: {result.get('error', 'an unknown issue')}. "
                "Please try again or contact us directly for assistance."
            )


def prewarm_process(proc: JobProcess):
    # preload silero VAD in memory to speed up session start
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    fnc_ctx = AssistantFnc()  # create our fnc ctx instance
    initial_chat_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a friendly and professional voice assistant for CineLounge, located at 4456 Hollywood Boulevard, Los Angeles, CA, USA. Your interface with users will be voice. "
            "You assist customers with booking reservations and providing information about services and pricing."
            "Do not include any headers or special formatting in your responses. Keep the conversation natural and engaging like a human talking."
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
            "You can also help the customer with checking the details of his existing reservation, or canceling it, but we cant update the reservation details as of now, but it will be available soon."
            "For reservations, follow these structured steps: "
            "1. Collect the customer's contact information, including their name and phone number. "
            "2. Ask for reservation details: date, time, movie name, and the number of attendees, in this order. "
            "3. Summarize the reservation details in human non-robotic way and confirm with the customer before finalizing the booking. "
            "4. Provide a reservation ID and any necessary follow-up information upon successful confirmation. "
            "Use concise, conversational responses. Ensure clarity and politely handle invalid inputs or corrections. "
            "What We Do:"
            """At CineLounge, we specialize in offering private, luxurious cinema experiences tailored to your preferences. Whether it's a cozy movie night, or a special celebration, we provide personalized rooms, a curated movie library, and snack and drink options. Our goal is to create unforgettable moments for you and your guests.

            Working Hours:
            Daily from 9:00 AM to 11:00 PM

            Services:
            - Private room reservations with various capacities (2 to 10 people).
            - On-demand movie screenings from a curated library.
            - snack and drink packages.

            Pricing:
            - Small Room (2 up to 4 people): $100 per movie
            - Medium Room (5 up to 7 people): $150 per movie
            - Large Room (8 up to 10 people): $200 per movie
            - Snacks & Drinks: $10 per person
            """
        ),
    )
    logger.info(f"connecting to room {ctx.room.name}")
    participant = await ctx.wait_for_participant()
    stt = deepgram.STT(api_key=os.getenv("DEEPGRAM_API_KEY", ""))

    # tts = elevenlabs.TTS(api_key=os.getenv("ELEVENLABS_API_KEY", ""))
    # tts = cartesia.TTS(api_key=os.getenv('CARTESIA_API_KEY', ""))
    tts = deepgram.TTS(api_key=os.getenv("DEEPGRAM_API_KEY", ""))
    # tts = openai.TTS(api_key=os.getenv("OPENAI_API_KEY", ""),voice='nova')

    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=stt,
        # llm=openai.LLM.with_azure(
        #     azure_endpoint=os.getenv("AZURE_URL", ""),
        #     azure_deployment=os.getenv("AZURE_DEPLOYMENT", ""),
        #     api_key=os.getenv("AZURE_API_KEY", ""),
        #     api_version=os.getenv("AZURE_API_VERSION", ""),
        # ),
        llm=openai.LLM(model="gpt-4o-mini",api_key=os.getenv("OPENAI_API_KEY", "")),
        # llm=openai.LLM.with_groq(model="llama-3.1-8b-instant",api_key=os.getenv("GROQ_API_KEY", "")),
        # llm=openai.LLM.with_groq(
        #     model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY", "")
        # ),
        tts=tts,
        fnc_ctx=fnc_ctx,
        chat_ctx=initial_chat_ctx,
        max_nested_fnc_calls=2,
    )

    # Start the assistant. This will automatically publish a microphone track and listen to the participant.
    agent.start(ctx.room, participant)
    await agent.say(
        "Hi This is Emma from CineLounge! How can I help ?", allow_interruptions=True
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm_process,
        ),
    )
