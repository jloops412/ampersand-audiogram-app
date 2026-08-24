import { KeyboardEvent, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import HoverPlugin from 'wavesurfer.js/dist/plugins/hover.js';
import RegionsPlugin, { type Region } from 'wavesurfer.js/dist/plugins/regions.js';
import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.js';

import type { WaveformPeaks } from './types';
import {
  MAX_AUDITION_SECONDS,
  MIN_AUDITION_SECONDS,
  type AuditionRange,
  type AuditionPlaybackState,
  type SourceSwitchSnapshot,
  auditionPlaybackAfterSeeking,
  auditionRangeAt,
  beginAuditionPlayback,
  clampPlaybackTime,
  normalizeAuditionRange,
  preserveSourceSwitchSnapshot,
  selectWaveformLevel,
  toWaveSurferPeaks,
  waveformDurationSeconds,
} from './waveformPeaks.js';

interface WaveformProps {
  waveform: WaveformPeaks | null;
  waveformError?: string;
  audioUrl: string;
  sourceLabel: string;
}

type PreparedWaveform = {
  duration: number;
  peaks: Float32Array[];
  samplesPerChannel: number;
};

type Preparation = { data: PreparedWaveform; error?: never } | { data?: never; error: string } | null;
type PlaybackTransitionSnapshot = { time: number; wasPlaying: boolean };

const useIsomorphicLayoutEffect = typeof window === 'undefined' ? useEffect : useLayoutEffect;

export function Waveform({ waveform, waveformError, audioUrl, sourceLabel }: WaveformProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const waveSurferRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<RegionsPlugin | null>(null);
  const regionRef = useRef<Region | null>(null);
  const selectionRef = useRef<AuditionRange | null>(null);
  const sourceLabelRef = useRef(sourceLabel);
  const loadedUrlRef = useRef('');
  const loadGenerationRef = useRef(0);
  const sourceSwitchRef = useRef<SourceSwitchSnapshot | null>(null);
  const auditionPlaybackRef = useRef<AuditionPlaybackState>({});
  const interactionsRef = useRef<{ enable: () => void; disable: () => void } | null>(null);
  const interactionReadyRef = useRef(false);
  const mediaWaitAbortRef = useRef<AbortController | null>(null);
  const playbackTransitionRef = useRef<PlaybackTransitionSnapshot | null>(null);
  const finePointerRef = useRef(true);
  const lastTimeUpdateRef = useRef(0);

  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [message, setMessage] = useState('Loading source timeline…');
  const [currentTime, setCurrentTime] = useState(0);
  const [zoom, setZoom] = useState(0);
  const [selection, setSelection] = useState<AuditionRange | null>(null);

  const preparation = useMemo<Preparation>(() => {
    if (!waveform) return null;
    try {
      const level = selectWaveformLevel(waveform);
      return {
        data: {
          duration: waveformDurationSeconds(waveform),
          peaks: toWaveSurferPeaks(waveform),
          samplesPerChannel: level.windows.length * 2,
        },
      };
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Waveform peak data is unavailable.' };
    }
  }, [waveform]);

  const prepared = preparation?.data;
  const nativeFallback = !prepared;
  const mediaElementKey = nativeFallback ? `native-fallback:${audioUrl}` : 'wavesurfer-media';
  sourceLabelRef.current = sourceLabel;

  useEffect(() => {
    selectionRef.current = selection;
  }, [selection]);

  useIsomorphicLayoutEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    return () => {
      const snapshot = {
        time: Number.isFinite(audio.currentTime) ? audio.currentTime : 0,
        wasPlaying: !audio.paused,
      };
      if (!playbackTransitionRef.current) playbackTransitionRef.current = snapshot;
      audio.pause();
    };
  }, [mediaElementKey]);

  useEffect(() => {
    if (!nativeFallback) return;
    const audio = audioRef.current;
    const snapshot = playbackTransitionRef.current;
    if (!audio || !snapshot) return;
    let cancelled = false;

    const restore = async () => {
      if (cancelled || audioRef.current !== audio) return;
      let resumeAt = 0;
      try {
        const duration = Number.isFinite(audio.duration) && audio.duration > 0 ? audio.duration : snapshot.time;
        resumeAt = duration > 0 ? clampPlaybackTime(snapshot.time, duration) : 0;
        audio.currentTime = resumeAt;
        setCurrentTime(resumeAt);
        if (!snapshot.wasPlaying) {
          if (playbackTransitionRef.current === snapshot) playbackTransitionRef.current = null;
          return;
        }
        await audio.play();
      } catch {
        if (cancelled || audioRef.current !== audio) return;
        if (playbackTransitionRef.current === snapshot) playbackTransitionRef.current = null;
        setMessage(`Audio restored at ${formatClock(resumeAt)}; press play to continue.`);
        return;
      }
      if (cancelled || audioRef.current !== audio) {
        audio.pause();
        return;
      }
      if (playbackTransitionRef.current === snapshot) playbackTransitionRef.current = null;
    };
    const onCanPlay = () => void restore();
    if (audio.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA) void restore();
    else audio.addEventListener('canplay', onCanPlay, { once: true });

    return () => {
      cancelled = true;
      audio.removeEventListener('canplay', onCanPlay);
    };
  }, [mediaElementKey, nativeFallback]);

  useEffect(() => {
    const container = containerRef.current;
    const audio = audioRef.current;
    if (!container || !audio || !prepared || !audioUrl) return;

    const initialAudioUrl = audioUrl;
    finePointerRef.current = !(window.matchMedia?.('(pointer: coarse)').matches ?? false);
    let cancelled = false;

    const regions = RegionsPlugin.create();
    const timeline = TimelinePlugin.create({
      height: 24,
      style: { color: '#8f9794', fontSize: '10px' },
      formatTimeCallback: formatClock,
    });
    const hover = HoverPlugin.create({
      lineColor: '#6becc5',
      labelBackground: '#111719',
      labelColor: '#f5f0e8',
      labelSize: 11,
      formatTimeCallback: formatClock,
    });
    const waveSurfer = WaveSurfer.create({
      container,
      media: audio,
      backend: 'MediaElement',
      height: 154,
      waveColor: '#9c805c',
      progressColor: '#d0ad79',
      cursorColor: '#6becc5',
      cursorWidth: 2,
      minPxPerSec: 0,
      fillParent: true,
      normalize: false,
      interact: false,
      dragToSeek: false,
      autoScroll: true,
      autoCenter: true,
      plugins: [regions, timeline, hover],
    });

    waveSurferRef.current = waveSurfer;
    regionsRef.current = regions;
    loadedUrlRef.current = audioUrl;
    interactionReadyRef.current = false;
    setStatus('loading');
    setMessage(`Rendering the ${sourceLabel.toLowerCase()} timeline and buffering private audio…`);

    const updateSelection = (region: Region) => {
      const next = normalizeAuditionRange(region.start, region.end, prepared.duration);
      if (Math.abs(region.start - next.start) > 0.001 || Math.abs(region.end - next.end) > 0.001) {
        region.setOptions({ start: next.start, end: next.end });
      }
      if (auditionPlaybackRef.current.end != null) {
        audio.pause();
        auditionPlaybackRef.current = {};
      }
      regionRef.current = region;
      selectionRef.current = next;
      setSelection(next);
    };
    const onRegionCreated = (region: Region) => {
      const previous = regionRef.current;
      if (previous && previous !== region) previous.remove();
      updateSelection(region);
    };
    const onRegionRemoved = (region: Region) => {
      if (regionRef.current !== region) return;
      regionRef.current = null;
      selectionRef.current = null;
      auditionPlaybackRef.current = {};
      setSelection(null);
    };
    const onRegionClicked = (region: Region, event: MouseEvent) => {
      event.stopPropagation();
      if (!interactionReadyRef.current) return;
      auditionPlaybackRef.current = {};
      waveSurfer.setTime(region.start);
      setCurrentTime(region.start);
    };

    let dragSelectionEnabled = false;
    let disableDragSelection = () => {};
    const enableInteractions = () => {
      waveSurfer.toggleInteraction(true);
      regionRef.current?.setOptions({ drag: finePointerRef.current, resize: finePointerRef.current });
      if (dragSelectionEnabled || !finePointerRef.current) return;
      disableDragSelection = regions.enableDragSelection(
        {
          color: 'rgba(107, 236, 197, .16)',
          content: 'Audition only',
          drag: true,
          resize: true,
          minLength: Math.min(MIN_AUDITION_SECONDS, prepared.duration),
          maxLength: Math.min(MAX_AUDITION_SECONDS, prepared.duration),
        },
        5,
      );
      dragSelectionEnabled = true;
    };
    const disableInteractions = () => {
      waveSurfer.toggleInteraction(false);
      regionRef.current?.setOptions({ drag: false, resize: false });
      disableDragSelection();
      disableDragSelection = () => {};
      dragSelectionEnabled = false;
    };
    const interactions = { enable: enableInteractions, disable: disableInteractions };
    interactionsRef.current = interactions;

    let timelineRendered = false;
    let mediaCanPlay = audio.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA;
    let initialReadyAnnounced = false;
    const announceInitialReady = () => {
      if (
        initialReadyAnnounced ||
        !timelineRendered ||
        !mediaCanPlay ||
        loadedUrlRef.current !== initialAudioUrl
      ) return;
      initialReadyAnnounced = true;
      interactionReadyRef.current = true;
      enableInteractions();
      setStatus('ready');
      const transitionSnapshot = playbackTransitionRef.current;
      if (!transitionSnapshot) {
        setMessage(`${sourceLabelRef.current} timeline rendered; private audio can play.`);
        return;
      }

      const resumeAt = clampPlaybackTime(transitionSnapshot.time, prepared.duration);
      waveSurfer.setTime(resumeAt);
      setCurrentTime(resumeAt);
      setMessage(`${sourceLabelRef.current} timeline rendered at ${formatClock(resumeAt)}; private audio can play.`);
      if (!transitionSnapshot.wasPlaying) {
        if (playbackTransitionRef.current === transitionSnapshot) playbackTransitionRef.current = null;
        return;
      }
      void waveSurfer.play().then(
        () => {
          if (cancelled || loadedUrlRef.current !== initialAudioUrl) return;
          if (playbackTransitionRef.current === transitionSnapshot) playbackTransitionRef.current = null;
        },
        () => {
          if (cancelled || loadedUrlRef.current !== initialAudioUrl) return;
          if (playbackTransitionRef.current === transitionSnapshot) playbackTransitionRef.current = null;
          setMessage(`${sourceLabelRef.current} audio can play at ${formatClock(resumeAt)}; press play to continue.`);
        },
      );
    };
    const onCanPlay = () => {
      mediaCanPlay = true;
      announceInitialReady();
    };
    const enforceAuditionEnd = () => {
      const auditionEnd = auditionPlaybackRef.current.end;
      if (auditionEnd == null || audio.currentTime < auditionEnd) return;
      audio.pause();
      audio.currentTime = auditionEnd;
      auditionPlaybackRef.current = {};
      setCurrentTime(auditionEnd);
    };
    const onVisibilityChange = () => {
      if (!document.hidden || auditionPlaybackRef.current.end == null) return;
      audio.pause();
      auditionPlaybackRef.current = {};
      setMessage('Audition paused because this tab is hidden.');
    };
    audio.addEventListener('canplay', onCanPlay);
    audio.addEventListener('timeupdate', enforceAuditionEnd);
    document.addEventListener('visibilitychange', onVisibilityChange);

    const unsubscribeCreated = regions.on('region-created', onRegionCreated);
    const unsubscribeUpdated = regions.on('region-updated', updateSelection);
    const unsubscribeRemoved = regions.on('region-removed', onRegionRemoved);
    const unsubscribeClicked = regions.on('region-clicked', onRegionClicked);
    const unsubscribeReady = waveSurfer.on('ready', () => {
      timelineRendered = true;
      announceInitialReady();
    });
    const unsubscribeTime = waveSurfer.on('timeupdate', (time) => {
      const now = performance.now();
      if (now - lastTimeUpdateRef.current < 200 && time < prepared.duration) return;
      lastTimeUpdateRef.current = now;
      setCurrentTime(time);
    });
    const unsubscribeSeeking = waveSurfer.on('seeking', (time) => {
      auditionPlaybackRef.current = auditionPlaybackAfterSeeking(auditionPlaybackRef.current, time);
      setCurrentTime(time);
    });
    const unsubscribeFinish = waveSurfer.on('finish', () => {
      auditionPlaybackRef.current = {};
      setCurrentTime(prepared.duration);
    });
    const unsubscribePause = waveSurfer.on('pause', () => {
      auditionPlaybackRef.current = {};
    });
    const unsubscribeError = waveSurfer.on('error', (error) => {
      interactionReadyRef.current = false;
      disableInteractions();
      setStatus('error');
      setMessage(error.message || 'The private audio stream could not be loaded.');
    });

    // Loading explicitly avoids WaveSurfer's deferred constructor auto-load, which can outlive
    // a React StrictMode cleanup and resurrect a destroyed instance.
    void waveSurfer.load(audioUrl, prepared.peaks, prepared.duration).catch(() => {});

    return () => {
      cancelled = true;
      loadGenerationRef.current += 1;
      mediaWaitAbortRef.current?.abort();
      mediaWaitAbortRef.current = null;
      disableInteractions();
      audio.removeEventListener('canplay', onCanPlay);
      audio.removeEventListener('timeupdate', enforceAuditionEnd);
      document.removeEventListener('visibilitychange', onVisibilityChange);
      unsubscribeCreated();
      unsubscribeUpdated();
      unsubscribeRemoved();
      unsubscribeClicked();
      unsubscribeReady();
      unsubscribeTime();
      unsubscribeSeeking();
      unsubscribeFinish();
      unsubscribePause();
      unsubscribeError();
      waveSurfer.destroy();
      audio.pause();
      audio.removeAttribute('src');
      audio.load();
      waveSurferRef.current = null;
      regionsRef.current = null;
      regionRef.current = null;
      loadedUrlRef.current = '';
      sourceSwitchRef.current = null;
      interactionReadyRef.current = false;
      auditionPlaybackRef.current = {};
      selectionRef.current = null;
      setSelection(null);
      setZoom(0);
      if (interactionsRef.current === interactions) interactionsRef.current = null;
    };
  }, [prepared]);

  useEffect(() => {
    const waveSurfer = waveSurferRef.current;
    const audio = audioRef.current;
    if (!waveSurfer || !audio || !prepared || !audioUrl || loadedUrlRef.current === audioUrl) return;
    const generation = ++loadGenerationRef.current;
    mediaWaitAbortRef.current?.abort();
    const mediaWaitController = new AbortController();
    mediaWaitAbortRef.current = mediaWaitController;
    const transitionSnapshot = playbackTransitionRef.current;
    const preserved = preserveSourceSwitchSnapshot(
      sourceSwitchRef.current,
      transitionSnapshot?.time ?? waveSurfer.getCurrentTime(),
      prepared.duration,
      transitionSnapshot?.wasPlaying ?? waveSurfer.isPlaying(),
      transitionSnapshot ? undefined : auditionPlaybackRef.current.end,
    );
    sourceSwitchRef.current = preserved;
    interactionReadyRef.current = false;
    interactionsRef.current?.disable();
    const { resumeAt, wasPlaying, auditionEnd } = preserved;
    loadedUrlRef.current = audioUrl;
    setStatus('loading');
    setMessage(`Rendering the ${sourceLabel.toLowerCase()} timeline and buffering audio…`);

    void (async () => {
      try {
        await waveSurfer.load(audioUrl, prepared.peaks, prepared.duration);
        await waitForMediaCanPlay(audio, audioUrl, mediaWaitController.signal);
        if (generation !== loadGenerationRef.current) return;
        interactionReadyRef.current = true;
        interactionsRef.current?.enable();
        auditionPlaybackRef.current = auditionEnd && resumeAt < auditionEnd
          ? beginAuditionPlayback({ start: resumeAt, end: auditionEnd })
          : {};
        waveSurfer.setTime(resumeAt);
        setCurrentTime(resumeAt);
        setStatus('ready');
        setMessage(`${sourceLabel} timeline rendered at ${formatClock(resumeAt)}; private audio can play.`);
        if (!wasPlaying) {
          auditionPlaybackRef.current = {};
          sourceSwitchRef.current = null;
          if (playbackTransitionRef.current === transitionSnapshot) playbackTransitionRef.current = null;
          return;
        }
        try {
          await waveSurfer.play(undefined, auditionEnd && resumeAt < auditionEnd ? auditionEnd : undefined);
        } catch {
          if (generation !== loadGenerationRef.current) return;
          auditionPlaybackRef.current = {};
          sourceSwitchRef.current = null;
          if (playbackTransitionRef.current === transitionSnapshot) playbackTransitionRef.current = null;
          setMessage(`${sourceLabel} audio can play at ${formatClock(resumeAt)}; press play to continue.`);
          return;
        }
        if (generation !== loadGenerationRef.current) return;
        sourceSwitchRef.current = null;
        if (playbackTransitionRef.current === transitionSnapshot) playbackTransitionRef.current = null;
      } catch (error: unknown) {
        if (generation !== loadGenerationRef.current) return;
        loadedUrlRef.current = '';
        sourceSwitchRef.current = null;
        if (playbackTransitionRef.current === transitionSnapshot) playbackTransitionRef.current = null;
        interactionReadyRef.current = false;
        auditionPlaybackRef.current = {};
        setStatus('error');
        setMessage(
          error instanceof Error && error.name !== 'AbortError'
            ? error.message
            : 'The private audio stream could not be switched.',
        );
      } finally {
        if (mediaWaitAbortRef.current === mediaWaitController) mediaWaitAbortRef.current = null;
      }
    })();
  }, [audioUrl, prepared, sourceLabel]);

  const replaceSelection = (next: AuditionRange) => {
    const regions = regionsRef.current;
    if (!regions || !prepared || status !== 'ready') return;
    const bounded = normalizeAuditionRange(next.start, next.end, prepared.duration);
    if (auditionPlaybackRef.current.end != null) waveSurferRef.current?.pause();
    auditionPlaybackRef.current = {};
    regionRef.current?.remove();
    const region = regions.addRegion({
      id: 'audition-selection',
      start: bounded.start,
      end: bounded.end,
      color: 'rgba(107, 236, 197, .16)',
      content: 'Audition only',
      drag: finePointerRef.current,
      resize: finePointerRef.current,
      minLength: Math.min(MIN_AUDITION_SECONDS, prepared.duration),
      maxLength: Math.min(MAX_AUDITION_SECONDS, prepared.duration),
    });
    regionRef.current = region;
    selectionRef.current = bounded;
    setSelection(bounded);
  };

  const setAuditionAtPlayhead = () => {
    const waveSurfer = waveSurferRef.current;
    if (!waveSurfer || !prepared) return;
    replaceSelection(auditionRangeAt(waveSurfer.getCurrentTime(), prepared.duration));
  };

  const setIn = () => {
    const waveSurfer = waveSurferRef.current;
    if (!waveSurfer || !prepared) return;
    const time = waveSurfer.getCurrentTime();
    const next = selection
      ? normalizeAuditionRange(time, Math.max(time + MIN_AUDITION_SECONDS, selection.end), prepared.duration)
      : auditionRangeAt(time, prepared.duration);
    replaceSelection(next);
  };

  const setOut = () => {
    const waveSurfer = waveSurferRef.current;
    if (!waveSurfer || !prepared) return;
    const time = waveSurfer.getCurrentTime();
    replaceSelection(
      selection
        ? normalizeAuditionRange(selection.start, time, prepared.duration)
        : normalizeAuditionRange(Math.max(0, time - 10), time, prepared.duration),
    );
  };

  const updateBoundary = (boundary: 'start' | 'end', value: number) => {
    if (!selection || !prepared || !Number.isFinite(value)) return;
    const next = normalizeAuditionRange(
      boundary === 'start' ? value : selection.start,
      boundary === 'end' ? value : selection.end,
      prepared.duration,
    );
    replaceSelection(next);
  };

  const playSelection = async () => {
    const waveSurfer = waveSurferRef.current;
    if (!waveSurfer || !selection || status !== 'ready') return;
    auditionPlaybackRef.current = beginAuditionPlayback(selection);
    setMessage(`Playing audition from ${formatClock(selection.start)} to ${formatClock(selection.end)}.`);
    try {
      await waveSurfer.play(selection.start, selection.end);
    } catch {
      auditionPlaybackRef.current = {};
      setMessage('Playback was blocked. Use the native play control and try again.');
    }
  };

  const clearSelection = () => {
    if (auditionPlaybackRef.current.end != null) waveSurferRef.current?.pause();
    auditionPlaybackRef.current = {};
    regionRef.current?.remove();
  };

  const changeZoom = (nextZoom: number) => {
    if (status !== 'ready') return;
    const bounded = Math.max(0, Math.min(80, nextZoom));
    setZoom(bounded);
    waveSurferRef.current?.zoom(bounded);
  };

  const handleTimelineKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const waveSurfer = waveSurferRef.current;
    if (!waveSurfer || !prepared || status !== 'ready') return;
    if (event.key === ' ' || event.key.toLowerCase() === 'k') {
      event.preventDefault();
      auditionPlaybackRef.current = {};
      void waveSurfer.playPause().catch(() => setMessage('Playback was blocked. Use the native play control and try again.'));
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      auditionPlaybackRef.current = {};
      waveSurfer.skip(-5);
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      auditionPlaybackRef.current = {};
      waveSurfer.skip(5);
    } else if (event.key === 'Home') {
      event.preventDefault();
      auditionPlaybackRef.current = {};
      waveSurfer.setTime(0);
    } else if (event.key === 'End') {
      event.preventDefault();
      auditionPlaybackRef.current = {};
      waveSurfer.setTime(prepared.duration);
    }
  };

  const fallbackIssue = preparation?.error || waveformError;
  const fallbackMessage = fallbackIssue || (!waveform ? 'Loading precomputed source peaks…' : null);

  return (
    <div className="waveform-shell">
      <div className="waveform-meta">
        <div>
          <strong>Source timeline</strong>
          <small>
            {prepared
              ? `${waveform?.channels ?? 0} channel${waveform?.channels === 1 ? '' : 's'} · ${prepared.samplesPerChannel.toLocaleString()} precomputed samples/channel`
              : fallbackMessage}
          </small>
        </div>
        <output aria-label="Current timeline position">{formatClock(currentTime)}</output>
      </div>

      {prepared ? (
        <div
          ref={containerRef}
          className="waveform-stage"
          role="group"
          tabIndex={0}
          aria-label="Interactive source waveform. Space or K toggles playback; left and right arrows seek five seconds; Home and End seek to the boundaries."
          onKeyDown={handleTimelineKeyDown}
        />
      ) : (
        <div className="waveform-fallback" role="status">{fallbackMessage}</div>
      )}

      <div className="waveform-toolbar">
        <label className="waveform-zoom">
          <span>Timeline zoom</span>
          <input
            type="range"
            min="0"
            max="80"
            step="5"
            value={zoom}
            disabled={!prepared || status !== 'ready'}
            onChange={(event) => changeZoom(Number(event.target.value))}
            aria-valuetext={zoom === 0 ? 'Fit entire timeline' : `${zoom} pixels per second`}
          />
          <output>{zoom === 0 ? 'Fit' : `${zoom} px/s`}</output>
        </label>
        <button type="button" className="button button-secondary button-compact" disabled={!prepared || status !== 'ready' || zoom === 0} onClick={() => changeZoom(0)}>Fit timeline</button>
      </div>

      <div className="audition-panel">
        <div className="audition-copy">
          <strong>Audition only</strong>
          <small>Drag with a mouse, or use the controls on any device. This does not change, trim, or re-render exports.</small>
        </div>
        <div className="audition-actions">
          <button type="button" onClick={setAuditionAtPlayhead} disabled={!prepared || status !== 'ready'}>Set 10s here</button>
          <button type="button" onClick={setIn} disabled={!prepared || status !== 'ready'}>Set in</button>
          <button type="button" onClick={setOut} disabled={!prepared || status !== 'ready'}>Set out</button>
          <button type="button" className="selected" onClick={() => void playSelection()} disabled={!selection || status !== 'ready'}>Play selection</button>
          <button type="button" onClick={clearSelection} disabled={!selection}>Clear</button>
        </div>
        {selection && prepared && (
          <div className="audition-bounds">
            <label>In <input type="number" min="0" max={prepared.duration} step="0.1" value={roundTenths(selection.start)} disabled={status !== 'ready'} onChange={(event) => updateBoundary('start', Number(event.target.value))} /></label>
            <span>→</span>
            <label>Out <input type="number" min="0" max={prepared.duration} step="0.1" value={roundTenths(selection.end)} disabled={status !== 'ready'} onChange={(event) => updateBoundary('end', Number(event.target.value))} /></label>
            <small>{(selection.end - selection.start).toFixed(1)}s</small>
          </div>
        )}
      </div>

      <audio
        key={mediaElementKey}
        ref={audioRef}
        src={nativeFallback ? audioUrl : undefined}
        controls
        preload={nativeFallback ? 'metadata' : 'auto'}
        aria-label={`${sourceLabel} audio`}
      />
      <p className={`waveform-status ${status === 'error' || fallbackIssue ? 'error' : ''}`} role="status" aria-live="polite">
        {fallbackIssue ? `${fallbackIssue} Native audio playback remains available.` : message}
      </p>
    </div>
  );
}

