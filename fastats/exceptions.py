#!/usr/bin/env python3
# coding=utf-8

class ParsingException(Exception):
    pass


class AuthenticationError(ParsingException):
    pass
