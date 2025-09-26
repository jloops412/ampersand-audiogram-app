import type { CustomizationOptions, TranscriptCue } from '../types';
import { WaveformStyle } from '../types';

interface GenerateVideoParams {
  audioFile: File;
  backgroundImageFile: File | null;
  options: CustomizationOptions;
  transcriptCues: TranscriptCue[] | null;
  canvasElement: HTMLCanvasElement;
  onProgress: (progress: number) => void;
}

interface Particle {
    x: number;
    y: number;
    vx: number;
    vy: number;
    life: number;
    size: number;
}
let particles: Particle[] = [];

// Helper to convert hex color to rgba
function hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Helper to draw wrapped text on canvas
function drawWrappedText(
    ctx: CanvasRenderingContext2D, 
    text: string, 
    x: number, 
    y: number, 
    maxWidth: number, 
    lineHeight: number
) {
    const words = text.split(' ');
    let line = '';
    const lines = [];

    for (let n = 0; n < words.length; n++) {
        const testLine = line + words[n] + ' ';
        const metrics = ctx.measureText(testLine);
        const testWidth = metrics.width;
        if (testWidth > maxWidth && n > 0) {
            lines.push(line);
            line = words[n] + ' ';
        } else {
            line = testLine;
        }
    }
    lines.push(line);

    // Adjust y position for vertical alignment
    let startY = y;
    if (ctx.textBaseline === 'middle') {
      startY -= ((lines.length - 1) * lineHeight) / 2;
    } else if (ctx.textBaseline === 'bottom') {
      startY -= (lines.length - 1) * lineHeight;
    }

    lines.forEach((l, i) => {
        ctx.fillText(l.trim(), x, startY + (i * lineHeight));
    });
}

