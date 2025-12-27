# app/handlers/__init__.py
from .start import register_start_handlers
from .generate import register_generate_handlers

__all__ = ['register_start_handlers', 'register_generate_handlers']