function roundTenths(value: number): number {
  return Math.round(value * 10) / 10;
}

function formatClock(seconds: number): string {
  const safe = Number.isFinite(seconds) ? Math.max(0, seconds) : 0;
  const whole = Math.floor(safe);
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  const remainder = whole % 60;
  return hours
    ? `${hours}:${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
    : `${minutes}:${String(remainder).padStart(2, '0')}`;
}

function waitForMediaCanPlay(audio: HTMLAudioElement, expectedUrl: string, signal: AbortSignal): Promise<void> {
  const expected = new URL(expectedUrl, document.baseURI).href;
  const sourceMatches = () => (audio.currentSrc || audio.src) === expected;
  if (audio.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA && sourceMatches()) return Promise.resolve();

  return new Promise((resolve, reject) => {
    const cleanup = () => {
      audio.removeEventListener('canplay', onCanPlay);
      audio.removeEventListener('error', onError);
      signal.removeEventListener('abort', onAbort);
    };
    const onCanPlay = () => {
      if (!sourceMatches()) return;
      cleanup();
      resolve();
    };
    const onError = () => {
      cleanup();
      reject(audio.error || new Error('The private audio stream could not be loaded.'));
    };
    const onAbort = () => {
      cleanup();
      reject(new DOMException('Media readiness wait was aborted.', 'AbortError'));
    };

    audio.addEventListener('canplay', onCanPlay);
    audio.addEventListener('error', onError);
    signal.addEventListener('abort', onAbort, { once: true });
    if (signal.aborted) onAbort();
  });
}
