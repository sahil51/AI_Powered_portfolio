import hashlib

import google.generativeai as genai

from decouple import config

from services.cache_service import CacheService


class LLMService:

    @staticmethod
    def generate(prompt):

        cache_key = (
            "gemini:"
            + hashlib.md5(
                prompt.encode()
            ).hexdigest()
        )

        cached_response = (
            CacheService.get(
                cache_key
            )
        )

        if cached_response:

            print(
                "CACHE HIT"
            )

            return cached_response

        print(
            "CACHE MISS"
        )

        genai.configure(
            api_key=config(
                "GEMINI_API_KEY"
            )
        )

        model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

        response = model.generate_content(
            prompt
        )

        result = response.text

        CacheService.set(
            cache_key,
            result,
            timeout=3600
        )

        return result