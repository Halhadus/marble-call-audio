# Reverse engineering the voice path

The firmware profile contains RX/TX graph configuration and calibration
captured from a vendor Android audio stack.

## Capture

1. Identify the audio process owning the GPR device by matching open file
   descriptors. Record idle, handset, output-switch and hangup mixer states.
2. Trace GPR packet writes and decode header size, packet size, domains,
   source/destination ports, token and opcode. Correlate reply status when
   capturing responses.
3. For commands using shared memory, instrument the userspace message builder
   and shared-memory allocation path. Copy the payload while its allocation
   is live, using the mapped handle and address association. A syscall trace
   alone contains no out-of-band graph or calibration bytes.
4. Check library build IDs and instruction fingerprints before attaching
   hooks. Validate packet/payload sizes and hashes; reject missing shared
   memory associations. Offsets from one vendor build are not portable.
5. Decode APM parameter headers, nested graph records and command ordering.
   Preserve unknown module properties and calibration bodies as opaque bytes.

The kernel allocates fresh GPR client ports, DMA addresses and memory-map
handles for each session; their captured values are not replayed.

## Findings

The initial pair contains five voice subgraphs plus hardware/adaptation
subgraphs, 60 declared module instances, shared containers, data connections
and control links. GRAPH_OPEN associates decoder, encoder, mailbox and
Smart Sync instances with VCPM. Subsequent commands set the session VSID,
TX processing channels and calibration keys.

Five persistent calibration tables belong to the initial RX/TX pair.
Their complete bytes are retained, including internal sections not covered
by the public table header. Matching a module ID in firmware does not prove
calibration compatibility with another firmware build.

RX uses a tertiary TDM sink at 96 kHz with 32-bit samples, four slots and
three DSP channels. The physical amplifier PCM negotiates two channels.
TX uses CODEC DMA at 48 kHz, 16 bits and two channels with decimator mask
`0xa`. Processing rates and physical bus rates are separate fields.
The raw voice endpoint owns TDM BCLK; the machine driver retains the LPASS
clock vote without making a competing host BCLK request.

The sequence configures and starts RX before the final TX endpoint setup,
then starts TX and sends the final module/calibration-key updates. That order
is preserved. Both graphs must stop before calibration or physical ports are
released. Unacknowledged commands keep their DMA resources owned.

The capture also contains an A-to-B-to-A device-processing graph transition.
Those alternate graphs are not selected by the supplied handset profile.
Their presence alone does not identify the associated user-visible routes.
External data/control peers are retained as captured; successful graph
acceptance on the target is not proof that all vendor processing is reproduced.

## Physical route and policy

The board shares its top amplifier between loudspeaker and receiver through
GPIO52. Receiver mode therefore needs the GPIO, the top Receiver profile and
a separately muted bottom amplifier. Codec profile gains must survive
Music/Receiver transitions without a call-start volume reset.

The working primary TX route sends ADC1/SWR_MIC0 to both DEC1 and DEC3.
The secondary ADC route is not enabled. The graph and calibration remain
two-channel; independent microphone processing has not been established.

Audio-server discovery selects UCM verbs and probes PCMs before a call.
Voice cannot start in the verb EnableSequence. The call microphone requests
startup after its routes are configured, while a silent timed PCM gives the
existing policy stack a sink/source lifetime without a second media graph.

## Public references

- [APM subgraphs and VSID](https://github.com/AudioReach/audioreach-engine/blob/184997fcea8d69066413b3fab917005188f5d6a3/fwk/api/apm/apm_sub_graph_api.h)
- [APM module and connection API](https://github.com/AudioReach/audioreach-engine/blob/184997fcea8d69066413b3fab917005188f5d6a3/fwk/api/apm/apm_module_api.h)
- [VCPM API](https://github.com/AudioReach/audioreach-engine/blob/184997fcea8d69066413b3fab917005188f5d6a3/fwk/api/vcpm/vcpm_api.h)
- [Mailbox API](https://github.com/AudioReach/audioreach-graphservices/blob/50ed44f2d72d61a9242c6bb08443267a8f9f3f4e/spf/api/modules/mailbox_api.h)
- [TDM API](https://github.com/AudioReach/audioreach-graphservices/blob/50ed44f2d72d61a9242c6bb08443267a8f9f3f4e/spf/api/modules/pcm_tdm_api.h)
- [Control intents](https://github.com/AudioReach/audioreach-graphservices/blob/50ed44f2d72d61a9242c6bb08443267a8f9f3f4e/spf/api/modules/imcl_fwk_intent_api.h)
- [ASoC DPCM](https://docs.kernel.org/sound/soc/dpcm.html)
- [ALSA UCM configuration](https://www.alsa-project.org/alsa-doc/alsa-lib/group__ucm__conf.html)