export async function generateVideo({
  audioFile,
  backgroundImageFile,
  options,
  transcriptCues,
  canvasElement,
  onProgress,
}: GenerateVideoParams): Promise<Blob> {
  const audioContext = new AudioContext();
  const processedAudioBuffer = await audioFile.arrayBuffer().then(buffer => audioContext.decodeAudioData(buffer));
  
  // --- REAL-TIME RENDERING ---
  const audioSource = audioContext.createBufferSource();
  audioSource.buffer = processedAudioBuffer;

  const analyser = audioContext.createAnalyser();
  analyser.fftSize = 2048;
  analyser.smoothingTimeConstant = 0.7;
  const frequencyData = new Uint8Array(analyser.frequencyBinCount);
  const timeDomainData = new Uint8Array(analyser.fftSize);

  const canvasStream = canvasElement.captureStream(30);
  const audioDestination = audioContext.createMediaStreamDestination();
  
  audioSource.connect(analyser);
  audioSource.connect(audioDestination);
  
  const [audioTrack] = audioDestination.stream.getAudioTracks();
  const [videoTrack] = canvasStream.getVideoTracks();
  const combinedStream = new MediaStream([videoTrack, audioTrack]);

  const recorder = new MediaRecorder(combinedStream, { mimeType: 'video/webm; codecs=vp9' });
  const chunks: Blob[] = [];
  recorder.ondataavailable = (event) => {
    if (event.data.size > 0) chunks.push(event.data);
  };
  
  particles = [];

  return new Promise((resolve, reject) => {
    const ctx = canvasElement.getContext('2d');
    if (!ctx) return reject(new Error('Could not get canvas context'));

    const bgImage = new Image();
    bgImage.crossOrigin = "anonymous";
    let bgReady = !backgroundImageFile;
    if (backgroundImageFile) {
        bgImage.onload = () => { bgReady = true; };
        bgImage.src = URL.createObjectURL(backgroundImageFile);
    }
    
    const drawFrame = () => {
      const animationClock = audioContext.currentTime;

      if (audioContext.state === 'closed' || animationClock > processedAudioBuffer.duration + 0.1) {
        return;
      }
      
      requestAnimationFrame(drawFrame);
      
      ctx.fillStyle = options.backgroundColor;
      ctx.fillRect(0, 0, canvasElement.width, canvasElement.height);

      if (backgroundImageFile && bgReady) {
        ctx.drawImage(bgImage, 0, 0, canvasElement.width, canvasElement.height);
      }
      
      const waveformRgbaColor = hexToRgba(options.waveformColor, options.waveformOpacity);
      ctx.fillStyle = waveformRgbaColor;
      ctx.strokeStyle = waveformRgbaColor;
      ctx.lineCap = options.lineCap;

      const centerX = canvasElement.width / 2;
      let centerY;

      switch (options.waveformPosition) {
          case 'top': centerY = canvasElement.height * 0.25; break;
          case 'bottom': centerY = canvasElement.height * 0.75; break;
          default: centerY = canvasElement.height / 2;
      }
      
      if ([WaveformStyle.Circle, WaveformStyle.Radial, WaveformStyle.Particles, WaveformStyle.Equalizer].includes(options.waveformStyle)) {
            centerY = canvasElement.height / 2;
      }
      
      switch (options.waveformStyle) {
        case WaveformStyle.Line:
        case WaveformStyle.MirroredLine: {
            analyser.getByteTimeDomainData(timeDomainData);
            ctx.lineWidth = options.lineWidth;
            ctx.beginPath();
            
            const sliceWidth = canvasElement.width * 1.0 / analyser.fftSize;
            let x = 0;

            for (let i = 0; i < analyser.fftSize; i++) {
                const v = (timeDomainData[i] - 128) / 128.0;
                const y = centerY - (v * options.amplitude);

                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
                x += sliceWidth;
            }
            ctx.stroke();

            if (options.waveformStyle === WaveformStyle.MirroredLine) {
                ctx.beginPath();
                x = 0;
                for (let i = 0; i < analyser.fftSize; i++) {
                    const v = (timeDomainData[i] - 128) / 128.0;
                    const y = centerY + (v * options.amplitude);
                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                    x += sliceWidth;
                }
                ctx.stroke();
            }
            break;
        }
        case WaveformStyle.Bars:
        case WaveformStyle.Equalizer:
          analyser.getByteFrequencyData(frequencyData);
          const barPlusSpacing = options.barWidth + options.barSpacing;
          const totalBarWidth = options.barCount * barPlusSpacing;
          const startX = centerX - totalBarWidth / 2;
          const spectrumWidth = analyser.frequencyBinCount * 0.9;
          
          for (let i = 0; i < options.barCount; i++) {
            const dataIndex = Math.floor((i / options.barCount) * spectrumWidth);
            const barHeight = (frequencyData[dataIndex] / 255) * options.amplitude * 2.5;
            const x = startX + i * barPlusSpacing;
            if (options.waveformStyle === WaveformStyle.Bars) {
                ctx.fillRect(x, centerY - barHeight / 2, options.barWidth, barHeight);
            } else {
                ctx.fillRect(x, canvasElement.height - barHeight, options.barWidth, barHeight);
            }
          }
          break;
        case WaveformStyle.Circle:
          analyser.getByteFrequencyData(frequencyData);
          ctx.lineWidth = options.lineWidth;
          const points = 360;
          const spectrumPoints = Math.floor(frequencyData.length * 0.5);
          for (let i = 0; i < points; i++) {
            const mirrorI = i > 180 ? 360 - i : i;
            const dataIndex = Math.floor((mirrorI / 180) * spectrumPoints);
            const amplitude = (frequencyData[dataIndex] / 255) * options.amplitude;
            const angle = (i - 90) * (Math.PI / 180);
            const x1 = centerX + options.circleRadius * Math.cos(angle);
            const y1 = centerY + options.circleRadius * Math.sin(angle);
            const x2 = centerX + (options.circleRadius + amplitude) * Math.cos(angle);
            const y2 = centerY + (options.circleRadius + amplitude) * Math.sin(angle);
            ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
          }
          break;
        case WaveformStyle.Bricks:
            analyser.getByteFrequencyData(frequencyData);
            const brickFullWidth = (canvasElement.width / options.brickCount);
            const brickWidth = brickFullWidth - options.brickSpacing;
            const brickFullHeight = options.brickHeight + options.brickSpacing;
            const spectrumSlice = Math.floor(analyser.frequencyBinCount * 0.8 / options.brickCount);
            for(let i=0; i<options.brickCount; i++){
                const dataIndex = i * spectrumSlice;
                const brickValue = frequencyData[dataIndex] / 255;
                const numBricks = Math.floor(brickValue * options.amplitude / brickFullHeight);
                const x = i * brickFullWidth;
                for(let j=0; j < numBricks; j++){
                    const y = centerY - (j * brickFullHeight) - brickFullHeight/2;
                    ctx.globalAlpha = 1 - (j / (options.amplitude / brickFullHeight));
                    ctx.fillRect(x, y, brickWidth, options.brickHeight);
                }
            }
            ctx.globalAlpha = 1;
            break;
        case WaveformStyle.Radial:
            analyser.getByteFrequencyData(frequencyData);
            ctx.lineWidth = options.lineWidth;
            const spokeSpectrum = Math.floor(frequencyData.length * 0.6);
            for(let i=0; i < options.spokeCount; i++){
                const angle = (i / options.spokeCount) * Math.PI * 2;
                const dataIndex = Math.floor((i % (options.spokeCount / 2)) / (options.spokeCount / 2) * spokeSpectrum);
                const amplitude = (frequencyData[dataIndex] / 255) * options.amplitude;
                const x1 = centerX + options.innerRadius * Math.cos(angle);
                const y1 = centerY + options.innerRadius * Math.sin(angle);
                const x2 = centerX + (options.innerRadius + amplitude) * Math.cos(angle);
                const y2 = centerY + (options.innerRadius + amplitude) * Math.sin(angle);
                ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2, y2); ctx.stroke();
            }
            break;
        case WaveformStyle.Particles:
            analyser.getByteFrequencyData(frequencyData);
            particles.forEach((p, index) => {
                p.x += p.vx; p.y += p.vy; p.life -= 1;
                if(p.life <= 0) particles.splice(index, 1);
                ctx.globalAlpha = p.life / 100;
                ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2); ctx.fill();
            });
            ctx.globalAlpha = 1;
            let totalEnergy = frequencyData.reduce((sum, val) => sum + val, 0) / frequencyData.length;
            const particlesToEmit = (totalEnergy / 255) * 5;
            for(let i=0; i < particlesToEmit; i++){
                if(particles.length < options.particleCount){
                    const angle = Math.random() * Math.PI * 2;
                    const speed = (Math.random() * options.particleSpeed) + 0.5;
                    particles.push({ x: centerX, y: centerY, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed, life: 100, size: Math.random() * options.particleSize + 1 });
                }
            }
            break;
      }
      
      const currentCue = transcriptCues?.find(cue => animationClock >= cue.startTime && animationClock < cue.endTime);
      const textToDraw = currentCue ? currentCue.text : options.overlayText;

      if (textToDraw) {
        ctx.fillStyle = options.fontColor;
        ctx.font = `${options.fontSize}px "${options.fontFamily}"`;
        ctx.textAlign = options.textAlign;

        const padding = 60;
        let x: number;
        if (options.textAlign === 'left') x = padding;
        else if (options.textAlign === 'right') x = canvasElement.width - padding;
        else x = canvasElement.width / 2;
        let y: number;
        if (options.textPosition === 'top') { y = padding; ctx.textBaseline = 'top'; } 
        else if (options.textPosition === 'bottom') { y = canvasElement.height - padding; ctx.textBaseline = 'bottom'; } 
        else { y = canvasElement.height / 2; ctx.textBaseline = 'middle'; }

        const maxWidth = canvasElement.width - (padding * 2);
        const lineHeight = options.fontSize * 1.2;
        drawWrappedText(ctx, textToDraw, x, y, maxWidth, lineHeight);
      }

      onProgress(Math.min(100, (animationClock / processedAudioBuffer.duration) * 100));
    };
    
    recorder.onstop = () => {
      const videoBlob = new Blob(chunks, { type: 'video/webm' });
      resolve(videoBlob);
      if (backgroundImageFile) URL.revokeObjectURL(bgImage.src);
      if (audioContext.state !== 'closed') {
        audioContext.close().catch(console.error);
      }
    };

    audioSource.onended = () => {
        setTimeout(() => {
          if (recorder.state === 'recording') {
            recorder.stop();
          }
        }, 100);
    };

    const startProcess = async () => {
        if (!bgReady) {
            setTimeout(startProcess, 100);
            return;
        }
        
        await document.fonts.load(`${options.fontSize}px "${options.fontFamily}"`);
        
        recorder.start();
        audioSource.start();
        requestAnimationFrame(drawFrame);
    };
    startProcess();
  });
}
