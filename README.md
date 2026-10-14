# Marble call audio

Hostless AudioReach handset calls for Xiaomi Poco F5 / Redmi Note 12 Turbo
(`marble`). Includes kernel patches, the firmware profile and its builder,
and ALSA UCM configuration.

The handset path uses the top amplifier in Receiver mode and the primary
microphone. Music and Receiver retain separate hardware volume settings.
The UCM configuration uses the existing audio server and callaudiod.

## Kernel

Base: [linux-marble](https://github.com/iLtanaka/linux-marble),
commit `c9f87aac17d306786d1d15f67d8bdd226770e27a`.

From that kernel checkout, using the board's build configuration:

```sh
PATCH_DIR=/path/to/marble-call-audio/patches/kernel
git am "$PATCH_DIR"/*.patch
make ARCH=arm64 LLVM=1 olddefconfig
make ARCH=arm64 LLVM=1 -j"$(nproc)" Image modules dtbs
```

Deploy the kernel, modules and Marble DTB from the same build.
The machine driver selects
`CONFIG_SND_VMASTER`; the amplifier needs `CONFIG_SND_SOC_AW88261`.

## Firmware and UCM

The profile targets `ADSP.HT.5.7-01183-WAIPIO-1` and VSID `0x11c05000`.
The builder requires Python 3.9 or later.

```sh
make
make install DESTDIR="$PWD/stage"
```

Install the staged `lib/firmware/qcom/marble-voice-active.bin` and
`usr/share/alsa/ucm2/` files on the target with the patched kernel.
The UCM files are also available directly under `ucm2/`.

See [profile format](docs/profile-format.md) for the binary layout and
[reverse engineering](docs/reverse-engineering.md) for its derivation.

## Runtime

UCM exports `HiFi` and `Voice Call`. Enabling the call microphone requests
startup; disabling it stops both DSP graphs before releasing the physical
routes. `Voice Call UCM Switch` reports the request; `Voice Call Switch`
reports the active session. Startup failures are reported in the kernel log.

PCM 13 is a policy endpoint: playback is discarded and capture is silence.
Modem samples stay inside the DSP. Microphone mute and Receiver volume use
hardware controls through UCM.

Calls support Earpiece and the primary Mic. Primary microphone samples feed
both DEC1 and DEC3 for the two-channel DSP configuration. Speakerphone and
independent dual-mic capture are not supported. Music speaker playback is
available in HiFi.

Unresolved DSP ownership keeps DMA and backends reserved until reboot.
Automatic DSP restart recovery, dual SIM and call recording are not supported.
