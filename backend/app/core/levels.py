"""Fleng levels: A0 is introductory, not an official CEFR band."""

from typing import Literal, get_args

LearningLevel = Literal["A0", "A1", "A2", "B1", "B2", "C1", "C2"]
LEARNING_LEVELS = get_args(LearningLevel)
