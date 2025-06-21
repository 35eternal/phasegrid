class DummyNotifier:
    def sms(self, **_):
        # placeholder: always succeed
        return True

notifier = DummyNotifier()
