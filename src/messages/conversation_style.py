"""Shared style guidance for conversation prompts."""

from state.user_state_store import ReplyStyle

BRIEF_CONVERSATION_STYLE = (
    "Keep replies conversational and brief by default: one or two short "
    "sentences. Respond directly to the learner and ask at most one relevant "
    "follow-up question. Avoid lists, lectures, and unnecessary repetition. "
    "Give more detail when the learner asks for it."
)


CONVERSATION_STYLES: dict[ReplyStyle, str] = {
    "brief": BRIEF_CONVERSATION_STYLE,
    "balanced": (
        "Keep replies conversational and balanced by default: a few sentences "
        "with useful context. Respond directly to the learner and ask at most "
        "one relevant follow-up question. Avoid lectures and unnecessary "
        "repetition. Adjust the level of detail when the learner asks for it."
    ),
    "detailed": (
        "Keep replies conversational and detailed by default: one or two short "
        "paragraphs with fuller explanations and relevant examples when useful. "
        "Respond directly to the learner and ask at most one relevant follow-up "
        "question. Avoid lectures and unnecessary repetition. Adjust the level "
        "of detail when the learner asks for it."
    ),
}
