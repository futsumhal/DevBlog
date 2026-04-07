#!/usr/bin/env bash
gunicorn "app:create_app()"
