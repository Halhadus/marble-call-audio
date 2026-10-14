PYTHON ?= python3
DESTDIR ?=
PROFILE = profiles/marble/voice.json
FIRMWARE = firmware/qcom/marble-voice-active.bin
UCM = ucm2/Qualcomm/sm8450/xiaomi-marble

.PHONY: all check install
all: $(FIRMWARE)

$(FIRMWARE): $(PROFILE) tools/build-profile.py
	$(PYTHON) tools/build-profile.py $(PROFILE) $@

check:
	$(PYTHON) tools/build-profile.py --check $(PROFILE) $(FIRMWARE)

install: all
	install -D -m 0644 $(FIRMWARE) $(DESTDIR)/lib/firmware/qcom/marble-voice-active.bin
	install -D -m 0644 $(UCM)/HiFi.conf $(DESTDIR)/usr/share/alsa/$(UCM)/HiFi.conf
	install -D -m 0644 $(UCM)/VoiceCall.conf $(DESTDIR)/usr/share/alsa/$(UCM)/VoiceCall.conf
	install -D -m 0644 ucm2/conf.d/sm8450/SM8475-Xiaomi-Marble.conf $(DESTDIR)/usr/share/alsa/ucm2/conf.d/sm8450/SM8475-Xiaomi-Marble.conf
