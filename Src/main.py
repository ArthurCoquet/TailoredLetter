import asyncio

from config.settings import get_settings
from Application.build_application import build_application
from Application.pipeline import pipeline
from Schemas.job_offer_input import JobOfferInput

async def main():

    settings = get_settings()

    application = build_application(settings)

    job_offer = JobOfferInput(
        url="",
        title="",
        content=""
    )
    
    await pipeline(application=application, job_offer=job_offer)

if __name__ == "__main__":
    asyncio.run(main())