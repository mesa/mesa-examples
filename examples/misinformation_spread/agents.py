import os
import litellm
from dotenv import load_dotenv
from mesa_llm.llm_agent import LLMAgent

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "ollama/llama3")
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://localhost:11434")


class BelieverAgent(LLMAgent):
    """
    Tends to trust and share information easily.
    Belief strengthens with repeated exposure to the claim.

    Note: This model uses litellm.completion() directly rather than
    ReActReasoning because ReActReasoning hardwires output to a
    reasoning: / action: format that cannot be overridden by prompt
    instructions. Direct litellm calls allow clean structured two-line
    responses (BELIEVE: yes / SHARE: yes) that can be reliably parsed.
    Decision history is managed manually via self.history to avoid the
    ghost latency caused by STLTMemory's background LLM calls when its
    short-term buffer fills up.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.believes = False
        self.shared = False
        self.times_exposed = 0
        self.history = []

    def step(self):
        self.times_exposed += 1
        prior = "yes" if self.believes else "no"

        history_text = ""
        if self.history:
            history_text = (
                "Your decision history so far:\n"
                + "\n".join(
                    f"  Step {i + 1}: believed={d['believed']}, shared={d['shared']}"
                    for i, d in enumerate(self.history)
                )
                + "\n\n"
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a social media user who tends to trust "
                    "information easily. The more times you see a claim, "
                    "the more you believe it. "
                    "You MUST respond with ONLY two lines exactly as shown. "
                    "No other text whatsoever."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"You have now seen this claim {self.times_exposed} time(s): "
                    f'"{self.model.misinformation_claim}"\n\n'
                    f"{history_text}"
                    f"Last step you believed: {prior}. "
                    f"Does repeated exposure change your mind?\n\n"
                    "Respond with ONLY these two lines:\n"
                    "BELIEVE: yes\n"
                    "SHARE: yes\n\n"
                    "or\n\n"
                    "BELIEVE: no\n"
                    "SHARE: no"
                ),
            },
        ]

        response = litellm.completion(
            model=LLM_MODEL,
            messages=messages,
            api_base=LLM_API_BASE if "ollama" in LLM_MODEL else None,
        )

        text = response.choices[0].message.content.lower()
        self._parse_decision(text)

    def _parse_decision(self, text):
        self.believes = "believe: yes" in text
        self.shared = "share: yes" in text
        self.history.append({"believed": self.believes, "shared": self.shared})
        if self.shared and self.believes:
            self.model.spread_count += 1


class SkepticAgent(LLMAgent):
    """
    Questions information before believing or sharing.
    May gradually become convinced after many exposures,
    but starts with strong resistance.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.believes = False
        self.shared = False
        self.times_exposed = 0
        self.history = []

    def step(self):
        self.times_exposed += 1
        prior = "yes" if self.believes else "no"

        history_text = ""
        if self.history:
            history_text = (
                "Your decision history so far:\n"
                + "\n".join(
                    f"  Step {i + 1}: believed={d['believed']}, shared={d['shared']}"
                    for i, d in enumerate(self.history)
                )
                + "\n\n"
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a skeptical social media user who rarely believes "
                    "claims without evidence. However, after seeing a claim "
                    "many times from many people, even skeptics can start to "
                    "wonder if there is something to it. "
                    "You MUST respond with ONLY two lines exactly as shown. "
                    "No other text whatsoever."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"You have now seen this claim {self.times_exposed} time(s): "
                    f'"{self.model.misinformation_claim}"\n\n'
                    f"{history_text}"
                    f"Last step you believed: {prior}. "
                    f"After {self.times_exposed} exposures, do you start to wonder "
                    f"if it might be true?\n\n"
                    "Respond with ONLY these two lines:\n"
                    "BELIEVE: yes\n"
                    "SHARE: yes\n\n"
                    "or\n\n"
                    "BELIEVE: no\n"
                    "SHARE: no"
                ),
            },
        ]

        response = litellm.completion(
            model=LLM_MODEL,
            messages=messages,
            api_base=LLM_API_BASE if "ollama" in LLM_MODEL else None,
        )

        text = response.choices[0].message.content.lower()
        self._parse_decision(text)

    def _parse_decision(self, text):
        self.believes = "believe: yes" in text
        self.shared = "share: yes" in text
        self.history.append({"believed": self.believes, "shared": self.shared})
        if self.shared and self.believes:
            self.model.spread_count += 1


class SpreaderAgent(LLMAgent):
    """
    Actively amplifies information regardless of truth.
    Always shares, reinforced by seeing others share too.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.believes = False
        self.shared = False
        self.times_exposed = 0
        self.history = []

    def step(self):
        self.times_exposed += 1
        prior = "yes" if self.shared else "no"

        history_text = ""
        if self.history:
            history_text = (
                "Your sharing history so far:\n"
                + "\n".join(
                    f"  Step {i + 1}: believed={d['believed']}, shared={d['shared']}"
                    for i, d in enumerate(self.history)
                )
                + "\n\n"
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a social media user who shares everything "
                    "to maximize engagement. You love viral content and "
                    "the more people are talking about something, the more "
                    "you want to share it. You almost always say yes. "
                    "You MUST respond with ONLY two lines exactly as shown. "
                    "No other text whatsoever."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"You have now seen this claim {self.times_exposed} time(s): "
                    f'"{self.model.misinformation_claim}"\n\n'
                    f"{history_text}"
                    f"Last step you shared: {prior}. "
                    f"This is going viral - {self.times_exposed} exposures already. "
                    f"Do you keep sharing?\n\n"
                    "Respond with ONLY these two lines:\n"
                    "BELIEVE: yes\n"
                    "SHARE: yes\n\n"
                    "or\n\n"
                    "BELIEVE: no\n"
                    "SHARE: no"
                ),
            },
        ]

        response = litellm.completion(
            model=LLM_MODEL,
            messages=messages,
            api_base=LLM_API_BASE if "ollama" in LLM_MODEL else None,
        )

        text = response.choices[0].message.content.lower()
        self._parse_decision(text)

    def _parse_decision(self, text):
        self.believes = "believe: yes" in text
        self.shared = "share: yes" in text
        self.history.append({"believed": self.believes, "shared": self.shared})
        if self.shared and self.believes:
            self.model.spread_count += 1
