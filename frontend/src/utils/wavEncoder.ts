/**
 * WAV Encoder Utility
 * Converts raw PCM audio data to WAV format with proper headers
 */

/**
 * Encodes raw PCM audio data into WAV format
 * @param samples Float32Array of audio samples (-1.0 to 1.0)
 * @param sampleRate Sample rate in Hz (e.g., 48000, 44100)
 * @returns Blob containing WAV file data
 */
export function encodeWAV(samples: Float32Array, sampleRate: number): Blob {
  const buffer = encodeWAVBuffer(samples, sampleRate);
  return new Blob([buffer], { type: 'audio/wav' });
}

/**
 * Creates a WAV file buffer from audio samples
 * @param samples Float32Array of audio samples
 * @param sampleRate Sample rate in Hz
 * @returns ArrayBuffer containing complete WAV file
 */
function encodeWAVBuffer(samples: Float32Array, sampleRate: number): ArrayBuffer {
  // Convert float samples to 16-bit PCM
  const length = samples.length;
  const buffer = new ArrayBuffer(44 + length * 2);
  const view = new DataView(buffer);

  // Write WAV header
  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  // RIFF chunk descriptor
  writeString(0, 'RIFF');
  view.setUint32(4, 36 + length * 2, true); // File size - 8
  writeString(8, 'WAVE');

  // fmt sub-chunk
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
  view.setUint16(20, 1, true); // AudioFormat (1 for PCM)
  view.setUint16(22, 1, true); // NumChannels (1 for mono)
  view.setUint32(24, sampleRate, true); // SampleRate
  view.setUint32(28, sampleRate * 2, true); // ByteRate (SampleRate * NumChannels * BitsPerSample/8)
  view.setUint16(32, 2, true); // BlockAlign (NumChannels * BitsPerSample/8)
  view.setUint16(34, 16, true); // BitsPerSample

  // data sub-chunk
  writeString(36, 'data');
  view.setUint32(40, length * 2, true); // Subchunk2Size

  // Convert float samples to 16-bit PCM
  let offset = 44;
  for (let i = 0; i < length; i++) {
    const sample = Math.max(-1, Math.min(1, samples[i])); // Clamp between -1 and 1
    const int16 = sample < 0 ? sample * 0x8000 : sample * 0x7FFF; // Convert to 16-bit integer
    view.setInt16(offset, int16, true);
    offset += 2;
  }

  return buffer;
}

/**
 * Merges multiple audio buffers into a single buffer
 * @param buffers Array of Float32Arrays to merge
 * @returns Single Float32Array containing all audio data
 */
export function mergeBuffers(buffers: Float32Array[]): Float32Array {
  let length = 0;
  buffers.forEach(buffer => {
    length += buffer.length;
  });

  const result = new Float32Array(length);
  let offset = 0;
  buffers.forEach(buffer => {
    result.set(buffer, offset);
    offset += buffer.length;
  });

  return result;
}

/**
 * Downsamples audio data to a target sample rate
 * @param buffer Original audio buffer
 * @param originalRate Original sample rate
 * @param targetRate Target sample rate
 * @returns Downsampled audio buffer
 */
export function downsampleBuffer(
  buffer: Float32Array,
  originalRate: number,
  targetRate: number
): Float32Array {
  if (originalRate === targetRate) {
    return buffer;
  }

  const sampleRateRatio = originalRate / targetRate;
  const newLength = Math.round(buffer.length / sampleRateRatio);
  const result = new Float32Array(newLength);

  let offsetResult = 0;
  let offsetBuffer = 0;

  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
    let accum = 0;
    let count = 0;

    for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
      accum += buffer[i];
      count++;
    }

    result[offsetResult] = accum / count;
    offsetResult++;
    offsetBuffer = nextOffsetBuffer;
  }

  return result;
}

/**
 * Creates an audio context with fallback for different browsers
 */
export function createAudioContext(): AudioContext {
  const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
  return new AudioContextClass();
}