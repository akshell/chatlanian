#!/usr/bin/env python

# (c) 2010 by Anton Korenyushkin

from django.core.management import execute_manager
import settings


if __name__ == '__main__':
    execute_manager(settings)
