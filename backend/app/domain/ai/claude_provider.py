import json
import logging
from typing import Optional

from app.core.config import settings
from app.domain.ai.provider import AIProvider, AINonRetryableError, AITransientError
from app.domain.ai.schemas import AIDiagnosisOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a payment recovery diagnosis assistant.
Analyze the supplied failed-payment context and identify the most likely recovery-relevant diagnosis.
CONSTRAINTS:
- Do not execute anything.
- Do not authorize anything.
- Do not invent unavailable facts.
- Do not assume an intervention is allowed.
- Do not calculate authoritative policy decisions.
- Do not calculate authoritative ERV.
- Return only the requested structured output.
- Separate diagnostic confidence from estimated recovery probability.
- State uncertainty when evidence is weak.
- Your recovery_probability output is an ADVISORY AI estimate, NOT an authoritative value.
"""

class ClaudeProvider(AIProvider):
    """Anthropic Claude provider for structured AI diagnosis.

    Does NOT instantiate the SDK at import time. Requires API key only at invocation.
    """

    def __init__(self):
        # We only import anthropic here or inside diagnose to avoid startup crashes if missing.
        try:
            import anthropic
            self.anthropic_lib = anthropic
        except ImportError:
            self.anthropic_lib = None

    async def diagnose(self, context_payload: dict) -> AIDiagnosisOutput:
        if not self.anthropic_lib:
            raise AINonRetryableError("Anthropic SDK is not installed.")

        if not settings.ANTHROPIC_API_KEY:
            raise AINonRetryableError("ANTHROPIC_API_KEY is not configured.")

        try:
            client = self.anthropic_lib.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        except Exception as e:
            raise AINonRetryableError(f"Failed to initialize Anthropic client: {e}")

        prompt = f"Context payload:\n{json.dumps(context_payload, indent=2)}\n\nProvide the diagnosis."

        try:
            # We use messages API and ask Claude to output raw JSON matching our schema.
            # No tool use or agent loops per constraints.
            response = await client.messages.create(
                model=settings.AI_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "Here is the JSON response:\n{"}
                ]
            )

            raw_text = "{" + response.content[0].text

            try:
                # Find the end of JSON if Claude appended trailing text (which it shouldn't given the prompt setup)
                # For simplicity, we assume strict JSON output for this phase
                json_data = json.loads(raw_text)
                return AIDiagnosisOutput.model_validate(json_data)
            except Exception as e:
                # Validation or JSON parse error
                logger.error(f"Claude output validation failed: {e}")
                raise AINonRetryableError("Failed to parse or validate AI output.")

        except self.anthropic_lib.RateLimitError as e:
            logger.warning(f"Anthropic rate limit: {e}")
            raise AITransientError(str(e))
        except self.anthropic_lib.APITimeoutError as e:
            logger.warning(f"Anthropic timeout: {e}")
            raise AITransientError(str(e))
        except self.anthropic_lib.APIConnectionError as e:
            logger.warning(f"Anthropic connection error: {e}")
            raise AITransientError(str(e))
        except self.anthropic_lib.APIStatusError as e:
            # e.g. 400 Bad Request, 401 Unauthorized
            logger.error(f"Anthropic API error: {e.status_code} - {e.response}")
            raise AINonRetryableError(str(e))
        except AITransientError:
            raise
        except AINonRetryableError:
            raise
        except Exception as e:
            logger.error(f"Unexpected ClaudeProvider error: {e}")
            raise AINonRetryableError("Unexpected provider failure.")
