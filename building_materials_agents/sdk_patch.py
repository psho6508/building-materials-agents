"""SDK monkey-patch 공유 모듈.

claude_code_sdk가 rate_limit_event 등 알 수 없는 메시지 타입을
수신할 때 발생하는 MessageParseError를 무시하도록 패치한다.
멱등성 보장: 여러 번 호출해도 한 번만 적용된다.
"""

_applied = False


def apply_sdk_patches():
    """SDK message parser를 패치하여 알 수 없는 메시지 타입을 무시한다."""
    global _applied
    if _applied:
        return
    import claude_code_sdk._internal.message_parser as _mp
    import claude_code_sdk._internal.client as _client

    _original_parse = _mp.parse_message

    def _patched_parse(data):
        try:
            return _original_parse(data)
        except _mp.MessageParseError as e:
            if "Unknown message type" in str(e):
                return None
            raise

    _mp.parse_message = _patched_parse
    _client.parse_message = _patched_parse
    _applied = True
