# Flashcards Study App

A lightweight web application built with Django to help users study using flashcards, inspired by Anki.

## Overview

This project was developed as a minimal viable product (MVP) focused on simplicity, usability, and effective learning. It allows users to create flashcards, organize them into categories, and study them through an interactive workflow.

## Features

- Create and manage flashcards (question & answer)
- Organize flashcards into categories
- Study mode with:
  - Answer input
  - Answer comparison (user vs correct answer)
  - Self-assessment (correct / incorrect)
- Basic learning analytics:
  - Tracks attempts and outcomes
  - Prioritizes cards with more mistakes
- Simple and clean user interface (HTMX-based interactions)

## Tech Stack

- Django (backend & templating)
- PostgreSQL (database)
- HTMX (dynamic UI interactions)
- Gunicorn (production server)

## Purpose

The goal of this app is to provide a focused and distraction-free study experience, while introducing a simple adaptive review mechanism to reinforce learning.

## Status

MVP completed. Future improvements may include:
- Advanced spaced repetition algorithm
- User authentication (multi-user support)
- Enhanced dashboard and analytics

## How to Run

Instructions may vary depending on deployment setup. Typically:

```bash
python manage.py migrate
python manage.py runserver
